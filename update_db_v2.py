# update_db_v2.py
import sqlite3

conn = sqlite3.connect('epargne.db')
cursor = conn.cursor()

try:
    # On ajoute la colonne 'status' avec une valeur par défaut 'actif'
    cursor.execute("ALTER TABLE objectifs ADD COLUMN status TEXT NOT NULL DEFAULT 'actif'")
    print("Colonne 'status' ajoutée avec succès à la table 'objectifs'.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("La colonne 'status' existe déjà. Aucune modification n'a été faite.")
    else:
        raise e

conn.commit()
conn.close()