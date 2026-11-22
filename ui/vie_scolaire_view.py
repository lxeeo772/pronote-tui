from __future__ import annotations
from typing import List
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, DataTable, Label, Rule
from textual.binding import Binding

from ..data_provider import AbsenceItem, PunishmentItem

class VieScolaireView(Container):
    """Vue Vie Scolaire : Absences, Retards, et Sanctions."""

    BINDINGS = [
        Binding("tab", "switch_table", "Basculer table"),
        Binding("shift+tab", "switch_table", "Basculer table"),
        Binding("j", "row_down", "Ligne suivante", show=False),
        Binding("k", "row_up", "Ligne précédente", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.absences: List[AbsenceItem] = []
        self.punishments: List[PunishmentItem] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            # KPI Cards Row
            with Horizontal(classes="vie-kpi-row"):
                yield Static(id="kpi-total-abs", classes="vie-kpi-card")
                yield Static(id="kpi-justified-abs", classes="vie-kpi-card")
                yield Static(id="kpi-unjustified-abs", classes="vie-kpi-card")
                yield Static(id="kpi-punishments", classes="vie-kpi-card")

            with Horizontal(classes="vie-layout"):
                with Vertical(classes="vie-col-left"):
                    yield Label("[bold #38bdf8]🚨 Absences & Retards[/bold #38bdf8] [dim](Tab pour alterner)[/dim]")
                    yield DataTable(id="absences-table", cursor_type="row")

                with Vertical(classes="vie-col-right"):
                    yield Label("[bold #f43f5e]⚡ Retenues, Sanctions & Observations[/bold #f43f5e]")
                    yield DataTable(id="punishments-table", cursor_type="row")

    def on_mount(self):
        abs_table = self.query_one("#absences-table", DataTable)
        abs_table.add_column("Date", key="date", width=12)
        abs_table.add_column("Durée", key="dur", width=12)
        abs_table.add_column("Motif", key="reason", width=22)
        abs_table.add_column("Statut", key="justified", width=14)

        pun_table = self.query_one("#punishments-table", DataTable)
        pun_table.add_column("Date", key="date", width=12)
        pun_table.add_column("Nature", key="type", width=16)
        pun_table.add_column("Par", key="giver", width=16)
        pun_table.add_column("Motif", key="reason", width=22)

    def update_data(self, absences: List[AbsenceItem], punishments: List[PunishmentItem]):
        self.absences = absences
        self.punishments = punishments

        justified_count = sum(1 for a in absences if a.justified)
        unjustified_count = len(absences) - justified_count

        self.query_one("#kpi-total-abs", Static).update(
            f"[dim]Total Absences[/dim]\n[bold #38bdf8]{len(absences)} événement(s)[/bold #38bdf8]"
        )
        self.query_one("#kpi-justified-abs", Static).update(
            f"[dim]Justifiées[/dim]\n[bold #34d399]✓ {justified_count} justifiée(s)[/bold #34d399]"
        )
        self.query_one("#kpi-unjustified-abs", Static).update(
            f"[dim]Injustifiées[/dim]\n[bold #f43f5e]✗ {unjustified_count} injustifiée(s)[/bold #f43f5e]"
        )
        self.query_one("#kpi-punishments", Static).update(
            f"[dim]Sanctions / Retenues[/dim]\n[bold #fbbf24]⚡ {len(punishments)} sanction(s)[/bold #fbbf24]"
        )

        abs_table = self.query_one("#absences-table", DataTable)
        abs_table.clear()
        for a in self.absences:
            statut_badge = "[bold #34d399]✓ Justifiée[/bold #34d399]" if a.justified else "[bold #f43f5e]✗ Injustifiée[/bold #f43f5e]"
            abs_table.add_row(a.date_str, a.duration, a.reason, statut_badge, key=a.id)

        pun_table = self.query_one("#punishments-table", DataTable)
        pun_table.clear()
        for p in self.punishments:
            pun_table.add_row(p.date_str, f"[bold #fbbf24]{p.punishment_type}[/bold #fbbf24]", p.giver, p.reason, key=p.id)

    def action_switch_table(self):
        abs_table = self.query_one("#absences-table", DataTable)
        pun_table = self.query_one("#punishments-table", DataTable)
        if abs_table.has_focus:
            pun_table.focus()
        else:
            abs_table.focus()

    def action_row_down(self):
        for table in [self.query_one("#absences-table", DataTable), self.query_one("#punishments-table", DataTable)]:
            if table.has_focus:
                table.action_cursor_down()
                break

    def action_row_up(self):
        for table in [self.query_one("#absences-table", DataTable), self.query_one("#punishments-table", DataTable)]:
            if table.has_focus:
                table.action_cursor_up()
                break
