from __future__ import annotations
import sys
from pathlib import Path
from datetime import date
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Label
from textual.containers import Horizontal, Vertical
from textual import work

from .config import AppConfig
from .data_provider import DataProvider, StudentProfile
from .mock_data import MockDataProvider
from .pronote_client import connect_pronote, PronotePyDataProvider
from .ui import (
    NotesView,
    TimetableView,
    HomeworkView,
    SimulatorView,
    VieScolaireView,
    LoginModal,
    HelpModal,
)

class PronotermApp(App):
    """Client Pronote complet pour terminal Linux - 100% piloté au clavier."""

    TITLE = "Pronote-TUI"
    SUB_TITLE = "Terminal Edition • En Ligne & Démo"
    CSS_PATH = "ui/styles.tcss"

    TAB_ORDER = ["tab-notes", "tab-timetable", "tab-homework", "tab-sim", "tab-vie"]

    BINDINGS = [
        # Tab 1: Notes (Chiffre 1, AZERTY &, Pavé num, F1)
        Binding("1", "switch_tab('tab-notes')", "Notes [1]", show=True),
        Binding("ampersand", "switch_tab('tab-notes')", "Notes", show=False),
        Binding("kp_1", "switch_tab('tab-notes')", "Notes", show=False),
        Binding("f1", "switch_tab('tab-notes')", "Notes [F1]", show=False),

        # Tab 2: Timetable (Chiffre 2, AZERTY é, Pavé num, F2)
        Binding("2", "switch_tab('tab-timetable')", "Emploi du temps [2]", show=True),
        Binding("eacute", "switch_tab('tab-timetable')", "Emploi du temps", show=False),
        Binding("kp_2", "switch_tab('tab-timetable')", "Emploi du temps", show=False),
        Binding("f2", "switch_tab('tab-timetable')", "Emploi du temps [F2]", show=False),

        # Tab 3: Homework (Chiffre 3, AZERTY \", Pavé num, F3)
        Binding("3", "switch_tab('tab-homework')", "Devoirs [3]", show=True),
        Binding("quotedbl", "switch_tab('tab-homework')", "Devoirs", show=False),
        Binding("kp_3", "switch_tab('tab-homework')", "Devoirs", show=False),
        Binding("f3", "switch_tab('tab-homework')", "Devoirs [F3]", show=False),

        # Tab 4: Simulator (Chiffre 4, AZERTY ', Pavé num, F4)
        Binding("4", "switch_tab('tab-sim')", "Simulateur [4]", show=True),
        Binding("apostrophe", "switch_tab('tab-sim')", "Simulateur", show=False),
        Binding("kp_4", "switch_tab('tab-sim')", "Simulateur", show=False),
        Binding("f4", "switch_tab('tab-sim')", "Simulateur [F4]", show=False),

        # Tab 5: Vie Scolaire (Chiffre 5, AZERTY (, Pavé num, F5)
        Binding("5", "switch_tab('tab-vie')", "Vie Scolaire [5]", show=True),
        Binding("parenleft", "switch_tab('tab-vie')", "Vie Scolaire", show=False),
        Binding("kp_5", "switch_tab('tab-vie')", "Vie Scolaire", show=False),
        Binding("f5", "switch_tab('tab-vie')", "Vie Scolaire [F5]", show=False),

        # Tab cycling
        Binding("ctrl+right", "next_tab", "Onglet Suivant", show=False),
        Binding("ctrl+left", "prev_tab", "Onglet Précédent", show=False),

        # Timetable navigation
        Binding("left", "prev_day", "Jour -1", show=False),
        Binding("h", "prev_day", "Jour -1", show=False),
        Binding("right", "next_day", "Jour +1", show=False),
        Binding("l", "next_day", "Jour +1", show=False),
        Binding("t", "today", "Aujourd'hui", show=False),

        # Homework toggle & navigation
        Binding("space", "toggle_hw", "Cocher Devoir [Espace]", show=True),
        Binding("d", "toggle_hw", "Cocher Devoir", show=False),
        Binding("j", "cursor_down", "Bas", show=False),
        Binding("k", "cursor_up", "Haut", show=False),
        Binding("down", "cursor_down", "Bas", show=False),
        Binding("up", "cursor_up", "Haut", show=False),

        # Connection / Refresh / Help / Quit
        Binding("c", "open_login", "Connexion [c]", show=True),
        Binding("r", "refresh_data", "Actualiser [r]", show=True),
        Binding("question_mark", "open_help", "Aide (?)", show=True),
        Binding("slash", "open_help", "Aide", show=False),
        Binding("q", "quit", "Quitter [q]", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.config = AppConfig.load()
        self.provider: DataProvider = MockDataProvider()
        self.profile = StudentProfile()
        self._is_connecting = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # Profile Top Banner
        with Horizontal(id="profile-banner"):
            with Vertical(id="student-info"):
                yield Label("Chargement du profil...", id="student-name")
                yield Label("", id="student-meta")
            with Horizontal(id="banner-stats"):
                yield Static(id="banner-badge-status")
                yield Static(id="banner-mg-box", classes="stat-box")

        # Main tabs
        with TabbedContent(id="main-tabs", initial="tab-notes"):
            with TabPane("📊 [1] Notes & Moyennes", id="tab-notes"):
                yield NotesView(id="view-notes")
            with TabPane("📅 [2] Emploi du Temps", id="tab-timetable"):
                yield TimetableView(id="view-timetable")
            with TabPane("📝 [3] Devoirs & Travail", id="tab-homework"):
                yield HomeworkView(id="view-homework")
            with TabPane("🔮 [4] Simulateur", id="tab-sim"):
                yield SimulatorView(id="view-sim")
            with TabPane("📯 [5] Vie Scolaire", id="tab-vie"):
                yield VieScolaireView(id="view-vie")

        yield Footer()

    def on_mount(self):
        if not self.config.use_demo and self.config.url and self.config.username and self.config.password:
            self.start_connection_worker(self.config)
        else:
            self.provider = MockDataProvider()
            self.load_all_views()

    def start_connection_worker(self, config: AppConfig):
        self._set_connecting_state(True)
        self.connect_worker(config)

    def _set_connecting_state(self, is_connecting: bool):
        self._is_connecting = is_connecting
        badge = self.query_one("#banner-badge-status", Static)
        if is_connecting:
            badge.update("[bold black on #38bdf8] 🔄 CONNEXION EN COURS... [/bold black on #38bdf8]\n[dim cyan]Authentification Pronote...[/dim cyan]")
            self.notify("Connexion à Pronote en cours...", title="Pronote En Ligne", severity="information", timeout=5)
        else:
            if self.profile.is_demo:
                badge.update("[bold black on #f59e0b] ⚡ MODE DÉMO [/bold black on #f59e0b]\n[dim]Touche [bold #fbbf24]c[/bold #fbbf24] pour En Ligne[/dim]")
            else:
                badge.update("[bold white on #059669] 🟢 EN LIGNE [/bold white on #059669]\n[dim green]Pronote Connecté[/dim green]")

    @work(thread=True, exclusive=True)
    def connect_worker(self, config: AppConfig):
        """Tâche d'arrière-plan sans aucun blocage de l'interface utilisateur."""
        try:
            provider = connect_pronote(
                config.url,
                config.username,
                config.password,
                config.ent_name
            )
            profile = provider.get_profile()
            self.call_from_thread(self._on_connection_success, provider, profile)
        except Exception as exc:
            self.call_from_thread(self._on_connection_failure, str(exc))

    def _on_connection_success(self, provider: DataProvider, profile: StudentProfile):
        self._is_connecting = False
        self.provider = provider
        self.profile = profile
        self.config.use_demo = False
        self.config.save()
        self.load_all_views()
        self.notify("Connecté à Pronote avec succès ! Vos données sont en direct.", title="Pronote En Ligne", severity="information")

    def _on_connection_failure(self, err_msg: str):
        self._is_connecting = False
        self.provider = MockDataProvider()
        self.profile = self.provider.get_profile()
        self.load_all_views()
        self.notify(f"Connexion impossible : {err_msg}.\nBascule automatique en Mode Démo.", title="Pronote Hors-Ligne", severity="error", timeout=9)

    def load_all_views(self):
        self.profile = self.provider.get_profile()

        # Update top banner
        name_lbl = self.query_one("#student-name", Label)
        meta_lbl = self.query_one("#student-meta", Label)
        badge = self.query_one("#banner-badge-status", Static)
        mg_box = self.query_one("#banner-mg-box", Static)

        name_parts = [p for p in self.profile.name.split() if p]
        initials = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else (self.profile.name[:2].upper() if self.profile.name else "EL")
        avatar_bg = "#059669" if not self.profile.is_demo else "#d97706"
        avatar = f"[bold white on {avatar_bg}] {initials} [/bold white on {avatar_bg}]"

        name_lbl.update(f"{avatar}  [bold #34d399]{self.profile.name}[/bold #34d399] [bold #38bdf8]({self.profile.class_name})[/bold #38bdf8]")
        
        ent_str = f" • [cyan]{self.config.ent_name}[/cyan]" if not self.profile.is_demo and self.config.ent_name != "Aucun (Connexion directe)" else ""
        meta_lbl.update(f"[dim]{self.profile.school_name} • {self.profile.period_name}{ent_str}[/dim]")

        if self._is_connecting:
            badge.update("[bold black on #38bdf8] 🔄 CONNEXION EN COURS... [/bold black on #38bdf8]\n[dim cyan]Authentification Pronote...[/dim cyan]")
        elif self.profile.is_demo:
            badge.update("[bold black on #f59e0b] ⚡ MODE DÉMO [/bold black on #f59e0b]\n[dim]Touche [bold #fbbf24]c[/bold #fbbf24] pour En Ligne[/dim]")
        else:
            badge.update("[bold white on #059669] 🟢 EN LIGNE [/bold white on #059669]\n[dim green]Pronote Connecté[/dim green]")

        # Fetch grades & averages
        subjects, overall = self.provider.get_grades_and_averages()
        
        mg = overall.student_avg or 0.0
        mc = overall.class_avg or 0.0
        diff = mg - mc
        diff_str = f"+{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
        diff_color = "#34d399" if diff >= 0 else "#f43f5e"

        filled = max(0, min(10, int(round((mg / 20.0) * 10))))
        bar = "█" * filled + "░" * (10 - filled)
        mg_color = "#34d399" if mg >= 14 else ("#38bdf8" if mg >= 12 else ("#fbbf24" if mg >= 10 else "#f43f5e"))

        mg_box.update(
            f"[dim]Moyenne Générale[/dim]\n"
            f"[bold {mg_color}]{mg:05.2f}[/bold {mg_color}] [dim]/20[/dim]  "
            f"[{mg_color}]{bar}[/{mg_color}]  "
            f"[{diff_color}]({diff_str})[/]"
        )

        # Update views
        self.query_one("#view-notes", NotesView).update_data(subjects, overall)
        self.query_one("#view-sim", SimulatorView).update_data(subjects, overall)

        # Timetable
        tt_view = self.query_one("#view-timetable", TimetableView)
        lessons = self.provider.get_timetable(tt_view.current_date)
        tt_view.update_lessons(lessons)

        # Homework
        hw = self.provider.get_homework()
        self.query_one("#view-homework", HomeworkView).update_homework(hw)

        # Vie Scolaire
        absences, punishments = self.provider.get_vie_scolaire()
        self.query_one("#view-vie", VieScolaireView).update_data(absences, punishments)

    # Tab switching actions
    def action_switch_tab(self, tab_id: str):
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = tab_id
        if tab_id == "tab-homework":
            self.query_one("#view-homework", HomeworkView).focus()
        elif tab_id == "tab-timetable":
            self.query_one("#view-timetable", TimetableView).focus()
        elif tab_id == "tab-notes":
            self.query_one("#subjects-table").focus()
        elif tab_id == "tab-sim":
            self.query_one("#sim-input-grade").focus()
        elif tab_id == "tab-vie":
            self.query_one("#absences-table").focus()

    def action_next_tab(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active in self.TAB_ORDER:
            idx = self.TAB_ORDER.index(tabs.active)
            next_tab = self.TAB_ORDER[(idx + 1) % len(self.TAB_ORDER)]
            self.action_switch_tab(next_tab)

    def action_prev_tab(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active in self.TAB_ORDER:
            idx = self.TAB_ORDER.index(tabs.active)
            prev_tab = self.TAB_ORDER[(idx - 1) % len(self.TAB_ORDER)]
            self.action_switch_tab(prev_tab)

    def action_cursor_up(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-homework":
            self.query_one("#view-homework", HomeworkView).action_cursor_up()
        elif tabs.active == "tab-notes":
            self.query_one("#view-notes", NotesView).action_row_up()
        elif tabs.active == "tab-vie":
            self.query_one("#view-vie", VieScolaireView).action_row_up()

    def action_cursor_down(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-homework":
            self.query_one("#view-homework", HomeworkView).action_cursor_down()
        elif tabs.active == "tab-notes":
            self.query_one("#view-notes", NotesView).action_row_down()
        elif tabs.active == "tab-vie":
            self.query_one("#view-vie", VieScolaireView).action_row_down()

    # Timetable date actions
    def action_prev_day(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-timetable":
            self.query_one("#view-timetable", TimetableView).prev_day()

    def action_next_day(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-timetable":
            self.query_one("#view-timetable", TimetableView).next_day()

    def action_today(self):
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-timetable":
            self.query_one("#view-timetable", TimetableView).go_today()

    def on_timetable_view_date_changed(self, event: TimetableView.DateChanged):
        lessons = self.provider.get_timetable(event.new_date)
        self.query_one("#view-timetable", TimetableView).update_lessons(lessons)

    # Homework actions
    def action_toggle_hw(self):
        hw_view = self.query_one("#view-homework", HomeworkView)
        hw_view.toggle_selected_or_first()

    def on_homework_view_toggle_homework(self, event: HomeworkView.ToggleHomework):
        success = self.provider.set_homework_done(event.hw_id, event.new_status)
        if success:
            hw = self.provider.get_homework()
            self.query_one("#view-homework", HomeworkView).update_homework(hw)
            status_text = "terminé" if event.new_status else "à faire"
            self.notify(f"Devoir marqué comme {status_text}.", title="Cahier de texte")

    # Refresh
    def action_refresh_data(self):
        if not self.profile.is_demo and self.config.url and self.config.username:
            self.start_connection_worker(self.config)
        else:
            self.load_all_views()
            self.notify("Données actualisées avec succès.", title="Actualisation")

    # Login / ENT Modal
    def action_open_login(self):
        def on_login_close(result: Optional[tuple[AppConfig, Optional[PronotePyDataProvider]]]):
            if result is not None:
                config, provider = result
                self.config = config
                if provider is not None:
                    self.provider = provider
                    self.profile = provider.get_profile()
                    self.config.use_demo = False
                    self.config.save()
                    self.load_all_views()
                    self.notify("Connecté à Pronote avec succès ! Vos données sont en direct.", title="Pronote En Ligne", severity="information")
                elif not self.config.use_demo and self.config.url and self.config.username and self.config.password:
                    self.start_connection_worker(self.config)
                else:
                    self.provider = MockDataProvider()
                    self.profile = self.provider.get_profile()
                    self.load_all_views()

        self.push_screen(LoginModal(self.config), on_login_close)

    # Help Modal
    def action_open_help(self):
        self.push_screen(HelpModal())


def main():
    app = PronotermApp()
    app.run()

if __name__ == "__main__":
    main()
