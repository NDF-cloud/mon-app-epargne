# ==============================================================================
# SCRIPT DE CONFIGURATION POSTGRESQL POUR L'APPLICATION D'ÉPARGNE
# ==============================================================================
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def setup_database():
    # Récupération de l'URL de la base de données depuis les variables d'environnement
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("❌ ERREUR : Variable d'environnement DATABASE_URL non définie")
        print("💡 Assurez-vous que DATABASE_URL est configurée dans vos variables d'environnement")
        return False

    try:
        # Connexion à la base de données PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Connexion à PostgreSQL réussie")

        # Création de la table users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password VARCHAR(120) NOT NULL,
                security_question TEXT NOT NULL,
                security_answer VARCHAR(120) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'users' créée/vérifiée")

        # Création de la table objectifs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objectifs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                nom VARCHAR(200) NOT NULL,
                montant_objectif DECIMAL(10,2) NOT NULL,
                montant_actuel DECIMAL(10,2) DEFAULT 0,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archive BOOLEAN DEFAULT FALSE,
                description TEXT
            )
        """)
        print("✅ Table 'objectifs' créée/vérifiée")

        # Création de la table transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                objectif_id INTEGER NOT NULL REFERENCES objectifs(id) ON DELETE CASCADE,
                montant DECIMAL(10,2) NOT NULL,
                date_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        print("✅ Table 'transactions' créée/vérifiée")

        # Création de la table tâches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taches (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                titre VARCHAR(200) NOT NULL,
                description TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                termine BOOLEAN DEFAULT FALSE,
                ordre INTEGER DEFAULT 0
            )
        """)
        print("✅ Table 'taches' créée/vérifiée")

        # Création de la table étapes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etapes (
                id SERIAL PRIMARY KEY,
                tache_id INTEGER NOT NULL REFERENCES taches(id) ON DELETE CASCADE,
                description VARCHAR(500) NOT NULL,
                terminee BOOLEAN DEFAULT FALSE,
                ordre INTEGER NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'etapes' créée/vérifiée")

        # Validation des changements
        conn.commit()
        print("✅ Toutes les tables ont été créées avec succès !")

        # Test de connexion et affichage des informations
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 Version PostgreSQL : {version[0]}")

        cursor.execute("SELECT COUNT(*) FROM users;")
        nb_users = cursor.fetchone()[0]
        print(f"👥 Nombre d'utilisateurs : {nb_users}")

        cursor.execute("SELECT COUNT(*) FROM objectifs;")
        nb_objectifs = cursor.fetchone()[0]
        print(f"💰 Nombre d'objectifs : {nb_objectifs}")

        cursor.execute("SELECT COUNT(*) FROM taches;")
        nb_taches = cursor.fetchone()[0]
        print(f"📝 Nombre de tâches : {nb_taches}")

        cursor.close()
        conn.close()

        print("\n🎉 Configuration PostgreSQL terminée avec succès !")
        print("🚀 Votre application est prête à être utilisée.")

        return True

    except Exception as e:
        print(f"❌ ERREUR lors de la configuration : {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configuration de la base de données PostgreSQL...")
    success = setup_database()

    if success:
        print("\n✅ Configuration terminée avec succès !")
        print("💡 Vous pouvez maintenant lancer votre application avec : python app.py")
    else:
        print("\n❌ Échec de la configuration")
        print("💡 Vérifiez vos paramètres de connexion PostgreSQL")