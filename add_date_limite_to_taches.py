#!/usr/bin/env python3
"""
Script pour ajouter le champ date_limite à la table taches existante
"""

import sqlite3
import os

def add_date_limite_to_taches():
    """Ajoute le champ date_limite à la table taches si il n'existe pas"""
    
    # Vérifier si la base SQLite existe
    if not os.path.exists('epargne.db'):
        print("Base de données SQLite non trouvée. Création d'une nouvelle base...")
        return
    
    conn = sqlite3.connect('epargne.db')
    cur = conn.cursor()
    
    try:
        # Vérifier si le champ date_limite existe déjà
        cur.execute("PRAGMA table_info(taches)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'date_limite' not in columns:
            print("Ajout du champ date_limite à la table taches...")
            cur.execute("ALTER TABLE taches ADD COLUMN date_limite TEXT")
            conn.commit()
            print("✅ Champ date_limite ajouté avec succès !")
        else:
            print("✅ Le champ date_limite existe déjà dans la table taches.")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du champ date_limite : {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_date_limite_to_taches() 