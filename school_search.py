"""
Module de recherche d'établissements scolaires Pronote (style Papillon).
Permet de rechercher une ville ou un code postal, de lister les lycées et collèges,
d'en déduire automatiquement l'URL Pronote et l'ENT associé, et d'ouvrir la page de connexion.
"""
from __future__ import annotations
import json
import re
import urllib.parse
import webbrowser
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
import requests

try:
    from .config import normalize_pronote_url
except ImportError:
    from config import normalize_pronote_url


@dataclass
class SchoolInfo:
    name: str
    city: str
    postal_code: str
    url: str
    uai: str
    ent_name: str
    type_etab: str  # "Lycée", "Collège", "Autre"

    @property
    def display_label(self) -> str:
        icon = "🏫" if self.type_etab == "Lycée" else ("🎓" if self.type_etab == "Collège" else "📍")
        return f"{icon} {self.name} ({self.postal_code} {self.city})"

    @property
    def value(self) -> str:
        return self.url


# Cache de secours pour démonstration et utilisation hors-ligne
FALLBACK_SCHOOLS = [
    SchoolInfo(
        name="LYCEE JEAN PERRIN",
        city="Saint-Ouen-l'Aumône",
        postal_code="95310",
        url="https://0951104j.index-education.net/pronote/eleve.html",
        uai="0951104J",
        ent_name="ile_de_france",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="LYCEE EDMOND ROSTAND",
        city="Saint-Ouen-l'Aumône",
        postal_code="95310",
        url="https://0951728m.index-education.net/pronote/eleve.html",
        uai="0951728M",
        ent_name="ile_de_france",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="COLLEGE LE PARC",
        city="Saint-Ouen-l'Aumône",
        postal_code="95310",
        url="https://0950039b.index-education.net/pronote/eleve.html",
        uai="0950039B",
        ent_name="val_doise",
        type_etab="Collège"
    ),
    SchoolInfo(
        name="LYCEE KASTLER",
        city="Cergy",
        postal_code="95000",
        url="https://0951614n.index-education.net/pronote/eleve.html",
        uai="0951614N",
        ent_name="ile_de_france",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="LYCEE JANSON DE SAILLY",
        city="Paris",
        postal_code="75016",
        url="https://0750699c.index-education.net/pronote/eleve.html",
        uai="0750699C",
        ent_name="ile_de_france",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="LYCEE CONDORCET",
        city="Paris",
        postal_code="75009",
        url="https://0750654j.index-education.net/pronote/eleve.html",
        uai="0750654J",
        ent_name="ile_de_france",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="LYCEE DU PARC",
        city="Lyon",
        postal_code="69006",
        url="https://0690026d.index-education.net/pronote/eleve.html",
        uai="0690026D",
        ent_name="ent_auvergnerhonealpe",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="LYCEE THIERS",
        city="Marseille",
        postal_code="13001",
        url="https://0130038e.index-education.net/pronote/eleve.html",
        uai="0130038E",
        ent_name="atrium_sud",
        type_etab="Lycée"
    ),
    SchoolInfo(
        name="SERVEUR DEMONSTRATION OFFICIEL",
        city="France",
        postal_code="00000",
        url="https://demo.index-education.net/pronote/eleve.html",
        uai="DEMO",
        ent_name="Aucun (Connexion directe)",
        type_etab="Lycée"
    ),
]


def determine_type_etab(name: str) -> str:
    """Détermine si l'établissement est un lycée, collège ou autre."""
    upper = name.upper()
    if "LYC" in upper or "LPO" in upper or "LP " in upper or "LGT" in upper:
        return "Lycée"
    if "COL" in upper or "CLG" in upper:
        return "Collège"
    return "Établissement"


def get_recommended_ent(postal_code: str, school_name: str) -> str:
    """Détecte automatiquement le nom de l'ENT selon le département et le type d'établissement."""
    dept = postal_code[:2] if len(postal_code) >= 2 else ""
    type_e = determine_type_etab(school_name)

    # Île-de-France (75, 77, 78, 91, 92, 93, 94, 95)
    if dept in ("75", "77", "78", "91", "92", "93", "94", "95"):
        if type_e == "Lycée":
            return "ile_de_france"  # MonLycée.net
        if dept == "75":
            return "paris_classe_numerique"
        if dept == "77":
            return "ent77"
        if dept == "78":
            return "ent_ecollege78"
        if dept == "91":
            return "ent_essonne"
        if dept == "94":
            return "ent_94"
        if dept == "95":
            return "val_doise"
        return "ile_de_france"

    # Hauts-de-France
    if dept in ("59", "62", "02", "60", "80"):
        return "ent_hdf"

    # Grand Est
    if dept in ("67", "68", "08", "10", "51", "52", "54", "55", "57", "88"):
        return "monbureaunumerique"

    # Région Sud (PACA)
    if dept in ("04", "05", "06", "13", "83", "84"):
        return "atrium_sud"

    # Nouvelle-Aquitaine
    if dept in ("16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"):
        return "lyceeconnecte_edu"

    # Bourgogne-Franche-Comté
    if dept in ("21", "25", "39", "58", "70", "71", "89", "90"):
        return "eclat_bfc"

    # Normandie
    if dept in ("14", "27", "50", "61", "76"):
        return "l_normandie"

    # Occitanie
    if dept in ("31", "09", "12", "32", "46", "65", "81", "82"):
        return "occitanie_toulouse_edu"
    if dept in ("34", "11", "30", "48", "66"):
        return "occitanie_montpellier_educonnect"

    # Pays de la Loire
    if dept in ("44", "49", "53", "72", "85"):
        return "ent_elyco"

    # Auvergne-Rhône-Alpes
    if dept in ("01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"):
        return "ent_auvergnerhonealpe"

    return "Aucun (Connexion directe)"


def search_schools_by_city(query: str, timeout: float = 6.0) -> Tuple[str, str, List[SchoolInfo]]:
    """
    Recherche les lycées et collèges d'une ville, code postal ou code UAI via l'API Index Education.
    Retourne (nom_ville, code_postal, liste_etablissements).
    """
    clean_query = query.strip()
    if not clean_query:
        return "", "", []

    # 0. Détection directe d'un code UAI/RNE (ex: 0951104J ou URL avec code)
    uai_match = re.search(r"([0-9]{7}[a-zA-Z])", clean_query)
    if uai_match:
        target_uai = uai_match.group(1).upper()
        # Chercher dans les établissements connus
        matched_known = [s for s in FALLBACK_SCHOOLS if s.uai.upper() == target_uai]
        if matched_known:
            return matched_known[0].city, matched_known[0].postal_code, matched_known

        # Si non trouvé dans le fallback, construire dynamiquement la fiche de l'établissement
        dept_prefix = target_uai[:3]
        target_url = f"https://{target_uai.lower()}.index-education.net/pronote/eleve.html"
        ent_rec = get_recommended_ent(dept_prefix + "00", "Lycée")
        direct_school = SchoolInfo(
            name=f"Établissement {target_uai}",
            city=f"Département ({dept_prefix})",
            postal_code=f"{dept_prefix}00",
            url=target_url,
            uai=target_uai,
            ent_name=ent_rec,
            type_etab="Lycée"
        )
        return direct_school.city, direct_school.postal_code, [direct_school]

    # 1. Résolution de la commune via l'API nationale des adresses (api-adresse.data.gouv.fr)
    city_name = clean_query
    postcode = clean_query if clean_query.isdigit() and len(clean_query) == 5 else ""
    lat = None
    lon = None

    try:
        url_geo = f"https://api-adresse.data.gouv.fr/search/?q={urllib.parse.quote(clean_query)}&type=municipality"
        resp = requests.get(url_geo, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if not features:
                # Essayer sans le filtre type=municipality
                url_geo_any = f"https://api-adresse.data.gouv.fr/search/?q={urllib.parse.quote(clean_query)}"
                resp_any = requests.get(url_geo_any, timeout=timeout)
                if resp_any.status_code == 200:
                    features = resp_any.json().get("features", [])

            if features:
                best = features[0]
                lon, lat = best["geometry"]["coordinates"]
                props = best.get("properties", {})
                city_name = props.get("city") or props.get("name") or city_name
                postcode = props.get("postcode") or postcode
    except Exception:
        pass

    # 2. Requête du service de géolocalisation d'Index Education
    results: List[SchoolInfo] = []
    if lat is not None and lon is not None:
        try:
            payload = {
                "data": json.dumps({"nomFonction": "geoLoc", "lat": str(lat), "long": str(lon)})
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X)"
            }
            r = requests.post(
                "https://www.index-education.com/swie/geoloc.php",
                data=payload,
                headers=headers,
                timeout=timeout
            )
            if r.status_code == 200:
                raw_list = r.json()
                dept = postcode[:2] if len(postcode) >= 2 else ""

                for item in raw_list:
                    nom = item.get("nomEtab", "").strip()
                    cp = item.get("cp", "").strip()
                    raw_url = item.get("url", "").strip()
                    if not nom or not raw_url:
                        continue

                    # Extraire UAI si présent dans l'URL (ex: 0951104J)
                    uai_match = re.search(r"https?://([0-9a-zA-Z]{7,8})\.", raw_url)
                    uai = uai_match.group(1).upper() if uai_match else ""

                    clean_url = normalize_pronote_url(raw_url)
                    type_e = determine_type_etab(nom)
                    ent = get_recommended_ent(cp, nom)

                    results.append(SchoolInfo(
                        name=nom,
                        city=city_name,
                        postal_code=cp,
                        url=clean_url,
                        uai=uai,
                        ent_name=ent,
                        type_etab=type_e
                    ))

                # Tri : exact code postal d'abord, puis même département, puis Lycées avant collèges
                results.sort(
                    key=lambda s: (
                        s.postal_code != postcode,
                        not s.postal_code.startswith(dept) if dept else False,
                        0 if s.type_etab == "Lycée" else (1 if s.type_etab == "Collège" else 2),
                        s.name
                    )
                )
        except Exception:
            pass

    # 3. Si aucun résultat via le réseau (ex: sandbox ou panne), utiliser le catalogue de secours
    if not results:
        q_upper = clean_query.upper()
        matching_fallbacks = [
            s for s in FALLBACK_SCHOOLS
            if q_upper in s.name.upper() or q_upper in s.city.upper() or q_upper in s.postal_code or q_upper in s.uai
        ]
        if matching_fallbacks:
            return city_name, postcode, matching_fallbacks
        # Si la recherche ne matche aucun fallback mais qu'on a besoin d'afficher des lycées
        return city_name, postcode, FALLBACK_SCHOOLS

    return city_name, postcode, results


def open_school_login_page(pronote_url: str) -> bool:
    """Ouvre la page de connexion de l'établissement dans le navigateur par défaut."""
    if not pronote_url:
        return False
    norm = normalize_pronote_url(pronote_url)
    try:
        return webbrowser.open(norm)
    except Exception:
        return False
