from flask import flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_uploads import UploadSet, IMAGES
from wtforms import StringField, SubmitField, BooleanField, PasswordField, FileField, HiddenField, RadioField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, URL, ValidationError, NumberRange
from NSSGolf.models import User

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

class UploadForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired(), FileAllowed(images, 'Images only!')])
    youtube_link = StringField('YouTube Link')
    hole_number = IntegerField('Hole Number', validators=[DataRequired(), NumberRange(min=1, max=18)])
    wind_speed = IntegerField('Wind Speed', validators=[DataRequired(), NumberRange(min=2, max=33)])
    wind_direction = SelectField('Wind Direction', choices=[('N','N'),('S','S'),('E','E'),('W','W'),('NE','NE'),('SE','SE'),('SW','SW'),('NW','NW'),('Center','Center')], validators=[DataRequired()])
    flag_position = SelectField('Flag Position', choices=[('N','N'),('S','S'),('E','E'),('W','W'),('NE','NE'),('SE','SE'),('SW','SW'),('NW','NW'),('Center','Center')], validators=[DataRequired()])
    yard_distance = IntegerField('Yard Distance', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    hole_number = IntegerField('Hole Number', validators=[DataRequired(), NumberRange(min=1, max=18)])
    wind_speed = IntegerField('Wind Speed', validators=[DataRequired(), NumberRange(min=2, max=33)])
    wind_direction = SelectField('Wind Direction', choices=[('N','N'),('S','S'),('E','E'),('W','W'),('NE','NE'),('SE','SE'),('SW','SW'),('NW','NW'),('Center','Center')], validators=[DataRequired()])
    flag_position = SelectField('Flag Position', choices=[('N','N'),('S','S'),('E','E'),('W','W'),('NE','NE'),('SE','SE'),('SW','SW'),('NW','NW'),('Center','Center')], validators=[DataRequired()])
    yard_distance = IntegerField('Yard Distance', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Search')

class AdminForm(FlaskForm):
    image_id = HiddenField('Image ID')
    action = SelectField('Action', choices=[('Approve', 'Approve'), ('Reject', 'Reject')], validators=[DataRequired()])
    submit = SubmitField('Submit')
