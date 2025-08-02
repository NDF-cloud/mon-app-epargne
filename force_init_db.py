#!/usr/bin/env python3
"""
Script pour forcer l'initialisation de la base de données PostgreSQL en production
"""

import os
import psycopg2

def force_init_database():
    """Force l'initialisation de la base de données PostgreSQL"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL non définie")
        return False
    
    try:
        print("🔗 Connexion à la base de données PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🗑️  Suppression des anciennes tables...")
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
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(120) NOT NULL,
            security_question VARCHAR(200),
            security_answer VARCHAR(120),
            display_currency BOOLEAN DEFAULT TRUE,
            display_progress BOOLEAN DEFAULT TRUE,
            notification_enabled BOOLEAN DEFAULT TRUE,
            auto_delete_completed BOOLEAN DEFAULT FALSE,
            auto_delete_days INTEGER DEFAULT 90,
            countdown_enabled BOOLEAN DEFAULT TRUE,
            countdown_days INTEGER DEFAULT 30,
            default_currency VARCHAR(3) DEFAULT 'XAF',
            nom VARCHAR(100),
            prenom VARCHAR(100),
            date_naissance DATE,
            telephone VARCHAR(20),
            email VARCHAR(120),
            sexe VARCHAR(10),
            photo_profil VARCHAR(200),
            bio TEXT,
            adresse TEXT,
            ville VARCHAR(100),
            pays VARCHAR(100) DEFAULT 'Cameroun',
            date_creation_profil TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # Table objectifs
        cur.execute('''
        CREATE TABLE objectifs (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(200) NOT NULL,
            montant_cible DECIMAL(15,2) NOT NULL,
            montant_actuel DECIMAL(15,2) DEFAULT 0,
            date_limite DATE,
            status VARCHAR(20) DEFAULT 'actif',
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # Table transactions
        cur.execute('''
        CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            objectif_id INTEGER REFERENCES objectifs(id) ON DELETE CASCADE,
            montant DECIMAL(15,2) NOT NULL,
            type_transaction VARCHAR(20) NOT NULL,
            devise_saisie VARCHAR(3) DEFAULT 'XAF',
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # Table taches
        cur.execute('''
        CREATE TABLE taches (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(200) NOT NULL,
            description TEXT,
            priorite VARCHAR(20) DEFAULT 'moyenne',
            status VARCHAR(20) DEFAULT 'en_cours',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_limite DATE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        # Table etapes
        cur.execute('''
        CREATE TABLE etapes (
            id SERIAL PRIMARY KEY,
            tache_id INTEGER REFERENCES taches(id) ON DELETE CASCADE,
            description VARCHAR(200) NOT NULL,
            terminee BOOLEAN DEFAULT FALSE,
            ordre INTEGER DEFAULT 0
        );
        ''')
        
        # Table evenements
        cur.execute('''
        CREATE TABLE evenements (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(200) NOT NULL,
            description TEXT,
            date_debut TIMESTAMP NOT NULL,
            date_fin TIMESTAMP,
            lieu VARCHAR(200),
            type_evenement VARCHAR(50) DEFAULT 'general',
            rappel_minutes INTEGER DEFAULT 30,
            termine BOOLEAN DEFAULT FALSE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # Table notifications
        cur.execute('''
        CREATE TABLE notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            titre VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type_notification VARCHAR(50) DEFAULT 'info',
            lue BOOLEAN DEFAULT FALSE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    print("🚀 Force initialisation de la base de données PostgreSQL...")
    
    if force_init_database():
        print("✅ Base de données initialisée avec succès !")
    else:
        print("❌ Échec de l'initialisation") 