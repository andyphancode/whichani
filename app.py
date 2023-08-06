import os
import random
import requests
from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from routes.list import list
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm, EditUserForm
from app import *
from secret import API_KEY_CONFIG

CURR_USER_KEY = "curr_user"

app = Flask(__name__) 
app.register_blueprint(list)
app.app_context().push() 
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', API_KEY_CONFIG)
# debug = DebugToolbarExtension(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///whichani')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)


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

@app.route('/signup/', methods=["GET", "POST"])
def signup():

    form = SignUpForm()

    # if already logged in
    if g.user:
        return redirect("/")

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

@app.route('/logout/', methods=["GET"])
def logout():
    """Logout a user."""

    do_logout()
    return redirect("/")

@app.route('/login/', methods=["GET", "POST"])
def login():
    """Login a user."""

    form = LoginForm()

    # if already logged in
    if g.user:
        return redirect("/")

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user:
            do_login(user)
            return redirect("/")
        
        flash("Invalid credentials.", 'danger')

    return render_template('/user/login.html', form=form)



######################################################
# User
######################################################
@app.route("/user/<int:user_id>/", methods=["GET","POST"])
def show_user(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        about_me = request.form.get('about_me')
        user.about_me = about_me
        db.session.add(user)
        db.session.commit()


    return render_template("/user/profile.html", user=user)
    


@app.route("/user/<int:user_id>/edit/", methods=["GET","POST"])
def edit_user(user_id):

    user = User.query.get_or_404(user_id)

    form = EditUserForm()

    if not g.user:
        return redirect(f"/user/{user_id}")

    if request.method == "POST":

        email = form.email.data
        profile_image_url = form.profile_image_url.data
        old_password = form.old_password.data
        new_password = form.new_password.data
        new_password_confirm = form.new_password_confirm.data

        if profile_image_url == "":
            profile_image_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

        if new_password != new_password_confirm:
            flash("New passwords do not match!", "danger")
            return redirect(f"/user/{user_id}/edit")
        
        user_edit = User.authenticate(g.user.username, old_password)

        if user_edit:
            try:
                user_edit.email = email
                user_edit.profile_image_url = profile_image_url

                db.session.add(user_edit)
                db.session.commit()
                flash("Settings successfully changed.","success")
                if new_password != "":
                    success = User.update_password(user_edit.username, new_password)
                    if success:
                        flash("Password successfully changed.","success")
            except IntegrityError:
                flash("Email already in use!", "danger")
                return redirect(f"/user/{user_id}/edit") 

        else: 
            flash("Incorrect credentials.", "danger")
        

        return redirect(f"/user/{user_id}/edit")
       
    return render_template("/user/edit_profile.html", form=form, user=user)    

@app.route("/user/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    if not g.user:
        return redirect(f"/user/{user_id}")
    
    db.session.delete(user)
    db.session.commit()
    return redirect("/")

######################################################
# Error page
######################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 page."""

    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()