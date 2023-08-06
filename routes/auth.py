from flask import Flask, request, render_template, redirect, flash, session, jsonify, g, Blueprint
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm, EditUserForm
from sqlalchemy.exc import IntegrityError

CURR_USER_KEY = "curr_user"

auth = Blueprint('auth', __name__,template_folder='routes')


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

    form = SignUpForm()

    # if already logged in
    # if g.user:
    #     return redirect("/")

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
        
        do_login(user)

        return redirect("/")
        
    else: 
        return render_template('/user/signup.html', form=form)

@auth.route('/logout/', methods=["GET"])
def logout():
    """Logout a user."""

    do_logout()
    return redirect("/")

@auth.route('/login/', methods=["GET", "POST"])
def login():
    """Login a user."""

    form = LoginForm()

    # if already logged in
    # if g.user:
    #     return redirect("/")

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user:
            do_login(user)
            return redirect("/")
        
        flash("Invalid credentials.", 'danger')

    return render_template('/user/login.html', form=form)
