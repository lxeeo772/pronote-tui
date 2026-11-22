from __future__ import annotations
import socket
import json
import requests
import pronotepy
import pronotepy.ent
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pronotepy.ent.generic_func import _open_ent_ng_edu, _open_ent_ng
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional
from .data_provider import (
    DataProvider, StudentProfile, GradeItem, SubjectAverage,
    OverallAverage, LessonItem, HomeworkItem, AbsenceItem, PunishmentItem
)
from .config import normalize_pronote_url

# ==============================================================================
# Global Network Timeout Setup
# Ensures no HTTP request inside requests, pronotepy, or ENT scrapers can hang.
# ==============================================================================
DEFAULT_TIMEOUT_SECONDS = 12.0

def install_network_timeouts(timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
    socket.setdefaulttimeout(timeout_seconds)
    _orig_request = requests.Session.request

    def _timeout_request(self, method, url, **kwargs):
        if "timeout" not in kwargs or kwargs["timeout"] is None:
            kwargs["timeout"] = timeout_seconds
        return _orig_request(self, method, url, **kwargs)

    requests.Session.request = _timeout_request

install_network_timeouts(DEFAULT_TIMEOUT_SECONDS)


# ==============================================================================
# Modern ENT Patches (Fixing decommissioned domains in pronotepy)
# ==============================================================================
def ent_monlycee_modern(username: str, password: str, pronote_url: str = "", **kwargs):
    """
    Gestionnaire moderne pour MonLycée.net (Île-de-France) avec support CAS/Keycloak SSO.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    target_url = pronote_url if pronote_url else "https://monlycee.net"
    try:
        res = session.get(target_url, allow_redirects=True, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")
        form = soup.find("form")
        if form and form.get("action"):
            action_url = urljoin(res.url, form.get("action"))
            payload = {}
            for input_tag in form.find_all("input"):
                name = input_tag.get("name")
                if name:
                    payload[name] = input_tag.get("value", "")
            payload["username"] = username
            payload["password"] = password

            post_res = session.post(action_url, data=payload, allow_redirects=True, timeout=12)
            post_soup = BeautifulSoup(post_res.text, "html.parser")
            if "login-actions/authenticate" in post_res.url or post_soup.find("span", {"id": "input-error"}):
                raise ValueError("Identifiant ou mot de passe MonLycée.net incorrect.")
            return session.cookies
    except Exception as exc:
        if "incorrect" in str(exc):
            raise
    # Fallback to EduConnect / Open NG
    try:
        return _open_ent_ng_edu(username, password, domain="https://monlycee.net")
    except Exception:
        return _open_ent_ng(username, password, url="https://monlycee.net/auth/login")

# Remplacement du gestionnaire obsolète dans pronotepy
pronotepy.ent.ile_de_france = ent_monlycee_modern


class PronotePyDataProvider(DataProvider):
    """Fournisseur de données en direct via l'API Pronote (pronotepy)."""

    def __init__(self, client: pronotepy.Client):
        self.client = client
        self._cached_period = None
        self._load_period()

    def _load_period(self):
        try:
            self._cached_period = self.client.current_period
        except Exception:
            if hasattr(self.client, "periods") and self.client.periods:
                self._cached_period = self.client.periods[-1]

    def get_profile(self) -> StudentProfile:
        try:
            info = getattr(self.client, "info", None)
            name = getattr(info, "name", "Élève Pronote")
            class_name = getattr(info, "class_name", "Classe")
            school = getattr(info, "establishment", "Établissement")
            period_name = getattr(self._cached_period, "name", "Trimestre Actuel") if self._cached_period else "Période"
            return StudentProfile(
                name=name,
                class_name=class_name,
                school_name=school,
                period_name=period_name,
                is_demo=False
            )
        except Exception:
            return StudentProfile(name="Élève Pronote", is_demo=False)

    def get_grades_and_averages(self) -> Tuple[List[SubjectAverage], OverallAverage]:
        subjects_map = {}
        overall = OverallAverage()

        if not self._cached_period:
            return [], overall

        try:
            # Averages from period
            if hasattr(self._cached_period, "averages"):
                for avg in self._cached_period.averages:
                    sub_name = getattr(avg.subject, "name", "Matière")
                    student_val = None
                    try:
                        student_val = float(str(avg.student).replace(",", "."))
                    except (ValueError, TypeError):
                        pass
                    
                    class_val = None
                    try:
                        class_val = float(str(avg.class_average).replace(",", "."))
                    except (ValueError, TypeError):
                        pass

                    min_val = None
                    try:
                        min_val = float(str(avg.min).replace(",", "."))
                    except (ValueError, TypeError):
                        pass

                    max_val = None
                    try:
                        max_val = float(str(avg.max).replace(",", "."))
                    except (ValueError, TypeError):
                        pass

                    subjects_map[sub_name] = SubjectAverage(
                        subject=sub_name,
                        student_avg=student_val,
                        class_avg=class_val,
                        min_avg=min_val,
                        max_avg=max_val,
                        coeff=1.0,
                        grades=[]
                    )

            # Overall average
            if hasattr(self._cached_period, "overall_average"):
                try:
                    val = float(str(self._cached_period.overall_average).replace(",", "."))
                    overall.student_avg = val
                except (ValueError, TypeError):
                    pass
            if hasattr(self._cached_period, "class_overall_average"):
                try:
                    val = float(str(self._cached_period.class_overall_average).replace(",", "."))
                    overall.class_avg = val
                except (ValueError, TypeError):
                    pass

            # Grades
            if hasattr(self._cached_period, "grades"):
                for idx, g in enumerate(self._cached_period.grades):
                    sub_name = getattr(g.subject, "name", "Autre")
                    val = 0.0
                    try:
                        val = float(str(g.grade).replace(",", "."))
                    except (ValueError, TypeError):
                        val = 0.0

                    out_of = 20.0
                    try:
                        out_of = float(str(g.out_of).replace(",", "."))
                    except (ValueError, TypeError):
                        out_of = 20.0

                    coeff = 1.0
                    try:
                        coeff = float(str(g.coefficient).replace(",", "."))
                    except (ValueError, TypeError):
                        coeff = 1.0

                    class_avg = None
                    try:
                        class_avg = float(str(g.average).replace(",", "."))
                    except (ValueError, TypeError):
                        pass

                    grade_item = GradeItem(
                        id=f"g_{idx}",
                        subject=sub_name,
                        value=val,
                        out_of=out_of,
                        coeff=coeff,
                        class_avg=class_avg,
                        date=getattr(g, "date", None),
                        title=getattr(g, "comment", "Devoir") or "Évaluation"
                    )

                    if sub_name not in subjects_map:
                        subjects_map[sub_name] = SubjectAverage(
                            subject=sub_name,
                            student_avg=None,
                            class_avg=None,
                            min_avg=None,
                            max_avg=None,
                            coeff=coeff,
                            grades=[]
                        )
                    subjects_map[sub_name].grades.append(grade_item)

            # Recalculate overall if missing
            if (overall.student_avg == 0.0 or overall.student_avg is None) and subjects_map:
                valid_avgs = [s.student_avg for s in subjects_map.values() if s.student_avg is not None]
                if valid_avgs:
                    overall.student_avg = round(sum(valid_avgs) / len(valid_avgs), 2)

            return list(subjects_map.values()), overall

        except Exception:
            return list(subjects_map.values()), overall

    def get_timetable(self, target_date: date) -> List[LessonItem]:
        lessons = []
        try:
            raw_lessons = self.client.timetable(target_date)
            for idx, l in enumerate(raw_lessons):
                start_str = l.start.strftime("%H:%M") if hasattr(l, "start") and l.start else "00:00"
                end_str = l.end.strftime("%H:%M") if hasattr(l, "end") and l.end else "00:00"
                sub_name = getattr(l.subject, "name", "Cours") if hasattr(l, "subject") and l.subject else "Autre"
                teacher = getattr(l, "teacher_name", "") or (getattr(l, "teacher_names", [""])[0] if getattr(l, "teacher_names", None) else "")
                room = getattr(l, "classroom", "") or "Salle ?"
                is_cancelled = getattr(l, "canceled", False)
                status = getattr(l, "status", None)

                lessons.append(LessonItem(
                    id=f"lesson_{idx}",
                    subject=sub_name,
                    teacher=teacher,
                    room=room,
                    start_time=start_str,
                    end_time=end_str,
                    date=target_date,
                    is_cancelled=is_cancelled,
                    status=status
                ))
        except Exception:
            pass
        return lessons

    def get_homework(self) -> List[HomeworkItem]:
        hw_items = []
        try:
            today = date.today()
            raw_hw = self.client.homework(date_from=today - timedelta(days=2), date_to=today + timedelta(days=14))
            for idx, h in enumerate(raw_hw):
                sub_name = getattr(h.subject, "name", "Matière") if hasattr(h, "subject") and h.subject else "Devoir"
                due_d = getattr(h, "date", today)
                desc = getattr(h, "description", "")
                done = getattr(h, "done", False)

                hw_items.append(HomeworkItem(
                    id=str(idx),
                    subject=sub_name,
                    due_date=due_d,
                    description=desc,
                    done=done
                ))
        except Exception:
            pass
        return hw_items

    def set_homework_done(self, homework_id: str, done: bool) -> bool:
        try:
            idx = int(homework_id)
            today = date.today()
            raw_hw = self.client.homework(date_from=today - timedelta(days=2), date_to=today + timedelta(days=14))
            if 0 <= idx < len(raw_hw):
                raw_hw[idx].set_done(done)
                return True
        except Exception:
            pass
        return False

    def get_vie_scolaire(self) -> Tuple[List[AbsenceItem], List[PunishmentItem]]:
        absences = []
        punishments = []
        try:
            if hasattr(self._cached_period, "absences"):
                for idx, a in enumerate(self._cached_period.absences):
                    d_str = a.from_date.strftime("%d/%m/%Y") if hasattr(a, "from_date") else "Date inconnue"
                    dur = str(getattr(a, "hours", "1h"))
                    reason = getattr(a, "reasons", ["Non renseigné"])[0] if getattr(a, "reasons", None) else "Non renseigné"
                    justified = getattr(a, "justified", False)
                    absences.append(AbsenceItem(f"ab_{idx}", d_str, dur, reason, justified))

            if hasattr(self._cached_period, "punishments"):
                for idx, p in enumerate(self._cached_period.punishments):
                    d_str = p.given.strftime("%d/%m/%Y") if hasattr(p, "given") else "Date inconnue"
                    reason = getattr(p, "reasons", ["Motif non précisé"])[0] if getattr(p, "reasons", None) else "Motif non précisé"
                    giver = getattr(p, "giver", "Vie Scolaire")
                    p_type = getattr(p, "nature", "Retenue")
                    dur = str(getattr(p, "duration", ""))
                    punishments.append(PunishmentItem(f"pu_{idx}", d_str, reason, giver, p_type, dur))
        except Exception:
            pass
        return absences, punishments


def check_pronote_url_warnings(url: str) -> List[str]:
    """Détecte les erreurs courantes comme avoir saisi l'URL de l'ENT à la place de Pronote."""
    warnings = []
    u = url.lower()
    ent_domains = [
        ("monlycee.net", "Île-de-France (MonLycée.net)"),
        ("parisclassenumerique.fr", "Paris Classe Numérique (PCN)"),
        ("monbureaunumerique.fr", "Mon Bureau Numérique (Grand Est)"),
        ("atrium-sud.fr", "Atrium Sud"),
        ("lyceeconnecte.fr", "Lycée Connecté (Nouvelle-Aquitaine)"),
        ("eclat-bfc.fr", "Éclat BFC"),
        ("educonnect.gouv.fr", "EduConnect"),
        ("ent.iledefrance.fr", "ENT Île-de-France"),
    ]
    for domain, ent_label in ent_domains:
        if domain in u and "pronote" not in u and "index-education" not in u:
            warnings.append(
                f"Vous avez saisi l'URL du portail ENT ({domain}) au lieu de l'URL directe Pronote. "
                f"Dans votre navigateur, ouvrez Pronote depuis l'ENT et copiez l'URL de l'onglet Pronote (ex: https://xxxx.index-education.net/pronote/eleve.html)."
            )
            break
    return warnings


def connect_pronote(url: str, username: str, password: str, ent_name: Optional[str] = None) -> PronotePyDataProvider:
    """Connecte à Pronote en direct avec ou sans ENT et URL normalisée, sans blocage infini."""
    normalized_url = normalize_pronote_url(url)
    if not normalized_url:
        raise ValueError("L'URL Pronote est vide ou invalide.")

    # Warning on common ENT copy-paste mistake
    url_warnings = check_pronote_url_warnings(normalized_url)
    if url_warnings:
        raise ValueError(url_warnings[0])

    ent_func = None
    if ent_name and ent_name != "Aucun (Connexion directe)":
        if hasattr(pronotepy.ent, ent_name):
            ent_func = getattr(pronotepy.ent, ent_name)
        else:
            raise ValueError(f"L'ENT '{ent_name}' n'est pas reconnu par le client.")

    try:
        if ent_func:
            client = pronotepy.Client(normalized_url, username=username, password=password, ent=ent_func)
        else:
            client = pronotepy.Client(normalized_url, username=username, password=password)
    except Exception as exc:
        err_msg = str(exc)
        if "Timeout" in err_msg or "timed out" in err_msg:
            raise TimeoutError("Délai d'attente dépassé (timeout 12s). Le serveur Pronote ou l'ENT met trop de temps à répondre.") from exc
        if "[Errno -3]" in err_msg or "Temporary failure in name resolution" in err_msg:
            raise ConnectionError(
                "Accès réseau bloqué : résolution DNS impossible.\n"
                "➔ Si vous êtes dans un terminal isolé/sandbox, lancez l'application dans votre terminal Linux standard (avec Internet) :\n"
                "   /home/lxeeochrome/pronote-tui/pronoterm/run.sh"
            ) from exc
        if "Failed to resolve" in err_msg or "NameResolutionError" in err_msg or "ConnectTimeout" in err_msg:
            raise ConnectionError(f"Impossible de joindre le serveur ({err_msg}). Vérifiez l'adresse URL et votre connexion Internet.") from exc
        if "Unable to connect to pronote" in err_msg:
            raise ValueError(
                "Le serveur Pronote de votre établissement bloque l'accès direct et impose de passer par un ENT.\n"
                "➔ Veuillez sélectionner votre ENT (ex: 'Île-de-France (MonLycée.net)' ou 'EduConnect') dans le menu déroulant."
            ) from exc
        if "ENTLoginError" in err_msg or "Open NG" in err_msg:
            raise ValueError(
                f"Échec de connexion auprès de l'ENT ({ent_name}).\n"
                "➔ Identifiant ou mot de passe incorrect pour cet ENT.\n"
                "➔ Vérifiez s'il s'agit de vos identifiants MonLycée ou EduConnect."
            ) from exc
        if "22" in err_msg or "onglet is not normally accessible" in err_msg:
            raise ValueError(
                "Connexion directe refusée par l'établissement.\n"
                "➔ Votre établissement impose de passer par un ENT.\n"
                "➔ Sélectionnez votre ENT dans la liste au lieu de 'Connexion directe'."
            ) from exc
        if "login" in err_msg.lower() or "credentials" in err_msg.lower() or "authentification" in err_msg.lower():
            raise ValueError("Identifiant ou mot de passe incorrect.") from exc
        raise ValueError(f"Échec de connexion : {err_msg}") from exc

    if not getattr(client, "logged_in", False):
        raise ValueError("Échec de connexion : identifiants ou ENT incorrects.")

    return PronotePyDataProvider(client)


def connect_pronote_qr(qr_code_raw: str, pin: str, uuid: str = "pronoterm-cli-v1") -> PronotePyDataProvider:
    """Connecte à Pronote via un QR Code / PIN (comme l'application mobile et Papillon)."""
    clean_raw = qr_code_raw.strip()
    if not clean_raw:
        raise ValueError("Le contenu du code QR est vide.")
    if not pin or len(pin.strip()) != 4 or not pin.strip().isdigit():
        raise ValueError("Le code PIN doit comporter exactement 4 chiffres.")

    try:
        if isinstance(clean_raw, str):
            qr_dict = json.loads(clean_raw)
        else:
            qr_dict = clean_raw
    except Exception as exc:
        raise ValueError("Format de code QR invalide. Le code QR doit être au format JSON Pronote.") from exc

    try:
        client = pronotepy.Client.qrcode_login(qr_dict, pin=pin.strip(), uuid=uuid)
    except Exception as exc:
        err_msg = str(exc)
        if "expired" in err_msg.lower():
            raise ValueError("Le code QR a expiré (validité de 10 minutes). Veuillez en générer un nouveau sur Pronote Web.") from exc
        if "pin" in err_msg.lower() or "bad username/password" in err_msg.lower():
            raise ValueError("Code PIN incorrect ou code QR expiré.") from exc
        raise ValueError(f"Échec de connexion par code QR : {err_msg}") from exc

    if not getattr(client, "logged_in", False):
        raise ValueError("Échec de connexion par code QR. Vérifiez votre code PIN.")

    return PronotePyDataProvider(client)

