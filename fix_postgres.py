# fix_postgres.py - Script pour corriger la base de données PostgreSQL
import os
import psycopg2

# URL de la base de données PostgreSQL
DATABASE_URL = "postgresql://epargne_db_2_user:RxRRGVzGoq8xgpPJhdb6EOIpbZc2noy7@dpg-d24go0p5pdvs7397t69g-a.frankfurt-postgres.render.com/epargne_db_2"

def fix_postgres_database():
    """Corriger la structure de la base de données PostgreSQL"""
    print("🔧 Correction de la base de données PostgreSQL...")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()

        # Vérifier et ajouter les colonnes manquantes à la table users
        print("Vérification de la table users...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Colonnes existantes dans la table users: {existing_columns}")

        # Colonnes à ajouter si elles n'existent pas
        columns_to_add = [
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
            ('date_creation_profil', 'TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone \'utc\')')
        ]

        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"Ajout de la colonne {column_name}...")
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne {column_name} ajoutée avec succès")
                except Exception as e:
                    print(f"⚠️  Erreur lors de l'ajout de '{column_name}': {e}")

        # Créer la table evenements si elle n'existe pas
        print("Vérification de la table evenements...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'evenements'
            )
        """)
        evenements_exists = cur.fetchone()[0]

        if not evenements_exists:
            print("Création de la table evenements...")
            cur.execute('''
                CREATE TABLE evenements (
                    id SERIAL PRIMARY KEY,
                    titre TEXT NOT NULL,
                    description TEXT,
                    date_debut DATE NOT NULL,
                    heure_debut TIME,
                    date_fin DATE,
                    heure_fin TIME,
                    lieu TEXT,
                    statut TEXT DEFAULT 'actif',
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
                )
            ''')
            print("✅ Table evenements créée avec succès")
        else:
            print("✅ Table evenements existe déjà")

        # Créer la table taches si elle n'existe pas
        print("Vérification de la table taches...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'taches'
            )
        """)
        taches_exists = cur.fetchone()[0]

        if not taches_exists:
            print("Création de la table taches...")
            cur.execute('''
                CREATE TABLE taches (
                    id SERIAL PRIMARY KEY,
                    titre TEXT NOT NULL,
                    description TEXT,
                    priorite TEXT DEFAULT 'moyenne',
                    statut TEXT DEFAULT 'en_cours',
                    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                    date_limite TEXT,
                    user_id INTEGER NOT NULL REFERENCES users(id)
                )
            ''')
            print("✅ Table taches créée avec succès")
        else:
            print("✅ Table taches existe déjà")

        # Créer la table etapes si elle n'existe pas
        print("Vérification de la table etapes...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'etapes'
            )
        """)
        etapes_exists = cur.fetchone()[0]

        if not etapes_exists:
            print("Création de la table etapes...")
            cur.execute('''
                CREATE TABLE etapes (
                    id SERIAL PRIMARY KEY,
                    titre TEXT NOT NULL,
                    description TEXT,
                    statut TEXT DEFAULT 'en_cours',
                    tache_id INTEGER NOT NULL REFERENCES taches(id) ON DELETE CASCADE,
                    ordre INTEGER DEFAULT 0
                )
            ''')
            print("✅ Table etapes créée avec succès")
        else:
            print("✅ Table etapes existe déjà")

        # Vérifier et corriger la colonne status dans objectifs
        print("Vérification de la colonne status dans objectifs...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'objectifs' AND column_name = 'status'
        """)
        status_exists = cur.fetchone()

        if not status_exists:
            print("Ajout de la colonne status à la table objectifs...")
            cur.execute("ALTER TABLE objectifs ADD COLUMN status TEXT NOT NULL DEFAULT 'actif'")
            print("✅ Colonne status ajoutée à objectifs")
        else:
            print("✅ Colonne status existe déjà dans objectifs")

        conn.commit()
        print("🎉 Base de données PostgreSQL corrigée avec succès!")

    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_postgres_database()