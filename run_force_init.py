#!/usr/bin/env python3
"""
Script pour exécuter force_init_db.py en production
"""

import subprocess
import sys
import os

def run_force_init():
    """Exécute le script force_init_db.py"""
    
    print("🚀 Exécution du script force_init_db.py...")
    
    try:
        # Exécution du script
        result = subprocess.run([sys.executable, 'force_init_db.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print("📤 Sortie standard:")
        print(result.stdout)
        
        if result.stderr:
            print("📤 Sortie d'erreur:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Script exécuté avec succès")
            return True
        else:
            print(f"❌ Script terminé avec le code de retour: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: le script a pris trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Démarrage de l'exécution forcée de l'initialisation...")
    success = run_force_init()
    if success:
        print("✅ Exécution terminée avec succès")
    else:
        print("❌ Exécution terminée avec des erreurs") 