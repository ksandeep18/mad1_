from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, IntegerField, DateField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError, Optional
from datetime import date
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    qualification = StringField('Qualification', validators=[Length(max=100)])
    dob = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_dob(self, dob):
        if dob.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

class ChapterForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    name = StringField('Chapter Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

class QuizForm(FlaskForm):
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    date = DateField('Quiz Date', validators=[DataRequired()], format='%Y-%m-%d')
    duration = IntegerField('Duration (minutes)', validators=[DataRequired()])
    submit = SubmitField('Submit')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()])
    option_a = StringField('Option A', validators=[DataRequired()])
    option_b = StringField('Option B', validators=[DataRequired()])
    option_c = StringField('Option C', validators=[DataRequired()])
    option_d = StringField('Option D', validators=[DataRequired()])
    correct_answer = RadioField('Correct Answer', 
                               choices=[(0, 'Option A'), (1, 'Option B'), (2, 'Option C'), (3, 'Option D')],
                               coerce=int,
                               validators=[DataRequired()])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
