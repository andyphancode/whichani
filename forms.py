from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, Length

class SignUpForm(FlaskForm):
    """Form for user signup."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=8)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    profile_image_url = StringField('Profile Image URL (Optional)')

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=8)])

