import os
import random
from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm, RecommendForm
from app import *
from secret import API_KEY_CONFIG

CURR_USER_KEY = "curr_user"

app = Flask(__name__) 
app.app_context().push() 
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', API_KEY_CONFIG)
# debug = DebugToolbarExtension(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///whichani')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

######################################################
# User signup/login/logout functions
######################################################

@app.before_request
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
# Home
######################################################

@app.route('/', methods=["GET"])
def home():
    """Render homepage based on login status."""

    return render_template('home.html')

######################################################
# User signup/login/logout view functions
######################################################

@app.route('/signup', methods=["GET", "POST"])
def signup():

    form = SignUpForm()

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
            flash("Username unavailable!", "danger")
            return render_template('/user/signup.html', form=form)
        
        do_login(user)

        return redirect("/")
        
    else: 
        return render_template('/user/signup.html', form=form)

@app.route('/logout', methods=["GET"])
def logout():
    """Logout a user."""

    do_logout()
    return redirect("/")

@app.route('/login', methods=["GET", "POST"])
def login():
    """Login a user."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user:
            do_login(user)
            return redirect("/")
        
        flash("Invalid credentials.", 'danger')

    return render_template('/user/login.html', form=form)

######################################################
# List functions
######################################################

@app.route("/recommend", methods=["GET", "POST"])
def recommend():

    form = RecommendForm()

    if request.method == "GET":

        return render_template("recommend.html", form=form)
    

    random.sample(range(20), 10)

######################################################
# Error page
######################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 page."""

    return render_template('404.html'), 404