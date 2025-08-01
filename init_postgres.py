# init_postgres.py (Version Finale Corrigée)
import os
import psycopg2

# IMPORTANT : Récupérez l'URL "External" de votre NOUVELLE DB sur Render
DATABASE_URL = "postgresql://epargne_db_2_user:RxRRGVzGoq8xgpPJhdb6EOIpbZc2noy7@dpg-d24go0p5pdvs7397t69g-a.frankfurt-postgres.render.com/epargne_db_2"

if DATABASE_URL == "postgresql://epargne_db_2_user:RxRRGVzGoq8xgpPJhdb6EOIpbZc2noy7@dpg-d24go0p5pdvs7397t69g-a.frankfurt-postgres.render.com/epargne_db_2":
    print("ERREUR : Veuillez remplacer l'URL de la base de données dans le script.")
else:
    print("Connexion à la base de données PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("Suppression des anciennes tables (si elles existent)...")
    cur.execute("DROP TABLE IF EXISTS transactions;")
    cur.execute("DROP TABLE IF EXISTS objectifs;")
    cur.execute("DROP TABLE IF EXISTS evenements;")
    cur.execute("DROP TABLE IF EXISTS taches;")
    cur.execute("DROP TABLE IF EXISTS etapes;")
    cur.execute("DROP TABLE IF EXISTS users;")

    print("Création de la structure des tables...")
    cur.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nom TEXT,
        prenom TEXT,
        date_naissance TEXT,
        telephone TEXT,
        email TEXT,
        sexe TEXT,
        photo_profil TEXT,
        bio TEXT,
        adresse TEXT,
        ville TEXT,
        pays TEXT DEFAULT 'Cameroun',
        date_creation_profil TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
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
    );
    ''')
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
    );
    ''')
    cur.execute('''
    CREATE TABLE etapes (
        id SERIAL PRIMARY KEY,
        titre TEXT NOT NULL,
        description TEXT,
        statut TEXT DEFAULT 'en_cours',
        tache_id INTEGER NOT NULL REFERENCES taches(id) ON DELETE CASCADE,
        ordre INTEGER DEFAULT 0
    );
    ''')
    print("Structure des tables créée avec succès.")
    conn.commit()
    cur.close()
    conn.close()
    print("Connexion fermée.")