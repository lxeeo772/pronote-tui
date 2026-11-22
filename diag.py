#!/usr/bin/env python3
"""
Outil de diagnostic et de test de connexion Pronote.
Permet d'analyser une URL, de tester la recherche d'établissement (style Papillon),
de vérifier la joignabilité réseau et de tester l'authentification.
"""
import sys
import getpass
from pathlib import Path

# Assurer l'accès aux modules pronoterm
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pronoterm.config import normalize_pronote_url
from pronoterm.pronote_client import connect_pronote, check_pronote_url_warnings
from pronoterm.school_search import search_schools_by_city, open_school_login_page
import pronotepy.ent

def run_diagnostic():
    print("=" * 65)
    print(" 🛠️  DIAGNOSTIC DE CONNEXION PRONOTE (AVEC MÉTHODE PAPILLON)")
    print("=" * 65)
    print("\nQue souhaitez-vous tester ?")
    print(" [1] 🦋 Recherche automatique d'établissement par ville ou code postal (Style Papillon)")
    print(" [2] 🔐 Tester la connexion directe avec vos identifiants (ou ENT)")
    print(" [3] 🌐 Tester la connexion sur le serveur démo officiel d'Index-Education")
    
    mode = input("\nVotre choix (1, 2 ou 3, défaut: 1) : ").strip() or "1"

    if mode == "1":
        query = input("\nEntrez le nom de votre ville, votre code postal ou code UAI (ex: Saint-Ouen-l'Aumône, 95310, 0951104J) : ").strip()
        if not query:
            query = "Saint-Ouen-l'Aumône"
        print(f"\n🔍 Recherche en cours pour '{query}'...")
        city, cp, schools = search_schools_by_city(query)
        print(f"\n✅ Résultat : {len(schools)} établissement(s) trouvé(s) pour {city} ({cp}) :\n")
        for idx, s in enumerate(schools[:8], 1):
            print(f" {idx}. {s.display_label}")
            print(f"    ➔ URL Pronote : {s.url}")
            print(f"    ➔ ENT suggéré : {s.ent_name}\n")
        
        ouvrir = input("Voulez-vous ouvrir la page de connexion du 1er établissement dans votre navigateur ? (o/N) : ").strip().lower()
        if ouvrir in ("o", "oui", "y", "yes") and schools:
            print(f"🌐 Ouverture de {schools[0].url}...")
            open_school_login_page(schools[0].url)
        return

    if mode == "3":
        print("\n⏳ Test sur le serveur démo officiel (https://demo.index-education.net)...")
        try:
            provider = connect_pronote("https://demo.index-education.net/pronote/eleve.html", "demonstration", "pronotevs", "Aucun (Connexion directe)")
            profile = provider.get_profile()
            print("✅ SUCCÈS : Connecté au serveur de démonstration officiel !")
            print(f"• Profil : {profile.name} ({profile.school_name})")
        except Exception as e:
            print(f"❌ Échec démo : {e}")
        return

    # Mode 2: Test connexion directe
    url = input("\n1. Entrez l'URL de votre établissement : ").strip()
    if not url:
        print("❌ Erreur : URL vide.")
        return

    normalized_url = normalize_pronote_url(url)
    print(f"   ➔ URL normalisée : {normalized_url}")

    # Vérification détection ENT
    warnings = check_pronote_url_warnings(normalized_url)
    if warnings:
        print("\n⚠️  ATTENTION DÉTECTÉE :")
        for w in warnings:
            print(f"   {w}")

    # 2. Choix ENT
    print("\n2. Votre établissement utilise-t-il un ENT ?")
    print("   [0] Aucun (Connexion directe Pronote)")
    print("   [1] Île-de-France (MonLycée.net)")
    print("   [2] Paris Classe Numérique (PCN)")
    print("   [3] Mon Bureau Numérique (Grand Est)")
    print("   [4] Atrium Sud (PACA)")
    print("   [5] Lycée Connecté (Nouvelle-Aquitaine)")
    print("   [6] Éclat BFC")
    print("   [7] Autre (EduConnect, etc.)")
    choice = input("   Votre choix (0-7, défaut: 0) : ").strip() or "0"

    ent_mapping = {
        "0": "Aucun (Connexion directe)",
        "1": "ile_de_france",
        "2": "paris_classe_numerique",
        "3": "monbureaunumerique",
        "4": "atrium_sud",
        "5": "lyceeconnecte_edu",
        "6": "eclat_bfc",
        "7": "autre",
    }
    ent_name = ent_mapping.get(choice, "Aucun (Connexion directe)")
    if ent_name == "autre":
        ent_name = input("   Nom technique de l'ENT (ex: cas_arsene76_edu) : ").strip()

    print(f"   ➔ ENT sélectionné : {ent_name}")

    # 3. Identifiants
    username = input("\n3. Identifiant : ").strip()
    password = getpass.getpass("4. Mot de passe : ").strip()

    print("\n⏳ Test de connexion en cours (timeout: 12s)...")
    try:
        provider = connect_pronote(normalized_url, username, password, ent_name)
        profile = provider.get_profile()
        print("\n" + "=" * 65)
        print(" ✅ CONNEXION RÉUSSIE AVEC SUCCÈS !")
        print("=" * 65)
        print(f"• Élève : {profile.name} ({profile.class_name})")
        print(f"• Établissement : {profile.school_name}")
        print(f"• Période : {profile.period_name}")
    except Exception as exc:
        print("\n" + "=" * 65)
        print(" ❌ ÉCHEC DE LA CONNEXION")
        print("=" * 65)
        print(f"Raison détectée : {exc}")
        print("\n💡 Conseils :")
        print("1. Vous pouvez ouvrir la page de connexion dans votre navigateur pour vous authentifier directement.")
        print("2. Vous pouvez utiliser le Mode Code QR & PIN (alternative Papillon sans mot de passe).")
        print("3. Vous pouvez lancer le Mode Démo pour utiliser l'interface immédiatement.")

if __name__ == "__main__":
    run_diagnostic()
