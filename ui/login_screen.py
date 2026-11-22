from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Input, Select, Button, Label, Checkbox, Rule
from textual.binding import Binding
from textual import work

try:
    from ..config import AppConfig, normalize_pronote_url
    from ..pronote_client import (
        connect_pronote, connect_pronote_qr,
        PronotePyDataProvider, check_pronote_url_warnings
    )
    from ..school_search import (
        search_schools_by_city, open_school_login_page,
        SchoolInfo, FALLBACK_SCHOOLS
    )
except ImportError:
    from config import AppConfig, normalize_pronote_url
    from pronote_client import (
        connect_pronote, connect_pronote_qr,
        PronotePyDataProvider, check_pronote_url_warnings
    )
    from school_search import (
        search_schools_by_city, open_school_login_page,
        SchoolInfo, FALLBACK_SCHOOLS
    )

POPULAR_ENTS = [
    ("Connexion directe (sans ENT)", "Aucun (Connexion directe)"),
    ("Île-de-France (MonLycée.net)", "ile_de_france"),
    ("Paris Classe Numérique (PCN)", "paris_classe_numerique"),
    ("Mon Bureau Numérique (Grand Est)", "monbureaunumerique"),
    ("Atrium Sud (PACA / Région Sud)", "atrium_sud"),
    ("Lycée Connecté (Nouvelle-Aquitaine)", "lyceeconnecte_edu"),
    ("Éclat BFC (Bourgogne-Franche-Comté)", "eclat_bfc"),
    ("L'Normandie (Normandie)", "l_normandie"),
    ("Occitanie Toulouse EduConnect", "occitanie_toulouse_edu"),
    ("Occitanie Montpellier EduConnect", "occitanie_montpellier_educonnect"),
    ("Cybercollèges 42", "cas_cybercolleges42_edu"),
    ("Arsène 76 EduConnect", "cas_arsene76_edu"),
    ("ENT 94 (Val-de-Marne)", "ent_94"),
    ("ENT 77 (Seine-et-Marne)", "ent77"),
    ("E-Collège 78 (Yvelines)", "ent_ecollege78"),
    ("ENT Essonne", "ent_essonne"),
    ("ENT HDF (Hauts-de-France)", "ent_hdf"),
    ("e-lyco (Pays de la Loire)", "ent_elyco"),
    ("Laclasse.com (Lyon)", "laclasse_educonnect"),
    ("ENT Auvergne-Rhône-Alpes", "ent_auvergnerhonealpe"),
    ("ENT Val-d'Oise", "val_doise"),
    ("Académie d'Orléans-Tours", "ac_orleans_tours"),
    ("Académie de Poitiers", "ac_poitiers"),
    ("Académie de Rennes", "ac_rennes"),
    ("Académie de Reims", "ac_reims"),
]


class LoginModal(ModalScreen[Optional[Tuple[AppConfig, Optional[PronotePyDataProvider]]]]):
    """
    Dialogue de connexion Pronote avec recherche d'établissement par ville (style Papillon),
    redirection vers le portail de l'établissement et connexion directe / QR code.
    """

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Fermer [Echap]"),
    ]

    def __init__(self, current_config: AppConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = current_config
        self._is_connecting = False
        self._schools_map: Dict[str, SchoolInfo] = {}
        self._qr_mode = False

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="login-dialog"):
            yield Label("[bold #34d399]🔐 Connexion Pronote & Recherche d'Établissement[/bold #34d399]", id="login-title")
            
            with Vertical(classes="papillon-banner"):
                yield Label(
                    "[bold #38bdf8]🦋 Trouver mon Lycée / Collège (Méthode Papillon)[/bold #38bdf8]\n"
                    "[dim]1. Indiquez votre ville ou code postal  ➔  2. Choisissez votre lycée  ➔  3. Connectez-vous ![/dim]"
                )

            # Étape 1 : Saisie de la ville ou code postal
            yield Label("[bold white]1. Votre Ville ou Code Postal :[/bold white]")
            with Horizontal(classes="search-box-row"):
                yield Input(
                    placeholder="ex: Saint-Ouen-l'Aumône, 95310, Sarcelles, Paris, Lyon...",
                    id="city-search-input"
                )
                yield Button("🔍 Chercher", id="btn-search-city", variant="primary")

            # Étape 2 : Liste des établissements proposés
            yield Label("[bold white]2. Choisissez votre Établissement :[/bold white]")
            yield Select(
                [(s.display_label, s.url) for s in FALLBACK_SCHOOLS],
                prompt="Sélectionnez un lycée ou collège dans la liste...",
                id="select-school"
            )
            yield Static("", id="school-info-badge", classes="school-selected-badge")

            # Étape 3 : Bouton de redirection web (demande expresse de l'utilisateur)
            with Horizontal(classes="web-action-row"):
                yield Button("🌐 Ouvrir la page de connexion du lycée", id="btn-open-web", variant="warning")
                yield Button("📱 Mode Code QR / PIN", id="btn-toggle-qr", variant="default")

            yield Rule()

            # Section Identifiants / Paramètres techniques
            with Vertical(id="credentials-container"):
                yield Label("[bold white]3. URL Pronote (remplie automatiquement) :[/bold white]")
                yield Input(
                    placeholder="https://0951104j.index-education.net/pronote/eleve.html",
                    value=self.config.url,
                    id="login-input-url"
                )

                yield Label("[bold white]4. ENT de votre établissement :[/bold white]")
                current_ent = self.config.ent_name if any(e[1] == self.config.ent_name for e in POPULAR_ENTS) else "Aucun (Connexion directe)"
                yield Select(
                    POPULAR_ENTS,
                    value=current_ent,
                    id="login-select-ent"
                )

                with Vertical(id="std-login-fields"):
                    yield Label("[bold white]5. Identifiant élève ou email ENT :[/bold white]")
                    yield Input(
                        placeholder="Identifiant de connexion",
                        value=self.config.username,
                        id="login-input-user"
                    )

                    yield Label("[bold white]6. Mot de passe :[/bold white]")
                    yield Input(
                        placeholder="Mot de passe",
                        password=True,
                        value=self.config.password,
                        id="login-input-pwd"
                    )

                with Vertical(id="qr-login-fields"):
                    yield Label("[bold #38bdf8]📱 Connexion par Code QR / PIN (depuis Pronote Web) :[/bold #38bdf8]")
                    yield Label("[dim]Dans Pronote sur votre navigateur, cliquez sur le QR Code à côté de votre nom.[/dim]")
                    yield Input(
                        placeholder="Texte JSON du code QR ou lien jeton",
                        id="login-input-qr-raw"
                    )
                    yield Input(
                        placeholder="Code PIN à 4 chiffres (ex: 1234)",
                        password=True,
                        max_length=4,
                        id="login-input-qr-pin"
                    )

                yield Checkbox("Se souvenir de moi", value=self.config.remember_password, id="login-chk-remember")

            yield Static(id="login-status-box")

            with Horizontal(classes="modal-btn-row"):
                yield Button("🟢 Se connecter", id="btn-do-login", variant="success")
                yield Button("🟡 Mode Démo", id="btn-use-demo", variant="primary")
                yield Button("🌐 Démo Publique", id="btn-fill-demo", variant="default")
                yield Button("Fermer [Echap]", id="btn-cancel", variant="default")

    def on_mount(self):
        # Initialiser le dictionnaire des lycées avec les fallbacks
        for s in FALLBACK_SCHOOLS:
            self._schools_map[s.url] = s

        # Cacher la section QR code par défaut
        qr_fields = self.query_one("#qr-login-fields", Vertical)
        qr_fields.display = False

        # Cacher le badge d'info initial s'il n'y a pas encore de sélection
        badge = self.query_one("#school-info-badge", Static)
        if self.config.url:
            badge.update(f"[bold #38bdf8]📍 Établissement configuré :[/bold #38bdf8] [dim]{self.config.url}[/dim]")
            badge.display = True
        else:
            badge.display = False

    def action_dismiss_modal(self):
        if not self._is_connecting:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "city-search-input":
            self._trigger_city_search()
        elif not self._is_connecting:
            self._process_login()

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn-cancel":
            self.action_dismiss_modal()
        elif btn_id == "btn-search-city":
            self._trigger_city_search()
        elif btn_id == "btn-open-web":
            self._open_web_login()
        elif btn_id == "btn-toggle-qr":
            self._toggle_qr_mode()
        elif btn_id == "btn-fill-demo":
            self._fill_official_demo()
        elif btn_id == "btn-use-demo":
            self.config.use_demo = True
            self.config.save()
            self.dismiss((self.config, None))
        elif btn_id == "btn-do-login":
            self._process_login()

    def _toggle_qr_mode(self):
        self._qr_mode = not self._qr_mode
        std_fields = self.query_one("#std-login-fields", Vertical)
        qr_fields = self.query_one("#qr-login-fields", Vertical)
        btn_toggle = self.query_one("#btn-toggle-qr", Button)
        
        if self._qr_mode:
            std_fields.display = False
            qr_fields.display = True
            btn_toggle.label = "🔑 Mode Identifiants"
        else:
            std_fields.display = True
            qr_fields.display = False
            btn_toggle.label = "📱 Mode Code QR / PIN"

    def _trigger_city_search(self):
        city_query = self.query_one("#city-search-input", Input).value.strip()
        status_box = self.query_one("#login-status-box", Static)
        if not city_query:
            status_box.update("[bold #fbbf24]⚠️ Veuillez saisir une ville ou un code postal.[/bold #fbbf24]")
            return

        status_box.update(f"[bold #38bdf8]🔍 Recherche des lycées et collèges à '{city_query}'...[/bold #38bdf8]")
        self.worker_search_city(city_query)

    @work(thread=True, exclusive=True)
    def worker_search_city(self, query: str):
        try:
            city_name, postcode, schools = search_schools_by_city(query)
            self.app.call_from_thread(self._on_schools_found, city_name, postcode, schools)
        except Exception as exc:
            self.app.call_from_thread(self._on_search_failure, str(exc))

    def _on_schools_found(self, city_name: str, postcode: str, schools: List[SchoolInfo]):
        status_box = self.query_one("#login-status-box", Static)
        select_widget = self.query_one("#select-school", Select)

        if not schools:
            status_box.update(f"[bold #f43f5e]Aucun établissement trouvé pour '{city_name}'.[/bold #f43f5e]")
            return

        for s in schools:
            self._schools_map[s.url] = s

        options = [(s.display_label, s.url) for s in schools]
        select_widget.set_options(options)
        
        # Sélectionner le premier résultat automatiquement
        first_school = schools[0]
        select_widget.value = first_school.url
        self._apply_school_selection(first_school)

        label_place = f"{city_name} ({postcode})" if postcode else city_name
        status_box.update(
            f"[bold #34d399]✓ {len(schools)} établissement(s) trouvé(s) pour {label_place} ![/bold #34d399]\n"
            f"[dim]Choisissez votre lycée dans le menu n°2 ou ouvrez sa page de connexion.[/dim]"
        )

    def _on_search_failure(self, err_msg: str):
        status_box = self.query_one("#login-status-box", Static)
        status_box.update(f"[bold #f43f5e]Erreur lors de la recherche : {err_msg}[/bold #f43f5e]")

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "select-school" and event.value != Select.BLANK:
            school = self._schools_map.get(str(event.value))
            if school:
                self._apply_school_selection(school)

    def _apply_school_selection(self, school: SchoolInfo):
        # 1. Remplir l'URL
        url_input = self.query_one("#login-input-url", Input)
        url_input.value = school.url

        # 2. Ajuster l'ENT
        ent_select = self.query_one("#login-select-ent", Select)
        if any(e[1] == school.ent_name for e in POPULAR_ENTS):
            ent_select.value = school.ent_name
        else:
            ent_select.value = "Aucun (Connexion directe)"

        # 3. Mettre à jour le badge de confirmation
        badge = self.query_one("#school-info-badge", Static)
        badge.display = True
        badge.update(
            f"[bold #34d399]✓ Établissement sélectionné :[/bold #34d399] [bold white]{school.name}[/bold white]\n"
            f"[dim cyan]📍 {school.postal_code} {school.city} | ENT suggéré : {school.ent_name}[/dim cyan]"
        )

    def _open_web_login(self):
        """Ouvre la page de connexion du lycée dans le navigateur (demande de l'utilisateur style Papillon)."""
        url = self.query_one("#login-input-url", Input).value.strip()
        status_box = self.query_one("#login-status-box", Static)
        if not url:
            status_box.update("[bold #f43f5e]⚠️ Veuillez d'abord choisir un établissement ou entrer une URL.[/bold #f43f5e]")
            return

        success = open_school_login_page(url)
        if success:
            status_box.update(
                f"[bold #38bdf8]🌐 Page de connexion de votre lycée ouverte dans le navigateur ![/bold #38bdf8]\n"
                f"[dim white]➔ Connectez-vous sur la page web ouverte dans votre navigateur.\n"
                f"➔ Pour Pronoterm : vous pouvez saisir vos identifiants ci-dessous, ou utiliser le Mode QR Code.[/dim white]"
            )
        else:
            status_box.update(
                f"[bold #fbbf24]🌐 URL de votre lycée : {url}[/bold #fbbf24]\n"
                f"[dim]Ouvrez cette adresse dans votre navigateur web.[/dim]"
            )

    def _fill_official_demo(self):
        self.query_one("#login-input-url", Input).value = "https://demo.index-education.net/pronote/eleve.html"
        self.query_one("#login-input-user", Input).value = "demonstration"
        self.query_one("#login-input-pwd", Input).value = "pronotevs"
        self.query_one("#login-select-ent", Select).value = "Aucun (Connexion directe)"
        badge = self.query_one("#school-info-badge", Static)
        badge.display = True
        badge.update("[bold #34d399]✓ Serveur Démonstration Officiel (Index-Education)[/bold #34d399]")
        self.query_one("#login-status-box", Static).update(
            "[bold #34d399]✓ Serveur démo pré-rempli ![/bold #34d399] Cliquez sur 'Se connecter'."
        )

    def _process_login(self):
        if self._is_connecting:
            return

        raw_url = self.query_one("#login-input-url", Input).value.strip()
        ent = self.query_one("#login-select-ent", Select).value
        remember = self.query_one("#login-chk-remember", Checkbox).value
        status_box = self.query_one("#login-status-box", Static)

        if not raw_url:
            status_box.update("[bold #f43f5e]⚠️ Veuillez indiquer ou sélectionner l'URL de votre établissement.[/bold #f43f5e]")
            return

        normalized = normalize_pronote_url(raw_url)
        warnings = check_pronote_url_warnings(normalized)
        if warnings:
            status_box.update(f"[bold #f43f5e]⚠️ {warnings[0]}[/bold #f43f5e]")
            return

        if self._qr_mode:
            qr_raw = self.query_one("#login-input-qr-raw", Input).value.strip()
            qr_pin = self.query_one("#login-input-qr-pin", Input).value.strip()
            if not qr_raw or not qr_pin:
                status_box.update("[bold #f43f5e]⚠️ Veuillez coller le code QR et saisir le code PIN à 4 chiffres.[/bold #f43f5e]")
                return

            self._is_connecting = True
            self.query_one("#btn-do-login", Button).disabled = True
            status_box.update("[bold #38bdf8]🔄 Connexion par Code QR en cours...[/bold #38bdf8]")
            self.worker_attempt_qr_connection(qr_raw, qr_pin, normalized)
            return

        username = self.query_one("#login-input-user", Input).value.strip()
        password = self.query_one("#login-input-pwd", Input).value

        if not username or not password:
            status_box.update(
                "[bold #f43f5e]⚠️ Veuillez renseigner votre identifiant et votre mot de passe (ou utilisez le Mode Démo).[/bold #f43f5e]"
            )
            return

        self.config.url = normalized
        self.config.username = username
        self.config.password = password
        self.config.ent_name = str(ent) if ent else "Aucun (Connexion directe)"
        self.config.remember_password = remember
        self.config.use_demo = False

        self._is_connecting = True
        btn_login = self.query_one("#btn-do-login", Button)
        btn_login.disabled = True

        status_box.update(
            f"[bold #38bdf8]🔄 Connexion en cours vers Pronote...[/bold #38bdf8]\n"
            f"[dim cyan]Établissement : {normalized}\nENT : {self.config.ent_name}[/dim cyan]"
        )

        self.worker_attempt_connection(self.config)

    @work(thread=True, exclusive=True)
    def worker_attempt_qr_connection(self, qr_raw: str, pin: str, pronote_url: str):
        try:
            provider = connect_pronote_qr(qr_raw, pin)
            profile = provider.get_profile()
            self.config.url = pronote_url
            self.config.use_demo = False
            self.app.call_from_thread(self._on_connection_success, provider, profile)
        except Exception as exc:
            self.app.call_from_thread(self._on_connection_failure, str(exc))

    @work(thread=True, exclusive=True)
    def worker_attempt_connection(self, config: AppConfig):
        try:
            provider = connect_pronote(
                config.url,
                config.username,
                config.password,
                config.ent_name
            )
            profile = provider.get_profile()
            self.app.call_from_thread(self._on_connection_success, provider, profile)
        except Exception as exc:
            self.app.call_from_thread(self._on_connection_failure, str(exc))

    def _on_connection_success(self, provider: PronotePyDataProvider, profile):
        self._is_connecting = False
        self.config.save()
        status_box = self.query_one("#login-status-box", Static)
        status_box.update(f"[bold #34d399]✅ Connecté avec succès ! Bienvenue {profile.name}.[/bold #34d399]")
        self.dismiss((self.config, provider))

    def _on_connection_failure(self, err_msg: str):
        self._is_connecting = False
        btn_login = self.query_one("#btn-do-login", Button)
        btn_login.disabled = False

        status_box = self.query_one("#login-status-box", Static)
        status_box.update(
            f"[bold #f43f5e]❌ {err_msg}[/bold #f43f5e]\n\n"
            f"[bold #fbbf24]💡 Options pour réussir votre connexion :[/bold #fbbf24]\n"
            f"• [bold white]Redirection Web[/bold white] : Cliquez sur '[bold yellow]🌐 Ouvrir la page de connexion[/bold yellow]' pour vous identifier sur le portail officiel de votre lycée.\n"
            f"• [bold white]Mode Code QR[/bold white] : Cliquez sur '[bold cyan]📱 Mode Code QR / PIN[/bold cyan]' pour importer la session sans mot de passe.\n"
            f"• [bold white]Mode Démo[/bold white] : Cliquez sur '[bold green]Mode Démo[/bold green]' pour explorer toutes les vues sans compte."
        )
