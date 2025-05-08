from datetime import datetime, timedelta, timezone
import shutil
from flask import Flask, jsonify, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import re
import pytz

app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# Load configuration
if 'WEBSITE_HOSTNAME' not in os.environ:
    app.config.from_object('azureproject.development')
else:
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Image

@app.route('/')
def index():
    # Redirect to the gallery page or render a placeholder page
    return render_template('index.html')

@app.route('/upload-log', methods=['GET'])
def upload_log():
    # Query all images to simulate an upload log
    logs = Image.query.order_by(Image.reception_date.desc()).all()
    return render_template('upload_log.html', logs=logs)

@app.route('/add', methods=['POST'])
@csrf.exempt
def upload_image():
    try:
        file_name       = request.form.get('file_name')
        user_name       = request.form.get('username')
        suffix          = request.form.get('suffix')
        red_pixels      = int(request.form.get('red_pixels'))
        green_pixels    = int(request.form.get('green_pixels'))
        blue_pixels     = int(request.form.get('blue_pixels'))
        original_file   = request.files.get('original_image')
        processed_file  = request.files.get('processed_image')

        # creamos la entrada sin URL ni fecha todavia
        new_entry = Image(
            file_name           = f"{file_name} ({suffix})",
            user_name           = user_name,
            red_pixels          = red_pixels,
            green_pixels        = green_pixels,
            blue_pixels         = blue_pixels,
            original_image_url  = "", # placeholder
            processed_image_url = "", # placeholder
            # Spanish timezone (Madrid) - handles DST automatically
            reception_date = datetime.now(pytz.timezone('Europe/Madrid'))
        )
        db.session.add(new_entry)
        db.session.flush()   # fuerza INSERT para obtener new_entry.id

        # construimos nombres con el ID y el suffix
        orig_filename = secure_filename(f"{new_entry.id}_orig_{file_name}.bmp")
        proc_filename = secure_filename(f"{new_entry.id}_{suffix}_{file_name}.bmp")

        orig_path = os.path.join(app.static_folder, 'uploads', orig_filename)
        proc_path = os.path.join(app.static_folder, 'uploads', proc_filename)
        os.makedirs(os.path.dirname(orig_path), exist_ok=True)

        # guardamos archivos en disco
        original_file.save(orig_path)
        processed_file.save(proc_path)

        # actualizamos las URLs usando url_for
        new_entry.original_image_url  = url_for('static', filename=f'uploads/{orig_filename}')
        new_entry.processed_image_url = url_for('static', filename=f'uploads/{proc_filename}')

        db.session.commit()

        return f"Entry {new_entry.id} added.", 201

    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}", 500
    

@app.route('/clear_uploads', methods=['GET'])
@csrf.exempt
def clear_uploads():
    try:
        # Ruta al directorio de uploads
        uploads_dir = os.path.join(app.static_folder, 'uploads')

        # Borrar todo el directorio y recrearlo vacío
        if os.path.exists(uploads_dir):
            shutil.rmtree(uploads_dir)
        os.makedirs(uploads_dir, exist_ok=True)

        # Eliminar todas las filas de la tabla Image
        deleted = Image.query.delete()
        db.session.commit()

        return jsonify({
            'status': 'ok',
            'deleted_entries': deleted,
            'uploads_folder_cleared': True
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500