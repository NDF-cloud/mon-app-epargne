# ==============================================================================
# FICHIER FINAL, ULTIME ET 100% COMPLET : app.py
# (Multi-Utilisateurs + PostgreSQL + Toutes les fonctionnalités)
# ==============================================================================
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = 'une-cle-vraiment-secrete-pour-les-sessions-utilisateurs'

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        try:
            return psycopg2.connect(db_url)
        except Exception as e:
            print(f"!!! ERREUR DE CONNEXION POSTGRESQL : {e}")
            return None
    else:
        # Mode local pour les tests
        conn = sqlite3.connect('epargne.db')
        conn.row_factory = sqlite3.Row
        return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_security_questions():
    return ["Quel est le nom de votre premier animal de compagnie ?", "Quelle est votre ville de naissance ?", "Quel était le nom de votre école primaire ?"]

# --- Adaptateur SQL pour la syntaxe des paramètres ---
def sql_placeholder(query):
    return query.replace('?', '%s') if os.environ.get('DATABASE_URL') else query

# --- AUTHENTIFICATION ---
@app.route('/register', methods=('GET', 'POST'))
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        question = request.form['security_question']
        answer = request.form['security_answer']
        if not all([username, password, question, answer]):
            flash("Veuillez remplir tous les champs.", "error")
            return render_template('register.html', questions=get_security_questions())

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                hashed_password = generate_password_hash(password)
                hashed_answer = generate_password_hash(answer)
                sql = sql_placeholder('INSERT INTO users (username, password, security_question, security_answer) VALUES (?, ?, ?, ?)')
                cur.execute(sql, (username, hashed_password, question, hashed_answer))
            conn.commit()
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except (sqlite3.IntegrityError, psycopg2.IntegrityError):
            flash(f"L'utilisateur '{username}' existe déjà.", 'error')
        finally:
            if conn: conn.close()
    return render_template('register.html', questions=get_security_questions())

@app.route('/login', methods=('GET', 'POST'))
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur_factory = psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None
        with conn.cursor(cursor_factory=cur_factory) as cur:
            sql = sql_placeholder('SELECT * FROM users WHERE username = ?')
            cur.execute(sql, (username,))
            user = cur.fetchone()
        conn.close()
        if user is None or not check_password_hash(user['password'], password):
            flash('Identifiants incorrects. Veuillez réessayer.', 'error')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté avec succès.', 'success')
    return redirect(url_for('login'))

# --- FLUX DE RÉINITIALISATION DE MOT DE PASSE OUBLIÉ ---
@app.route('/forgot_password', methods=('GET', 'POST'))
def forgot_password_request():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
            sql = sql_placeholder('SELECT id, security_question FROM users WHERE username = ?')
            cur.execute(sql, (username,))
            user = cur.fetchone()
        conn.close()
        if user and user['security_question']:
            session['reset_user'] = username
            return redirect(url_for('forgot_password_answer'))
        else:
            flash("Utilisateur non trouvé ou aucune question de sécurité définie.", "error")
    return render_template('forgot_password_request.html')

@app.route('/forgot_password/answer', methods=('GET', 'POST'))
def forgot_password_answer():
    username = session.get('reset_user')
    if not username: return redirect(url_for('login'))
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT security_question, security_answer FROM users WHERE username = ?')
        cur.execute(sql, (username,))
        user = cur.fetchone()
    conn.close()
    if user is None:
        flash("Erreur de session. Veuillez recommencer.", "error")
        return redirect(url_for('forgot_password_request'))
    if request.method == 'POST':
        answer = request.form['answer']
        if check_password_hash(user['security_answer'], answer):
            session['reset_authorized'] = True
            return redirect(url_for('reset_password_final'))
        else:
            flash("La réponse secrète est incorrecte.", "error")
    return render_template('forgot_password_answer.html', question=user['security_question'])

@app.route('/reset_password_final', methods=('GET', 'POST'))
def reset_password_final():
    username = session.get('reset_user')
    if not session.get('reset_authorized') or not username: return redirect(url_for('login'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_password = generate_password_hash(new_password)
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql = sql_placeholder('UPDATE users SET password = ? WHERE username = ?')
            cur.execute(sql, (hashed_password, username))
        conn.commit()
        conn.close()
        session.pop('reset_user', None)
        session.pop('reset_authorized', None)
        flash("Mot de passe réinitialisé ! Vous pouvez vous connecter.", "success")
        return redirect(url_for('login'))
    return render_template('reset_password_final.html')

# --- ROUTES DE L'APPLICATION ---
@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()
    cur_factory = psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None
    with conn.cursor(cursor_factory=cur_factory) as cur:
        sql = sql_placeholder("SELECT * FROM objectifs WHERE status = 'actif' AND user_id = ? ORDER BY id DESC")
        cur.execute(sql, (user_id,))
        objectifs_db = cur.fetchall()
        sql = sql_placeholder("SELECT SUM(montant_actuel) as total FROM objectifs WHERE status = 'actif' AND user_id = ?")
        cur.execute(sql, (user_id,))
        total_epargne_result = cur.fetchone()
    conn.close()
    total_epargne = total_epargne_result['total'] if total_epargne_result and total_epargne_result['total'] is not None else 0
    objectifs = [dict(obj) for obj in objectifs_db]
    for obj in objectifs:
        progression = (obj['montant_actuel'] / obj['montant_cible']) * 100 if obj['montant_cible'] > 0 else 0
        obj['progression'] = progression
    return render_template('index.html', objectifs=objectifs, total_epargne=total_epargne)

@app.route('/archives')
@login_required
def archives():
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder("SELECT * FROM objectifs WHERE status = 'archivé' AND user_id = ? ORDER BY id DESC")
        cur.execute(sql, (user_id,))
        objectifs_archives = cur.fetchall()
    conn.close()
    return render_template('archives.html', objectifs=objectifs_archives)

@app.route('/objectif/<int:objectif_id>')
@login_required
def objectif_detail(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT * FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif is None:
            flash("Cet objectif n'existe pas ou ne vous appartient pas.", "error")
            return redirect(url_for('index'))
        sql = sql_placeholder('SELECT * FROM transactions WHERE objectif_id = ? AND user_id = ? ORDER BY date DESC')
        cur.execute(sql, (objectif_id, user_id))
        transactions = cur.fetchall()
    conn.close()
    progression = (objectif['montant_actuel'] / objectif['montant_cible']) * 100 if objectif['montant_cible'] > 0 else 0
    montant_restant = objectif['montant_cible'] - objectif['montant_actuel']
    rythme_quotidien = 0
    if objectif['date_limite'] and montant_restant > 0:
        try:
            date_limite = datetime.strptime(objectif['date_limite'], '%Y-%m-%d')
            jours_restants = (date_limite - datetime.now()).days
            if jours_restants > 0: rythme_quotidien = montant_restant / jours_restants
        except (ValueError, TypeError): pass
    return render_template('objectif_detail.html', objectif=objectif, transactions=transactions, progression=progression, montant_restant=montant_restant, rythme_quotidien=rythme_quotidien)

@app.route('/formulaire_objectif/', defaults={'objectif_id': None}, methods=['GET'])
@app.route('/formulaire_objectif/<int:objectif_id>', methods=['GET'])
@login_required
def formulaire_objectif(objectif_id):
    objectif = None
    if objectif_id:
        user_id = session['user_id']
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
            sql = sql_placeholder('SELECT * FROM objectifs WHERE id = ? AND user_id = ?')
            cur.execute(sql, (objectif_id, user_id))
            objectif = cur.fetchone()
        conn.close()
        if objectif is None:
            flash("Cet objectif n'existe pas ou ne vous appartient pas.", "error")
            return redirect(url_for('index'))
    return render_template('formulaire_objectif.html', objectif=objectif)

@app.route('/sauvegarder_objectif/', defaults={'objectif_id': None}, methods=['POST'])
@app.route('/sauvegarder_objectif/<int:objectif_id>', methods=['POST'])
@login_required
def sauvegarder_objectif(objectif_id):
    user_id = session['user_id']
    password = request.form.get('password')
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
        if not password or not check_password_hash(user['password'], password):
            flash("Mot de passe incorrect !", "error")
            conn.close()
            return redirect(url_for('formulaire_objectif', objectif_id=objectif_id))

        nom = request.form['nom']
        montant_cible = float(request.form['montant_cible'])
        date_limite = request.form['date_limite'] if request.form['date_limite'] else None

        if objectif_id:
            sql = sql_placeholder('UPDATE objectifs SET nom = ?, montant_cible = ?, date_limite = ? WHERE id = ? AND user_id = ?')
            cur.execute(sql, (nom, montant_cible, date_limite, objectif_id, user_id))
            flash(f"L'objectif '{nom}' a été mis à jour.", 'success')
        else:
            sql = sql_placeholder('INSERT INTO objectifs (nom, montant_cible, montant_actuel, date_limite, status, user_id) VALUES (?, ?, ?, ?, ?, ?)')
            cur.execute(sql, (nom, montant_cible, 0, date_limite, 'actif', user_id))
            flash(f"L'objectif '{nom}' a été créé.", 'success')
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/supprimer_objectif/<int:objectif_id>', methods=['POST'])
@login_required
def supprimer_objectif(objectif_id):
    user_id = session['user_id']
    password = request.form.get('password')
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
        if not password or not check_password_hash(user['password'], password):
            flash("Mot de passe incorrect ! Suppression annulée.", "error")
            conn.close()
            return redirect(request.referrer or url_for('index'))

        sql = sql_placeholder('SELECT id FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif:
            sql_trans = sql_placeholder('DELETE FROM transactions WHERE objectif_id = ?')
            cur.execute(sql_trans, (objectif_id,))
            sql_obj = sql_placeholder('DELETE FROM objectifs WHERE id = ?')
            cur.execute(sql_obj, (objectif_id,))
            flash("L'objectif a été supprimé définitivement.", 'success')
        else:
            flash("Action non autorisée.", "error")
        conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/objectif/<int:objectif_id>/archiver', methods=['POST'])
@login_required
def archiver_objectif(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor() as cur:
        sql = sql_placeholder("UPDATE objectifs SET status = 'archivé' WHERE id = ? AND user_id = ?")
        cur.execute(sql, (objectif_id, user_id))
    conn.commit()
    conn.close()
    flash("Objectif archivé avec succès !", "success")
    return redirect(url_for('index'))

@app.route('/objectif/<int:objectif_id>/add_transaction', methods=['POST'])
@login_required
def add_transaction(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT * FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif is None:
            flash("Action non autorisée.", "error")
            return redirect(url_for('index'))
        montant = float(request.form['montant'])
        type_transaction = request.form['type_transaction']
        montant_actuel = objectif['montant_actuel']
        nouveau_montant = montant_actuel + montant if type_transaction == 'entree' else montant_actuel - montant
        sql_update = sql_placeholder('UPDATE objectifs SET montant_actuel = ? WHERE id = ?')
        cur.execute(sql_update, (nouveau_montant, objectif_id))
        sql_insert = sql_placeholder('INSERT INTO transactions (objectif_id, montant, type_transaction, user_id) VALUES (?, ?, ?, ?)')
        cur.execute(sql_insert, (objectif_id, montant, type_transaction, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('objectif_detail', objectif_id=objectif_id))

@app.route('/parametres')
@login_required
def parametres():
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT username, security_question FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
    conn.close()
    return render_template('parametres.html', username=user['username'], security_question=user['security_question'])

@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    user_id = session['user_id']
    ancien_mdp = request.form.get('ancien_mdp')
    nouveau_mdp = request.form.get('nouveau_mdp')
    if not ancien_mdp or not nouveau_mdp:
        flash("Les deux champs sont requis.", "error")
        return redirect(url_for('parametres'))
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
        if not check_password_hash(user['password'], ancien_mdp):
            flash("L'ancien mot de passe est incorrect.", "error")
        else:
            hashed_password = generate_password_hash(nouveau_mdp)
            sql_update = sql_placeholder('UPDATE users SET password = ? WHERE id = ?')
            cur.execute(sql_update, (hashed_password, user_id))
            conn.commit()
            flash("Mot de passe mis à jour.", "success")
    conn.close()
    return redirect(url_for('parametres'))

# --- API Routes ---
@app.route('/api/check_user_password', methods=['POST'])
@login_required
def check_user_password():
    user_id = session['user_id']
    password = request.json.get('password')
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/chart_data/<int:objectif_id>')
@login_required
def chart_data(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor if os.environ.get('DATABASE_URL') else None) as cur:
        sql_obj = sql_placeholder('SELECT id FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql_obj, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif is None: return jsonify({'error': 'Not authorized'}), 403
        sql_trans = sql_placeholder('SELECT montant, type_transaction, date FROM transactions WHERE objectif_id = ? AND user_id = ? ORDER BY date ASC')
        cur.execute(sql_trans, (objectif_id, user_id))
        transactions = cur.fetchall()
    conn.close()
    labels, data_entrees, data_sorties = ["Départ"], [0], [0]
    montant_cumulatif_entrees, montant_cumulatif_sorties = 0, 0
    for trans in transactions:
        if trans['type_transaction'] == 'entree': montant_cumulatif_entrees += trans['montant']
        else: montant_cumulatif_sorties += trans['montant']
        date_obj = trans['date']
        # La date de PostgreSQL est un objet datetime, on la formate
        formatted_date = date_obj.strftime('%d/%m/%Y')
        labels.append(formatted_date)
        data_entrees.append(montant_cumulatif_entrees)
        data_sorties.append(montant_cumulatif_sorties)
    return jsonify({'labels': labels, 'data_entrees': data_entrees, 'data_sorties': data_sorties})

# --- Point de démarrage ---
if __name__ == '__main__':
    if not os.path.exists('epargne.db') and not os.environ.get('DATABASE_URL'):
        print("Base de données SQLite non trouvée, création...")
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, security_question TEXT, security_answer TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS objectifs (id INTEGER PRIMARY KEY, nom TEXT NOT NULL, montant_cible REAL NOT NULL, montant_actuel REAL NOT NULL, date_limite TEXT, status TEXT NOT NULL DEFAULT 'actif', user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, objectif_id INTEGER NOT NULL, montant REAL NOT NULL, type_transaction TEXT NOT NULL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id INTEGER NOT NULL, FOREIGN KEY (objectif_id) REFERENCES objectifs (id), FOREIGN KEY (user_id) REFERENCES users (id))")
        conn.commit()
        conn.close()
        print("Base de données SQLite créée.")

    app.run(debug=True)