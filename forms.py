from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea
from models import Tag

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
