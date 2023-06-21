from flask import flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_uploads import UploadSet, IMAGES
from wtforms import StringField, SubmitField, BooleanField, PasswordField, FileField, HiddenField, RadioField, IntegerField, FloatField, SelectField, TextAreaField
from wtforms.validators import Optional, DataRequired, Length, EqualTo, URL, ValidationError, NumberRange
from NSSGolf.models import User, Tutorial, Image, Role

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            flash('That username is taken. Please choose a different one.', 'danger')
            raise ValidationError('That username is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

images = UploadSet('images', IMAGES)

class TutorialUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=120)])
    video_link = StringField('YouTube Link', validators=[DataRequired()])
    category = SelectField('Category', choices = [('Putting','Putting'), ('Chipping','Chipping'), ('Strategies','Strategies'), ('Wind','Wind'), ('Terrain','Terrain'), ('Mechanics','Mechanics'),('Other','Other')], validators=[DataRequired()])
    submit = SubmitField('Submit')

class ShotUploadForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired(), FileAllowed(images, 'Images only!')])
    youtube_link = StringField('YouTube Link')
    hole_number = IntegerField('Hole Number', validators=[DataRequired(), NumberRange(min=1, max=21, message='Hole number must be between 1 and 21.')])
    wind_speed = IntegerField('Wind Speed', validators=[DataRequired()])
    wind_direction = SelectField('Wind Direction', choices=[('North','North'),('South','South'),('East','East'),('West','West'),('North-East','North-East'),('North-West','North-West'),('South-East','South-East'),('South-West','South-West'),('Center','Center')], validators=[DataRequired()])
    flag_position = SelectField('Flag Position', choices=[('North','North'),('South','South'),('East','East'),('West','West'),('North-East','North-East'),('North-West','North-West'),('South-East','South-East'),('South-West','South-West'),('Center','Center')], validators=[DataRequired()])
    shot_distance = FloatField('Shot Distance', validators=[DataRequired()])
    wind_speed_units = SelectField('Wind Speed Unit', choices=[('MPH','MPH'),('KM/H','KM/H'),('m/s', 'm/s')], validators=[DataRequired()])
    distance_units = SelectField('Distance Unit', choices=[('yd','Yards'),('ft', 'Feet'),('m','Meters')], validators=[DataRequired()])
    submit = SubmitField('Submit')

class TutorialSearchForm(FlaskForm):
    category = SelectField('Category', choices = [('Putting','Putting'), ('Chipping','Chipping'), ('Strategies','Strategies'), ('Wind','Wind'), ('Terrain','Terrain'), ('Mechanics','Mechanics'),('Other','Other')], validators=[DataRequired()])
    submit = SubmitField('Search')

class ShotSearchForm(FlaskForm):
    hole_number = IntegerField('Hole Number', validators=[DataRequired(), NumberRange(min=1, max=21)])
    wind_speed = IntegerField('Wind Speed', validators=[Optional(), NumberRange(min=1, max=54)])
    wind_direction = SelectField('Wind Direction', choices=[('','Select...'),('North','North'),('South','South'),('East','East'),('West','West'),('North-East','North-East'),('North-West','North-West'),('South-East','South-East'),('South-West','South-West'),('Center','Center')], validators=[Optional()])
    flag_position = SelectField('Flag Position', choices=[('','Select...'),('North','North'),('South','South'),('East','East'),('West','West'),('North-East','North-East'),('North-West','North-West'),('South-East','South-East'),('South-West','South-West'),('Center','Center')], validators=[Optional()])
    shot_distance = FloatField('Shot Distance', validators=[Optional()])
    wind_speed_units = SelectField('Wind Unit', choices=[('','Select...'),('MPH','MPH'),('KM/H','KM/H'),('m/s', 'm/s')], validators=[Optional()])
    distance_units = SelectField('Distance Unit', choices=[('','Select...'),('yd','Yards'),('ft', 'Feet'),('m','Meters')], validators=[Optional()])
    submit = SubmitField('Search')

class AdminForm(FlaskForm):
    image_id = HiddenField('Image ID')
    tutorial_id = HiddenField('Tutorial ID')
    action = SelectField('Action', choices=[('Approve', 'Approve'), ('Reject', 'Reject')], validators=[DataRequired()])
    rejection_reason = TextAreaField('Rejection Reason', render_kw={'placeholder': 'Add a reason for rejection here.'})
    submit = SubmitField('Submit')
