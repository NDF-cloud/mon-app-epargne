# ==============================================================================
# FICHIER FINAL PRÊT À L'EMPLOI : setup_postgres.py
# (Contient votre URL et la structure complète de la DB)
# ==============================================================================
import psycopg2

# Votre URL externe, directement intégrée.
DATABASE_URL = "postgresql://overview_db_user:mjfjXVEr7SDMOp9JLafC81qmyJOoiYec@dpg-d24lug3e5dus73fqh7dg-a.frankfurt-postgres.render.com/overview_db"

print("Connexion à PostgreSQL avec votre URL...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("Connexion réussie.")

    print("Suppression des anciennes tables (si elles existent)...")
    cur.execute("DROP TABLE IF EXISTS transactions;")
    cur.execute("DROP TABLE IF EXISTS objectifs;")
    cur.execute("DROP TABLE IF EXISTS users;")
    print("Anciennes tables supprimées.")

    print("Création de la structure finale...")
    cur.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        security_question TEXT,
        security_answer TEXT
    );
    ''')

    cur.execute('''
    CREATE TABLE objectifs (
        id SERIAL PRIMARY KEY,
        nom TEXT NOT NULL,
        montant_cible REAL NOT NULL,
        montant_actuel REAL NOT NULL,
        date_limite TEXT,
        status TEXT NOT NULL DEFAULT 'actif',
        user_id INTEGER NOT NULL REFERENCES users(id)
    );
    ''')

    cur.execute('''
    CREATE TABLE transactions (
        id SERIAL PRIMARY KEY,
        objectif_id INTEGER NOT NULL REFERENCES objectifs(id),
        montant REAL NOT NULL,
        type_transaction TEXT NOT NULL,
        date TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
        user_id INTEGER NOT NULL REFERENCES users(id)
    );
    ''')
    print("Structure des tables créée avec succès.")

    conn.commit()
    print("Changements sauvegardés.")

except Exception as e:
    print(f"\n\n--- ERREUR ---")
    print(f"Une erreur est survenue : {e}")
    print("Vérifiez que votre URL de base de données est correcte et que la DB est active sur Render.")

finally:
    if 'conn' in locals() and conn is not None:
        cur.close()
        conn.close()
        print("Connexion fermée. La base de données est prête.")