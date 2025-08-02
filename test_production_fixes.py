#!/usr/bin/env python3
"""
Script de test pour vérifier que les corrections de production fonctionnent
"""

import os
import sqlite3
import requests
import time

def test_database_structure():
    """Teste la structure de la base de données"""
    print("🔍 Test de la structure de la base de données...")
    
    try:
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        
        # Test de la table taches
        cur.execute("PRAGMA table_info(taches)")
        columns = [column[1] for column in cur.fetchall()]
        print(f"📋 Colonnes de la table taches : {columns}")
        
        if 'date_limite' in columns:
            print("✅ Colonne date_limite présente dans la table taches")
        else:
            print("❌ Colonne date_limite manquante dans la table taches")
        
        # Test de la table evenements
        cur.execute("PRAGMA table_info(evenements)")
        columns = [column[1] for column in cur.fetchall()]
        print(f"📅 Colonnes de la table evenements : {columns}")
        
        required_columns = ['heure_debut', 'heure_fin', 'couleur']
        for col in required_columns:
            if col in columns:
                print(f"✅ Colonne {col} présente dans la table evenements")
            else:
                print(f"❌ Colonne {col} manquante dans la table evenements")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la structure : {e}")

def test_task_creation():
    """Teste la création de tâches"""
    print("\n🔧 Test de création de tâches...")
    
    try:
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        
        # Insérer une tâche de test
        cur.execute("""
            INSERT INTO taches (titre, description, date_limite, user_id)
            VALUES (?, ?, ?, ?)
        """, ("Tâche de test", "Description de test", "2024-12-31", 1))
        
        task_id = cur.lastrowid
        print(f"✅ Tâche créée avec l'ID : {task_id}")
        
        # Vérifier que la tâche a été créée
        cur.execute("SELECT * FROM taches WHERE id = ?", (task_id,))
        task = cur.fetchone()
        if task:
            print("✅ Tâche récupérée avec succès")
            print(f"   Titre : {task[1]}")
            print(f"   Date limite : {task[6]}")
        else:
            print("❌ Tâche non trouvée")
        
        # Nettoyer
        cur.execute("DELETE FROM taches WHERE id = ?", (task_id,))
        conn.commit()
        print("🧹 Tâche de test supprimée")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de création de tâches : {e}")

def test_event_creation():
    """Teste la création d'événements"""
    print("\n📅 Test de création d'événements...")
    
    try:
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        
        # Insérer un événement de test
        cur.execute("""
            INSERT INTO evenements (titre, description, date_debut, lieu, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ("Événement de test", "Description de test", "2024-12-31 10:00:00", "Lieu de test", 1))
        
        event_id = cur.lastrowid
        print(f"✅ Événement créé avec l'ID : {event_id}")
        
        # Vérifier que l'événement a été créé
        cur.execute("SELECT * FROM evenements WHERE id = ?", (event_id,))
        event = cur.fetchone()
        if event:
            print("✅ Événement récupéré avec succès")
            print(f"   Titre : {event[1]}")
            print(f"   Date début : {event[3]}")
        else:
            print("❌ Événement non trouvé")
        
        # Nettoyer
        cur.execute("DELETE FROM evenements WHERE id = ?", (event_id,))
        conn.commit()
        print("🧹 Événement de test supprimé")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de création d'événements : {e}")

def test_web_app():
    """Teste l'application web"""
    print("\n🌐 Test de l'application web...")
    
    try:
        # Attendre que l'app démarre
        time.sleep(2)
        
        # Test de la page d'accueil
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        if response.status_code == 302:  # Redirection vers login
            print("✅ Page d'accueil accessible (redirection vers login)")
        else:
            print(f"⚠️  Page d'accueil : {response.status_code}")
        
        # Test de l'API tab-content agenda
        response = requests.get('http://127.0.0.1:5000/api/tab-content/agenda', timeout=5)
        if response.status_code == 200:
            print("✅ API tab-content agenda accessible")
        else:
            print(f"❌ API tab-content agenda : {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'application web")
    except Exception as e:
        print(f"❌ Erreur lors du test web : {e}")

if __name__ == "__main__":
    print("🚀 Début des tests de correction de production...")
    test_database_structure()
    test_task_creation()
    test_event_creation()
    test_web_app()
    print("\n✅ Tous les tests terminés !") 