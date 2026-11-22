from __future__ import annotations
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button, Label, Rule
from textual.binding import Binding

HELP_MARKDOWN = """
### ⌨️ Raccourcis Clavier Pronote-TUI (100% piloté au clavier)

* **Navigation par onglets (claviers AZERTY, QWERTY, Pavé Numérique & F-Keys) :**
  * `1` / `&` / `F1` : 📊 **Notes & Moyennes** (détail par matière, coefficients, min/max)
  * `2` / `é` / `F2` : 📅 **Emploi du Temps** (cours, salles, profs, annulations)
  * `3` / `"` / `F3` : 📝 **Devoirs** (cahier de texte, travail à faire)
  * `4` / `'` / `F4` : 🔮 **Simulateur** (simulation de note, calcul d'objectif)
  * `5` / `(` / `F5` : 📯 **Vie Scolaire** (absences, retards, retenues)
  * `Ctrl + →` / `Ctrl + ←` : Onglet suivant / précédent

* **Onglet Notes [1] :**
  * `Tab` / `Maj+Tab` : Basculer entre les matières et le tableau des notes
  * `↑` / `↓` ou `j` / `k` : Faire défiler les matières

* **Onglet Emploi du Temps [2] :**
  * `←` / `h` / `p` : Jour précédent
  * `→` / `l` / `n` : Jour suivant
  * `t` / `Origine` : Revenir à aujourd'hui

* **Onglet Devoirs [3] :**
  * `↑` / `↓` ou `j` / `k` : Sélectionner un devoir
  * `Espace` ou `d` ou `Entrée` : Marquer comme **Fait / À faire**

* **Onglet Simulateur [4] :**
  * `Entrée` dans n'importe quel champ pour calculer immédiatement

* **Général :**
  * `c` : Menu de **Connexion Pronote En Ligne** / Mode Démo
  * `r` : **Actualiser** les données
  * `?` / `/` : Ouvrir cette aide
  * `Echap` : Fermer une boîte de dialogue (modal)
  * `q` : **Quitter** l'application

---

### 🦋 Connexion Facile (Méthode Papillon)

1. **Recherche automatique de votre lycée / collège :**
   * Appuyez sur `c` pour ouvrir l'écran de connexion.
   * Tapez simplement le **nom de votre ville** ou votre **code postal** (ex: *Saint-Ouen-l'Aumône*, *95310*, *Paris*, *Lyon*).
   * Cliquez sur **🔍 Chercher** (ou appuyez sur Entrée). Pronoterm localise les lycées et collèges de votre commune.
   * Sélectionnez votre établissement dans la liste : l'URL Pronote et l'ENT sont automatiquement configurés !

2. **Redirection vers la page de connexion :**
   * Cliquez sur **🌐 Ouvrir la page de connexion du lycée** pour ouvrir directement le portail officiel de votre lycée dans votre navigateur.

3. **Connexion par Code QR / PIN (Alternative Mobile) :**
   * Dans votre navigateur sur Pronote, cliquez sur le petit logo QR Code à côté de votre nom.
   * Choisissez un code PIN à 4 chiffres (ex: 1234).
   * Dans Pronoterm, activez **📱 Mode Code QR / PIN**, collez le code et saisissez votre PIN pour une connexion instantanée sans mot de passe !

4. **Tester sans identifiants :**
   * Dans l'écran de connexion (`c`), cliquez sur **'🌐 Démo Publique'** pour tester le serveur officiel d'Index-Education, ou sur **'Mode Démo'** pour naviguer hors-ligne.
"""

class HelpModal(ModalScreen):
    """Modal d'aide avec la liste complète des raccourcis clavier et guide de connexion."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Fermer [Echap]"),
        Binding("enter", "dismiss_modal", "Fermer [Entrée]"),
        Binding("q", "dismiss_modal", "Fermer [q]"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("[bold #38bdf8]❓ Guide Pronote-TUI & Aide Connexion[/bold #38bdf8]")
            yield Rule()
            yield Static(HELP_MARKDOWN)
            yield Button("Fermer [Echap ou Entrée]", id="btn-close-help", variant="primary")

    def action_dismiss_modal(self):
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-close-help":
            self.action_dismiss_modal()
