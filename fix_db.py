import sqlite3

def fix_database():
    conn = sqlite3.connect('epargne.db')
    cursor = conn.cursor()

    print("=== Correction de la base de données ===")

    # Ajouter la colonne date_creation à la table evenements si elle n'existe pas
    try:
        cursor.execute("ALTER TABLE evenements ADD COLUMN date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✓ Colonne date_creation ajoutée à la table evenements")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ Colonne date_creation existe déjà dans evenements")
        else:
            print(f"⚠ Erreur lors de l'ajout de date_creation: {e}")

    # Ajouter la colonne rappel_minutes si elle n'existe pas
    try:
        cursor.execute("ALTER TABLE evenements ADD COLUMN rappel_minutes INTEGER DEFAULT 0")
        print("✓ Colonne rappel_minutes ajoutée à la table evenements")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ Colonne rappel_minutes existe déjà dans evenements")
        else:
            print(f"⚠ Erreur lors de l'ajout de rappel_minutes: {e}")

    # Vérifier et corriger la colonne rappel
    try:
        cursor.execute("SELECT rappel FROM evenements LIMIT 1")
        print("✓ Colonne rappel existe dans evenements")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE evenements ADD COLUMN rappel TEXT")
            print("✓ Colonne rappel ajoutée à la table evenements")
        except sqlite3.OperationalError as e:
            print(f"⚠ Erreur lors de l'ajout de rappel: {e}")

    conn.commit()
    conn.close()
    print("\n=== Base de données corrigée ===")

if __name__ == "__main__":
    fix_database()