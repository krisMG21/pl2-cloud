from flask import Flask, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import re

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
    return render_template('index.html', restaurants=[])

@app.route('/upload-log', methods=['GET'])
def upload_log():
    # Query all images to simulate an upload log
    logs = Image.query.order_by(Image.reception_date.desc()).all()
    return render_template('upload_log.html', logs=logs)

@app.route('/add', methods=['POST'])
@csrf.exempt
def upload_image():
    try:
        file_name = request.form.get('file_name')
        red_pixels = request.form.get('red_pixels')
        green_pixels = request.form.get('green_pixels')
        blue_pixels = request.form.get('blue_pixels')
        original_file = request.files.get('original_image')
        processed_file = request.files.get('processed_image')

        if not file_name or not red_pixels or not green_pixels or not blue_pixels or not original_file or not processed_file:
            return "Missing required fields.", 400

        try:
            red_pixels = int(red_pixels)
            green_pixels = int(green_pixels)
            blue_pixels = int(blue_pixels)
        except ValueError:
            return "Pixel values must be integers.", 400

        orig_filename = secure_filename(original_file.filename)
        proc_filename = secure_filename(processed_file.filename)
        orig_path = os.path.join(app.static_folder, 'uploads', orig_filename)
        proc_path = os.path.join(app.static_folder, 'uploads', proc_filename)
        os.makedirs(os.path.dirname(orig_path), exist_ok=True)
        original_file.save(orig_path)
        processed_file.save(proc_path)

        original_image_url = url_for('static', filename=f'uploads/{orig_filename}')
        processed_image_url = url_for('static', filename=f'uploads/{proc_filename}')

        new_entry = Image(
            file_name=file_name,
            red_pixels=red_pixels,
            green_pixels=green_pixels,
            blue_pixels=blue_pixels,
            original_image_url=original_image_url,
            processed_image_url=processed_image_url
        )
        db.session.add(new_entry)
        db.session.commit()

        return f"Entry added successfully for {file_name}.", 201
    except Exception as e:
        return f"Error uploading image: {str(e)}", 500

# @app.route('/gallery', methods=['GET'])
# def gallery():
#     images = Image.query.all()
#     return render_template('gallery.html', images=images)