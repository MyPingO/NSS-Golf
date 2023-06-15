from flask import render_template, redirect, url_for, flash, request, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from NSSGolf import app, db
from NSSGolf.forms import LoginForm, UploadForm, SearchForm, RegistrationForm, AdminForm
from NSSGolf.models import Image, User

@app.route('/')
def home():
    images = Image.query.filter_by(approved=True).all()
    return render_template('index.html', images=images)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        User.create_user(form.username.data, form.password.data)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = secure_filename(image.filename)
        filepath = f"{app.config['UPLOAD_FOLDER']}/{filename}"
        image.save(filepath)
        image_title = f'Hole {form.hole_number.data} | {form.wind_speed.data}MPH Going {form.wind_direction.data} | {form.flag_position.data} Side Flag Position | {form.yard_distance.data}yd/{form.yard_distance.data * 3}ft Away'
        new_image = Image(title=image_title, img_file=filename, youtube_link=form.youtube_link.data, 
                          hole_number=form.hole_number.data, wind_speed=form.wind_speed.data, 
                          wind_direction=form.wind_direction.data, flag_position=form.flag_position.data,
                          yard_distance=form.yard_distance.data)
        db.session.add(new_image)
        db.session.commit()

        flash('Image uploaded and is pending approval.')
        return redirect(url_for('home'))
    return render_template('upload.html', form=form)


@app.route('/delete_image/<int:id>', methods=['POST'])
@login_required
def delete_image(id):
    if current_user.role_id != 2:
        abort(403)  # Forbidden

    image = Image.query.get(id)
    if image:
        db.session.delete(image)
        db.session.commit()
        flash('The image has been deleted successfully.', 'success')
    else:
        flash('Image not found.', 'error')
    return redirect(url_for('home'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.role_id == 2:
        flash('You are not an admin.', 'danger')
        return redirect(url_for('home'))
    form = AdminForm()
    if form.validate_on_submit():
        image_id = form.image_id.data
        action = form.action.data
        image = Image.query.get(image_id)
        if action == 'Approve':
            image.approved = True
        elif action == 'Reject':
            db.session.delete(image)
        db.session.commit()
        flash('Action successful.', 'success')
        return redirect(url_for('admin'))
    # Only images waiting for approval
    images = Image.query.filter_by(approved=False).all()
    return render_template('admin.html', title='Admin', form=form, images=images)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        # Extract data from form
        hole_number = form.hole_number.data
        wind_speed = form.wind_speed.data
        yard_distance = form.yard_distance.data
        flag_position = form.flag_position.data

        # Search for images matching the criteria
        images = Image.query.filter_by(hole_number=hole_number, 
                                        wind_speed=wind_speed, 
                                        yard_distance=yard_distance, 
                                        flag_position=flag_position, 
                                        approved=True).all()  # Only approved images
        if (len(images) == 0):
            flash('No images found matching the criteria.', 'danger')
        return render_template('search.html', title='Search', form=form, images=images)
    return render_template('search.html', title='Search', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
