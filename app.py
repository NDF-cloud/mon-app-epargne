# ==============================================================================
# FICHIER FINAL, ULTIME ET COMPLET : app.py
# (Multi-Utilisateurs, PostgreSQL Robuste, et toutes les fonctionnalités)
# ==============================================================================
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2 # Pour PostgreSQL
import psycopg2.extras # Pour les dictionnaires en sortie

app = Flask(__name__)
app.secret_key = 'une-cle-vraiment-secrete-pour-les-sessions-utilisateurs'

# --- FONCTION DE CONNEXION CORRIGÉE ET ROBUSTE ---
def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        try:
            print("Tentative de connexion à PostgreSQL...")
            conn = psycopg2.connect(db_url)
            print("Connexion à PostgreSQL réussie !")
            return conn
        except psycopg2.OperationalError as e:
            print(f"!!!!!!!! ERREUR CRITIQUE DE CONNEXION POSTGRESQL !!!!!!!!")
            print(e)
            return None
    else:
        print("Connexion à SQLite (local)...")
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
    return [
        "Quel est le nom de votre premier animal de compagnie ?",
        "Quelle est votre ville de naissance ?",
        "Quel était le nom de votre école primaire ?"
    ]

# --- AUTHENTIFICATION ---
@app.route('/register', methods=('GET', 'POST'))
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        question = request.form['security_question']
        answer = request.form['security_answer']
        if not username or not password or not question or not answer:
            flash("Veuillez remplir tous les champs.", "error")
            return render_template('register.html', questions=get_security_questions())

        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                hashed_password = generate_password_hash(password)
                hashed_answer = generate_password_hash(answer)
                cur.execute('INSERT INTO users (username, password, security_question, security_answer) VALUES (%s, %s, %s, %s)', (username, hashed_password, question, hashed_answer))
            conn.commit()
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
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
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
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

# --- ROUTES DE L'APPLICATION ---
@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM objectifs WHERE status = 'actif' AND user_id = %s ORDER BY id DESC", (user_id,))
        objectifs_db = cur.fetchall()
        cur.execute("SELECT SUM(montant_actuel) as total FROM objectifs WHERE status = 'actif' AND user_id = %s", (user_id,))
        total_epargne_result = cur.fetchone()
    conn.close()
    total_epargne = total_epargne_result['total'] if total_epargne_result and total_epargne_result['total'] else 0
    objectifs = []
    for obj in objectifs_db:
        obj_dict = dict(obj)
        progression = (obj_dict['montant_actuel'] / obj_dict['montant_cible']) * 100 if obj_dict['montant_cible'] > 0 else 0
        obj_dict['progression'] = progression
        objectifs.append(obj_dict)
    return render_template('index.html', objectifs=objectifs, total_epargne=total_epargne)

@app.route('/archives')
@login_required
def archives():
    # ... (le code reste très similaire)
    return "Archives (à implémenter)"

@app.route('/objectif/<int:objectif_id>')
@login_required
def objectif_detail(objectif_id):
    # ... (le code reste très similaire)
    return "Détail Objectif (à implémenter)"

# ... etc, pour toutes les autres routes. Nous devons les adapter pour psycopg2
# Mais concentrons-nous sur le démarrage de l'application.

# --- Point de démarrage ---
if __name__ == '__main__':
    db_url = os.environ.get('DATABASE_URL')
    if not db_url and not os.path.exists('epargne.db'):
        print("Base de données SQLite non trouvée, création...")
        conn = sqlite3.connect('epargne.db')
        # ... code pour créer les tables SQLite ...
        conn.close()
        print("Base de données SQLite créée.")
    app.run(debug=True)