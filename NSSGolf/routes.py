from datetime import datetime
import os
from flask import render_template, redirect, url_for, flash, request, send_from_directory, abort, Markup
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from NSSGolf import app, db
from NSSGolf.forms import LoginForm, ShotUploadForm, TutorialUploadForm, ShotSearchForm, TutorialSearchForm, RegistrationForm, AdminForm
from NSSGolf.models import Image, User, Tutorial, Notification

@app.route('/')
def gallery():
    images = Image.query.filter_by(approved=True).all()
    if current_user.is_authenticated:
        notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
        for notification in notifications:
            notification.read = True
        db.session.commit()
        return render_template('gallery.html', images=images, notifications=notifications, user=current_user)
    return render_template('gallery.html', images=images, user=current_user)

@app.route('/tutorials')
def tutorials():
    tutorials = Tutorial.query.filter_by(approved=True).all()
    return render_template('tutorials.html', tutorials=tutorials, user=current_user)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'danger')
        return redirect(url_for('gallery'))
    form = RegistrationForm()
    if form.validate_on_submit():
        User.create_user(form.username.data, form.password.data)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'danger')
        return redirect(url_for('gallery'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('gallery'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form_shot = ShotUploadForm()
    form_tutorial = TutorialUploadForm()
    active_form = request.args.get('form')

    if active_form == 'shot' and form_shot.validate_on_submit():
        if form_shot.wind_speed_units.data == 'MPH' and not 2 <= form_shot.wind_speed.data <= 33:
            flash('Invalid wind speed, must be between 2 and 33 MPH.', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)
        elif form_shot.wind_speed_units.data == 'KM/H' and not 3 <= form_shot.wind_speed.data <= 55:
            flash('Invalid wind speed, must be between 3 and 55 KM/H.', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)
        elif form_shot.wind_speed_units.data == 'm/s' and not 1 <= form_shot.wind_speed.data <= 15:
            flash('Invalid wind speed, must be between 1 and 15 m/s', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)

        if form_shot.shot_distance.data <= 0:
            flash('Invalid shot distance, must be greater than 0.', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)

        image = form_shot.image.data
        filename = secure_filename(image.filename)
        filename, extension = os.path.splitext(filename)  # Split the filename and extension
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{filename}_{timestamp}{extension}" # Add timestamp to filename to make it unique
        filepath = f"{app.config['UPLOAD_FOLDER']}/{unique_filename}"
        image.save(filepath)
        #Markup makes the <br> work in the HTML
        image_title = Markup(f'-Hole {form_shot.hole_number.data}<br>-{form_shot.wind_speed.data}{form_shot.wind_speed_units.data.upper()} Wind Going {form_shot.wind_direction.data}<br>-{form_shot.flag_position.data} Side Flag Position<br>-Shot from {form_shot.shot_distance.data}{form_shot.distance_units.data} Away')
        new_image = Image(title=image_title, img_file=unique_filename, youtube_link=form_shot.youtube_link.data, 
                        hole_number=form_shot.hole_number.data, wind_speed=form_shot.wind_speed.data, wind_speed_units=form_shot.wind_speed_units.data, 
                        wind_direction=form_shot.wind_direction.data, flag_position=form_shot.flag_position.data,
                        shot_distance=form_shot.shot_distance.data, distance_units=form_shot.distance_units.data, 
                        user_id=current_user.id)
        db.session.add(new_image)
        db.session.commit()

        flash('Image uploaded and is pending approval.')
        return redirect(url_for('gallery'))
    
    elif active_form == 'tutorial' and form_tutorial.validate_on_submit():
        new_tutorial = Tutorial(title=form_tutorial.title.data, video_link=form_tutorial.video_link.data, category=form_tutorial.category.data, user_id=current_user.id)
        db.session.add(new_tutorial)
        db.session.commit()

        flash('Tutorial uploaded and is pending approval.')
        return redirect(url_for('gallery'))
    
    return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)


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
    return redirect(url_for('gallery'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.role_id == 2:
        flash('You are not an admin.', 'danger')
        return redirect(url_for('gallery'))
    form = AdminForm()
    if form.validate_on_submit():
        image = None
        tutorial = None
        image_id = form.image_id.data
        tutorial_id = form.tutorial_id.data
        if image_id:
            image = Image.query.get(image_id)
            action = form.action.data
            if action == 'Approve':
                image.approved = True
            elif action == 'Reject':
                # Check that a rejection reason was provided
                if not form.rejection_reason.data:
                    flash('Please provide a reason for rejection.', 'danger')
                    return redirect(url_for('admin'))
                notification = Notification(message=form.rejection_reason.data, user_id=image.user_id)
                db.session.add(notification)
                db.session.delete(image)
        elif tutorial_id:
            tutorial = Tutorial.query.get(tutorial_id)
            action = form.action.data
            if action == 'Approve':
                tutorial.approved = True
            elif action == 'Reject':
                # Check that a rejection reason was provided
                if not form.rejection_reason.data:
                    flash('Please provide a reason for rejection.', 'danger')
                    return redirect(url_for('admin'))
                notification = Notification(message=form.rejection_reason.data, user_id=tutorial.user_id)
                db.session.add(notification)
                db.session.delete(tutorial)
        db.session.commit()
        flash('Action successful.', 'success')
        return redirect(url_for('admin'))
    # Only images waiting for approval
    images = Image.query.filter_by(approved=False).all()
    tutorials = Tutorial.query.filter_by(approved=False).all()
    return render_template('admin.html', title='Admin', form=form, images=images, tutorials=tutorials)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form_shot = ShotSearchForm()
    form_tutorial = TutorialSearchForm()
    active_form = request.args.get('form')
    if active_form == 'shot' and form_shot.validate_on_submit():
        if form_shot.wind_speed_units.data == 'MPH' and not 2 <= form_shot.wind_speed.data <= 33:
            flash('Invalid wind speed, must be between 2 and 33 MPH.', 'error')
            return render_template('upload.html', form_shot=form_shot)
        elif form_shot.wind_speed_units.data == 'KM/H' and not 3 <= form_shot.wind_speed.data <= 55:
            flash('Invalid wind speed, must be between 3 and 55 KM/H.', 'error')
            return render_template('upload.html', form_shot=form_shot)
        elif form_shot.wind_speed_units.data == 'm/s' and not 1 <= form_shot.wind_speed.data <= 15:
            flash('Invalid wind speed, must be between 1 and 15 m/s', 'error')
            return render_template('upload.html', form_shot=form_shot)

        if form_shot.shot_distance.data <= 0:
            flash('Invalid shot distance, must be greater than 0.', 'error')
            return render_template('upload.html', form_shot=form_shot)
        # Extract data from form
        hole_number = form_shot.hole_number.data
        wind_speed = form_shot.wind_speed.data
        shot_distance = form_shot.shot_distance.data
        flag_position = form_shot.flag_position.data

        # Search for images matching the criteria
        images = Image.query.filter_by(hole_number=hole_number, 
                                        wind_speed=wind_speed, 
                                        shot_distance=shot_distance, 
                                        flag_position=flag_position, 
                                        approved=True).all()  # Only approved images
        if (len(images) == 0):
            flash('No images found matching the criteria.', 'danger')
        return render_template('search.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form, images=images)
    elif active_form == 'tutorial' and form_tutorial.validate_on_submit():
        # Extract data from form
        category = form_tutorial.category.data

        # Search for tutorials matching the criteria
        tutorials = Tutorial.query.filter_by(category=category, approved=True).all()
        if (len(tutorials) == 0):
            flash('No tutorials found matching the criteria.', 'danger')
        return render_template('search.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form, tutorials=tutorials)
    return render_template('search.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('gallery'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
