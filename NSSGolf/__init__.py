from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os

database_name = 'NSSGolfPSL.db'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'NSSGOLFSECRETKEY'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_name}'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

images = UploadSet('images', IMAGES)
app.config['UPLOADED_IMAGES_DEST'] = app.config['UPLOAD_FOLDER']
configure_uploads(app, images)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# create the extension
db = SQLAlchemy()

# initialize the app with the extension
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

from NSSGolf.models import User, Role, Image

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

with app.app_context():
    db.create_all()
    if not Role.query.filter_by(name='user').first():
        user_role = Role(id=1, name='user')
        db.session.add(user_role)
    if not Role.query.filter_by(name='admin').first():
        admin_role = Role(id=2, name='admin')
        db.session.add(admin_role)
    db.session.commit()
    print('Created Database!')

from NSSGolf import routes
