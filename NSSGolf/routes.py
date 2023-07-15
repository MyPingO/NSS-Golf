from datetime import datetime
import os
from flask import render_template, jsonify, redirect, Response, url_for, flash, request, send_from_directory, abort, Markup
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from NSSGolf import app, db
from NSSGolf.forms import LoginForm, EditImageForm, ShotUploadForm, TutorialUploadForm, ShotSearchForm, TutorialSearchForm, RegistrationForm, AdminForm
from NSSGolf.models import Role, Image, User, Tutorial, Notification, ImageLike, TutorialLike

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

@app.route('/')
def home():
    return redirect(url_for('gallery', page=1))

@app.route('/gallery/<int:page>')
def gallery(page=1):
    per_page = 9
    images = Image.query.filter_by(approved=True).paginate(page, per_page, error_out=False)
    if images.pages < page:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            flash('No more images', 'error')
            return redirect(url_for('gallery', page=1))
        return "No more images", 404
    if current_user.is_authenticated:
        #dictionary comprehension to get all the liked images for the current user
        user_likes = {image.id: image.is_liked_by(current_user) for image in images.items}
        notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
        for notification in notifications:
            db.session.delete(notification)
        db.session.commit()
        return render_template('gallery.html', images=images.items, notifications=notifications, user_likes=user_likes, user=current_user)
    return render_template('gallery.html', images=images.items, user=current_user)

@app.route('/like_image/<int:image_id>', methods=['POST'])
@login_required
def like_image(image_id):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        flash("Can't go there!", 'error')
        return redirect(url_for('gallery', page=1))

    image = Image.query.get(image_id)
    if not image:
        flash('Image not found.', 'error')
        return redirect(url_for('gallery', page=1))

    # Check if user has already liked the image
    like = ImageLike.query.filter_by(user_id=current_user.id, image_id=image_id).first()
    if like:
        # If a Like record exists, unlike the image
        with db.session.no_autoflush:
            # Decrement the like count atomically to prevent race conditions
            db.session.query(Image).filter_by(id=image_id).update({Image.like_count: Image.like_count - 1})
            db.session.delete(like)
            db.session.commit()
        return jsonify(like_count=image.like_count), 200
    else:
        # If no Like record exists, like the image
        new_like = ImageLike(user_id=current_user.id, image_id=image_id)
        db.session.add(new_like)
        with db.session.no_autoflush:
            # Increment the like count atomically to prevent race conditions
            db.session.query(Image).filter_by(id=image_id).update({Image.like_count: Image.like_count + 1})
            db.session.commit()
        return jsonify(like_count=image.like_count), 201

@app.route('/tutorials')
def tutorials():
    tutorials = Tutorial.query.filter_by(approved=True).all()
    if current_user.is_authenticated:
        #dictionary comprehension to get all the liked images for the current user
        user_likes = {tutorial.id: tutorial.is_liked_by(current_user) for tutorial in tutorials}
        return render_template('tutorials.html', tutorials=tutorials, user_likes=user_likes, user=current_user)
    return render_template('tutorials.html', tutorials=tutorials, user=current_user)

@app.route('/like_tutorial/<int:tutorial_id>', methods=['POST'])
@login_required
def like_tutorial(tutorial_id):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        flash("Can't go there!", 'error')
        return redirect(url_for('tutorials'))

    tutorial = Tutorial.query.get(tutorial_id)
    if not tutorial:
        flash('Tutorial not found.', 'error')
        return redirect(url_for('tutorials'))
    
    # Check if user has already liked the tutorial
    like = TutorialLike.query.filter_by(user_id=current_user.id, tutorial_id=tutorial_id).first()
    if like:
        with db.session.no_autoflush:
            # Decrement the like count atomically to prevent race conditions
            db.session.query(Tutorial).filter_by(id=tutorial_id).update({Tutorial.like_count: Tutorial.like_count - 1})
            db.session.delete(like)
            db.session.commit()
        tutorial = Tutorial.query.get(tutorial_id)
        return jsonify(like_count=tutorial.like_count), 200 # 200 = OK

    else:
        # If no Like record exists, like the tutorial
        new_like = TutorialLike(user_id=current_user.id, tutorial_id=tutorial_id)
        db.session.add(new_like)
        with db.session.no_autoflush:
            # Increment the like count atomically to prevent race conditions
            db.session.query(Tutorial).filter_by(id=tutorial_id).update({Tutorial.like_count: Tutorial.like_count + 1})
            db.session.commit()
        tutorial = Tutorial.query.get(tutorial_id)
        return jsonify(like_count=tutorial.like_count), 201 # 201 = Created

@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'danger')
        return redirect(url_for('gallery', page=1))
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
        return redirect(url_for('gallery', page=1))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            return redirect(url_for('gallery', page=1))
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
        if form_shot.wind_speed_units.data == 'MPH' and not 0 <= form_shot.wind_speed.data <= 33:
            flash('Invalid wind speed, must be between 0 and 33 MPH.', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)
        elif form_shot.wind_speed_units.data == 'KM/H' and not 0 <= form_shot.wind_speed.data <= 54:
            flash('Invalid wind speed, must be between 0 and 54 KM/H.', 'error')
            return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)
        elif form_shot.wind_speed_units.data == 'm/s' and not 0 <= form_shot.wind_speed.data <= 15:
            flash('Invalid wind speed, must be between 0 and 15 m/s', 'error')
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
        hole_text = f'Hole {form_shot.hole_number.data}'
        wind_text = f'{form_shot.wind_speed.data}{form_shot.wind_speed_units.data.upper()} Wind Going {form_shot.wind_direction.data}' if form_shot.wind_speed.data > 0 else 'No Wind'
        flag_text = f'{form_shot.flag_position.data} Side Flag Position'
        distance_text = f'Shot from {form_shot.shot_distance.data}{form_shot.distance_units.data} Away'

        #Markup makes the <br> work in the HTML
        image_title = Markup(f'-{hole_text}<br>-{wind_text}<br>-{flag_text}<br>-{distance_text}')
        new_image = Image(title=image_title, img_file=unique_filename, youtube_link=form_shot.youtube_link.data, 
                        hole_number=form_shot.hole_number.data, wind_speed=form_shot.wind_speed.data, wind_speed_units=form_shot.wind_speed_units.data, 
                        wind_direction=form_shot.wind_direction.data, flag_position=form_shot.flag_position.data,
                        shot_distance=form_shot.shot_distance.data, distance_units=form_shot.distance_units.data, 
                        user_id=current_user.id)
        db.session.add(new_image)
        db.session.commit()

        flash('Image uploaded and is pending approval.')
        return redirect(url_for('gallery', page=1))
    
    elif active_form == 'tutorial' and form_tutorial.validate_on_submit():
        new_tutorial = Tutorial(title=form_tutorial.title.data, video_link=form_tutorial.video_link.data, category=form_tutorial.category.data, user_id=current_user.id)
        db.session.add(new_tutorial)
        db.session.commit()

        flash('Tutorial uploaded and is pending approval.')
        return redirect(url_for('gallery', page=1))
    
    
    return render_template('upload.html', form_shot=form_shot, form_tutorial=form_tutorial, active_form=active_form)


#not using this for now except for in the actual build
def send_email():
    from_address = "nssgolfshots@gmail.com"
    to_address = "nssgolfshots@gmail.com"
    password = "Password"  # Use application-specific password if 2FA is enabled

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = "New Submission to nssgolfshots.com"

    body = f"{current_user.username} submitted something to nssgolfshots.com."
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_address, password)
    text = msg.as_string()
    server.sendmail(from_address, to_address, text)
    server.quit()

@app.route('/delete_image_submission/<int:image_id>', methods=['POST'])
@login_required
def delete_image_submission(image_id, from_admin_route=False):
    image = Image.query.get_or_404(image_id)
    
    # Delete the image file from the server
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.img_file))
    except Exception as e:
        flash('Error: {}'.format(e), 'error')
    
    # Delete all likes related to this image
    likes = ImageLike.query.filter_by(image_id=image.id).all()
    for like in likes:
        db.session.delete(like)
    
    # Then delete the image from the database
    db.session.delete(image)
    db.session.commit()

    if from_admin_route:
        return "success"
    else:
        return redirect(url_for('gallery', page=1))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form_shot = ShotSearchForm()
    form_tutorial = TutorialSearchForm()
    active_form = request.args.get('form')
    if active_form == 'shot' and form_shot.validate_on_submit():

        # Start query
        query = Image.query
        print(form_shot.wind_speed.data)

        # Add filters based on form data
        if form_shot.hole_number.data:
            query = query.filter(Image.hole_number == form_shot.hole_number.data)
        if form_shot.wind_speed.data or form_shot.wind_speed.data == 0:
            query = query.filter(Image.wind_speed == form_shot.wind_speed.data)
        if form_shot.wind_direction.data:
            query = query.filter(Image.wind_direction == form_shot.wind_direction.data)
        if form_shot.flag_position.data:
            query = query.filter(Image.flag_position == form_shot.flag_position.data)
        if form_shot.shot_distance.data:
            query = query.filter(Image.shot_distance == form_shot.shot_distance.data)
        if form_shot.wind_speed_units.data:
            query = query.filter(Image.wind_speed_units == form_shot.wind_speed_units.data)
        if form_shot.distance_units.data:
            query = query.filter(Image.distance_units == form_shot.distance_units.data)

        # Filter by approved status and execute query
        images = query.filter_by(approved=True).all()

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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.role_id == 2:
        flash('You are not an admin.', 'danger')
        return redirect(url_for('gallery', page=1))
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
                db.session.commit()
            elif action == 'Reject':
                # Check that a rejection reason was provided
                if not form.rejection_reason.data:
                    flash('Please provide a reason for rejection.', 'danger')
                    return redirect(url_for('admin'))
                notification = Notification(message=form.rejection_reason.data, user_id=image.user_id)
                db.session.add(notification)
                db.session.commit()
                delete_image_submission(image_id, from_admin_route=True)
        elif tutorial_id:
            tutorial = Tutorial.query.get(tutorial_id)
            action = form.action.data
            if action == 'Approve':
                tutorial.approved = True
                db.session.commit()
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


@app.route('/edit_image/<int:image_id>', methods=['GET', 'POST'])
@login_required
def edit_image(image_id):
    if not current_user.role_id == 2:
        flash('You are not an admin.', 'danger')
        return redirect(url_for('gallery', page=1))

    image = Image.query.get_or_404(image_id)
    form = EditImageForm(obj=image)

    if form.validate_on_submit():
        if form.image.data:
            # Delete the old file from the server
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.img_file))
            except Exception as e:
                flash('Error: {}'.format(e), 'error')           
            # If a new file has been uploaded, save it and update the image record
            filename = secure_filename(form.image.data.filename)
            filename, extension = os.path.splitext(filename)  # Split the filename and extension
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{filename}_{timestamp}{extension}"
            filepath = f"{app.config['UPLOAD_FOLDER']}/{unique_filename}"
            form.image.data.save(filepath)
            image.img_file = unique_filename
        form.populate_obj(image)  # Update the image object with the form data

        # Update the image title
        hole_text = f'Hole {form.hole_number.data}'
        wind_text = f'{form.wind_speed.data}{form.wind_speed_units.data.upper()} Wind Going {form.wind_direction.data}' if form.wind_speed.data > 0 else 'No Wind'
        flag_text = f'{form.flag_position.data} Side Flag Position'
        distance_text = f'Shot from {form.shot_distance.data}{form.distance_units.data} Away'

        #Markup makes the <br> work in the HTML
        new_title = Markup(f'-{hole_text}<br>-{wind_text}<br>-{flag_text}<br>-{distance_text}')
        image.title = new_title
        db.session.commit()
        flash('Image updated successfully.', 'success')
        from_admin_route = request.args.get('from_admin_route', default=False, type=bool)
        if from_admin_route:
            flash('Edit successful.', 'success')
            return redirect(url_for('admin'))
        return redirect(url_for('gallery', page=1))

    return render_template('edit_image.html', form=form, image=image)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('gallery', page=1))

@app.route('/uploads/<filename>')
def get_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
