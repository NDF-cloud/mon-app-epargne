# ==============================================================================
# FICHIER COMPLET, FINAL ET CORRIGÉ POUR : app.py
# (Inclut la correction pour le graphique sur Render)
# ==============================================================================

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'une-cle-vraiment-secrete-pour-la-securite'

PASSWORD_FILE = "password.txt"

# --- Fonctions utilitaires ---
def get_password():
    if not os.path.exists(PASSWORD_FILE): return None
    with open(PASSWORD_FILE, 'r') as f: return f.read().strip()

def set_password(new_password):
    with open(PASSWORD_FILE, 'w') as f: f.write(new_password)

def get_db_connection():
    conn = sqlite3.connect('epargne.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Routes principales ---
@app.route('/')
def index():
    conn = get_db_connection()
    objectifs_db = conn.execute("SELECT * FROM objectifs WHERE status = 'actif' ORDER BY id DESC").fetchall()
    total_epargne_result = conn.execute("SELECT SUM(montant_actuel) as total FROM objectifs WHERE status = 'actif'").fetchone()
    total_epargne = total_epargne_result['total'] if total_epargne_result['total'] else 0
    conn.close()

    objectifs = []
    for obj in objectifs_db:
        obj = dict(obj)
        progression = (obj['montant_actuel'] / obj['montant_cible']) * 100 if obj['montant_cible'] > 0 else 0
        obj['progression'] = progression
        objectifs.append(obj)

    return render_template('index.html', objectifs=objectifs, total_epargne=total_epargne)

@app.route('/archives')
def archives():
    conn = get_db_connection()
    objectifs_archives = conn.execute("SELECT * FROM objectifs WHERE status = 'archivé' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('archives.html', objectifs=objectifs_archives)

# --- Routes de gestion des objectifs ---
@app.route('/objectif/<int:objectif_id>')
def objectif_detail(objectif_id):
    conn = get_db_connection()
    objectif = conn.execute('SELECT * FROM objectifs WHERE id = ?', (objectif_id,)).fetchone()
    transactions = conn.execute('SELECT * FROM transactions WHERE objectif_id = ? ORDER BY date DESC', (objectif_id,)).fetchall()
    conn.close()

    if objectif is None: return "Objectif non trouvé!", 404

    progression = 0
    montant_restant = objectif['montant_cible'] - objectif['montant_actuel']
    rythme_quotidien = 0

    if objectif['montant_cible'] > 0:
        progression = (objectif['montant_actuel'] / objectif['montant_cible']) * 100

    if objectif['date_limite'] and montant_restant > 0:
        try:
            date_limite = datetime.strptime(objectif['date_limite'], '%Y-%m-%d')
            jours_restants = (date_limite - datetime.now()).days
            if jours_restants > 0: rythme_quotidien = montant_restant / jours_restants
        except (ValueError, TypeError): pass

    return render_template('objectif_detail.html', objectif=objectif, transactions=transactions, progression=progression, montant_restant=montant_restant, rythme_quotidien=rythme_quotidien)

@app.route('/formulaire_objectif/')
@app.route('/formulaire_objectif/<int:objectif_id>')
def formulaire_objectif(objectif_id=None):
    objectif = None
    if objectif_id:
        conn = get_db_connection()
        objectif = conn.execute('SELECT * FROM objectifs WHERE id = ?', (objectif_id,)).fetchone()
        conn.close()
    return render_template('formulaire_objectif.html', objectif=objectif)

@app.route('/sauvegarder_objectif', methods=['POST'])
@app.route('/sauvegarder_objectif/<int:objectif_id>', methods=['POST'])
def sauvegarder_objectif(objectif_id=None):
    mdp_saisi = request.form.get('password')
    mdp_actuel = get_password()
    if mdp_actuel and mdp_saisi != mdp_actuel:
        flash("Mot de passe incorrect !", 'error')
        return redirect(url_for('formulaire_objectif', objectif_id=objectif_id))

    nom = request.form['nom']
    montant_cible = float(request.form['montant_cible'])
    date_limite = request.form['date_limite']
    conn = get_db_connection()
    if objectif_id:
        conn.execute('UPDATE objectifs SET nom = ?, montant_cible = ?, date_limite = ? WHERE id = ?', (nom, montant_cible, date_limite, objectif_id))
        flash(f"L'objectif '{nom}' a été mis à jour.", 'success')
    else:
        conn.execute('INSERT INTO objectifs (nom, montant_cible, montant_actuel, date_limite, status) VALUES (?, ?, ?, ?, ?)', (nom, montant_cible, 0, date_limite, 'actif'))
        flash(f"L'objectif '{nom}' a été créé.", 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/supprimer_objectif/<int:objectif_id>', methods=['POST'])
def supprimer_objectif(objectif_id):
    mdp_saisi = request.form.get('password')
    mdp_actuel = get_password()
    if mdp_actuel and mdp_saisi != mdp_actuel:
        flash("Mot de passe incorrect ! Suppression annulée.", 'error')
        return redirect(request.referrer or url_for('index'))

    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE objectif_id = ?', (objectif_id,))
    conn.execute('DELETE FROM objectifs WHERE id = ?', (objectif_id,))
    conn.commit()
    conn.close()
    flash("L'objectif a été supprimé définitivement.", 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/objectif/<int:objectif_id>/archiver', methods=['POST'])
def archiver_objectif(objectif_id):
    conn = get_db_connection()
    conn.execute("UPDATE objectifs SET status = 'archivé' WHERE id = ?", (objectif_id,))
    conn.commit()
    conn.close()
    flash("Objectif archivé avec succès !", "success")
    return redirect(url_for('index'))

@app.route('/objectif/<int:objectif_id>/add_transaction', methods=['POST'])
def add_transaction(objectif_id):
    montant = float(request.form['montant'])
    type_transaction = request.form['type_transaction']
    conn = get_db_connection()
    objectif = conn.execute('SELECT * FROM objectifs WHERE id = ?', (objectif_id,)).fetchone()
    montant_actuel = objectif['montant_actuel']
    if type_transaction == 'entree': nouveau_montant = montant_actuel + montant
    else: nouveau_montant = montant_actuel - montant
    conn.execute('UPDATE objectifs SET montant_actuel = ? WHERE id = ?', (nouveau_montant, objectif_id))
    conn.execute('INSERT INTO transactions (objectif_id, montant, type_transaction) VALUES (?, ?, ?)', (objectif_id, montant, type_transaction))
    conn.commit()
    conn.close()
    return redirect(url_for('objectif_detail', objectif_id=objectif_id))

# --- Routes des paramètres ---
@app.route('/parametres')
def parametres():
    password_exists = get_password() is not None
    return render_template('parametres.html', password_exists=password_exists)

@app.route('/update_password', methods=['POST'])
def update_password():
    ancien_mdp = request.form.get('ancien_mdp')
    nouveau_mdp = request.form.get('nouveau_mdp')
    mdp_actuel = get_password()
    if mdp_actuel and mdp_actuel != ancien_mdp:
        flash("Ancien mot de passe incorrect.", 'error')
        return redirect(url_for('parametres'))
    set_password(nouveau_mdp)
    flash("Mot de passe mis à jour avec succès.", 'success')
    return redirect(url_for('parametres'))

# --- API Routes ---
@app.route('/api/verify_password', methods=['POST'])
def api_verify_password():
    mdp_saisi = request.json.get('password')
    mdp_actuel = get_password()
    if mdp_actuel is None: return jsonify({'success': True})
    return jsonify({'success': (mdp_saisi == mdp_actuel)})

# ==============================================================================
# FONCTION CORRIGÉE POUR LE GRAPHIQUE
# ==============================================================================
@app.route('/api/chart_data/<int:objectif_id>')
def chart_data(objectif_id):
    conn = get_db_connection()
    transactions = conn.execute(
        'SELECT montant, type_transaction, date FROM transactions WHERE objectif_id = ? ORDER BY date ASC',
        (objectif_id,)
    ).fetchall()
    conn.close()

    labels = ["Départ"]
    data_entrees = [0]
    data_sorties = [0]

    montant_cumulatif_entrees = 0
    montant_cumulatif_sorties = 0

    for trans in transactions:
        if trans['type_transaction'] == 'entree':
            montant_cumulatif_entrees += trans['montant']
        else:
            montant_cumulatif_sorties += trans['montant']

        # Correction pour être plus robuste avec les formats de date
        date_part = trans['date'].split(' ')[0] # On prend seulement 'YYYY-MM-DD'
        try:
            year, month, day = date_part.split('-')
            formatted_date = f"{day}/{month}/{year}"
        except ValueError:
            formatted_date = "Date Inconnue"

        labels.append(formatted_date)
        data_entrees.append(montant_cumulatif_entrees)
        data_sorties.append(montant_cumulatif_sorties)

    return jsonify({
        'labels': labels,
        'data_entrees': data_entrees,
        'data_sorties': data_sorties
    })
# ==============================================================================

# --- Point de démarrage ---
if __name__ == '__main__':
    app.run(debug=True)