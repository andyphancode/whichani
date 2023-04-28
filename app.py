import os
import random
import requests
from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm
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

@app.route('/logout/', methods=["GET"])
def logout():
    """Logout a user."""

    do_logout()
    return redirect("/")

@app.route('/login/', methods=["GET", "POST"])
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

@app.route("/new_list/")
def new_list():
    """Create an empty new list."""


@app.route("/recommend/", methods=["GET", "POST"])
def recommend():
    if request.method == "GET":
        return render_template("/list/recommend.html")
    if request.method == "POST":

        limit = 25
        type = request.form.get('type')
        if request.form.get('status') == "complete":
            status = "complete"
        else:
            status = "any"
        genres = ",".join(str(x) for x in request.form.getlist('genre'))
        min_score = 5
        sfw = 1
        order_by = "score" 
        sort = "desc"

        resp = requests.get("https://api.jikan.moe/v4/anime", params={
            "limit": limit,
            "type": type,
            "status":status,
            "genres":genres,
            "min_score":min_score,
            "sfw":sfw,
            "order_by":order_by,
            "sort":sort
            })

        i = 0
        while i < len(resp.json()['data']):
            if Anime.query.get(resp.json()['data'][i]['mal_id']) == None:
                anime = Anime(
                    anime_id=resp.json()['data'][i]['mal_id'],
                    anime_image_url=resp.json()['data'][i]['images']['jpg']['image_url'],
                    anime_title = resp.json()['data'][i]['title'],
                    anime_description = (resp.json()['data'][i]['synopsis']).replace('[Written by MAL Rewrite]','')
                )
                db.session.add(anime)
                db.session.commit()
            i += 1

        list = List(
            title="WhichAni Recommendations",
            description="Sign up to start making your own lists today!",
            user_id=1
        )

        db.session.add(list)
        db.session.commit()

        if len(resp.json()['data']) > 10:
            random_array = random.sample(range(len(resp.json()['data'])), 10)
            for num in random_array:
                listing = Listings(
                    list_id = list.list_id,
                    anime_id = resp.json()['data'][num]['mal_id'],
                    listing_description = (resp.json()['data'][num]['synopsis']).replace('[Written by MAL Rewrite]','')
                )
                db.session.add(listing)
                db.session.commit()
        return redirect(f"/list/{list.list_id}")

@app.route("/list/<int:list_id>/", methods=["GET", "POST"])
def show_list(list_id):

    list = List.query.get_or_404(list_id)

    if request.method == "GET":
        return render_template("/list/list.html", list=list)
    
    if request.method == "POST":
        list.title = request.form.get('title')
        list.description = request.form.get('description')

        db.session.add(list)
        db.session.commit()
        return redirect(f"/list/{list_id}")

@app.route("/list/<int:list_id>/delete/", methods=["GET", "POST"])
def delete_list(list_id):

    list = List.query.get_or_404(list_id)

    if list.user_id != g.user.user_id:
        flash("You do not have permission to do that!", "danger")
        return redirect(f"/list/{list_id}")
    
    if request.method == "GET":
        return render_template("/list/delete.html", list=list)

    if request.method == "POST":  
        Listings.query.filter_by(list_id=list_id).delete()
        db.session.delete(list)
        db.session.commit()
        return redirect(f"/")
        
@app.route("/list/<int:list_id>/search/", methods=["GET","POST"])
def search(list_id):

    list = List.query.get_or_404(list_id)

    if list.user_id != g.user.user_id:
        flash("You do not have permission to do that!", "danger")
        return redirect(f"/list/{list_id}") 
    
    if request.method == "GET":
        search_input = request.args.get('search_input')
        try:
            page = int(request.args.get('page'))
        except:
            page = 1

        resp = requests.get("https://api.jikan.moe/v4/anime", params={
            "q": search_input,
            "sfw":1,
            "order_by":"popularity",
            "page": page
        })

        data = resp.json()

        max_pages = resp.json()['pagination']['last_visible_page']
        
        return render_template("/list/search.html", list=list, data=data, search_input=search_input, page=page, max_pages=max_pages)

@app.route("/list/<int:list_id>/add", methods=["GET", "POST"])
def add_to_list(list_id):

    list = List.query.get_or_404(list_id)

    mal_id = request.args.get('mal_id')

    print(list, mal_id)

    if list.user_id != g.user.user_id:
        flash("You do not have permission to do that!", "danger")
        return redirect(f"/list/{list_id}") 
    
    if Anime.query.get(mal_id) == None:

        resp = requests.get(f"https://api.jikan.moe/v4/anime/{mal_id}")


        anime = Anime(
            anime_id=resp.json()['data']['mal_id'],
            anime_image_url=resp.json()['data']['images']['jpg']['image_url'],
            anime_title=resp.json()['data']['title'],
            anime_description=(resp.json()['data']['synopsis']).replace('[Written by MAL Rewrite]','')
        )

        db.session.add(anime)
        db.session.commit()

    listing = Listings(
        list_id=list_id,
        anime_id = resp.json()['data']['mal_id'],
        listing_description = (resp.json()['data']['synopsis']).replace('[Written by MAL Rewrite]','')
    )

    db.session.add(listing)
    db.session.commit()

    return redirect(f"/list/{list_id}")


@app.route("/listing/<int:listing_id>/edit/", methods=["GET","POST"])
def edit_listing(listing_id):

    listing = Listings.query.get_or_404(listing_id)

    if listing.lists.user_id != g.user.user_id:
        flash("You do not have permission to do that!", "danger")
        return redirect(f"/list/{listing.lists.list_id}")
    
    if request.method == "GET":
        return render_template("/list/edit_listing.html", listing=listing)

    if request.method == "POST":

        listing_description = request.form.get('listing-description')
        listing.listing_description = listing_description
        db.session.add(listing)
        db.session.commit()
        return redirect(f"/list/{listing.lists.list_id}")
    
@app.route("/listing/<int:listing_id>/delete/", methods=["GET","POST"])
def delete_listing(listing_id):

    listing = Listings.query.get_or_404(listing_id)

    if listing.lists.user_id != g.user.user_id:
        flash("You do not have permission to do that!", "danger")
        return redirect(f"/list/{listing.lists.list_id}")   
    
    db.session.delete(listing)
    db.session.commit()
    return redirect(f"/list/{listing.lists.list_id}")


######################################################
# User
######################################################
@app.route("/user/<int:user_id>/", methods=["GET","POST"])
def show_user(user_id):

    return render_template("/user/profile.html")


######################################################
# Error page
######################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 page."""

    return render_template('404.html'), 404