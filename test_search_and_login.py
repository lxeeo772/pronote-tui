"""Tests pour la recherche d'établissement style Papillon et l'écran de connexion."""
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Button, Static

try:
    from pronoterm.school_search import (
        search_schools_by_city, get_recommended_ent,
        open_school_login_page, SchoolInfo, FALLBACK_SCHOOLS
    )
    from pronoterm.config import AppConfig
    from pronoterm.ui.login_screen import LoginModal
except ImportError:
    from school_search import (
        search_schools_by_city, get_recommended_ent,
        open_school_login_page, SchoolInfo, FALLBACK_SCHOOLS
    )
    from config import AppConfig
    from ui.login_screen import LoginModal


def test_get_recommended_ent():
    assert get_recommended_ent("95310", "LYCEE JEAN PERRIN") == "ile_de_france"
    assert get_recommended_ent("95310", "COLLEGE LE PARC") == "val_doise"
    assert get_recommended_ent("75016", "LYCEE JANSON DE SAILLY") == "ile_de_france"
    assert get_recommended_ent("75012", "COLLEGE SAINT EXUPERY") == "paris_classe_numerique"
    assert get_recommended_ent("69006", "LYCEE DU PARC") == "ent_auvergnerhonealpe"
    assert get_recommended_ent("13001", "LYCEE THIERS") == "atrium_sud"
    assert get_recommended_ent("59000", "LYCEE FAIDHERBE") == "ent_hdf"


def test_fallback_search():
    city, cp, schools = search_schools_by_city("Saint-Ouen-l'Aumône", timeout=0.1)
    assert len(schools) > 0
    # Vérifier que le lycée Jean Perrin de l'utilisateur est présent
    jp = next((s for s in schools if "0951104" in s.url.lower()), None)
    assert jp is not None
    assert jp.postal_code == "95310"
    assert jp.ent_name == "ile_de_france"


async def test_login_modal_ui_flow():
    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Static("Test Root")

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        cfg = AppConfig()
        modal = LoginModal(cfg)
        await app.push_screen(modal)
        await pilot.pause()

        # 1. Vérifier que les widgets essentiels sont présents
        city_input = modal.query_one("#city-search-input", Input)
        btn_search = modal.query_one("#btn-search-city", Button)
        select_school = modal.query_one("#select-school", Select)
        url_input = modal.query_one("#login-input-url", Input)
        ent_select = modal.query_one("#login-select-ent", Select)
        btn_web = modal.query_one("#btn-open-web", Button)
        btn_qr = modal.query_one("#btn-toggle-qr", Button)

        assert city_input is not None
        assert btn_search is not None
        assert select_school is not None
        assert btn_web is not None

        # 2. Remplir une ville et déclencher la recherche
        city_input.value = "Saint-Ouen-l'Aumône"
        modal._trigger_city_search()
        await pilot.pause(0.2)

        # 3. Sélectionner Lycée Jean Perrin directement
        jp_school = next(s for s in FALLBACK_SCHOOLS if "0951104" in s.url.lower())
        modal._apply_school_selection(jp_school)
        await pilot.pause()

        assert "0951104j" in url_input.value.lower()
        assert ent_select.value == "ile_de_france"
        badge = modal.query_one("#school-info-badge", Static)
        assert "JEAN PERRIN" in str(badge.render())

        # 4. Tester le basculement en mode QR Code
        modal._toggle_qr_mode()
        await pilot.pause()
        assert modal._qr_mode is True
        assert modal.query_one("#qr-login-fields").display is True
        assert modal.query_one("#std-login-fields").display is False

        # 5. Rebasculer en mode standard
        modal._toggle_qr_mode()
        await pilot.pause()
        assert modal._qr_mode is False
        assert modal.query_one("#std-login-fields").display is True

        # 6. Tester le bouton Démo
        modal._fill_official_demo()
        await pilot.pause()
        assert "demo.index-education.net" in url_input.value

        # Fermer la modal
        modal.action_dismiss_modal()
        await pilot.pause()


if __name__ == "__main__":
    test_get_recommended_ent()
    test_fallback_search()
    asyncio.run(test_login_modal_ui_flow())
    print("ALL TESTS PASSED SUCCESSFULLY!")
