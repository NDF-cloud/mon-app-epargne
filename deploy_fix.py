#!/usr/bin/env python3
# deploy_fix.py - Script de déploiement et correction automatique

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Exécuter une commande avec gestion d'erreur"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de {description}: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False

def main():
    """Script principal de déploiement et correction"""
    print("🚀 Démarrage du processus de déploiement et correction...")

    # 1. Vérifier les dépendances
    print("\n📦 Vérification des dépendances...")
    if not run_command("pip install -r requirements.txt", "Installation des dépendances"):
        print("❌ Échec de l'installation des dépendances")
        return False

    # 2. Corriger la base de données SQLite locale
    print("\n🔧 Correction de la base de données SQLite...")
    if not run_command("python fix_db.py", "Correction de la base de données SQLite"):
        print("⚠️  Problème avec la correction SQLite, continuation...")

    # 3. Corriger la base de données PostgreSQL (si disponible)
    print("\n🔧 Correction de la base de données PostgreSQL...")
    if not run_command("python fix_postgres.py", "Correction de la base de données PostgreSQL"):
        print("⚠️  Problème avec la correction PostgreSQL, continuation...")

    # 4. Vérifier la syntaxe du code Python
    print("\n🔍 Vérification de la syntaxe Python...")
    if not run_command("python -m py_compile app.py", "Vérification de la syntaxe"):
        print("❌ Erreur de syntaxe dans app.py")
        return False

    # 5. Tester l'application
    print("\n🧪 Test de l'application...")
    test_command = "python -c \"import app; print('✅ Application importée avec succès')\""
    if not run_command(test_command, "Test d'import de l'application"):
        print("❌ Erreur lors du test de l'application")
        return False

    # 6. Démarrer l'application
    print("\n🚀 Démarrage de l'application...")
    print("📍 L'application sera accessible sur http://localhost:5000")
    print("📍 Pour arrêter l'application, appuyez sur Ctrl+C")

    try:
        # Démarrer l'application en mode développement
        subprocess.run("python app.py", shell=True, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application...")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False

    print("✅ Déploiement terminé avec succès!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)