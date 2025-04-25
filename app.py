from flask import Flask, request, redirect, render_template, send_from_directory, session, url_for
import os
import json
import re
from functools import wraps
from werkzeug.utils import secure_filename

# Initialisation de Flask
app = Flask(__name__)
app.secret_key = 'un_super_secret'  # À changer en production

# Dossier de stockage
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Fichier utilisateurs
USER_FILE = 'users.json'
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as f:
        json.dump({'admin': 'password'}, f)

def load_users():
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Décorateur : connexion requise
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Décorateur : admin requis
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Page d'accueil (accessible à tous les utilisateurs connectés)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@admin_required
def upload_file():
    if 'file' not in request.files:
        return 'Aucun fichier sélectionné'
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(request.referrer)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
@admin_required
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(request.referrer)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if users.get(username) == password:
            session['username'] = username
            session.modified = True  # Forcer la modification de la session
            return redirect(url_for('index'))
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect."
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        session.pop('username', None)
        session.modified = True
        error = "Accès révoqué. Veuillez vous reconnecter !"
        return render_template('login.html', error=error)

    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        users = load_users()

        # Vérifie si le nom commence par admin ou administrateur (peu importe la casse) suivi de chiffres
        if re.match(r'^(admin|administrateur)\d+$', username, re.IGNORECASE):
            error = "Ce nom d'utilisateur n'est pas autorisé."
        elif username in users:
            error = "Le nom d'utilisateur est déjà pris."
        elif password != confirm_password:
            error = "Les mots de passe ne correspondent pas."
        else:
            users[username] = password
            save_users(users)
            return redirect(url_for('login'))

    return render_template('signup.html', error=error)

@app.route('/documents')
@login_required
def documents():
    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    documents = [file for file in all_files if file.endswith(('.txt', '.pdf'))]
    return render_template('documents.html', documents=documents)

@app.route('/images')
@login_required
def images():
    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    images = [file for file in all_files if file.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('images.html', images=images)

@app.route('/videos')
@login_required
def videos():
    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    videos = [file for file in all_files if file.endswith(('.mp4', '.avi', '.mov'))]
    return render_template('videos.html', videos=videos)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    users = load_users()
    if users.get(session['username']) == current_password:
        users[session['username']] = new_password
        save_users(users)
        return redirect(url_for('settings'))
    else:
        return "Mot de passe actuel incorrect.", 403

@app.route('/change-theme', methods=['POST'])
@login_required
def change_theme():
    session['theme'] = request.form['theme']
    session.modified = True  # Assurer que la session est bien sauvegardée
    return redirect(url_for('settings'))

@app.route('/change-font', methods=['POST'])
@login_required
def change_font():
    session['font'] = request.form['font']
    session.modified = True  # Assurer que la session est bien sauvegardée
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.modified = True  # Assurer que la session est bien sauvegardée
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
