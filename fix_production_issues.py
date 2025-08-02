#!/usr/bin/env python3
"""
Script pour corriger les problèmes de production :
1. Ajouter la colonne date_limite à la table taches si elle n'existe pas
2. Corriger la fonction convert_evenement_to_dict pour correspondre au schéma réel
"""

import os
import psycopg2
import sqlite3
from sqlite3 import connect

def fix_production_issues():
    """Corrige les problèmes de production"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if DATABASE_URL:
        print("🔧 Correction des problèmes PostgreSQL...")
        fix_postgresql_issues(DATABASE_URL)
    else:
        print("🔧 Correction des problèmes SQLite...")
        fix_sqlite_issues()

def fix_postgresql_issues(database_url):
    """Corrige les problèmes PostgreSQL"""
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 1. Vérifier et ajouter la colonne date_limite à la table taches
        print("📋 Vérification de la colonne date_limite dans la table taches...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'taches' AND column_name = 'date_limite'
        """)
        
        if not cur.fetchone():
            print("➕ Ajout de la colonne date_limite à la table taches...")
            cur.execute("ALTER TABLE taches ADD COLUMN date_limite DATE")
            print("✅ Colonne date_limite ajoutée avec succès")
        else:
            print("✅ Colonne date_limite existe déjà")
        
        # 2. Vérifier et ajouter les colonnes manquantes à la table evenements
        print("📅 Vérification des colonnes de la table evenements...")
        
        # Vérifier heure_debut
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evenements' AND column_name = 'heure_debut'
        """)
        if not cur.fetchone():
            print("➕ Ajout de la colonne heure_debut à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN heure_debut TIME")
        
        # Vérifier heure_fin
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evenements' AND column_name = 'heure_fin'
        """)
        if not cur.fetchone():
            print("➕ Ajout de la colonne heure_fin à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN heure_fin TIME")
        
        # Vérifier couleur
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evenements' AND column_name = 'couleur'
        """)
        if not cur.fetchone():
            print("➕ Ajout de la colonne couleur à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN couleur VARCHAR(20) DEFAULT '#007bff'")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Corrections PostgreSQL terminées avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction PostgreSQL : {e}")

def fix_sqlite_issues():
    """Corrige les problèmes SQLite"""
    try:
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        
        # 1. Vérifier et ajouter la colonne date_limite à la table taches
        print("📋 Vérification de la colonne date_limite dans la table taches...")
        cur.execute("PRAGMA table_info(taches)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'date_limite' not in columns:
            print("➕ Ajout de la colonne date_limite à la table taches...")
            cur.execute("ALTER TABLE taches ADD COLUMN date_limite DATE")
            print("✅ Colonne date_limite ajoutée avec succès")
        else:
            print("✅ Colonne date_limite existe déjà")
        
        # 2. Vérifier et ajouter les colonnes manquantes à la table evenements
        print("📅 Vérification des colonnes de la table evenements...")
        cur.execute("PRAGMA table_info(evenements)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'heure_debut' not in columns:
            print("➕ Ajout de la colonne heure_debut à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN heure_debut TEXT")
        
        if 'heure_fin' not in columns:
            print("➕ Ajout de la colonne heure_fin à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN heure_fin TEXT")
        
        if 'couleur' not in columns:
            print("➕ Ajout de la colonne couleur à la table evenements...")
            cur.execute("ALTER TABLE evenements ADD COLUMN couleur TEXT DEFAULT '#007bff'")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Corrections SQLite terminées avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction SQLite : {e}")

def fix_convert_evenement_to_dict():
    """Corrige la fonction convert_evenement_to_dict dans app.py"""
    print("🔧 Correction de la fonction convert_evenement_to_dict...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer la fonction convert_evenement_to_dict
        old_function = '''def convert_evenement_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        return {
            'id': row[0], 'user_id': row[1], 'titre': row[2], 'description': row[3],
            'date_debut': row[4], 'date_fin': row[5], 'heure_debut': row[6], 'heure_fin': row[7],
            'lieu': row[8], 'couleur': row[9], 'rappel_minutes': row[10], 'termine': row[11],
            'date_creation': row[12]
        }'''
        
        new_function = '''def convert_evenement_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        # Schéma SQLite : id, titre, description, date_debut, date_fin, lieu, type_evenement, rappel_minutes, termine, user_id, date_creation, heure_debut, heure_fin, couleur
        return {
            'id': row[0], 'titre': row[1], 'description': row[2], 'date_debut': row[3], 
            'date_fin': row[4], 'lieu': row[5], 'type_evenement': row[6], 'rappel_minutes': row[7], 
            'termine': row[8], 'user_id': row[9], 'date_creation': row[10],
            'heure_debut': row[11] if len(row) > 11 else None,
            'heure_fin': row[12] if len(row) > 12 else None,
            'couleur': row[13] if len(row) > 13 else '#007bff'
        }'''
        
        if old_function in content:
            content = content.replace(old_function, new_function)
            
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fonction convert_evenement_to_dict corrigée avec succès")
        else:
            print("⚠️  Fonction convert_evenement_to_dict non trouvée, vérification manuelle nécessaire")
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction de la fonction : {e}")

if __name__ == "__main__":
    print("🚀 Début de la correction des problèmes de production...")
    fix_production_issues()
    fix_convert_evenement_to_dict()
    print("✅ Toutes les corrections ont été appliquées !") 