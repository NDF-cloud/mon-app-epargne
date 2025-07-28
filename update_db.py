# update_db.py
import sqlite3

conn = sqlite3.connect('epargne.db')
cursor = conn.cursor()

try:
    # On ajoute la colonne date_limite si elle n'existe pas déjà
    cursor.execute('ALTER TABLE objectifs ADD COLUMN date_limite TEXT')
    print("Colonne 'date_limite' ajoutée à la table 'objectifs'.")
except sqlite3.OperationalError as e:
    # Cette erreur se produit si la colonne existe déjà, on peut l'ignorer
    if "duplicate column name" in str(e):
        print("La colonne 'date_limite' existe déjà.")
    else:
        raise e

conn.commit()
conn.close()