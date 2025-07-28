import sqlite3

# Se connecter à la base de données (crée le fichier s'il n'existe pas)
conn = sqlite3.connect('epargne.db')
cursor = conn.cursor()

# Créer la table pour les objectifs
# On stocke le nom, le montant cible et le montant actuel
cursor.execute('''
    CREATE TABLE IF NOT EXISTS objectifs (
        id INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        montant_cible REAL NOT NULL,
        montant_actuel REAL NOT NULL
    )
''')

# Créer la table pour l'historique des transactions
# On lie chaque transaction à un objectif avec objectif_id
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        objectif_id INTEGER,
        montant REAL NOT NULL,
        type_transaction TEXT NOT NULL, -- 'entree' ou 'sortie'
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (objectif_id) REFERENCES objectifs (id)
    )
''')

# --- On insère un objectif de départ pour tester ---
# Vérifions d'abord s'il existe déjà pour ne pas le dupliquer
cursor.execute("SELECT * FROM objectifs WHERE id=1")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO objectifs (id, nom, montant_cible, montant_actuel) VALUES (?, ?, ?, ?)",
            (1, 'Mon Premier Objectif', 500000, 0))

# Sauvegarder les changements et fermer la connexion
conn.commit()
conn.close()

print("Base de données et tables créées avec succès. Objectif initial inséré.")