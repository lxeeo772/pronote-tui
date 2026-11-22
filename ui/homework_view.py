from __future__ import annotations
from datetime import date
from typing import List
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Static, Button, Label, Rule
from textual.message import Message
from textual.binding import Binding

from ..data_provider import HomeworkItem

class HomeworkView(Container):
    """Vue Cahier de texte et devoirs avec navigation au clavier et bascule Fait / À faire."""

    can_focus = True

    BINDINGS = [
        Binding("up", "cursor_up", "Devoir précédent", show=False),
        Binding("k", "cursor_up", "Devoir précédent", show=False),
        Binding("down", "cursor_down", "Devoir suivant", show=False),
        Binding("j", "cursor_down", "Devoir suivant", show=False),
        Binding("space", "toggle_current", "Cocher/Décocher", show=False),
        Binding("d", "toggle_current", "Cocher/Décocher", show=False),
        Binding("enter", "toggle_current", "Cocher/Décocher", show=False),
    ]

    class ToggleHomework(Message):
        def __init__(self, hw_id: str, new_status: bool):
            self.hw_id = hw_id
            self.new_status = new_status
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.homework: List[HomeworkItem] = []
        self.selected_index: int = 0
        self._button_map: dict[Button, str] = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="hw-header-row"):
                yield Label(
                    "[bold #38bdf8]📝 Cahier de Texte & Devoirs[/bold #38bdf8]  "
                    "[dim]([bold white]↑/↓[/bold white] ou [bold white]j/k[/bold white] pour naviguer  •  "
                    "[bold #34d399]Espace[/bold #34d399] ou [bold #34d399]d[/bold #34d399] pour valider)[/dim]",
                    id="hw-header-label"
                )
            yield ScrollableContainer(id="hw-items-container")

    def update_homework(self, homework: List[HomeworkItem]):
        self.homework = sorted(homework, key=lambda x: (x.done, x.due_date))
        if self.selected_index >= len(self.homework):
            self.selected_index = max(0, len(self.homework) - 1)
        self._render_items()

    def _render_items(self):
        container = self.query_one("#hw-items-container", ScrollableContainer)
        container.remove_children()
        self._button_map.clear()

        if not self.homework:
            container.mount(Static(
                "[bold #34d399]🎉 Aucun devoir à faire ! Tout est propre.[/bold #34d399]",
                classes="empty-msg"
            ))
            return

        today = date.today()
        for idx, hw in enumerate(self.homework):
            days_left = (hw.due_date - today).days
            if days_left < 0:
                due_badge = f"[bold white on #ef4444] 🚨 EN RETARD ({hw.due_date.strftime('%d/%m')}) [/]"
            elif days_left == 0:
                due_badge = "[bold black on #f59e0b] ⚡ AUJOURD'HUI [/]"
            elif days_left == 1:
                due_badge = "[bold black on #38bdf8] ⏳ DEMAIN [/]"
            else:
                due_badge = f"[bold #94a3b8]📅 {hw.due_date.strftime('%d/%m')}[/bold #94a3b8] [dim]({days_left}j)[/dim]"

            status_icon = "[bold #34d399][✓ FAIT][/bold #34d399]" if hw.done else "[bold #f59e0b][□ À FAIRE][/bold #f59e0b]"
            cursor_icon = "[bold #34d399]▶ [/bold #34d399]" if idx == self.selected_index else "  "
            
            is_selected = (idx == self.selected_index)
            base_class = "hw-item hw-done" if hw.done else ("hw-item hw-overdue" if days_left < 0 else "hw-item hw-todo")
            row_class = f"{base_class} hw-item-selected" if is_selected else base_class

            desc_text = f"[dim strike]{hw.description}[/dim strike]" if hw.done else f"[italic #cbd5e1]{hw.description}[/italic #cbd5e1]"
            hw_card = (
                f"{cursor_icon}{status_icon}  [bold white on #162238] {hw.subject} [/bold white on #162238]  —  {due_badge}\n"
                f"    {desc_text}"
            )
            
            btn_text = "À refaire" if hw.done else "Terminer"
            btn_variant = "default" if hw.done else "success"
            btn = Button(btn_text, variant=btn_variant, classes="hw-btn-toggle")
            self._button_map[btn] = hw.id
            
            row = Horizontal(
                Static(hw_card, classes="hw-card-text"),
                btn,
                classes=row_class,
            )
            container.mount(row)

    def _refresh_selection(self):
        container = self.query_one("#hw-items-container", ScrollableContainer)
        children = list(container.children)
        for idx, child in enumerate(children):
            if idx == self.selected_index:
                child.add_class("hw-item-selected")
                child.scroll_visible(animate=False)
            else:
                child.remove_class("hw-item-selected")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button in self._button_map:
            hw_id = self._button_map[event.button]
            for idx, hw in enumerate(self.homework):
                if hw.id == hw_id:
                    self.selected_index = idx
                    self.post_message(self.ToggleHomework(hw_id, not hw.done))
                    break

    def action_cursor_up(self):
        if self.homework and self.selected_index > 0:
            self.selected_index -= 1
            self._refresh_selection()

    def action_cursor_down(self):
        if self.homework and self.selected_index < len(self.homework) - 1:
            self.selected_index += 1
            self._refresh_selection()

    def action_toggle_current(self):
        if self.homework and 0 <= self.selected_index < len(self.homework):
            target = self.homework[self.selected_index]
            self.post_message(self.ToggleHomework(target.id, not target.done))

    def toggle_selected_or_first(self):
        self.action_toggle_current()
