#!/usr/bin/env python3
"""
Script pour corriger la base de données SQLite en ajoutant les colonnes manquantes
"""

import sqlite3
import os

def fix_database():
    """Ajoute les colonnes manquantes à la base de données SQLite"""

    # Chemin vers la base de données SQLite
    db_path = 'epargne.db'

    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée. Créez d'abord la base de données.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # Vérifier les colonnes existantes dans la table users
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        print(f"Colonnes existantes dans la table users: {columns}")

        # Liste des colonnes à ajouter
        columns_to_add = [
            ('display_currency', 'BOOLEAN DEFAULT 1'),
            ('display_progress', 'BOOLEAN DEFAULT 1'),
            ('notification_enabled', 'BOOLEAN DEFAULT 1'),
            ('auto_delete_completed', 'BOOLEAN DEFAULT 0'),
            ('auto_delete_days', 'INTEGER DEFAULT 90'),
            ('countdown_enabled', 'BOOLEAN DEFAULT 1'),
            ('countdown_days', 'INTEGER DEFAULT 30'),
            ('default_currency', 'TEXT DEFAULT "XAF"'),
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
            ('pays', 'TEXT DEFAULT "Cameroun"'),
            ('date_creation_profil', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]

        # Ajouter les colonnes manquantes
        added_columns = []
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"✅ Colonne '{column_name}' ajoutée")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erreur lors de l'ajout de '{column_name}': {e}")

        # Vérifier les colonnes dans la table objectifs
        cur.execute("PRAGMA table_info(objectifs)")
        objectif_columns = [column[1] for column in cur.fetchall()]
        print(f"Colonnes existantes dans la table objectifs: {objectif_columns}")

        # Ajouter les colonnes manquantes pour objectifs
        objectif_columns_to_add = [
            ('date_creation', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('date_modification', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]

        for column_name, column_type in objectif_columns_to_add:
            if column_name not in objectif_columns:
                try:
                    cur.execute(f"ALTER TABLE objectifs ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne '{column_name}' ajoutée à objectifs")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erreur lors de l'ajout de '{column_name}' à objectifs: {e}")

        # Vérifier les colonnes dans la table taches
        cur.execute("PRAGMA table_info(taches)")
        tache_columns = [column[1] for column in cur.fetchall()]
        print(f"Colonnes existantes dans la table taches: {tache_columns}")

        # Ajouter les colonnes manquantes pour taches
        tache_columns_to_add = [
            ('date_modification', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('termine', 'BOOLEAN DEFAULT 0'),
            ('ordre', 'INTEGER DEFAULT 0')
        ]

        for column_name, column_type in tache_columns_to_add:
            if column_name not in tache_columns:
                try:
                    cur.execute(f"ALTER TABLE taches ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne '{column_name}' ajoutée à taches")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erreur lors de l'ajout de '{column_name}' à taches: {e}")

        # Vérifier les colonnes dans la table evenements
        cur.execute("PRAGMA table_info(evenements)")
        evenement_columns = [column[1] for column in cur.fetchall()]
        print(f"Colonnes existantes dans la table evenements: {evenement_columns}")

        # Ajouter les colonnes manquantes pour evenements
        evenement_columns_to_add = [
            ('date_modification', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('termine', 'BOOLEAN DEFAULT 0'),
            ('heure_debut', 'TEXT'),
            ('heure_fin', 'TEXT'),
            ('lieu', 'TEXT')
        ]

        for column_name, column_type in evenement_columns_to_add:
            if column_name not in evenement_columns:
                try:
                    cur.execute(f"ALTER TABLE evenements ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne '{column_name}' ajoutée à evenements")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erreur lors de l'ajout de '{column_name}' à evenements: {e}")

        conn.commit()

        if added_columns:
            print(f"\n✅ {len(added_columns)} colonnes ajoutées avec succès!")
            print(f"Colonnes ajoutées: {', '.join(added_columns)}")
        else:
            print("\n✅ Toutes les colonnes nécessaires existent déjà!")

        print("\n🎉 Base de données corrigée avec succès!")

    except Exception as e:
        print(f"❌ Erreur lors de la correction de la base de données: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🔧 Correction de la base de données SQLite...")
    fix_database()