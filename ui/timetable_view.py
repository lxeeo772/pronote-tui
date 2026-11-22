from __future__ import annotations
from datetime import date, timedelta
from typing import List
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Static, Button, Label, Rule
from textual.message import Message
from textual.binding import Binding

from ..data_provider import LessonItem

FRENCH_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
FRENCH_MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

def get_subject_card_class(subject_name: str) -> str:
    sub = subject_name.lower()
    if "math" in sub:
        return "lesson-card lesson-card-maths"
    if "nsi" in sub or "info" in sub or "numérique" in sub:
        return "lesson-card lesson-card-nsi"
    if "philo" in sub:
        return "lesson-card lesson-card-philo"
    if "hist" in sub or "géo" in sub:
        return "lesson-card lesson-card-hg"
    if "anglais" in sub or "espagnol" in sub or "allemand" in sub or "lv" in sub:
        return "lesson-card lesson-card-lang"
    return "lesson-card"

class TimetableView(Container):
    """Vue Emploi du Temps au jour le jour avec navigation fluide."""

    can_focus = True

    BINDINGS = [
        Binding("left", "prev_day", "Jour -1", show=False),
        Binding("right", "next_day", "Jour +1", show=False),
        Binding("h", "prev_day", "Jour -1", show=False),
        Binding("l", "next_day", "Jour +1", show=False),
        Binding("p", "prev_day", "Jour -1", show=False),
        Binding("n", "next_day", "Jour +1", show=False),
        Binding("t", "go_today", "Aujourd'hui", show=False),
    ]

    class DateChanged(Message):
        def __init__(self, new_date: date):
            self.new_date = new_date
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date: date = date.today()
        if self.current_date.weekday() >= 5:
            self.current_date += timedelta(days=(7 - self.current_date.weekday()))
        self.lessons: List[LessonItem] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            # Navigation Header
            with Horizontal(id="timetable-nav"):
                yield Button("◀ [h/←] Précédent", id="btn-prev-day", variant="default")
                yield Label(id="timetable-date-label", content="Chargement...")
                yield Button("🎯 [t] Aujourd'hui", id="btn-today", variant="primary")
                yield Button("Suivant [l/→] ▶", id="btn-next-day", variant="default")
            
            yield ScrollableContainer(id="lessons-container")

    def update_lessons(self, lessons: List[LessonItem]):
        self.lessons = lessons
        day_name = FRENCH_DAYS[self.current_date.weekday()]
        month_name = FRENCH_MONTHS[self.current_date.month - 1]
        is_today = (self.current_date == date.today())
        today_badge = " [bold #34d399](Aujourd'hui)[/bold #34d399]" if is_today else ""
        date_str = f"📅 {day_name} {self.current_date.day} {month_name} {self.current_date.year}{today_badge} • {len(lessons)} cours"
        
        self.query_one("#timetable-date-label", Label).update(f"[bold #38bdf8]{date_str}[/bold #38bdf8]")
        
        container = self.query_one("#lessons-container", ScrollableContainer)
        container.remove_children()

        if not lessons:
            container.mount(Static(
                "[bold #34d399]🎉 Aucun cours prévu pour cette journée (Repos !)[/bold #34d399]\n"
                "[dim]Utilisez [h/←] ou [l/→] pour naviguer entre les journées.[/dim]",
                classes="empty-msg"
            ))
            return

        for lesson in lessons:
            if lesson.is_cancelled:
                card_class = "lesson-card-cancelled"
            elif lesson.is_modified or lesson.status:
                card_class = "lesson-card-modified"
            else:
                card_class = get_subject_card_class(lesson.subject)
            
            status_badge = ""
            if lesson.is_cancelled:
                reason = lesson.status or "Cours annulé"
                status_badge = f"   [bold white on #ef4444] ⛔ COURS ANNULÉ [/] [bold red]{reason}[/bold red]"
            elif lesson.status:
                status_badge = f"   [bold black on #f59e0b] ⚠️ MODIFIÉ [/] [bold yellow]{lesson.status}[/bold yellow]"

            card_content = (
                f"[bold #38bdf8]🕒 {lesson.start_time} ➔ {lesson.end_time}[/bold #38bdf8]   "
                f"[bold white]{lesson.subject}[/bold white]{status_badge}\n"
                f"[dim]Salle :[/dim] [bold #34d399]📍 {lesson.room}[/bold #34d399]    "
                f"[dim]Professeur :[/dim] [italic #94a3b8]👤 {lesson.teacher or 'Non renseigné'}[/italic #94a3b8]"
            )
            container.mount(Static(card_content, classes=card_class))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-prev-day":
            self.prev_day()
        elif event.button.id == "btn-next-day":
            self.next_day()
        elif event.button.id == "btn-today":
            self.go_today()

    def action_prev_day(self):
        self.prev_day()

    def action_next_day(self):
        self.next_day()

    def action_go_today(self):
        self.go_today()

    def prev_day(self):
        delta = 3 if self.current_date.weekday() == 0 else 1
        self.current_date -= timedelta(days=delta)
        self.post_message(self.DateChanged(self.current_date))

    def next_day(self):
        delta = 3 if self.current_date.weekday() == 4 else 1
        self.current_date += timedelta(days=delta)
        self.post_message(self.DateChanged(self.current_date))

    def go_today(self):
        self.current_date = date.today()
        self.post_message(self.DateChanged(self.current_date))
