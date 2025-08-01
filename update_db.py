# update_db.py - Script pour mettre à jour la base de données PostgreSQL
import os
import psycopg2
from urllib.parse import urlparse

def update_postgres_database():
    """Mettre à jour la structure de la base de données PostgreSQL"""
    print("🔧 Mise à jour de la base de données PostgreSQL...")

    # URL de la base de données PostgreSQL
    DATABASE_URL = "postgresql://epargne_db_2_user:RxRRGVzGoq8xgpPJhdb6EOIpbZc2noy7@dpg-d24go0p5pdvs7397t69g-a.frankfurt-postgres.render.com/epargne_db_2"

    try:
        # Parser l'URL de la base de données
        parsed_url = urlparse(DATABASE_URL)

        # Connexion avec paramètres SSL
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Enlever le '/' initial
            user=parsed_url.username,
            password=parsed_url.password,
            sslmode='require'
        )

        cur = conn.cursor()
        print("✅ Connexion à PostgreSQL établie")

        # 1. Vérifier et mettre à jour la table users
        print("\n📋 Vérification de la table users...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Colonnes existantes: {existing_columns}")

        # Colonnes nécessaires pour users
        required_columns = {
            'nom': 'TEXT',
            'prenom': 'TEXT',
            'date_naissance': 'TEXT',
            'telephone': 'TEXT',
            'email': 'TEXT',
            'sexe': 'TEXT',
            'photo_profil': 'TEXT',
            'bio': 'TEXT',
            'adresse': 'TEXT',
            'ville': 'TEXT',
            'pays': 'TEXT DEFAULT \'Cameroun\'',
            'date_creation_profil': 'TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone \'utc\')'
        }

        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                print(f"➕ Ajout de la colonne {col_name}...")
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Colonne {col_name} ajoutée")
                except Exception as e:
                    print(f"⚠️  Erreur pour {col_name}: {e}")

        # 2. Créer la table evenements si elle n'existe pas
        print("\n📅 Vérification de la table evenements...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'evenements'
            )
        """)
        evenements_exists = cur.fetchone()[0]

        if not evenements_exists:
            print("➕ Création de la table evenements...")
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
            print("✅ Table evenements créée")
        else:
            print("✅ Table evenements existe déjà")

        # 3. Créer la table taches si elle n'existe pas
        print("\n📝 Vérification de la table taches...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'taches'
            )
        """)
        taches_exists = cur.fetchone()[0]

        if not taches_exists:
            print("➕ Création de la table taches...")
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
            print("✅ Table taches créée")
        else:
            print("✅ Table taches existe déjà")

        # 4. Créer la table etapes si elle n'existe pas
        print("\n📋 Vérification de la table etapes...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'etapes'
            )
        """)
        etapes_exists = cur.fetchone()[0]

        if not etapes_exists:
            print("➕ Création de la table etapes...")
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
            print("✅ Table etapes créée")
        else:
            print("✅ Table etapes existe déjà")

        # 5. Vérifier la colonne status dans objectifs
        print("\n💰 Vérification de la table objectifs...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'objectifs' AND column_name = 'status'
        """)
        status_exists = cur.fetchone()

        if not status_exists:
            print("➕ Ajout de la colonne status à objectifs...")
            cur.execute("ALTER TABLE objectifs ADD COLUMN status TEXT NOT NULL DEFAULT 'actif'")
            print("✅ Colonne status ajoutée")
        else:
            print("✅ Colonne status existe déjà")

        # Valider les changements
        conn.commit()
        print("\n🎉 Base de données PostgreSQL mise à jour avec succès!")

        # Afficher un résumé
        print("\n📊 Résumé des tables:")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        for table in tables:
            print(f"  - {table}")

    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

    return True

if __name__ == "__main__":
    success = update_postgres_database()
    if success:
        print("\n✅ Mise à jour terminée avec succès!")
    else:
        print("\n❌ Échec de la mise à jour")
        exit(1)