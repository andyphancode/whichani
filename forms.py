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

class EditUserForm(FlaskForm):
    """Edit user form."""

    email = StringField('E-mail', validators=[Email()])
    profile_image_url = StringField('Profile Image URL')
    old_password = PasswordField('Old Password')
    new_password = PasswordField('New Password', validators=[Length(min=8)])
    new_password_confirm = PasswordField('Confirm New Password', validators=[Length(min=8)])
    
