import sqlite3

def check_database_structure():
    conn = sqlite3.connect('epargne.db')
    cursor = conn.cursor()

    print("=== Structure de la base de données ===")

    # Vérifier la table objectifs
    print("\n--- Table objectifs ---")
    cursor.execute("PRAGMA table_info(objectifs)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Vérifier la table taches
    print("\n--- Table taches ---")
    cursor.execute("PRAGMA table_info(taches)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Vérifier la table evenements
    print("\n--- Table evenements ---")
    cursor.execute("PRAGMA table_info(evenements)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    check_database_structure()