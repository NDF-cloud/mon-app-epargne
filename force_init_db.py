#!/usr/bin/env python3
"""
Script pour forcer l'initialisation de la base de données PostgreSQL en production
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def force_init_database():
    """Force l'initialisation complète de la base de données PostgreSQL"""
    
    # Récupération de l'URL de la base de données
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non définie")
        return False
    
    print(f"🔧 Connexion à la base de données PostgreSQL...")
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("✅ Connexion établie")
        
        # Suppression de toutes les tables existantes
        print("🗑️ Suppression des tables existantes...")
        cur.execute("""
            DROP TABLE IF EXISTS notifications CASCADE;
            DROP TABLE IF EXISTS transactions CASCADE;
            DROP TABLE IF EXISTS etapes CASCADE;
            DROP TABLE IF EXISTS taches CASCADE;
            DROP TABLE IF EXISTS evenements CASCADE;
            DROP TABLE IF EXISTS objectifs CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        """)
        conn.commit()
        print("✅ Tables supprimées")
        
        # Création de la table users
        print("📝 Création de la table users...")
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                devise VARCHAR(3) DEFAULT 'EUR',
                langue VARCHAR(5) DEFAULT 'fr'
            );
        """)
        
        # Création de la table objectifs
        print("📝 Création de la table objectifs...")
        cur.execute("""
            CREATE TABLE objectifs (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255) NOT NULL,
                description TEXT,
                montant_objectif DECIMAL(10,2) NOT NULL,
                montant_actuel DECIMAL(10,2) DEFAULT 0,
                devise VARCHAR(3) DEFAULT 'EUR',
                date_limite DATE,
                termine BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Création de la table taches
        print("📝 Création de la table taches...")
        cur.execute("""
            CREATE TABLE taches (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255) NOT NULL,
                description TEXT,
                priorite VARCHAR(20) DEFAULT 'moyenne',
                statut VARCHAR(20) DEFAULT 'a_faire',
                date_limite DATE,
                termine BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Création de la table etapes
        print("📝 Création de la table etapes...")
        cur.execute("""
            CREATE TABLE etapes (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255) NOT NULL,
                description TEXT,
                termine BOOLEAN DEFAULT FALSE,
                tache_id INTEGER REFERENCES taches(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Création de la table transactions
        print("📝 Création de la table transactions...")
        cur.execute("""
            CREATE TABLE transactions (
                id SERIAL PRIMARY KEY,
                montant DECIMAL(10,2) NOT NULL,
                devise VARCHAR(3) DEFAULT 'EUR',
                type_transaction VARCHAR(20) NOT NULL,
                description TEXT,
                date_transaction DATE NOT NULL,
                objectif_id INTEGER REFERENCES objectifs(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Création de la table evenements
        print("📝 Création de la table evenements...")
        cur.execute("""
            CREATE TABLE evenements (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255) NOT NULL,
                description TEXT,
                date_debut DATE NOT NULL,
                date_fin DATE,
                lieu VARCHAR(255),
                type_evenement VARCHAR(50) DEFAULT 'autre',
                rappel_minutes INTEGER DEFAULT 0,
                termine BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                heure_debut TIME,
                heure_fin TIME,
                couleur VARCHAR(7) DEFAULT '#007bff'
            );
        """)
        
        # Création de la table notifications
        print("📝 Création de la table notifications...")
        cur.execute("""
            CREATE TABLE notifications (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255) NOT NULL,
                message TEXT,
                type_notification VARCHAR(50) DEFAULT 'info',
                lu BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("✅ Toutes les tables créées avec succès")
        
        # Vérification des tables créées
        print("🔍 Vérification des tables créées...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print("📋 Tables disponibles:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cur.close()
        conn.close()
        
        print("🎉 Initialisation de la base de données terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage de l'initialisation forcée de la base de données...")
    success = force_init_database()
    if success:
        print("✅ Script terminé avec succès")
    else:
        print("❌ Script terminé avec des erreurs") 