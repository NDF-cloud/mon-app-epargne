# setup_database.py
import psycopg2

# REMPLACEZ CETTE LIGNE PAR L'URL "EXTERNAL" DE VOTRE NOUVELLE DB SUR RENDER
DATABASE_URL = "VOTRE_EXTERNAL_DATABASE_URL_ICI"

if "VOTRE_EXTERNAL_DATABASE_URL_ICI" in DATABASE_URL:
    print("ERREUR : Veuillez remplacer l'URL de la base de données dans le script.")
else:
    print("Connexion à PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("Suppression des anciennes tables (si elles existent)...")
    cur.execute("DROP TABLE IF EXISTS transactions;")
    cur.execute("DROP TABLE IF EXISTS objectifs;")
    cur.execute("DROP TABLE IF EXISTS users;")
    print("Création de la structure finale des tables...")
    cur.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        security_question TEXT,
        security_answer TEXT
    );
    ''')
    cur.execute('''
    CREATE TABLE objectifs (
        id SERIAL PRIMARY KEY,
        nom TEXT NOT NULL,
        montant_cible REAL NOT NULL,
        montant_actuel REAL NOT NULL,
        date_limite TEXT,
        status TEXT NOT NULL DEFAULT 'actif',
        user_id INTEGER NOT NULL REFERENCES users(id)
    );
    ''')
    cur.execute('''
    CREATE TABLE transactions (
        id SERIAL PRIMARY KEY,
        objectif_id INTEGER NOT NULL REFERENCES objectifs(id),
        montant REAL NOT NULL,
        type_transaction TEXT NOT NULL,
        date TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
        user_id INTEGER NOT NULL REFERENCES users(id)
    );
    ''')
    print("Structure des tables créée avec succès.")
    conn.commit()
    cur.close()
    conn.close()
    print("Connexion fermée. La base de données est prête.")