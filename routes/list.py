import requests
import random
from flask import request, render_template, redirect, g, Blueprint
from models import db, List, Listings, Anime, likes
from forms import EditListForm, EditListingForm



list = Blueprint('list', __name__,template_folder='routes')

######################################################
# List functions
######################################################

@list.route("/new_list/")
def new_list():
    """Create an empty new list."""

    if not g.user:
        return redirect("/") 

    list = List(
            title="",
            description="",
            user_id=g.user.user_id
        )
    db.session.add(list)
    db.session.commit()

    return redirect(f"/list/{list.list_id}")


@list.route("/recommend/", methods=["GET", "POST"])
def recommend():
    """Generate a list of recommendations."""

    if request.method == "GET":

        return render_template("/list/recommend.html")
    
    if request.method == "POST":

        # parameters for recommendations
        limit = 25
        type = request.form.get('type')
        status = request.form.get('status')
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
            user_id= g.user.user_id if g.user else 1
        )

        db.session.add(list)
        db.session.commit()

        # randomize if returned recommendations is greater than 10 count
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

@list.route("/list/<int:list_id>/", methods=["GET", "POST"])
def show_list(list_id):
    """Show list owned by user."""

    list = List.query.get_or_404(list_id)

    edit_form = EditListForm()
    # prepopulate the edit_form textarea
    edit_form.list_description.data = list.description

    edit_listing_form = EditListingForm()

    # Check if user has liked before 
    likes_count = db.session.query(likes).filter_by(list_id=list_id).count()

    if g.user:
        user_has_liked = db.session.query(likes).filter_by(user_id=g.user.user_id, list_id=list_id).first()
    else:
        user_has_liked = False

    if request.method == "GET":
        return render_template("/list/list.html", list=list, edit_form=edit_form, edit_listing_form=edit_listing_form, likes_count=likes_count, user_has_liked=user_has_liked)
    
    # If built in edit list details form is submitted
    if request.method == "POST":

        if g.user.user_id != list.user_id:
            return redirect(f"/list/{list_id}")

        list.title = request.form.get('list_title')
        list.description = request.form.get('list_description')

        db.session.add(list)
        db.session.commit()
        return redirect(f"/list/{list_id}")

@list.route("/list/<int:list_id>/delete/", methods=["GET", "POST"])
def delete_list(list_id):
    """Delete list."""

    list = List.query.get_or_404(list_id)

    if not g.user:
        return redirect(f"/list/{list_id}")

    if g.user.user_id != list.user_id:
        return redirect(f"/list/{list_id}")

    
    if request.method == "POST":  

        Listings.query.filter_by(list_id=list_id).delete()
        db.session.delete(list)
        db.session.commit()
        return redirect(f"/user/{list.user_id}")
        
@list.route("/list/<int:list_id>/search/", methods=["GET","POST"])
def search(list_id):
    """Search function."""

    list = List.query.get_or_404(list_id)

    if not g.user:
        return redirect(f"/list/{list_id}") 
    
    # preserve search_input through page swaps
    search_input = request.args.get('search_input')
    if search_input == None:
        # Setting default to search_input (seems to fix first search returning None)
        search_input = "Bocchi The Rock"

    # retrieve current page input
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

@list.route("/list/<int:list_id>/add", methods=["GET", "POST"])
def add_to_list(list_id):
    """Add an anime listing to our list."""

    list = List.query.get_or_404(list_id)

    if g.user.user_id != list.user_id:
        return redirect(f"/list/{list_id}")

    if not g.user:
        return redirect(f"/list/{list_id}") 
    
    mal_id = request.form.get('mal_id')

    # Checks if anime is already in our database (lowers how many API requests we have to make)
    if Anime.query.get(mal_id) == None:

        resp = requests.get(f"https://api.jikan.moe/v4/anime/{mal_id}")

        # Save anime to our database for future use
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
    
    else: 

        anime = Anime.query.get(mal_id)
        listing = Listings(
            list_id=list_id,
            anime_id = anime.anime_id,
            listing_description = anime.anime_description
        )

        db.session.add(listing)
        db.session.commit()

    return redirect(f"/list/{list_id}")


@list.route("/edit-listing/<int:listing_id>", methods=["GET","POST"])
def edit_listing(listing_id):
    """Edit a listing."""

    listing = Listings.query.get_or_404(listing_id)

    if not g.user:
        return redirect(f"/list/{listing.lists.list_id}")
    
    if g.user.user_id != listing.lists.user_id:
        return redirect("/")
    
    if request.method == "POST":

        listing_description = request.form.get('listing_description')
        listing.listing_description = listing_description
        db.session.add(listing)
        db.session.commit()
        return redirect(f"/list/{listing.lists.list_id}")
    
@list.route("/listing/<int:listing_id>/delete/", methods=["GET","POST"])
def delete_listing(listing_id):
    """Delete a listing."""

    listing = Listings.query.get_or_404(listing_id)
    # Preserve list_id in variable
    list_id = listing.lists.list_id


    if not g.user:
        return redirect(f"/list/{listing.lists.list_id}")  
    
    if g.user.user_id != listing.lists.user_id:
        return redirect(f"/list/{list_id}")
     
    if request.method == "POST":
        db.session.delete(listing)
        db.session.commit()
        return redirect(f"/list/{list_id}")


@list.route("/list/<int:list_id>/like", methods=["GET","POST"])
def like_list(list_id):
    """Like a list."""

    list = List.query.get_or_404(list_id)

    if not g.user:
        return redirect(f"/list/{list_id}")
    
    if request.method == "POST":

        if g.user in list.liked_by:
            list.liked_by.remove(g.user)
            db.session.commit()
        else:
            list.liked_by.append(g.user)
            db.session.commit()
        
        return redirect(f"/list/{list_id}")

        