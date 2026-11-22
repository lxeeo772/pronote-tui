from __future__ import annotations
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Static, Input, Select, Button, Label, Rule

from ..data_provider import SubjectAverage, OverallAverage

class SimulatorView(Container):
    """Simulateur de moyenne prévisionnelle et calculateur d'objectif."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subjects: List[SubjectAverage] = []
        self.overall = OverallAverage()

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="sim-container"):
            # Section 1: Note Simulation
            with Vertical(classes="sim-section-card"):
                yield Label("[bold #38bdf8]🔮 1. Simuler une Prochaine Note[/bold #38bdf8]")
                yield Label("[dim]Visualisez immédiatement l'impact d'une note sur la matière et la moyenne générale (Entrée pour valider).[/dim]")
                yield Rule()

                with Horizontal(classes="sim-row"):
                    with Vertical(classes="sim-col-40"):
                        yield Label("Matière :")
                        yield Select([], id="sim-select-subject", prompt="Choisir une matière...")
                    
                    with Vertical(classes="sim-col-25"):
                        yield Label("Note simulée (/20) :")
                        yield Input(placeholder="ex: 16.5", id="sim-input-grade")
                    
                    with Vertical(classes="sim-col-20"):
                        yield Label("Coeff :")
                        yield Input(value="2.0", id="sim-input-coeff")
                    
                    with Vertical(classes="sim-col-15"):
                        yield Label(" ")
                        yield Button("Simuler", id="sim-btn-calc", variant="primary")

                yield Static(id="sim-result-box", classes="sim-result-card")

            # Section 2: Goal Calculator
            with Vertical(classes="sim-section-card"):
                yield Label("[bold #34d399]🎯 2. Calculateur d'Objectif de Moyenne[/bold #34d399]")
                yield Label("[dim]Déterminez la note exacte nécessaire pour atteindre la moyenne souhaitée au prochain devoir.[/dim]")
                yield Rule()
                
                with Horizontal(classes="sim-row"):
                    with Vertical(classes="sim-col-40"):
                        yield Label("Matière cible :")
                        yield Select([], id="goal-select-subject", prompt="Choisir une matière...")
                    with Vertical(classes="sim-col-25"):
                        yield Label("Moyenne visée (/20) :")
                        yield Input(placeholder="ex: 15.0", id="goal-input-target")
                    with Vertical(classes="sim-col-20"):
                        yield Label("Coeff du devoir :")
                        yield Input(value="2.0", id="goal-input-coeff")
                    with Vertical(classes="sim-col-15"):
                        yield Label(" ")
                        yield Button("Calculer", id="goal-btn-calc", variant="success")

                yield Static(id="goal-result-box", classes="sim-result-card")

    def update_data(self, subjects: List[SubjectAverage], overall: OverallAverage):
        self.subjects = subjects
        self.overall = overall

        options = [(s.subject, s.subject) for s in self.subjects]
        
        sim_select = self.query_one("#sim-select-subject", Select)
        sim_select.set_options(options)
        if options:
            sim_select.value = options[0][0]

        goal_select = self.query_one("#goal-select-subject", Select)
        goal_select.set_options(options)
        if options:
            goal_select.value = options[0][0]

        self.query_one("#sim-result-box", Static).update(
            "[dim italic]Saisissez une note et un coeff, puis appuyez sur Entrée ou cliquez sur 'Simuler'.[/dim italic]"
        )
        self.query_one("#goal-result-box", Static).update(
            "[dim italic]Indiquez votre objectif et appuyez sur Entrée pour calculer la note requise.[/dim italic]"
        )

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id in ("sim-input-grade", "sim-input-coeff"):
            self.calculate_simulation()
        elif event.input.id in ("goal-input-target", "goal-input-coeff"):
            self.calculate_goal()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "sim-btn-calc":
            self.calculate_simulation()
        elif event.button.id == "goal-btn-calc":
            self.calculate_goal()

    def calculate_simulation(self):
        sim_select = self.query_one("#sim-select-subject", Select)
        grade_input = self.query_one("#sim-input-grade", Input)
        coeff_input = self.query_one("#sim-input-coeff", Input)
        res_box = self.query_one("#sim-result-box", Static)

        sub_name = sim_select.value
        if not sub_name:
            res_box.update("[bold red]⚠️ Veuillez sélectionner une matière.[/bold red]")
            return

        try:
            sim_grade = float(grade_input.value.replace(",", "."))
            sim_coeff = float(coeff_input.value.replace(",", "."))
            if sim_grade < 0 or sim_grade > 20 or sim_coeff <= 0:
                raise ValueError()
        except ValueError:
            res_box.update("[bold red]⚠️ Veuillez entrer une note valide entre 0 et 20 et un coefficient positif.[/bold red]")
            return

        subject = next((s for s in self.subjects if s.subject == sub_name), None)
        if not subject:
            return

        existing_pts = sum(g.value * (20.0 / g.out_of) * g.coeff for g in subject.grades)
        existing_coeff = sum(g.coeff for g in subject.grades)

        if existing_coeff == 0:
            new_sub_avg = sim_grade
            old_sub_avg = subject.student_avg or 0.0
        else:
            old_sub_avg = existing_pts / existing_coeff
            new_sub_avg = (existing_pts + sim_grade * sim_coeff) / (existing_coeff + sim_coeff)

        sub_diff = new_sub_avg - old_sub_avg
        sub_diff_str = f"+{sub_diff:.2f}" if sub_diff >= 0 else f"{sub_diff:.2f}"
        sub_diff_color = "#34d399" if sub_diff >= 0 else "#f43f5e"

        total_pts_old = sum(s.student_avg * s.coeff for s in self.subjects if s.student_avg is not None)
        total_coeff = sum(s.coeff for s in self.subjects if s.student_avg is not None)

        if total_coeff > 0:
            total_pts_new = total_pts_old - ((subject.student_avg or old_sub_avg) * subject.coeff) + (new_sub_avg * subject.coeff)
            new_overall = total_pts_new / total_coeff
            old_overall = self.overall.student_avg or 0.0
            ov_diff = new_overall - old_overall
            ov_diff_str = f"+{ov_diff:.2f}" if ov_diff >= 0 else f"{ov_diff:.2f}"
            ov_diff_color = "#34d399" if ov_diff >= 0 else "#f43f5e"
        else:
            new_overall = new_sub_avg
            ov_diff_str = "+0.00"
            ov_diff_color = "#34d399"

        res_box.update(
            f"[bold white]📊 Résultat de la simulation pour [bold #38bdf8]{sub_name}[/bold #38bdf8] :[/bold white]\n"
            f"• Note simulée : [bold yellow]{sim_grade:.2f}/20[/bold yellow] (coeff {sim_coeff:g})\n"
            f"• Moyenne de la matière : [dim]{old_sub_avg:.2f}[/dim] ➔ [bold {sub_diff_color}]{new_sub_avg:.2f}/20[/bold {sub_diff_color}] ([bold {sub_diff_color}]{sub_diff_str}[/bold {sub_diff_color}])\n"
            f"• Moyenne Générale : [dim]{self.overall.student_avg or 0:.2f}[/dim] ➔ [bold {ov_diff_color}]{new_overall:.2f}/20[/bold {ov_diff_color}] ([bold {ov_diff_color}]{ov_diff_str}[/bold {ov_diff_color}])"
        )

    def calculate_goal(self):
        goal_select = self.query_one("#goal-select-subject", Select)
        target_input = self.query_one("#goal-input-target", Input)
        coeff_input = self.query_one("#goal-input-coeff", Input)
        res_box = self.query_one("#goal-result-box", Static)

        sub_name = goal_select.value
        if not sub_name:
            res_box.update("[bold red]⚠️ Veuillez choisir une matière cible.[/bold red]")
            return

        try:
            target_avg = float(target_input.value.replace(",", "."))
            coeff = float(coeff_input.value.replace(",", "."))
            if target_avg < 0 or target_avg > 20 or coeff <= 0:
                raise ValueError()
        except ValueError:
            res_box.update("[bold red]⚠️ Veuillez entrer un objectif entre 0 et 20 et un coeff valide.[/bold red]")
            return

        subject = next((s for s in self.subjects if s.subject == sub_name), None)
        if not subject:
            return

        existing_pts = sum(g.value * (20.0 / g.out_of) * g.coeff for g in subject.grades)
        existing_coeff = sum(g.coeff for g in subject.grades)

        required_grade = (target_avg * (existing_coeff + coeff) - existing_pts) / coeff

        if required_grade > 20.0:
            res_box.update(
                f"[bold red]❌ Objectif inaccessible sur un seul devoir ![/bold red]\n"
                f"Il faudrait obtenir la note de [bold red]{required_grade:.2f}/20[/bold red] (coeff {coeff:g})."
            )
        elif required_grade < 0.0:
            res_box.update(
                f"[bold #34d399]🎉 Objectif déjà acquis ![/bold #34d399]\n"
                f"Même avec un 0/20 au prochain devoir, votre moyenne restera au-dessus de [bold]{target_avg:.2f}/20[/bold]."
            )
        else:
            res_box.update(
                f"[bold white]🎯 Pour atteindre [bold #34d399]{target_avg:.2f}/20[/bold #34d399] en [bold #38bdf8]{sub_name}[/bold #38bdf8] :[/bold white]\n"
                f"➔ Vous devez obtenir au minimum : [bold #fbbf24]{required_grade:.2f}/20[/bold #fbbf24] au prochain devoir (coeff {coeff:g})."
            )
