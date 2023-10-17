from flask import Flask, render_template, redirect, flash, session,  g, Blueprint
from models import db, User
from forms import SignUpForm, LoginForm, ResetRequestForm, ResetPasswordForm
from sqlalchemy.exc import IntegrityError
# from secret import WhichAniServicePW, WhichAniEmail
from flask_mail import Message, Mail
from flask import url_for
import os

CURR_USER_KEY = "curr_user"

auth = Blueprint('auth', __name__, template_folder='routes')

app = Flask(__name__) 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# for production, replace with secret variables
app.config['MAIL_USERNAME'] = os.environ.get('WhichAniEmail')
app.config['MAIL_PASSWORD'] = os.environ.get('WhichAniServicePW')

mail = Mail(app)
mail.init_app(app)

######################################################
# User signup/login/logout function helpers
######################################################

@auth.before_request
def add_user_to_g():
    """If logged in, add user to g."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.user_id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


######################################################
# User signup/login/logout view functions
######################################################

@auth.route('/signup/', methods=["GET", "POST"])
def signup():
    "Sign a user up."

    form = SignUpForm()

    # if already logged in
    if g.user:
        return redirect(url_for('home'))

    if form.validate_on_submit():
        try:
            user = User.signup(
                username = form.username.data,
                password = form.password.data,
                email = form.email.data,
                profile_image_url= form.profile_image_url.data or User.profile_image_url.default.arg
            )
            db.session.commit()

        except IntegrityError:
            flash("Username or email unavailable!", "danger")
            return render_template('/user/signup.html', form=form)
        
        print(f"Form has been validated for ${user}")
        
        do_login(user)

        return redirect(url_for('home'))
        
    else: 
        print("Sign up form page loading.")
        return render_template('/user/signup.html', form=form)


@auth.route('/logout/', methods=["GET"])
def logout():
    """Logout a user."""

    do_logout()
    return redirect(url_for('home'))

@auth.route('/login/', methods=["GET", "POST"])
def login():
    """Login a user."""

    form = LoginForm()

    # if already logged in
    if g.user:
        return redirect(url_for('home'))

    if form.validate_on_submit():

        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        print(f"Form has been validated for ${user}")
        
        if user:
            do_login(user)
            return redirect(url_for('home'))
        
        flash("Invalid credentials.", 'danger')
        
    print("Login form page loading.")
    return render_template('/user/login.html', form=form)

def send_mail(user):
    "Helper function for sending email."

    token=User.get_reset_token(user)

    msg = Message('WhichAni Password Reset Request', recipients=[user.email], sender='noreply@whichani.com')
    msg.body = f'''

        Click the link below to reset your WhichAni PW.
        {url_for('auth.reset_token', token=token, _external=True)}
        If you didn't make this request. Ignore this message.

    '''

    mail.send(msg)
    

@auth.route('/reset_password', methods=["GET", "POST"])
def reset_request():
    "Render page for sending reset password email"

    form=ResetRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if(user):
            send_mail(user)
            flash('Reset request sent! Check your email :) (and spam folder)')
            return redirect(url_for('auth.login'))
        
    return render_template('/user/reset_request.html', form=form)

@auth.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_token(token):
    "Render page for resetting password and handle password reset."

    user = User.verify_token(token)

    if user is None:
       flash('Invalid or expired token. Please try again.', 'warning')
       return redirect(url_for('auth.reset_request'))

    form=ResetPasswordForm()

    if form.validate_on_submit():

        new_password = form.new_password.data
        new_password_confirm = form.new_password_confirm.data

        if new_password != new_password_confirm:
            flash("New passwords do not match!", "danger")
            return redirect(url_for('auth.reset_token', token=token))
        
        if new_password != "":
            success = User.update_password(user.username, new_password)
            if success:
                flash("Password successfully changed.","success")
                return redirect(url_for('auth.login'))
            
    return render_template('/user/reset_password.html', form=form)
        