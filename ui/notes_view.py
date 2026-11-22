from __future__ import annotations
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, DataTable, Label, Rule
from textual.binding import Binding

from ..data_provider import SubjectAverage, OverallAverage, GradeItem

def format_grade(val: Optional[float], out_of: float = 20.0) -> str:
    if val is None:
        return "[dim]--[/dim]"
    color = "#34d399" if val >= 14 else ("#38bdf8" if val >= 12 else ("#fbbf24" if val >= 10 else "#f43f5e"))
    return f"[{color} bold]{val:05.2f}[/{color} bold]/[dim]{out_of:g}[/dim]"

def format_avg(val: Optional[float]) -> str:
    if val is None:
        return "[dim]--[/dim]"
    color = "#34d399" if val >= 14 else ("#38bdf8" if val >= 12 else ("#fbbf24" if val >= 10 else "#f43f5e"))
    return f"[{color} bold]{val:05.2f}[/{color} bold]"

class NotesView(Container):
    """Vue détaillée des notes et moyennes."""

    BINDINGS = [
        Binding("tab", "switch_table", "Basculer table"),
        Binding("shift+tab", "switch_table", "Basculer table"),
        Binding("j", "row_down", "Ligne suivante", show=False),
        Binding("k", "row_up", "Ligne précédente", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subjects: List[SubjectAverage] = []
        self.overall = OverallAverage()
        self.current_subject_index: int = 0

    def compose(self) -> ComposeResult:
        with Vertical():
            # Summary Banner
            yield Static(id="notes-summary-card", classes="summary-card")
            
            with Horizontal(id="notes-main-layout"):
                # Table of subjects
                with Vertical(id="subjects-col"):
                    yield Label("[bold #38bdf8]📋 Matières & Moyennes[/bold #38bdf8] [dim](↑/↓ ou j/k  •  Tab pour Notes)[/dim]")
                    yield DataTable(id="subjects-table", cursor_type="row")
                
                # Detail of grades for selected subject
                with Vertical(id="grades-detail-col"):
                    yield Label(id="detail-subject-title", content="[bold #34d399]📝 Évaluations de la matière[/bold #34d399]")
                    yield DataTable(id="grades-table", cursor_type="row")

    def on_mount(self):
        # Configure Subjects table
        sub_table = self.query_one("#subjects-table", DataTable)
        sub_table.add_column("Matière", key="name", width=24)
        sub_table.add_column("Moy.", key="avg", width=8)
        sub_table.add_column("Jauge", key="bar", width=12)
        sub_table.add_column("Coeff", key="coeff", width=6)
        sub_table.add_column("Classe", key="class", width=8)
        sub_table.add_column("Écart", key="diff", width=8)
        sub_table.add_column("Min - Max", key="range", width=12)

        # Configure Grades table
        grades_table = self.query_one("#grades-table", DataTable)
        grades_table.add_column("Date", key="date", width=9)
        grades_table.add_column("Intitulé / Évaluation", key="title", width=22)
        grades_table.add_column("Note", key="value", width=11)
        grades_table.add_column("Coeff", key="coeff", width=6)
        grades_table.add_column("Moy. Cl.", key="class_avg", width=9)

    def update_data(self, subjects: List[SubjectAverage], overall: OverallAverage):
        self.subjects = subjects
        self.overall = overall

        # Calculate high/low
        valid_subs = [s for s in self.subjects if s.student_avg is not None]
        top_sub = max(valid_subs, key=lambda x: x.student_avg).subject if valid_subs else "-"
        top_val = max(valid_subs, key=lambda x: x.student_avg).student_avg if valid_subs else 0.0

        # Render summary banner
        summary_widget = self.query_one("#notes-summary-card", Static)
        mg = self.overall.student_avg or 0.0
        mc = self.overall.class_avg or 0.0
        diff = mg - mc
        diff_str = f"+{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
        diff_color = "#34d399" if diff >= 0 else "#f43f5e"
        
        banner_content = (
            f"[bold white]🎯 MOYENNE GÉNÉRALE :[/bold white] {format_avg(mg)} / 20.00   |   "
            f"[bold white]👥 Classe :[/bold white] {format_avg(mc)} ([bold {diff_color}]{diff_str}[/bold {diff_color}])   |   "
            f"[bold white]📉 Min :[/bold white] {format_avg(self.overall.min_avg)}   |   "
            f"[bold white]📈 Max :[/bold white] {format_avg(self.overall.max_avg)}   |   "
            f"[bold #34d399]🏆 Top :[/bold #34d399] {top_sub[:14]} ({top_val:.2f})"
        )
        summary_widget.update(banner_content)

        # Populate subjects table
        sub_table = self.query_one("#subjects-table", DataTable)
        sub_table.clear()
        
        for idx, s in enumerate(self.subjects):
            range_str = f"{s.min_avg or 0:.1f}-{s.max_avg or 20:.1f}"
            
            # Visual bar
            val = s.student_avg or 0.0
            filled = max(0, min(8, int(round((val / 20.0) * 8))))
            bar_color = "#34d399" if val >= 14 else ("#38bdf8" if val >= 12 else ("#fbbf24" if val >= 10 else "#f43f5e"))
            bar_visual = f"[{bar_color}]{'█' * filled}{'░' * (8 - filled)}[/{bar_color}]"

            # Difference vs class
            s_diff = (s.student_avg - s.class_avg) if (s.student_avg is not None and s.class_avg is not None) else None
            if s_diff is not None:
                s_diff_str = f"+{s_diff:.1f}" if s_diff >= 0 else f"{s_diff:.1f}"
                s_diff_color = "#34d399" if s_diff >= 0 else "#f43f5e"
                diff_badge = f"[{s_diff_color}]{s_diff_str}[/{s_diff_color}]"
            else:
                diff_badge = "[dim]--[/dim]"

            sub_table.add_row(
                f"[bold white]{s.subject}[/bold white]",
                format_avg(s.student_avg),
                bar_visual,
                f"{s.coeff:g}",
                format_avg(s.class_avg),
                diff_badge,
                f"[dim]{range_str}[/dim]",
                key=str(idx)
            )

        if self.subjects:
            self.show_subject_grades(0)
            sub_table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id == "subjects-table":
            try:
                row_idx = int(event.row_key.value)
                self.show_subject_grades(row_idx)
            except (ValueError, TypeError):
                pass

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id == "subjects-table":
            try:
                row_idx = int(event.row_key.value)
                self.show_subject_grades(row_idx)
            except (ValueError, TypeError):
                pass

    def show_subject_grades(self, index: int):
        if index < 0 or index >= len(self.subjects):
            return
        self.current_subject_index = index
        sub = self.subjects[index]

        title_lbl = self.query_one("#detail-subject-title", Label)
        avg_str = f" • Moy: [bold]{sub.student_avg:.2f}/20[/bold]" if sub.student_avg is not None else ""
        title_lbl.update(f"[bold #34d399]📝 {sub.subject}[/bold #34d399] [dim]({len(sub.grades)} évaluations{avg_str})[/dim]")

        grades_table = self.query_one("#grades-table", DataTable)
        grades_table.clear()

        for g in sub.grades:
            d_str = g.date.strftime("%d/%m") if g.date else "--/--"
            grades_table.add_row(
                d_str,
                g.title[:22],
                format_grade(g.value, g.out_of),
                f"{g.coeff:g}",
                format_avg(g.class_avg),
                key=g.id
            )

    def action_switch_table(self):
        sub_table = self.query_one("#subjects-table", DataTable)
        grades_table = self.query_one("#grades-table", DataTable)
        if sub_table.has_focus:
            grades_table.focus()
        else:
            sub_table.focus()

    def action_row_down(self):
        for table in [self.query_one("#subjects-table", DataTable), self.query_one("#grades-table", DataTable)]:
            if table.has_focus:
                table.action_cursor_down()
                break

    def action_row_up(self):
        for table in [self.query_one("#subjects-table", DataTable), self.query_one("#grades-table", DataTable)]:
            if table.has_focus:
                table.action_cursor_up()
                break
