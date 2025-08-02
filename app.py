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

# Initialisation automatique de la base de données
def init_database():
    """Initialise la base de données PostgreSQL avec toutes les tables nécessaires"""

    # Récupérer l'URL de la base de données depuis les variables d'environnement
    DATABASE_URL = os.getenv('DATABASE_URL')

    if not DATABASE_URL:
        print("⚠️  DATABASE_URL non définie, utilisation de SQLite")
        return False

    try:
        print("🔗 Connexion à la base de données PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Vérifier si les tables existent déjà
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'users'
            );
        """)

        if cur.fetchone()[0]:
            print("✅ Tables déjà existantes, initialisation ignorée")
            cur.close()
            conn.close()
            return True

        print("🗑️  Suppression des anciennes tables (si elles existent)...")
        cur.execute("DROP TABLE IF EXISTS transactions CASCADE;")
        cur.execute("DROP TABLE IF EXISTS taches CASCADE;")
        cur.execute("DROP TABLE IF EXISTS etapes CASCADE;")
        cur.execute("DROP TABLE IF EXISTS evenements CASCADE;")
        cur.execute("DROP TABLE IF EXISTS objectifs CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")

        print("🏗️  Création de la structure des tables...")

        # Table users
        cur.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(120) NOT NULL,
            security_question VARCHAR(200),
            security_answer VARCHAR(120),
            display_currency BOOLEAN DEFAULT TRUE,
            display_progress BOOLEAN DEFAULT TRUE,
            notification_enabled BOOLEAN DEFAULT TRUE,
            auto_delete_completed BOOLEAN DEFAULT FALSE,
            auto_delete_days INTEGER DEFAULT 90,
            countdown_enabled BOOLEAN DEFAULT TRUE,
            countdown_days INTEGER DEFAULT 30,
            default_currency VARCHAR(3) DEFAULT 'XAF',
            nom VARCHAR(100),
            prenom VARCHAR(100),
            date_naissance DATE,
            telephone VARCHAR(20),
            email VARCHAR(120),
            sexe VARCHAR(10),
            photo_profil VARCHAR(200),
            bio TEXT,
            adresse TEXT,
            ville VARCHAR(100),
            pays VARCHAR(100) DEFAULT 'Cameroun',
            date_creation_profil TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table objectifs
        cur.execute('''
        CREATE TABLE objectifs (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(200) NOT NULL,
            montant_cible DECIMAL(15,2) NOT NULL,
            montant_actuel DECIMAL(15,2) DEFAULT 0,
            date_limite DATE,
            status VARCHAR(20) DEFAULT 'actif',
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table transactions
        cur.execute('''
        CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            objectif_id INTEGER REFERENCES objectifs(id) ON DELETE CASCADE,
            montant DECIMAL(15,2) NOT NULL,
            type_transaction VARCHAR(20) NOT NULL,
            devise_saisie VARCHAR(3) DEFAULT 'XAF',
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table taches
        cur.execute('''
        CREATE TABLE taches (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(200) NOT NULL,
            description TEXT,
            priorite VARCHAR(20) DEFAULT 'moyenne',
            status VARCHAR(20) DEFAULT 'en_cours',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_limite DATE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        );
        ''')

        # Table etapes
        cur.execute('''
        CREATE TABLE etapes (
            id SERIAL PRIMARY KEY,
            tache_id INTEGER REFERENCES taches(id) ON DELETE CASCADE,
            description VARCHAR(200) NOT NULL,
            terminee BOOLEAN DEFAULT FALSE,
            ordre INTEGER DEFAULT 0
        );
        ''')

        # Table evenements
        cur.execute('''
        CREATE TABLE evenements (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(200) NOT NULL,
            description TEXT,
            date_debut TIMESTAMP NOT NULL,
            date_fin TIMESTAMP,
            lieu VARCHAR(200),
            type_evenement VARCHAR(50) DEFAULT 'general',
            rappel_minutes INTEGER DEFAULT 30,
            termine BOOLEAN DEFAULT FALSE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table notifications
        cur.execute('''
        CREATE TABLE notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            titre VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type_notification VARCHAR(50) DEFAULT 'info',
            lue BOOLEAN DEFAULT FALSE,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        print("✅ Structure des tables créée avec succès.")
        conn.commit()
        cur.close()
        conn.close()
        print("🔒 Connexion fermée.")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        return False

# Initialiser la base de données au démarrage
if __name__ == "__main__":
    init_database()

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
    """Formate un montant selon la devise sélectionnée avec conversion automatique"""
    if currency is None:
        currency = session.get('default_currency', 'XAF')

    # Supposer que le montant est en XAF par défaut (devise de base)
    from_currency = 'XAF'

    # Convertir le montant vers la devise sélectionnée
    converted_amount = convert_currency(amount, from_currency, currency)

    return format_currency_direct(converted_amount, currency)

def format_currency_direct(amount, currency):
    """Formate un montant directement dans la devise spécifiée (sans conversion)"""
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
            'EUR': 0.001538,  # 1 XAF = 0.001538 EUR (1/650)
            'USD': 0.001667,  # 1 XAF = 0.001667 USD (1/600)
            'XAF': 1.0
        },
        'EUR': {
            'XAF': 650.0,     # 1 EUR = 650 XAF
            'USD': 1.08,      # 1 EUR = 1.08 USD
            'EUR': 1.0
        },
        'USD': {
            'XAF': 600.0,     # 1 USD = 600 XAF
            'EUR': 0.925926,  # 1 USD = 0.925926 EUR (1/1.08)
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

@app.route('/api/exchange_rates')
@login_required
def get_exchange_rates_api():
    """API pour récupérer les taux de change"""
    return jsonify(get_exchange_rates())

def convert_amount_to_system_currency(amount, from_currency='XAF'):
    """Convertit un montant vers la devise système"""
    devise_systeme = session.get('default_currency', 'XAF')
    return convert_currency(amount, from_currency, devise_systeme)

def format_amount_with_conversion(amount, from_currency='XAF', to_currency=None):
    """Formate un montant avec conversion automatique vers la devise sélectionnée"""
    if to_currency is None:
        to_currency = session.get('default_currency', 'XAF')

    converted_amount = convert_currency(amount, from_currency, to_currency)
    return format_currency(converted_amount, to_currency)

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
    # Rediriger vers la nouvelle interface avec onglets
    return redirect(url_for('app_with_tabs'))

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

    return render_template('objectif_detail.html', objectif=objectif_converti, transactions=transactions, progression=progression, montant_restant=montant_restant, rythme_quotidien=rythme_quotidien, format_currency=format_currency, format_currency_direct=format_currency_direct, get_currency_symbol=get_currency_symbol, get_all_currencies=get_all_currencies, convert_currency=convert_currency)

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
    return render_template('parametres.html')

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
    countdown_enabled = request.form.get('countdown_enabled', 'true') == 'true'
    countdown_days = request.form.get('countdown_days', 30)
    countdown_update_interval = request.form.get('countdown_update_interval', 60)
    countdown_warning_days = request.form.get('countdown_warning_days', 3)

    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('UPDATE users SET countdown_enabled = ?, countdown_days = ? WHERE id = ?')
        cur.execute(sql, (countdown_enabled, countdown_days, user_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    # Sauvegarder dans la session pour l'instant
    session['countdown_update_interval'] = int(countdown_update_interval)
    session['countdown_warning_days'] = int(countdown_warning_days)

    flash('Paramètres de compte à rebours mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_display_settings', methods=['POST'])
@login_required
def update_display_settings():
    user_id = session['user_id']
    display_currency = request.form.get('display_currency', 'true') == 'true'
    display_progress = request.form.get('display_progress', 'true') == 'true'
    show_countdown_on_list = request.form.get('show_countdown_on_list', 'true') == 'true'
    default_currency = request.form.get('default_currency', 'XAF')

    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('UPDATE users SET display_currency = ?, display_progress = ?, default_currency = ? WHERE id = ?')
        cur.execute(sql, (display_currency, display_progress, default_currency, user_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    # Sauvegarder dans la session pour l'instant
    session['show_countdown_on_list'] = show_countdown_on_list
    session['default_currency'] = default_currency

    flash('Paramètres d\'affichage mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_notification_settings', methods=['POST'])
@login_required
def update_notification_settings():
    user_id = session['user_id']
    notification_enabled = request.form.get('notification_enabled', 'true') == 'true'
    email_notifications = request.form.get('email_notifications', 'true') == 'true'
    notification_advance_days = request.form.get('notification_advance_days', 1)

    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('UPDATE users SET notification_enabled = ? WHERE id = ?')
        cur.execute(sql, (notification_enabled, user_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    # Sauvegarder dans la session pour l'instant
    session['email_notifications'] = email_notifications
    session['notification_advance_days'] = int(notification_advance_days)

    flash('Paramètres de notifications mis à jour !', 'success')
    return redirect(url_for('parametres'))

@app.route('/update_deletion_settings', methods=['POST'])
@login_required
def update_deletion_settings():
    user_id = session['user_id']
    auto_delete_completed = request.form.get('auto_delete_completed', 'true') == 'true'
    auto_delete_days = request.form.get('auto_delete_days', 90)

    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('UPDATE users SET auto_delete_completed = ?, auto_delete_days = ? WHERE id = ?')
        cur.execute(sql, (auto_delete_completed, auto_delete_days, user_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    flash('Paramètres de suppression automatique mis à jour !', 'success')
    return redirect(url_for('parametres'))

# --- ROUTES DU PROFIL UTILISATEUR ---
@app.route('/profil')
@login_required
def profil():
    """Page de profil utilisateur"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('''
            SELECT username, nom, prenom, date_naissance, telephone, email, sexe,
                   photo_profil, bio, adresse, ville, pays, date_creation_profil
            FROM users WHERE id = ?
        ''')
        cur.execute(sql, (user_id,))
        user_data = cur.fetchone()

        if is_postgres:
            profil = dict(user_data) if user_data else {}
        else:
            profil = {
                'username': user_data[0] if user_data else '',
                'nom': user_data[1] if user_data else '',
                'prenom': user_data[2] if user_data else '',
                'date_naissance': user_data[3] if user_data else '',
                'telephone': user_data[4] if user_data else '',
                'email': user_data[5] if user_data else '',
                'sexe': user_data[6] if user_data else '',
                'photo_profil': user_data[7] if user_data else '',
                'bio': user_data[8] if user_data else '',
                'adresse': user_data[9] if user_data else '',
                'ville': user_data[10] if user_data else '',
                'pays': user_data[11] if user_data else '',
                'date_creation_profil': user_data[12] if user_data else None
            }
    finally:
        cur.close()
        conn.close()

    return render_template('profil.html', profil=profil)

@app.route('/update_profil', methods=['POST'])
@login_required
def update_profil():
    """Mise à jour du profil utilisateur"""
    user_id = session['user_id']

    # Récupérer les données du formulaire
    nom = request.form.get('nom', '').strip()
    prenom = request.form.get('prenom', '').strip()
    date_naissance = request.form.get('date_naissance', '').strip()
    telephone = request.form.get('telephone', '').strip()
    email = request.form.get('email', '').strip()
    sexe = request.form.get('sexe', '').strip()
    bio = request.form.get('bio', '').strip()
    adresse = request.form.get('adresse', '').strip()
    ville = request.form.get('ville', '').strip()
    pays = request.form.get('pays', 'Cameroun').strip()

    # Gestion de la photo de profil
    photo_profil = None
    if 'photo_profil' in request.files:
        file = request.files['photo_profil']
        if file and file.filename:
            # Vérifier le type de fichier
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # Créer un nom de fichier unique
                filename = f"profil_{user_id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}"

                # Créer le dossier static/uploads s'il n'existe pas
                upload_folder = os.path.join(app.static_folder, 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                # Sauvegarder le fichier
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                photo_profil = f"uploads/{filename}"

    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        if photo_profil:
            # Mise à jour avec photo
            sql = sql_placeholder('''
                UPDATE users SET nom = ?, prenom = ?, date_naissance = ?, telephone = ?,
                               email = ?, sexe = ?, photo_profil = ?, bio = ?, adresse = ?,
                               ville = ?, pays = ? WHERE id = ?
            ''')
            cur.execute(sql, (nom, prenom, date_naissance, telephone, email, sexe,
                            photo_profil, bio, adresse, ville, pays, user_id))
        else:
            # Mise à jour sans photo
            sql = sql_placeholder('''
                UPDATE users SET nom = ?, prenom = ?, date_naissance = ?, telephone = ?,
                               email = ?, sexe = ?, bio = ?, adresse = ?, ville = ?, pays = ?
                               WHERE id = ?
            ''')
            cur.execute(sql, (nom, prenom, date_naissance, telephone, email, sexe,
                            bio, adresse, ville, pays, user_id))

        conn.commit()
        flash('Profil mis à jour avec succès !', 'success')

        # Mettre à jour le nom d'affichage dans la session
        if nom and prenom:
            session['display_name'] = f"{prenom} {nom}"
        elif nom:
            session['display_name'] = nom
        elif prenom:
            session['display_name'] = prenom
        else:
            session['display_name'] = session['username']

    except Exception as e:
        conn.rollback()
        flash(f'Erreur lors de la mise à jour du profil : {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('profil'))

@app.route('/api/user_info')
@login_required
def get_user_info():
    """API pour récupérer les informations utilisateur pour l'en-tête"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        sql = sql_placeholder('SELECT username, nom, prenom, photo_profil FROM users WHERE id = ?')
        cur.execute(sql, (user_id,))
        user_data = cur.fetchone()

        if is_postgres:
            user_info = dict(user_data) if user_data else {}
        else:
            user_info = {
                'username': user_data[0] if user_data else '',
                'nom': user_data[1] if user_data else '',
                'prenom': user_data[2] if user_data else '',
                'photo_profil': user_data[3] if user_data else ''
            }

        # Déterminer le nom d'affichage
        if user_info.get('prenom') and user_info.get('nom'):
            display_name = f"{user_info['prenom']} {user_info['nom']}"
        elif user_info.get('prenom'):
            display_name = user_info['prenom']
        elif user_info.get('nom'):
            display_name = user_info['nom']
        else:
            display_name = user_info.get('username', 'Utilisateur')

        return jsonify({
            'success': True,
            'display_name': display_name,
            'photo_profil': user_info.get('photo_profil', ''),
            'username': user_info.get('username', '')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

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
        return redirect(url_for('app_with_tabs'))

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
    return redirect(url_for('app_with_tabs'))

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
            return redirect(url_for('app_with_tabs'))

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
            WHERE user_id = ? AND status = 'actif' AND (montant_actuel / montant_cible) >= 0.9
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

        sql_epargne_actuelle = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = \'actif\'')
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

    return render_template('tab_content/rapports.html', stats=stats, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

# --- ROUTES D'EXPORTATION ---
@app.route('/export/pdf')
@login_required
def export_pdf():
    """Export des données en PDF"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Récupérer toutes les données de l'utilisateur
        sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? ORDER BY id DESC')
        cur.execute(sql_objectifs, (user_id,))
        objectifs_raw = cur.fetchall()
        objectifs = [convert_to_dict(obj, is_postgres) for obj in objectifs_raw]

        sql_taches = sql_placeholder('SELECT * FROM taches WHERE user_id = ? ORDER BY date_creation DESC')
        cur.execute(sql_taches, (user_id,))
        taches_raw = cur.fetchall()
        taches = [convert_tache_to_dict(tache, is_postgres) for tache in taches_raw]

        sql_evenements = sql_placeholder('SELECT * FROM evenements WHERE user_id = ? ORDER BY date_debut ASC')
        cur.execute(sql_evenements, (user_id,))
        evenements_raw = cur.fetchall()
        evenements = [convert_evenement_to_dict(evenement, is_postgres) for evenement in evenements_raw]

        # Calculer les statistiques
        total_epargne = sum(obj['montant_actuel'] for obj in objectifs if obj['status'] == 'actif')
        total_taches = len(taches)
        taches_terminees = sum(1 for tache in taches if tache.get('termine', False))
        taux_reussite = (taches_terminees / total_taches * 100) if total_taches > 0 else 0

        # Créer le contenu HTML pour le PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport d'Épargne - {session['username']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .section h2 {{ color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stats {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                .stat {{ text-align: center; padding: 10px; border: 1px solid #ddd; flex: 1; margin: 0 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport d'Épargne</h1>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                <p>Utilisateur: {session['username']}</p>
            </div>

            <div class="stats">
                <div class="stat">
                    <h3>Total Épargne</h3>
                    <p>{format_currency(total_epargne)}</p>
                </div>
                <div class="stat">
                    <h3>Objectifs Actifs</h3>
                    <p>{len([obj for obj in objectifs if obj['status'] == 'actif'])}</p>
                </div>
                <div class="stat">
                    <h3>Tâches Terminées</h3>
                    <p>{taches_terminees}/{total_taches} ({taux_reussite:.1f}%)</p>
                </div>
            </div>

            <div class="section">
                <h2>Objectifs d'Épargne</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Montant Cible</th>
                            <th>Montant Actuel</th>
                            <th>Progression</th>
                            <th>Date Limite</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for obj in objectifs:
            progression = (obj['montant_actuel'] / obj['montant_cible'] * 100) if obj['montant_cible'] > 0 else 0
            html_content += f"""
                        <tr>
                            <td>{obj['nom']}</td>
                            <td>{format_currency(obj['montant_cible'])}</td>
                            <td>{format_currency(obj['montant_actuel'])}</td>
                            <td>{progression:.1f}%</td>
                            <td>{obj['date_limite'] or 'Non définie'}</td>
                            <td>{obj['status']}</td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Tâches</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Titre</th>
                            <th>Description</th>
                            <th>Date Limite</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for tache in taches:
            html_content += f"""
                        <tr>
                            <td>{tache['titre']}</td>
                            <td>{tache.get('description', '')}</td>
                            <td>{tache.get('date_limite', 'Non définie')}</td>
                            <td>{'Terminée' if tache.get('termine', False) else 'En cours'}</td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Événements</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Titre</th>
                            <th>Description</th>
                            <th>Date Début</th>
                            <th>Date Fin</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for evenement in evenements:
            html_content += f"""
                        <tr>
                            <td>{evenement['titre']}</td>
                            <td>{evenement.get('description', '')}</td>
                            <td>{evenement['date_debut']}</td>
                            <td>{evenement.get('date_fin', 'Non définie')}</td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """

        # Retourner le HTML pour génération PDF côté client
        return jsonify({
            'success': True,
            'html': html_content,
            'filename': f'rapport_epargne_{session["username"]}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/export/excel')
@login_required
def export_excel():
    """Export des données en Excel (CSV)"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Récupérer toutes les données
        sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? ORDER BY id DESC')
        cur.execute(sql_objectifs, (user_id,))
        objectifs_raw = cur.fetchall()
        objectifs = [convert_to_dict(obj, is_postgres) for obj in objectifs_raw]

        sql_taches = sql_placeholder('SELECT * FROM taches WHERE user_id = ? ORDER BY date_creation DESC')
        cur.execute(sql_taches, (user_id,))
        taches_raw = cur.fetchall()
        taches = [convert_tache_to_dict(tache, is_postgres) for tache in taches_raw]

        sql_evenements = sql_placeholder('SELECT * FROM evenements WHERE user_id = ? ORDER BY date_debut ASC')
        cur.execute(sql_evenements, (user_id,))
        evenements_raw = cur.fetchall()
        evenements = [convert_evenement_to_dict(evenement, is_postgres) for evenement in evenements_raw]

        # Créer le contenu CSV
        csv_content = "Nom,Montant Cible,Montant Actuel,Progression,Date Limite,Statut\n"
        for obj in objectifs:
            progression = (obj['montant_actuel'] / obj['montant_cible'] * 100) if obj['montant_cible'] > 0 else 0
            csv_content += f'"{obj["nom"]}",{obj["montant_cible"]},{obj["montant_actuel"]},{progression:.1f}%,{obj["date_limite"] or ""},{obj["status"]}\n'

        csv_content += "\nTâches\n"
        csv_content += "Titre,Description,Date Limite,Statut\n"
        for tache in taches:
            csv_content += f'"{tache["titre"]}","{tache.get("description", "")}",{tache.get("date_limite", "")},{"Terminée" if tache.get("termine", False) else "En cours"}\n'

        csv_content += "\nÉvénements\n"
        csv_content += "Titre,Description,Date Début,Date Fin\n"
        for evenement in evenements:
            csv_content += f'"{evenement["titre"]}","{evenement.get("description", "")}",{evenement["date_debut"]},{evenement.get("date_fin", "")}\n'

        return jsonify({
            'success': True,
            'csv': csv_content,
            'filename': f'donnees_epargne_{session["username"]}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/export/charts')
@login_required
def export_charts():
    """Export des graphiques en image"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Récupérer les données pour les graphiques
        sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? AND status = \'actif\'')
        cur.execute(sql_objectifs, (user_id,))
        objectifs_raw = cur.fetchall()
        objectifs = [convert_to_dict(obj, is_postgres) for obj in objectifs_raw]

        sql_taches = sql_placeholder('SELECT * FROM taches WHERE user_id = ?')
        cur.execute(sql_taches, (user_id,))
        taches_raw = cur.fetchall()
        taches = [convert_tache_to_dict(tache, is_postgres) for tache in taches_raw]

        # Calculer les statistiques
        total_epargne = sum(obj['montant_actuel'] for obj in objectifs)
        total_taches = len(taches)
        taches_terminees = sum(1 for tache in taches if tache.get('termine', False))
        taux_reussite = (taches_terminees / total_taches * 100) if total_taches > 0 else 0

        # Créer les données pour les graphiques
        chart_data = {
            'objectifs': [
                {
                    'nom': obj['nom'],
                    'montant_cible': obj['montant_cible'],
                    'montant_actuel': obj['montant_actuel'],
                    'progression': (obj['montant_actuel'] / obj['montant_cible'] * 100) if obj['montant_cible'] > 0 else 0
                }
                for obj in objectifs
            ],
            'stats': {
                'total_epargne': total_epargne,
                'total_objectifs': len(objectifs),
                'total_taches': total_taches,
                'taches_terminees': taches_terminees,
                'taux_reussite': taux_reussite
            }
        }

        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'filename': f'graphiques_epargne_{session["username"]}_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/export/print')
@login_required
def export_print():
    """Préparation des données pour impression"""
    user_id = session['user_id']
    conn = get_db_connection()
    cur = get_cursor(conn)
    is_postgres = bool(os.environ.get('DATABASE_URL'))

    try:
        # Récupérer les données essentielles
        sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? AND status = \'actif\' ORDER BY id DESC')
        cur.execute(sql_objectifs, (user_id,))
        objectifs_raw = cur.fetchall()
        objectifs = [convert_to_dict(obj, is_postgres) for obj in objectifs_raw]

        sql_taches = sql_placeholder('SELECT * FROM taches WHERE user_id = ? ORDER BY date_creation DESC LIMIT 10')
        cur.execute(sql_taches, (user_id,))
        taches_raw = cur.fetchall()
        taches = [convert_tache_to_dict(tache, is_postgres) for tache in taches_raw]

        # Calculer les statistiques
        total_epargne = sum(obj['montant_actuel'] for obj in objectifs)
        total_taches = len(taches)
        taches_terminees = sum(1 for tache in taches if tache.get('termine', False))

        print_data = {
            'username': session['username'],
            'date_export': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            'total_epargne': total_epargne,
            'total_objectifs': len(objectifs),
            'total_taches': total_taches,
            'taches_terminees': taches_terminees,
            'objectifs': objectifs,
            'taches': taches
        }

        return jsonify({
            'success': True,
            'print_data': print_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

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
            sql_objectifs = sql_placeholder('SELECT * FROM objectifs WHERE user_id = ? AND status = \'actif\' ORDER BY id DESC')
            cur.execute(sql_objectifs, (user_id,))
            objectifs = cur.fetchall()

            # Calculer l'épargne totale
            sql_total_epargne = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = \'actif\'')
            cur.execute(sql_total_epargne, (user_id,))
            total_epargne = cur.fetchone()[0] or 0

            objectifs_list = []
            for row in objectifs:
                if is_postgres:
                    obj_dict = dict(row)
                else:
                    obj_dict = convert_to_dict(row)

                # Calculer la progression pour chaque objectif
                if obj_dict['montant_cible'] > 0:
                    obj_dict['progression'] = (obj_dict['montant_actuel'] / obj_dict['montant_cible']) * 100
                else:
                    obj_dict['progression'] = 0

                objectifs_list.append(obj_dict)

        finally:
            cur.close()
            conn.close()

        return render_template('tab_content/epargne.html', objectifs=objectifs_list, total_epargne=total_epargne, format_currency=format_currency, get_currency_symbol=get_currency_symbol)

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
            total_taches = 0
            taches_terminees = 0

            for row in taches:
                if is_postgres:
                    tache_dict = dict(row)
                else:
                    tache_dict = convert_tache_to_dict(row)

                # Récupérer les étapes de cette tâche
                sql_etapes = sql_placeholder('SELECT * FROM etapes WHERE tache_id = ? ORDER BY ordre ASC')
                cur.execute(sql_etapes, (tache_dict['id'],))
                etapes = cur.fetchall()

                etapes_list = []
                for etape_row in etapes:
                    if is_postgres:
                        etapes_list.append(dict(etape_row))
                    else:
                        etapes_list.append(convert_etape_to_dict(etape_row))

                tache_dict['etapes'] = etapes_list

                # Calculer la progression basée sur les étapes terminées
                total_etapes = len(etapes_list)
                etapes_terminees = sum(1 for etape in etapes_list if etape.get('terminee', False))

                if total_etapes > 0:
                    tache_dict['progression'] = (etapes_terminees / total_etapes) * 100
                    tache_dict['etapes_terminees'] = etapes_terminees
                    tache_dict['total_etapes'] = total_etapes
                else:
                    tache_dict['progression'] = 0
                    tache_dict['etapes_terminees'] = 0
                    tache_dict['total_etapes'] = 0

                total_taches += 1
                if tache_dict.get('termine', False):
                    taches_terminees += 1

                taches_list.append(tache_dict)

            # Calculer le pourcentage de progression global
            progression_globale = 0
            if total_taches > 0:
                progression_globale = (taches_terminees / total_taches) * 100

        finally:
            cur.close()
            conn.close()

        return render_template('tab_content/taches.html', taches=taches_list, progression_globale=progression_globale, total_taches=total_taches, taches_terminees=taches_terminees)

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
            sql_total_objectifs = sql_placeholder('SELECT COUNT(*) FROM objectifs WHERE user_id = ? AND status = \'actif\'')
            cur.execute(sql_total_objectifs, (user_id,))
            total_objectifs = cur.fetchone()[0]

            sql_epargne_totale = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = \'actif\'')
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

            sql_epargne_actuelle = sql_placeholder('SELECT SUM(montant_actuel) FROM objectifs WHERE user_id = ? AND status = \'actif\'')
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

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Une erreur interne s'est produite. Veuillez réessayer."), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page non trouvée."), 404


if __name__ == '__main__':
    # Initialiser la base de données PostgreSQL si nécessaire
    if os.environ.get('DATABASE_URL'):
        init_database()
    elif not os.path.exists('epargne.db'):
        print("Base de données SQLite non trouvée, création...")
        conn = sqlite3.connect('epargne.db')
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, security_question TEXT, security_answer TEXT, nom TEXT, prenom TEXT, date_naissance TEXT, telephone TEXT, email TEXT, sexe TEXT, photo_profil TEXT, bio TEXT, adresse TEXT, ville TEXT, pays TEXT DEFAULT 'Cameroun', date_creation_profil TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS objectifs (id INTEGER PRIMARY KEY, nom TEXT NOT NULL, montant_cible REAL NOT NULL, montant_actuel REAL NOT NULL, date_limite TEXT, status TEXT NOT NULL DEFAULT 'actif', user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, objectif_id INTEGER NOT NULL, montant REAL NOT NULL, type_transaction TEXT NOT NULL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id INTEGER NOT NULL, FOREIGN KEY (objectif_id) REFERENCES objectifs (id), FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS taches (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, titre TEXT NOT NULL, description TEXT, date_limite TEXT, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP, termine BOOLEAN DEFAULT FALSE, ordre INTEGER DEFAULT 0, FOREIGN KEY (user_id) REFERENCES users (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS etapes (id INTEGER PRIMARY KEY, tache_id INTEGER NOT NULL, description TEXT NOT NULL, terminee BOOLEAN DEFAULT FALSE, ordre INTEGER DEFAULT 0, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (tache_id) REFERENCES taches (id))")
        cur.execute("CREATE TABLE IF NOT EXISTS evenements (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, titre TEXT NOT NULL, description TEXT, date_debut TEXT NOT NULL, heure_debut TEXT, date_fin TEXT, heure_fin TEXT, lieu TEXT, couleur TEXT DEFAULT '#fd7e14', rappel TEXT, termine BOOLEAN DEFAULT FALSE, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id))")
        conn.commit()
        conn.close()
        print("Base de données SQLite créée.")

    app.run(debug=True)