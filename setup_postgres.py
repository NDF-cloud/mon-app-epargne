# ==============================================================================
# SCRIPT DE CONFIGURATION POSTGRESQL POUR L'APPLICATION D'ÉPARGNE
# ==============================================================================
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def init_database():
    """Initialise la base de données PostgreSQL avec toutes les tables nécessaires"""
    
    # Récupérer l'URL de la base de données depuis les variables d'environnement
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("⚠️  DATABASE_URL non définie, utilisation de SQLite")
        return False
    
    try:
        print("🔗 Connexion à la base de données PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🗑️  Suppression des anciennes tables (si elles existent)...")
        cur.execute("DROP TABLE IF EXISTS transactions CASCADE;")
        cur.execute("DROP TABLE IF EXISTS taches CASCADE;")
        cur.execute("DROP TABLE IF EXISTS etapes CASCADE;")
        cur.execute("DROP TABLE IF EXISTS evenements CASCADE;")
        cur.execute("DROP TABLE IF EXISTS objectifs CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        print("🏗️  Création de la structure des tables...")
        
        # Table users
        cur.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            security_question TEXT,
            security_answer TEXT,
            default_currency TEXT DEFAULT 'XAF',
            countdown_enabled BOOLEAN DEFAULT true,
            countdown_days INTEGER DEFAULT 30,
            display_currency BOOLEAN DEFAULT true,
            display_progress BOOLEAN DEFAULT true,
            notification_enabled BOOLEAN DEFAULT true,
            auto_delete_completed BOOLEAN DEFAULT false,
            auto_delete_days INTEGER DEFAULT 90
        );
        ''')
        
        # Table objectifs
        cur.execute('''
        CREATE TABLE objectifs (
            id SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            montant_cible REAL NOT NULL,
            montant_actuel REAL NOT NULL DEFAULT 0,
            date_limite TEXT,
            status TEXT NOT NULL DEFAULT 'actif',
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        # Table transactions
        cur.execute('''
        CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            objectif_id INTEGER NOT NULL REFERENCES objectifs(id) ON DELETE CASCADE,
            montant REAL NOT NULL,
            type_transaction TEXT NOT NULL,
            date TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        # Table taches
        cur.execute('''
        CREATE TABLE taches (
            id SERIAL PRIMARY KEY,
            titre TEXT NOT NULL,
            description TEXT,
            priorite TEXT DEFAULT 'normale',
            statut TEXT DEFAULT 'en_cours',
            date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
            date_limite TEXT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        # Table etapes
        cur.execute('''
        CREATE TABLE etapes (
            id SERIAL PRIMARY KEY,
            tache_id INTEGER NOT NULL REFERENCES taches(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            terminee BOOLEAN DEFAULT false,
            ordre INTEGER DEFAULT 0
        );
        ''')
        
        # Table evenements
        cur.execute('''
        CREATE TABLE evenements (
            id SERIAL PRIMARY KEY,
            titre TEXT NOT NULL,
            description TEXT,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            couleur TEXT DEFAULT '#007bff',
            rappel_minutes INTEGER DEFAULT 0,
            rappel TEXT,
            date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        print("✅ Structure des tables créée avec succès.")
        conn.commit()
        cur.close()
        conn.close()
        print("🔒 Connexion fermée.")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        return False

if __name__ == "__main__":
    init_database()