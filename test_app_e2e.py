"""Test end-to-end complet de l'application PronotermApp."""
import asyncio
from textual.widgets import DataTable, Input, Select, Button, Static

try:
    from pronoterm.app import PronotermApp
    from pronoterm.ui.notes_view import NotesView
    from pronoterm.ui.timetable_view import TimetableView
    from pronoterm.ui.homework_view import HomeworkView
    from pronoterm.ui.simulator_view import SimulatorView
    from pronoterm.ui.vie_scolaire_view import VieScolaireView
    from pronoterm.ui.login_screen import LoginModal
    from pronoterm.ui.help_screen import HelpModal
except ImportError:
    from app import PronotermApp
    from ui.notes_view import NotesView
    from ui.timetable_view import TimetableView
    from ui.homework_view import HomeworkView
    from ui.simulator_view import SimulatorView
    from ui.vie_scolaire_view import VieScolaireView
    from ui.login_screen import LoginModal
    from ui.help_screen import HelpModal


async def test_pronoterm_app_full():
    app = PronotermApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # 1. Vérifier l'en-tête et la bannière
        assert app.query_one("#student-name") is not None
        assert app.query_one("#banner-badge-status") is not None
        assert app.query_one("#banner-mg-box") is not None

        # 2. Vérifier que la vue Notes est affichée
        notes_view = app.query_one("#view-notes", NotesView)
        assert notes_view is not None
        sub_table = app.query_one("#subjects-table", DataTable)
        assert sub_table.row_count > 0

        # 3. Basculer vers Emploi du Temps [2]
        await pilot.press("2")
        await pilot.pause()
        tt_view = app.query_one("#view-timetable", TimetableView)
        assert tt_view is not None
        # Tester navigation jour suivant / précédent
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("left")
        await pilot.pause()
        await pilot.press("t")
        await pilot.pause()

        # 4. Basculer vers Devoirs [3]
        await pilot.press("3")
        await pilot.pause()
        hw_view = app.query_one("#view-homework", HomeworkView)
        assert hw_view is not None
        # Cocher / Décocher un devoir avec 'd' ou 'space'
        initial_done = hw_view.homework[0].done if hw_view.homework else False
        await pilot.press("d")
        await pilot.pause()

        # 5. Basculer vers Simulateur [4]
        await pilot.press("4")
        await pilot.pause()
        sim_grade_input = app.query_one("#sim-input-grade", Input)
        assert sim_grade_input.has_focus
        sim_grade_input.value = "18.5"
        await pilot.press("enter")
        await pilot.pause()
        sim_result = app.query_one("#sim-result-box", Static)
        assert "18.50" in str(sim_result.render())

        # 6. Basculer vers Vie Scolaire [5]
        await pilot.press("5")
        await pilot.pause()
        assert app.query_one("#kpi-total-abs") is not None
        assert app.query_one("#absences-table", DataTable).row_count > 0

        # 7. Tester l'ouverture de l'Aide
        app.action_open_help()
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)
        await pilot.press("escape")
        await pilot.pause()

        # 8. Tester l'ouverture de la Connexion
        app.action_open_login()
        await pilot.pause()
        assert isinstance(app.screen, LoginModal)
        login_modal = app.screen
        # Tester la recherche par code UAI
        login_modal.query_one("#city-search-input", Input).value = "0951104J"
        login_modal._trigger_city_search()
        await pilot.pause(0.2)
        # Vérifier que le lycée Jean Perrin est détecté
        url_input = login_modal.query_one("#login-input-url", Input)
        assert "0951104j" in url_input.value.lower()
        # Fermer la modal
        await pilot.press("escape")
        await pilot.pause()

    print("ALL E2E APP TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    asyncio.run(test_pronoterm_app_full())
