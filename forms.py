from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, HiddenField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo, ValidationError
from wtforms.widgets import TextArea
from models import Tag, User

class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username', validators=[
        DataRequired(message='Email or username is required')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    first_name = StringField('First Name', validators=[
        Optional(),
        Length(max=50, message='First name cannot exceed 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        Optional(),
        Length(max=50, message='Last name cannot exceed 50 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=10, max=200, message='Title must be between 10 and 200 characters')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required'),
        Length(min=20, message='Content must be at least 20 characters')
    ])
    tags = StringField('Tags', validators=[Optional()], 
                      render_kw={'placeholder': 'Enter tags separated by commas'})

class AnswerForm(FlaskForm):
    content = TextAreaField('Your Answer', validators=[
        DataRequired(message='Answer content is required'),
        Length(min=10, message='Answer must be at least 10 characters')
    ])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    tag = StringField('Tag', validators=[Optional()])

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
