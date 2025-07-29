# init_postgres.py (Version Finale Corrigée)
import os
import psycopg2

# IMPORTANT : Récupérez cette URL depuis la page de votre NOUVELLE DB sur Render (External URL)
DATABASE_URL = "VOTRE_EXTERNAL_DATABASE_URL_ICI"

if DATABASE_URL == "VOTRE_EXTERNAL_DATABASE_URL_ICI":
    print("ERREUR : Veuillez remplacer l'URL de la base de données dans le script.")
else:
    print("Connexion à la base de données PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Création de la structure des tables...")

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        security_question TEXT,
        security_answer TEXT
    );
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS objectifs (
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
    CREATE TABLE IF NOT EXISTS transactions (
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
    print("Connexion fermée.")