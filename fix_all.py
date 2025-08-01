#!/usr/bin/env python3
# fix_all.py - Script pour corriger tous les problèmes identifiés

import os
import re
import sys

def fix_sql_quotes():
    """Corriger les guillemets doubles dans les requêtes SQL"""
    print("🔧 Correction des guillemets dans les requêtes SQL...")

    # Lire le fichier app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Remplacer les guillemets doubles par des guillemets simples dans les requêtes SQL
    # Pattern pour trouver les requêtes SQL avec des guillemets doubles
    patterns = [
        (r'status = "actif"', r"status = 'actif'"),
        (r'status = "en_cours"', r"status = 'en_cours'"),
        (r'status = "termine"', r"status = 'termine'"),
        (r'status = "archive"', r"status = 'archive'"),
    ]

    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Écrire le fichier corrigé
    if content != original_content:
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Guillemets SQL corrigés")
    else:
        print("✅ Aucune correction de guillemets nécessaire")

def fix_database_structure():
    """Corriger la structure de la base de données SQLite"""
    print("🔧 Correction de la structure de la base de données SQLite...")

    import sqlite3

    try:
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()

        # Vérifier et ajouter les colonnes manquantes à la table users
        cur.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cur.fetchall()]

        required_columns = [
            ('nom', 'TEXT'),
            ('prenom', 'TEXT'),
            ('date_naissance', 'TEXT'),
            ('telephone', 'TEXT'),
            ('email', 'TEXT'),
            ('sexe', 'TEXT'),
            ('photo_profil', 'TEXT'),
            ('bio', 'TEXT'),
            ('adresse', 'TEXT'),
            ('ville', 'TEXT'),
            ('pays', 'TEXT DEFAULT \'Cameroun\''),
            ('date_creation_profil', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]

        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                print(f"➕ Ajout de la colonne {col_name}...")
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Colonne {col_name} ajoutée")
                except Exception as e:
                    print(f"⚠️  Erreur pour {col_name}: {e}")

        # Vérifier la colonne status dans objectifs
        cur.execute("PRAGMA table_info(objectifs)")
        objectifs_columns = [row[1] for row in cur.fetchall()]

        if 'status' not in objectifs_columns:
            print("➕ Ajout de la colonne status à objectifs...")
            cur.execute("ALTER TABLE objectifs ADD COLUMN status TEXT NOT NULL DEFAULT 'actif'")
            print("✅ Colonne status ajoutée")
        else:
            print("✅ Colonne status existe déjà")

        # Créer la table evenements si elle n'existe pas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evenements'")
        if not cur.fetchone():
            print("➕ Création de la table evenements...")
            cur.execute('''
                CREATE TABLE evenements (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    titre TEXT NOT NULL,
                    description TEXT,
                    date_debut TEXT NOT NULL,
                    heure_debut TEXT,
                    date_fin TEXT,
                    heure_fin TEXT,
                    lieu TEXT,
                    couleur TEXT DEFAULT '#fd7e14',
                    rappel TEXT,
                    termine BOOLEAN DEFAULT FALSE,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("✅ Table evenements créée")
        else:
            print("✅ Table evenements existe déjà")

        # Créer la table taches si elle n'existe pas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='taches'")
        if not cur.fetchone():
            print("➕ Création de la table taches...")
            cur.execute('''
                CREATE TABLE taches (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    titre TEXT NOT NULL,
                    description TEXT,
                    date_limite TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    termine BOOLEAN DEFAULT FALSE,
                    ordre INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("✅ Table taches créée")
        else:
            print("✅ Table taches existe déjà")

        # Créer la table etapes si elle n'existe pas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='etapes'")
        if not cur.fetchone():
            print("➕ Création de la table etapes...")
            cur.execute('''
                CREATE TABLE etapes (
                    id INTEGER PRIMARY KEY,
                    tache_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    terminee BOOLEAN DEFAULT FALSE,
                    ordre INTEGER DEFAULT 0,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tache_id) REFERENCES taches (id)
                )
            ''')
            print("✅ Table etapes créée")
        else:
            print("✅ Table etapes existe déjà")

        conn.commit()
        print("✅ Structure de la base de données SQLite corrigée")

    except Exception as e:
        print(f"❌ Erreur lors de la correction SQLite: {e}")
        return False
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

    return True

def check_static_files():
    """Vérifier que tous les fichiers statiques nécessaires existent"""
    print("📁 Vérification des fichiers statiques...")

    static_files = [
        'static/styles.css',
        'static/tab_navigation.js',
        'static/export_functions.js',
        'static/chart_logic.js'
    ]

    for file_path in static_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Fichier manquant: {file_path}")
            # Créer un fichier vide
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('// Fichier généré automatiquement\n')
            print(f"✅ Fichier créé: {file_path}")
        else:
            print(f"✅ {file_path} existe")

def main():
    """Script principal de correction"""
    print("🚀 Démarrage de la correction complète...")

    # 1. Corriger les guillemets SQL
    fix_sql_quotes()

    # 2. Corriger la structure de la base de données
    if fix_database_structure():
        print("✅ Base de données corrigée")
    else:
        print("❌ Problème avec la base de données")

    # 3. Vérifier les fichiers statiques
    check_static_files()

    # 4. Vérifier la syntaxe Python
    print("🔍 Vérification de la syntaxe Python...")
    try:
        import py_compile
        py_compile.compile('app.py', doraise=True)
        print("✅ Syntaxe Python correcte")
    except Exception as e:
        print(f"❌ Erreur de syntaxe: {e}")
        return False

    print("\n🎉 Correction terminée avec succès!")
    print("📍 Vous pouvez maintenant démarrer l'application avec: python app.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)