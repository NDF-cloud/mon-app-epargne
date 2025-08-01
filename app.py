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

# --- Helper pour créer un curseur compatible ---
class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name):
        return getattr(self.cursor, name)

def get_cursor(conn):
    if os.environ.get('DATABASE_URL'):
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        # Pour SQLite, on retourne un wrapper qui supporte le protocole de gestionnaire de contexte
        return SQLiteCursorWrapper(conn.cursor())

# --- Helper pour convertir les résultats en dictionnaires ---
def convert_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        # Pour SQLite, structure réelle: id, nom, montant_cible, montant_actuel, date_limite, status, user_id
        return {
            'id': row[0], 'nom': row[1], 'montant_cible': row[2], 'montant_actuel': row[3],
            'date_limite': row[4], 'status': row[5], 'user_id': row[6], 'date_creation': None
        }

def convert_tache_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        # Pour SQLite, structure de la table taches: id, user_id, titre, description, date_creation, date_modification, termine, ordre, date_limite
        return {
            'id': row[0], 'user_id': row[1], 'titre': row[2], 'description': row[3],
            'date_creation': row[4], 'date_modification': row[5], 'termine': row[6], 'ordre': row[7], 'date_limite': row[8] if len(row) > 8 else None
        }

def convert_etape_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        # Pour SQLite, structure de la table etapes: id, tache_id, description, terminee, ordre, date_creation, date_modification
        return {
            'id': row[0], 'tache_id': row[1], 'description': row[2], 'terminee': row[3],
            'ordre': row[4], 'date_creation': row[5], 'date_modification': row[6]
        }

def format_currency(amount, currency=None):
    """Formate un montant selon la devise sélectionnée"""
    if currency is None:
        currency = session.get('default_currency', 'XAF')

    currency_symbols = {
        'XAF': 'FCFA',
        'EUR': '€',
        'USD': '$'
    }

    symbol = currency_symbols.get(currency, 'FCFA')

    # Arrondir le montant selon la devise
    if currency == 'XAF':
        # Pour XAF, arrondir à l'unité (pas de décimales)
        rounded_amount = round(amount)
        formatted_amount = "{:,}".format(int(rounded_amount)).replace(',', ' ')
    else:
        # Pour EUR et USD, arrondir à 2 décimales et supprimer les .00 si nécessaire
        rounded_amount = round(amount, 2)
        if rounded_amount == int(rounded_amount):
            # Si c'est un nombre entier, pas de décimales
            formatted_amount = "{:,}".format(int(rounded_amount)).replace(',', ' ')
        else:
            # Sinon, afficher avec 2 décimales
            formatted_amount = "{:,.2f}".format(rounded_amount).replace(',', ' ').replace('.', ',')

    return f"{formatted_amount} {symbol}"

def get_currency_symbol():
    """Retourne le symbole de la devise actuelle"""
    currency = session.get('default_currency', 'XAF')
    currency_symbols = {
        'XAF': 'FCFA',
        'EUR': '€',
        'USD': '$'
    }
    return currency_symbols.get(currency, 'FCFA')

def get_exchange_rates():
    """Retourne les taux de change (simulés pour l'instant)"""
    return {
        'XAF': {
            'EUR': 0.00152,  # 1 XAF = 0.00152 EUR
            'USD': 0.00165,  # 1 XAF = 0.00165 USD
            'XAF': 1.0
        },
        'EUR': {
            'XAF': 657.89,   # 1 EUR = 657.89 XAF (1/0.00152)
            'USD': 1.09,     # 1 EUR = 1.09 USD
            'EUR': 1.0
        },
        'USD': {
            'XAF': 606.06,   # 1 USD = 606.06 XAF (1/0.00165)
            'EUR': 0.917431, # 1 USD = 0.917431 EUR (1/1.09)
            'USD': 1.0
        }
    }

def convert_currency(amount, from_currency, to_currency):
    """Convertit un montant d'une devise vers une autre"""
    if from_currency == to_currency:
        return amount

    rates = get_exchange_rates()
    if from_currency in rates and to_currency in rates[from_currency]:
        converted_amount = amount * rates[from_currency][to_currency]

        # Arrondir selon la devise de destination
        if to_currency == 'XAF':
            return round(converted_amount)  # Pas de décimales pour XAF
        else:
            return round(converted_amount, 2)  # 2 décimales pour EUR et USD

    return amount

def get_all_currencies():
    """Retourne toutes les devises disponibles"""
    return {
        'XAF': 'Franc CFA (FCFA)',
        'EUR': 'Euro (€)',
        'USD': 'Dollar US ($)'
    }

def convert_amount_to_system_currency(amount, from_currency='XAF'):
    """Convertit un montant vers la devise système"""
    devise_systeme = session.get('default_currency', 'XAF')
    return convert_currency(amount, from_currency, devise_systeme)

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
        cur = get_cursor(conn)
        try:
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
            cur.close()
            conn.close()
    return render_template('register.html', questions=get_security_questions())

@app.route('/login', methods=('GET', 'POST'))
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = get_cursor(conn)
        try:
            sql = sql_placeholder('SELECT * FROM users WHERE username = ?')
            cur.execute(sql, (username,))
            user = cur.fetchone()
        finally:
            cur.close()
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
        cur = get_cursor(conn)
        try:
            sql = sql_placeholder('SELECT id, security_question FROM users WHERE username = ?')
            cur.execute(sql, (username,))
            user = cur.fetchone()
        finally:
            cur.close()
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
    cur = get_cursor(conn)
    try:
        sql = sql_placeholder('SELECT security_question, security_answer FROM users WHERE username = ?')
        cur.execute(sql, (username,))
        user = cur.fetchone()
    finally:
        cur.close()
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
        cur = get_cursor(conn)
        try:
            sql = sql_placeholder('UPDATE users SET password = ? WHERE username = ?')
            cur.execute(sql, (hashed_password, username))
            conn.commit()
        finally:
            cur.close()
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
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder("SELECT * FROM objectifs WHERE status = 'actif' AND user_id = ? ORDER BY id DESC")
        cur.execute(sql, (user_id,))
        objectifs_db = cur.fetchall()
        sql = sql_placeholder("SELECT SUM(montant_actuel) as total FROM objectifs WHERE status = 'actif' AND user_id = ?")
        cur.execute(sql, (user_id,))
        total_epargne_result = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if is_postgres:
        total_epargne = total_epargne_result['total'] if total_epargne_result and total_epargne_result['total'] is not None else 0
        objectifs = [dict(obj) for obj in objectifs_db]
    else:
        total_epargne = total_epargne_result[0] if total_epargne_result and total_epargne_result[0] is not None else 0
        objectifs = [convert_to_dict(obj, is_postgres=False) for obj in objectifs_db]

    # Convertir le total vers la devise système
    total_epargne_converti = convert_amount_to_system_currency(total_epargne, 'XAF')

    for obj in objectifs:
        progression = (obj['montant_actuel'] / obj['montant_cible']) * 100 if obj['montant_cible'] > 0 else 0
        obj['progression'] = progression
    return render_template('index.html', objectifs=objectifs, total_epargne=total_epargne_converti, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

@app.route('/app')
@login_required
def app_with_tabs():
    """Page principale avec système d'onglets dynamiques"""
    return render_template('base_with_tabs.html')

@app.route('/archives')
@login_required
def archives():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder("SELECT * FROM objectifs WHERE status = 'archivé' AND user_id = ? ORDER BY id DESC")
        cur.execute(sql, (user_id,))
        objectifs_archives = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if is_postgres:
        objectifs = [dict(obj) for obj in objectifs_archives]
    else:
        objectifs = [convert_to_dict(obj, is_postgres=False) for obj in objectifs_archives]

    # Convertir les montants vers la devise système
    for obj in objectifs:
        obj['montant_cible'] = convert_amount_to_system_currency(obj['montant_cible'], 'XAF')
        obj['montant_actuel'] = convert_amount_to_system_currency(obj['montant_actuel'], 'XAF')

    return render_template('archives.html', objectifs=objectifs, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

@app.route('/objectif/<int:objectif_id>')
@login_required
def objectif_detail(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    with get_cursor(conn) as cur:
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
    # Convertir les montants vers la devise système
    montant_cible_converti = convert_amount_to_system_currency(objectif['montant_cible'], 'XAF')
    montant_actuel_converti = convert_amount_to_system_currency(objectif['montant_actuel'], 'XAF')

    progression = (montant_actuel_converti / montant_cible_converti) * 100 if montant_cible_converti > 0 else 0
    montant_restant = montant_cible_converti - montant_actuel_converti
    rythme_quotidien = 0
    if objectif['date_limite'] and montant_restant > 0:
        try:
            date_limite = datetime.strptime(objectif['date_limite'], '%Y-%m-%d')
            jours_restants = (date_limite - datetime.now()).days
            if jours_restants > 0: rythme_quotidien = montant_restant / jours_restants
        except (ValueError, TypeError): pass
    # Créer un objectif avec les montants convertis
    objectif_converti = dict(objectif)
    objectif_converti['montant_cible'] = montant_cible_converti
    objectif_converti['montant_actuel'] = montant_actuel_converti

    return render_template('objectif_detail.html', objectif=objectif_converti, transactions=transactions, progression=progression, montant_restant=montant_restant, rythme_quotidien=rythme_quotidien, format_currency=format_currency, get_currency_symbol=get_currency_symbol, get_all_currencies=get_all_currencies, convert_currency=convert_currency)

@app.route('/formulaire_objectif/', defaults={'objectif_id': None}, methods=['GET'])
@app.route('/formulaire_objectif/<int:objectif_id>', methods=['GET'])
@login_required
def formulaire_objectif(objectif_id):
    objectif = None
    if objectif_id:
        user_id = session['user_id']
        conn = get_db_connection()
        with get_cursor(conn) as cur:
            sql = sql_placeholder('SELECT * FROM objectifs WHERE id = ? AND user_id = ?')
            cur.execute(sql, (objectif_id, user_id))
            objectif = cur.fetchone()
        conn.close()
        if objectif is None:
            flash("Cet objectif n'existe pas ou ne vous appartient pas.", "error")
            return redirect(url_for('index'))
    return render_template('formulaire_objectif.html', objectif=objectif, get_currency_symbol=get_currency_symbol, get_all_currencies=get_all_currencies)

@app.route('/sauvegarder_objectif/', defaults={'objectif_id': None}, methods=['POST'])
@app.route('/sauvegarder_objectif/<int:objectif_id>', methods=['POST'])
@login_required
def sauvegarder_objectif(objectif_id):
    user_id = session['user_id']
    password = request.form.get('password')
    conn = get_db_connection()
    with get_cursor(conn) as cur:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user = cur.fetchone()
        if not password or not check_password_hash(user['password'], password):
            flash("Mot de passe incorrect !", "error")
            conn.close()
            return redirect(url_for('formulaire_objectif', objectif_id=objectif_id))

        nom = request.form['nom']
        montant_cible = float(request.form['montant_cible'])
        devise_cible = request.form.get('devise_cible', session.get('default_currency', 'XAF'))
        devise_systeme = session.get('default_currency', 'XAF')

        # Convertir le montant cible vers la devise du système
        montant_cible_converti = convert_currency(montant_cible, devise_cible, devise_systeme)
        date_limite = request.form['date_limite'] if request.form['date_limite'] else None

        if objectif_id:
            sql = sql_placeholder('UPDATE objectifs SET nom = ?, montant_cible = ?, date_limite = ? WHERE id = ? AND user_id = ?')
            cur.execute(sql, (nom, montant_cible_converti, date_limite, objectif_id, user_id))
            flash(f"L'objectif '{nom}' a été mis à jour.", 'success')
        else:
            sql = sql_placeholder('INSERT INTO objectifs (nom, montant_cible, montant_actuel, date_limite, status, user_id) VALUES (?, ?, ?, ?, ?, ?)')
            cur.execute(sql, (nom, montant_cible_converti, 0, date_limite, 'actif', user_id))
            if devise_cible != devise_systeme:
                flash(f"L'objectif '{nom}' a été créé avec un montant cible de {format_currency(montant_cible, devise_cible)} converti en {format_currency(montant_cible_converti, devise_systeme)}.", 'success')
            else:
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
    with get_cursor(conn) as cur:
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
    cur = get_cursor(conn)
    try:
        sql = sql_placeholder("UPDATE objectifs SET status = 'archivé' WHERE id = ? AND user_id = ?")
        cur.execute(sql, (objectif_id, user_id))
        conn.commit()
        flash("Objectif archivé avec succès !", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/objectif/<int:objectif_id>/add_transaction', methods=['POST'])
@login_required
def add_transaction(objectif_id):
    user_id = session['user_id']
    montant = float(request.form['montant'])
    type_transaction = request.form['type_transaction']
    devise_saisie = request.form.get('devise', session.get('default_currency', 'XAF'))
    devise_systeme = session.get('default_currency', 'XAF')

    # Convertir le montant vers la devise du système
    montant_converti = convert_currency(montant, devise_saisie, devise_systeme)

    conn = get_db_connection()
    with get_cursor(conn) as cur:
        sql = sql_placeholder('SELECT * FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif is None:
            flash("Action non autorisée.", "error")
            return redirect(url_for('index'))

        montant_actuel = objectif['montant_actuel']
        nouveau_montant = montant_actuel + montant_converti if type_transaction == 'entree' else montant_actuel - montant_converti

        sql_update = sql_placeholder('UPDATE objectifs SET montant_actuel = ? WHERE id = ?')
        cur.execute(sql_update, (nouveau_montant, objectif_id))

        # Ajouter la transaction avec la devise de saisie
        sql_insert = sql_placeholder('INSERT INTO transactions (objectif_id, montant, type_transaction, user_id, devise_saisie) VALUES (?, ?, ?, ?, ?)')
        cur.execute(sql_insert, (objectif_id, montant, type_transaction, user_id, devise_saisie))

        conn.commit()

        # Message de confirmation avec conversion
        if devise_saisie != devise_systeme:
            flash(f"Transaction {type_transaction} de {format_currency(montant, devise_saisie)} convertie en {format_currency(montant_converti, devise_systeme)} ajoutée avec succès !", "success")
        else:
            flash(f"Transaction {type_transaction} de {format_currency(montant, devise_saisie)} ajoutée avec succès !", "success")

    conn.close()
    return redirect(url_for('objectif_detail', objectif_id=objectif_id))

@app.route('/parametres')
@login_required
def parametres():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    try:
        sql = sql_placeholder('SELECT username, security_question FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user_raw = cur.fetchone()
        if is_postgres:
            user = dict(user_raw)
        else:
            user = {'username': user_raw[0], 'security_question': user_raw[1]}
    finally:
        cur.close()
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
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    try:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user_raw = cur.fetchone()
        if is_postgres:
            user = dict(user_raw)
        else:
            user = {'password': user_raw[0]}
        if not check_password_hash(user['password'], ancien_mdp):
            flash("L'ancien mot de passe est incorrect.", "error")
        else:
            hashed_password = generate_password_hash(nouveau_mdp)
            sql_update = sql_placeholder('UPDATE users SET password = ? WHERE id = ?')
            cur.execute(sql_update, (hashed_password, user_id))
            conn.commit()
            flash("Mot de passe mis à jour.", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('parametres'))

@app.route('/update_countdown_settings', methods=['POST'])
@login_required
def update_countdown_settings():
    user_id = session['user_id']
    countdown_update_interval = request.form.get('countdown_update_interval', 60)
    countdown_warning_days = request.form.get('countdown_warning_days', 3)

    # Sauvegarder dans la session pour l'instant (pourrait être stocké en base)
    session['countdown_update_interval'] = int(countdown_update_interval)
    session['countdown_warning_days'] = int(countdown_warning_days)

    flash('Paramètres de compte à rebours mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_display_settings', methods=['POST'])
@login_required
def update_display_settings():
    user_id = session['user_id']
    show_countdown_on_list = request.form.get('show_countdown_on_list', 'true') == 'true'
    show_urgency_charts = request.form.get('show_urgency_charts', 'true') == 'true'
    default_currency = request.form.get('default_currency', 'XAF')

    # Sauvegarder dans la session pour l'instant
    session['show_countdown_on_list'] = show_countdown_on_list
    session['show_urgency_charts'] = show_urgency_charts
    session['default_currency'] = default_currency

    flash('Paramètres d\'affichage mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_notification_settings', methods=['POST'])
@login_required
def update_notification_settings():
    user_id = session['user_id']
    email_notifications = request.form.get('email_notifications', 'true') == 'true'
    notification_advance_days = request.form.get('notification_advance_days', 1)

    # Sauvegarder dans la session pour l'instant
    session['email_notifications'] = email_notifications
    session['notification_advance_days'] = int(notification_advance_days)

    flash('Paramètres de notifications mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_deletion_settings', methods=['POST'])
@login_required
def update_deletion_settings():
    user_id = session['user_id']
    auto_archive_completed = request.form.get('auto_archive_completed', 'true') == 'true'
    confirm_deletions = request.form.get('confirm_deletions', 'true') == 'true'

    # Sauvegarder dans la session pour l'instant
    session['auto_archive_completed'] = auto_archive_completed
    session['confirm_deletions'] = confirm_deletions

    flash('Paramètres de suppression mis à jour !', 'success')
    return redirect(url_for('parametres'))

# --- API Routes ---
@app.route('/api/check_user_password', methods=['POST'])
@login_required
def check_user_password():
    user_id = session['user_id']
    password = request.json.get('password')
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    try:
        sql = sql_placeholder('SELECT password FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user_raw = cur.fetchone()
        if is_postgres:
            user = dict(user_raw)
        else:
            user = {'password': user_raw[0]}
    finally:
        cur.close()
        conn.close()
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/chart_data/<int:objectif_id>')
@login_required
def chart_data(objectif_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))
    try:
        sql_obj = sql_placeholder('SELECT id FROM objectifs WHERE id = ? AND user_id = ?')
        cur.execute(sql_obj, (objectif_id, user_id))
        objectif = cur.fetchone()
        if objectif is None: return jsonify({'error': 'Not authorized'}), 403
        sql_trans = sql_placeholder('SELECT montant, type_transaction, date FROM transactions WHERE objectif_id = ? AND user_id = ? ORDER BY date ASC')
        cur.execute(sql_trans, (objectif_id, user_id))
        transactions_raw = cur.fetchall()
        if is_postgres:
            transactions = [dict(trans) for trans in transactions_raw]
        else:
            transactions = [{'montant': trans[0], 'type_transaction': trans[1], 'date': trans[2]} for trans in transactions_raw]
    finally:
        cur.close()
        conn.close()
    labels, data_entrees, data_sorties = ["Départ"], [0], [0]
    montant_cumulatif_entrees, montant_cumulatif_sorties = 0, 0
    for trans in transactions:
        if trans['type_transaction'] == 'entree': montant_cumulatif_entrees += trans['montant']
        else: montant_cumulatif_sorties += trans['montant']
        date_obj = trans['date']
        # La date est stockée comme une chaîne, on l'utilise directement
        formatted_date = date_obj if date_obj else 'N/A'
        labels.append(formatted_date)
        data_entrees.append(montant_cumulatif_entrees)
        data_sorties.append(montant_cumulatif_sorties)
    return jsonify({'labels': labels, 'data_entrees': data_entrees, 'data_sorties': data_sorties})

# --- ROUTES POUR LA GESTION DES TÂCHES ---
@app.route('/taches')
@login_required
def taches():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Récupérer les tâches actives
        sql_actives = sql_placeholder('SELECT * FROM taches WHERE user_id = ? AND termine = FALSE ORDER BY ordre ASC, date_creation ASC')
        cur.execute(sql_actives, (user_id,))
        taches_actives_raw = cur.fetchall()
        taches_actives = [convert_tache_to_dict(tache, is_postgres) for tache in taches_actives_raw]

        # Récupérer les tâches terminées
        sql_terminees = sql_placeholder('SELECT * FROM taches WHERE user_id = ? AND termine = TRUE ORDER BY date_modification DESC')
        cur.execute(sql_terminees, (user_id,))
        taches_terminees_raw = cur.fetchall()
        taches_terminees = [convert_tache_to_dict(tache, is_postgres) for tache in taches_terminees_raw]

        # Calculer le pourcentage de progression pour chaque tâche active
        total_etapes_global = 0
        total_etapes_terminees_global = 0

        for tache in taches_actives:
            sql_etapes = sql_placeholder('SELECT COUNT(*) as total, SUM(CASE WHEN terminee = TRUE THEN 1 ELSE 0 END) as terminees FROM etapes WHERE tache_id = ?')
            cur.execute(sql_etapes, (tache['id'],))
            result = cur.fetchone()
            if is_postgres:
                total_etapes = result['total'] or 0
                etapes_terminees = result['terminees'] or 0
            else:
                total_etapes = result[0] or 0
                etapes_terminees = result[1] or 0
            tache['progression'] = (etapes_terminees / total_etapes * 100) if total_etapes > 0 else 0
            tache['total_etapes'] = total_etapes
            tache['etapes_terminees'] = etapes_terminees

            # Ajouter au total global
            total_etapes_global += total_etapes
            total_etapes_terminees_global += etapes_terminees

        # Calculer le taux d'achèvement global
        taux_achevement_global = (total_etapes_terminees_global / total_etapes_global * 100) if total_etapes_global > 0 else 0
    finally:
        cur.close()
        conn.close()

    return render_template('taches.html', taches_actives=taches_actives, taches_terminees=taches_terminees, taux_achevement_global=taux_achevement_global, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

@app.route('/formulaire_tache/', defaults={'tache_id': None}, methods=['GET'])
@app.route('/formulaire_tache/<int:tache_id>', methods=['GET'])
@login_required
def formulaire_tache(tache_id):
    tache = None
    etapes = []
    if tache_id:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))
        try:
            sql = sql_placeholder('SELECT * FROM taches WHERE id = ? AND user_id = ?')
            cur.execute(sql, (tache_id, user_id))
            tache_raw = cur.fetchone()
            if tache_raw:
                tache = convert_tache_to_dict(tache_raw, is_postgres)
                sql_etapes = sql_placeholder('SELECT * FROM etapes WHERE tache_id = ? ORDER BY ordre ASC')
                cur.execute(sql_etapes, (tache_id,))
                etapes_raw = cur.fetchall()
                etapes = [convert_etape_to_dict(etape, is_postgres) for etape in etapes_raw]
        finally:
            cur.close()
            conn.close()
    return render_template('formulaire_tache.html', tache=tache, etapes=etapes, get_currency_symbol=get_currency_symbol)

@app.route('/sauvegarder_tache/', defaults={'tache_id': None}, methods=['POST'])
@app.route('/sauvegarder_tache/<int:tache_id>', methods=['POST'])
@login_required
def sauvegarder_tache(tache_id):
    user_id = session['user_id']
    titre = request.form.get('titre')
    description = request.form.get('description', '')
    date_limite = request.form.get('date_limite')
    etapes_text = request.form.get('etapes', '')

    if not titre:
        flash("Le titre de la tâche est requis.", "error")
        return redirect(url_for('formulaire_tache', tache_id=tache_id))

    conn = get_db_connection()
    cur = get_cursor(conn)
    try:
        if tache_id:
            # Modification d'une tâche existante
            sql_update = sql_placeholder('UPDATE taches SET titre = ?, description = ?, date_limite = ?, date_modification = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?')
            cur.execute(sql_update, (titre, description, date_limite, tache_id, user_id))

            # Supprimer les anciennes étapes
            sql_delete_etapes = sql_placeholder('DELETE FROM etapes WHERE tache_id = ?')
            cur.execute(sql_delete_etapes, (tache_id,))
        else:
            # Création d'une nouvelle tâche
            sql_insert = sql_placeholder('INSERT INTO taches (user_id, titre, description, date_limite) VALUES (?, ?, ?, ?) RETURNING id')
            cur.execute(sql_insert, (user_id, titre, description, date_limite))
            tache_id = cur.fetchone()[0]

        # Ajouter les nouvelles étapes
        if etapes_text.strip():
            etapes_list = [etape.strip() for etape in etapes_text.split('\n') if etape.strip()]
            for i, etape in enumerate(etapes_list):
                sql_etape = sql_placeholder('INSERT INTO etapes (tache_id, description, ordre) VALUES (?, ?, ?)')
                cur.execute(sql_etape, (tache_id, etape, i + 1))

        conn.commit()
        flash("Tâche sauvegardée avec succès !", "success")
        return redirect(url_for('taches'))

    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de la sauvegarde : {str(e)}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('formulaire_tache', tache_id=tache_id))

@app.route('/tache/<int:tache_id>/toggle_etape/<int:etape_id>', methods=['POST'])
@login_required
def toggle_etape(tache_id, etape_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Vérifier que la tâche appartient à l'utilisateur
        sql_tache = sql_placeholder('SELECT id FROM taches WHERE id = ? AND user_id = ?')
        cur.execute(sql_tache, (tache_id, user_id))
        if not cur.fetchone():
            return jsonify({'success': False, 'error': 'Tâche non trouvée'})

        # Basculer le statut de l'étape
        sql_toggle = sql_placeholder('UPDATE etapes SET terminee = NOT terminee, date_modification = CURRENT_TIMESTAMP WHERE id = ? AND tache_id = ?')
        cur.execute(sql_toggle, (etape_id, tache_id))

        # Vérifier si toutes les étapes sont terminées
        sql_check = sql_placeholder('SELECT COUNT(*) as total, SUM(CASE WHEN terminee = TRUE THEN 1 ELSE 0 END) as terminees FROM etapes WHERE tache_id = ?')
        cur.execute(sql_check, (tache_id,))
        result = cur.fetchone()
        if is_postgres:
            total_etapes = result['total'] or 0
            etapes_terminees = result['terminees'] or 0
        else:
            total_etapes = result[0] or 0
            etapes_terminees = result[1] or 0

        # Si toutes les étapes sont terminées, marquer la tâche comme terminée
        if total_etapes > 0 and etapes_terminees == total_etapes:
            sql_termine = sql_placeholder('UPDATE taches SET termine = TRUE, date_modification = CURRENT_TIMESTAMP WHERE id = ?')
            cur.execute(sql_termine, (tache_id,))

        conn.commit()
        progression = (etapes_terminees / total_etapes * 100) if total_etapes > 0 else 0
        return jsonify({
            'success': True,
            'progression': round(progression, 1),
            'etapes_terminees': etapes_terminees,
            'total_etapes': total_etapes,
            'terminee': etapes_terminees == total_etapes if total_etapes > 0 else False
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/supprimer_tache/<int:tache_id>', methods=['POST'])
@login_required
def supprimer_tache(tache_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    try:
        sql = sql_placeholder('DELETE FROM taches WHERE id = ? AND user_id = ?')
        cur.execute(sql, (tache_id, user_id))
        if cur.rowcount > 0:
            conn.commit()
            flash("Tâche supprimée avec succès.", "success")
        else:
            flash("Tâche non trouvée.", "error")
    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('taches'))

@app.route('/tache/<int:tache_id>/detail')
@login_required
def tache_detail(tache_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql_tache = sql_placeholder('SELECT * FROM taches WHERE id = ? AND user_id = ?')
        cur.execute(sql_tache, (tache_id, user_id))
        tache_raw = cur.fetchone()

        if not tache_raw:
            flash("Tâche non trouvée.", "error")
            return redirect(url_for('taches'))

        tache = convert_tache_to_dict(tache_raw, is_postgres)

        sql_etapes = sql_placeholder('SELECT * FROM etapes WHERE tache_id = ? ORDER BY ordre ASC')
        cur.execute(sql_etapes, (tache_id,))
        etapes_raw = cur.fetchall()
        etapes = [convert_etape_to_dict(etape, is_postgres) for etape in etapes_raw]

        # Calculer la progression
        total_etapes = len(etapes)
        etapes_terminees = sum(1 for etape in etapes if etape['terminee'])
        progression = (etapes_terminees / total_etapes * 100) if total_etapes > 0 else 0
        tache['progression'] = progression
        tache['total_etapes'] = total_etapes
        tache['etapes_terminees'] = etapes_terminees

    finally:
        cur.close()
        conn.close()

    return render_template('tache_detail.html', tache=tache, etapes=etapes, progression=progression, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- AGENDA ROUTES ---
@app.route('/agenda')
@login_required
def agenda():
    # Rediriger vers le calendrier qui fait maintenant office d'agenda
    return redirect(url_for('calendrier'))

@app.route('/formulaire_evenement/', defaults={'evenement_id': None}, methods=['GET'])
@app.route('/formulaire_evenement/<int:evenement_id>', methods=['GET'])
@login_required
def formulaire_evenement(evenement_id):
    evenement = None
    if evenement_id:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            sql = sql_placeholder('SELECT * FROM evenements WHERE id = ? AND user_id = ?')
            cur.execute(sql, (evenement_id, user_id))
            evenement_raw = cur.fetchone()
            if evenement_raw:
                evenement = convert_evenement_to_dict(evenement_raw, is_postgres)
        finally:
            cur.close()
            conn.close()

    return render_template('formulaire_evenement.html', evenement=evenement)

@app.route('/sauvegarder_evenement/', defaults={'evenement_id': None}, methods=['POST'])
@app.route('/sauvegarder_evenement/<int:evenement_id>', methods=['POST'])
@login_required
def sauvegarder_evenement(evenement_id):
    user_id = session['user_id']
    titre = request.form['titre']
    description = request.form.get('description', '')
    date_debut = request.form['date_debut']
    heure_debut = request.form.get('heure_debut', '')
    date_fin = request.form.get('date_fin', '')
    heure_fin = request.form.get('heure_fin', '')
    lieu = request.form.get('lieu', '')
    couleur = request.form.get('couleur', '#fd7e14')
    rappel_minutes = request.form.get('rappel', '0')

    conn = get_db_connection()
    cur = get_cursor(conn)

    try:
        if evenement_id:
            sql = sql_placeholder('UPDATE evenements SET titre = ?, description = ?, date_debut = ?, heure_debut = ?, date_fin = ?, heure_fin = ?, lieu = ?, couleur = ?, rappel_minutes = ?, date_modification = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?')
            cur.execute(sql, (titre, description, date_debut, heure_debut, date_fin, heure_fin, lieu, couleur, rappel_minutes, evenement_id, user_id))
            flash("Événement modifié avec succès.", "success")
        else:
            sql = sql_placeholder('INSERT INTO evenements (user_id, titre, description, date_debut, heure_debut, date_fin, heure_fin, lieu, couleur, rappel_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
            cur.execute(sql, (user_id, titre, description, date_debut, heure_debut, date_fin, heure_fin, lieu, couleur, rappel_minutes))
            flash("Événement créé avec succès.", "success")

        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de la sauvegarde : {str(e)}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('calendrier'))

@app.route('/evenement/<int:evenement_id>/toggle', methods=['POST'])
@login_required
def toggle_evenement(evenement_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)

    try:
        sql = sql_placeholder('UPDATE evenements SET termine = NOT termine WHERE id = ? AND user_id = ?')
        cur.execute(sql, (evenement_id, user_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/supprimer_evenement/<int:evenement_id>', methods=['POST'])
@login_required
def supprimer_evenement(evenement_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)

    try:
        sql = sql_placeholder('DELETE FROM evenements WHERE id = ? AND user_id = ?')
        cur.execute(sql, (evenement_id, user_id))
        if cur.rowcount > 0:
            conn.commit()
            flash("Événement supprimé avec succès.", "success")
        else:
            flash("Événement non trouvé.", "error")
    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('agenda'))

def convert_evenement_to_dict(row, is_postgres=False):
    if is_postgres:
        return dict(row)
    else:
        return {
            'id': row[0], 'user_id': row[1], 'titre': row[2], 'description': row[3],
            'date_debut': row[4], 'date_fin': row[5], 'heure_debut': row[6], 'heure_fin': row[7],
            'lieu': row[8], 'couleur': row[9], 'rappel_minutes': row[10], 'termine': row[11],
            'date_creation': row[12]
        }

# --- DASHBOARD ROUTES ---
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Statistiques des objectifs
        sql_objectifs = sql_placeholder('SELECT COUNT(*) FROM objectifs WHERE user_id = ? AND status = "actif"')
        cur.execute(sql_objectifs, (user_id,))
        total_objectifs = cur.fetchone()[0]

        sql_epargne = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = "actif"')
        cur.execute(sql_epargne, (user_id,))
        total_epargne = cur.fetchone()[0] or 0
        # Convertir le total vers la devise système
        total_epargne_converti = convert_amount_to_system_currency(total_epargne, 'XAF')

        # Statistiques des tâches
        sql_taches = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ?')
        cur.execute(sql_taches, (user_id,))
        total_taches = cur.fetchone()[0]

        sql_taches_terminees = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ? AND termine = TRUE')
        cur.execute(sql_taches_terminees, (user_id,))
        taches_terminees = cur.fetchone()[0]

        # Statistiques des événements
        sql_evenements = sql_placeholder('SELECT COUNT(*) FROM evenements WHERE user_id = ? AND termine = FALSE')
        cur.execute(sql_evenements, (user_id,))
        evenements_a_venir = cur.fetchone()[0]

        # Objectifs proches de la fin
        sql_objectifs_proches = sql_placeholder('''
            SELECT id, nom, montant_cible, montant_actuel, date_limite, status, user_id
            FROM objectifs
            WHERE user_id = ? AND status = "actif"
            ORDER BY (montant_cible - montant_actuel) ASC
            LIMIT 3
        ''')
        cur.execute(sql_objectifs_proches, (user_id,))
        objectifs_proches_raw = cur.fetchall()
        objectifs_proches = [convert_to_dict(obj, is_postgres) for obj in objectifs_proches_raw]

        # Convertir les montants des objectifs vers la devise système
        for obj in objectifs_proches:
            obj['montant_cible'] = convert_amount_to_system_currency(obj['montant_cible'], 'XAF')
            obj['montant_actuel'] = convert_amount_to_system_currency(obj['montant_actuel'], 'XAF')

        # Tâches prioritaires (non terminées)
        sql_taches_prioritaires = sql_placeholder('''
            SELECT id, user_id, titre, description, date_creation, date_modification, termine, ordre
            FROM taches
            WHERE user_id = ? AND termine = FALSE
            ORDER BY date_creation ASC
            LIMIT 5
        ''')
        cur.execute(sql_taches_prioritaires, (user_id,))
        taches_prioritaires_raw = cur.fetchall()
        taches_prioritaires = [convert_tache_to_dict(tache, is_postgres) for tache in taches_prioritaires_raw]

    finally:
        cur.close()
        conn.close()

    stats = {
        'total_objectifs': total_objectifs,
        'total_epargne': total_epargne_converti,
        'total_taches': total_taches,
        'taches_terminees': taches_terminees,
        'evenements_a_venir': evenements_a_venir,
        'objectifs_proches': objectifs_proches,
        'taches_prioritaires': taches_prioritaires
    }

    return render_template('dashboard.html', stats=stats, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- NOTIFICATIONS ROUTES ---
@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Objectifs proches de la fin (90% ou plus)
        sql_objectifs_proches = sql_placeholder('''
            SELECT id, nom, montant_cible, montant_actuel, date_limite, status, user_id
            FROM objectifs
            WHERE user_id = ? AND status = "actif" AND (montant_actuel / montant_cible) >= 0.9
        ''')
        cur.execute(sql_objectifs_proches, (user_id,))
        objectifs_proches_raw = cur.fetchall()
        objectifs_proches = [convert_to_dict(obj, is_postgres) for obj in objectifs_proches_raw]

        # Convertir les montants des objectifs vers la devise système
        for obj in objectifs_proches:
            obj['montant_cible'] = convert_amount_to_system_currency(obj['montant_cible'], 'XAF')
            obj['montant_actuel'] = convert_amount_to_system_currency(obj['montant_actuel'], 'XAF')

        # Tâches en retard (créées il y a plus de 7 jours)
        sql_taches_retard = sql_placeholder('''
            SELECT id, user_id, titre, description, date_creation, date_modification, termine, ordre
            FROM taches
            WHERE user_id = ? AND termine = FALSE AND date_creation < date("now", "-7 days")
        ''')
        cur.execute(sql_taches_retard, (user_id,))
        taches_retard_raw = cur.fetchall()
        taches_retard = [convert_tache_to_dict(tache, is_postgres) for tache in taches_retard_raw]

        # Événements à venir (dans les 7 prochains jours)
        sql_evenements_proches = sql_placeholder('''
            SELECT id, user_id, titre, description, date_debut, date_fin, heure_debut, heure_fin, lieu, couleur, rappel_minutes, termine, date_creation
            FROM evenements
            WHERE user_id = ? AND termine = FALSE
            AND date_debut BETWEEN date("now") AND date("now", "+7 days")
            ORDER BY date_debut ASC, heure_debut ASC
        ''')
        cur.execute(sql_evenements_proches, (user_id,))
        evenements_proches_raw = cur.fetchall()
        evenements_proches = [convert_evenement_to_dict(evenement, is_postgres) for evenement in evenements_proches_raw]

    finally:
        cur.close()
        conn.close()

    notifications = {
        'objectifs_proches': objectifs_proches,
        'taches_retard': taches_retard,
        'evenements_proches': evenements_proches
    }

    return render_template('notifications.html', notifications=notifications, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- CALENDRIER ROUTES ---
@app.route('/calendrier')
@login_required
def calendrier():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('SELECT * FROM evenements WHERE user_id = ? ORDER BY date_debut ASC, heure_debut ASC')
        cur.execute(sql, (user_id,))
        evenements_raw = cur.fetchall()
        evenements = [convert_evenement_to_dict(evenement, is_postgres) for evenement in evenements_raw]
    finally:
        cur.close()
        conn.close()

    return render_template('calendrier.html', evenements=evenements, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- RAPPORTS ROUTES ---
@app.route('/rapports')
@login_required
def rapports():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Statistiques générales
        sql_total_objectifs = sql_placeholder('SELECT COUNT(*) FROM objectifs WHERE user_id = ?')
        cur.execute(sql_total_objectifs, (user_id,))
        total_objectifs = cur.fetchone()[0]

        sql_epargne_actuelle = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = "actif"')
        cur.execute(sql_epargne_actuelle, (user_id,))
        epargne_actuelle = cur.fetchone()[0] or 0
        # Convertir l'épargne vers la devise système
        epargne_actuelle_convertie = convert_amount_to_system_currency(epargne_actuelle, 'XAF')

        sql_total_taches = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ?')
        cur.execute(sql_total_taches, (user_id,))
        total_taches = cur.fetchone()[0]

        sql_taux_reussite = sql_placeholder('''
            SELECT
                CASE
                    WHEN COUNT(*) > 0 THEN (COUNT(CASE WHEN termine = TRUE THEN 1 END) * 100.0 / COUNT(*))
                    ELSE 0
                END
            FROM taches WHERE user_id = ?
        ''')
        cur.execute(sql_taux_reussite, (user_id,))
        taux_reussite = cur.fetchone()[0] or 0

        # Évolution mensuelle des épargnes
        sql_evolution_mensuelle = sql_placeholder('''
            SELECT
                '2024-12' as mois,
                SUM(montant_actuel) as total
            FROM objectifs
            WHERE user_id = ?
        ''')
        cur.execute(sql_evolution_mensuelle, (user_id,))
        evolution_mensuelle_raw = cur.fetchall()
        evolution_mensuelle = [{'mois': row[0], 'total': convert_amount_to_system_currency(row[1], 'XAF')} for row in evolution_mensuelle_raw]

        # Performance des tâches par mois
        sql_performance_taches = sql_placeholder('''
            SELECT
                '2024-12' as mois,
                COUNT(*) as total_taches,
                COUNT(CASE WHEN termine = TRUE THEN 1 END) as taches_terminees
            FROM taches
            WHERE user_id = ?
        ''')
        cur.execute(sql_performance_taches, (user_id,))
        performance_taches_raw = cur.fetchall()
        performance_taches = [{'mois': row[0], 'total': row[1], 'terminees': row[2]} for row in performance_taches_raw]

    finally:
        cur.close()
        conn.close()

    stats = {
        'total_objectifs': total_objectifs,
        'epargne_actuelle': epargne_actuelle_convertie,
        'total_taches': total_taches,
        'taux_reussite': round(taux_reussite, 1),
        'evolution_mensuelle': evolution_mensuelle,
        'performance_taches': performance_taches
    }

    return render_template('rapports.html', stats=stats, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- PARAMÈTRES AVANCÉS ROUTES ---
@app.route('/parametres_avances')
@login_required
def parametres_avances():
    return render_template('parametres_avances.html')

# --- ROUTES API POUR LES ONGLETS ---
@app.route('/api/tab-content/<tab_name>')
@login_required
def tab_content(tab_name):
    """API pour charger le contenu des onglets dynamiquement"""
    user_id = session['user_id']

    if tab_name == 'epargne':
        # Contenu de la page d'épargne (index)
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? AND status = "actif" ORDER BY id DESC')
            cur.execute(sql_objectifs, (user_id,))
            objectifs = cur.fetchall()

            objectifs_list = []
            for row in objectifs:
                if is_postgres:
                    objectifs_list.append(dict(row))
                else:
                    objectifs_list.append(convert_to_dict(row))

        finally:
            cur.close()
            conn.close()

        return render_template('tab_content/epargne.html', objectifs=objectifs_list, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

    elif tab_name == 'taches':
        # Contenu de la page des tâches
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            sql_taches = sql_placeholder('SELECT * FROM taches WHERE user_id = ? ORDER BY ordre ASC, date_creation DESC')
            cur.execute(sql_taches, (user_id,))
            taches = cur.fetchall()

            taches_list = []
            for row in taches:
                if is_postgres:
                    taches_list.append(dict(row))
                else:
                    taches_list.append(convert_tache_to_dict(row))

        finally:
            cur.close()
            conn.close()

        return render_template('tab_content/taches.html', taches=taches_list)

    elif tab_name == 'agenda':
        # Contenu de la page agenda (calendrier)
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            sql_evenements = sql_placeholder('SELECT * FROM evenements WHERE user_id = ? ORDER BY date_debut ASC')
            cur.execute(sql_evenements, (user_id,))
            evenements = cur.fetchall()

            evenements_list = []
            for row in evenements:
                if is_postgres:
                    evenements_list.append(dict(row))
                else:
                    evenements_list.append(convert_evenement_to_dict(row))

        finally:
            cur.close()
            conn.close()

        return render_template('tab_content/agenda.html', evenements=evenements_list)

    elif tab_name == 'dashboard':
        # Contenu du dashboard
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            # Statistiques pour le dashboard
            sql_total_objectifs = sql_placeholder('SELECT COUNT(*) FROM objectifs WHERE user_id = ? AND status = "actif"')
            cur.execute(sql_total_objectifs, (user_id,))
            total_objectifs = cur.fetchone()[0]

            sql_epargne_totale = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = "actif"')
            cur.execute(sql_epargne_totale, (user_id,))
            epargne_totale = cur.fetchone()[0] or 0

            sql_total_taches = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ?')
            cur.execute(sql_total_taches, (user_id,))
            total_taches = cur.fetchone()[0]

            sql_taches_terminees = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ? AND termine = TRUE')
            cur.execute(sql_taches_terminees, (user_id,))
            taches_terminees = cur.fetchone()[0]

        finally:
            cur.close()
            conn.close()

        stats = {
            'total_objectifs': total_objectifs,
            'epargne_totale': epargne_totale,
            'total_taches': total_taches,
            'taches_terminees': taches_terminees
        }

        return render_template('tab_content/dashboard.html', stats=stats, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

    elif tab_name == 'notifications':
        # Contenu des notifications
        return render_template('tab_content/notifications.html')

    elif tab_name == 'rapports':
        # Contenu des rapports
        conn = get_db_connection()
        cur = get_cursor(conn)
        is_postgres = bool(os.environ.get('DATABASE_URL'))

        try:
            # Statistiques pour les rapports
            sql_total_objectifs = sql_placeholder('SELECT COUNT(*) FROM objectifs WHERE user_id = ?')
            cur.execute(sql_total_objectifs, (user_id,))
            total_objectifs = cur.fetchone()[0]

            sql_epargne_actuelle = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = "actif"')
            cur.execute(sql_epargne_actuelle, (user_id,))
            epargne_actuelle = cur.fetchone()[0] or 0

            sql_total_taches = sql_placeholder('SELECT COUNT(*) FROM taches WHERE user_id = ?')
            cur.execute(sql_total_taches, (user_id,))
            total_taches = cur.fetchone()[0]

            sql_taux_reussite = sql_placeholder('''
                SELECT
                    CASE
                        WHEN COUNT(*) > 0 THEN (COUNT(CASE WHEN termine = TRUE THEN 1 END) * 100.0 / COUNT(*))
                        ELSE 0
                    END
                FROM taches WHERE user_id = ?
            ''')
            cur.execute(sql_taux_reussite, (user_id,))
            taux_reussite = cur.fetchone()[0] or 0

        finally:
            cur.close()
            conn.close()

        stats = {
            'total_objectifs': total_objectifs,
            'epargne_actuelle': epargne_actuelle,
            'total_taches': total_taches,
            'taux_reussite': round(taux_reussite, 1)
        }

        return render_template('tab_content/rapports.html', stats=stats, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

    else:
        return "Onglet non trouvé", 404

# --- Point de démarrage ---
if __name__ == '__main__':
    if not os.path.exists('epargne.db') and not os.environ.get('DATABASE_URL'):
        print("Base de données SQLite non trouvée, création...")
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, security_question TEXT, security_answer TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS objectifs (id INTEGER PRIMARY KEY, nom TEXT NOT NULL, montant_cible REAL NOT NULL, montant_actuel REAL NOT NULL, date_limite TEXT, status TEXT NOT NULL DEFAULT 'actif', user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, objectif_id INTEGER NOT NULL, montant REAL NOT NULL, type_transaction TEXT NOT NULL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id INTEGER NOT NULL, FOREIGN KEY (objectif_id) REFERENCES objectifs (id), FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS taches (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, titre TEXT NOT NULL, description TEXT, date_limite TEXT, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP, termine BOOLEAN DEFAULT FALSE, ordre INTEGER DEFAULT 0, FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS etapes (id INTEGER PRIMARY KEY, tache_id INTEGER NOT NULL, description TEXT NOT NULL, terminee BOOLEAN DEFAULT FALSE, ordre INTEGER DEFAULT 0, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (tache_id) REFERENCES taches (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS evenements (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, titre TEXT NOT NULL, description TEXT, date_debut TEXT NOT NULL, heure_debut TEXT, date_fin TEXT, heure_fin TEXT, lieu TEXT, couleur TEXT DEFAULT '#fd7e14', rappel TEXT, termine BOOLEAN DEFAULT FALSE, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id))")
        conn.commit()
        conn.close()
        print("Base de données SQLite créée.")

    app.run(debug=True)