from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, StringField, TextAreaField
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
    old_password = PasswordField('Current Password (Required)')
    new_password = PasswordField('New Password', validators=[Length(min=8)])
    new_password_confirm = PasswordField('Confirm New Password', validators=[Length(min=8)])

class ResetRequestForm(FlaskForm):
    "Request reset form."

    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    "Reset password form."
    new_password = PasswordField('New Password', validators=[Length(min=8)])
    new_password_confirm = PasswordField('Confirm New Password', validators=[Length(min=8)])

class EditListForm(FlaskForm):
    "Edit list form."
    list_title = StringField('List Title', validators=[Length(max=60)])
    list_description = TextAreaField('List Description', validators=[Length(max=280)])
    
class EditListingForm(FlaskForm):
    "Edit listing form."
    listing_description = TextAreaField('Listing Description', validators=[Length(max=1200)])
    
