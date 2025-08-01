import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('epargne.db')
cur = conn.cursor()

# Création de la table evenements
cur.execute('''
CREATE TABLE IF NOT EXISTS evenements (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    date_debut TEXT NOT NULL,
    date_fin TEXT,
    heure_debut TEXT,
    heure_fin TEXT,
    lieu TEXT,
    couleur TEXT DEFAULT '#fd7e14',
    rappel_minutes INTEGER DEFAULT 0,
    termine BOOLEAN DEFAULT FALSE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Validation des changements
conn.commit()
conn.close()

print("✅ Table 'evenements' créée avec succès dans la base de données!")
print("🎉 L'onglet Agenda devrait maintenant fonctionner correctement.")