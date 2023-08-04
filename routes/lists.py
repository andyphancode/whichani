from flask import Flask, request, render_template, redirect, flash, session, jsonify, g, Blueprint
from models import connect_db, db, User, List, Listings, Anime
import requests

lists = Blueprint('lists', __name__,template_folder='routes')

######################################################
# List functions
######################################################

@lists.route("/new_list/")
def new_list():
    """Create an empty new list."""

    list = List(
            title="",
            description="",
            user_id=g.user.user_id
        )
    db.session.add(list)
    db.session.commit()

    return redirect(f"/list/{list.list_id}")


@lists.route("/recommend/", methods=["GET", "POST"])
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

@lists.route("/list/<int:list_id>/", methods=["GET", "POST"])
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

@lists.route("/list/<int:list_id>/delete/", methods=["GET", "POST"])
def delete_list(list_id):

    list = List.query.get_or_404(list_id)

    if not g.user:
        return redirect(f"/list/{list_id}")
    
    if request.method == "GET":
        return render_template("/list/delete.html", list=list)

    if request.method == "POST":  
        Listings.query.filter_by(list_id=list_id).delete()
        db.session.delete(list)
        db.session.commit()
        return redirect(f"/user/{list.user_id}")
        
@lists.route("/list/<int:list_id>/search/", methods=["GET","POST"])
def search(list_id):

    list = List.query.get_or_404(list_id)

    if not g.user:
        return redirect(f"/list/{list_id}") 
    
    if request.method == "GET":
        search_input = request.args.get('search_input')
        if search_input == None:
            # Setting default to search_input (seems to fix first search returning None)
            search_input = "Bocchi"

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

@lists.route("/list/<int:list_id>/add", methods=["GET", "POST"])
def add_to_list(list_id):

    list = List.query.get_or_404(list_id)

    mal_id = request.args.get('mal_id')

    print(list, mal_id)

    if not g.user:
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
    
    else: 

        anime = Anime.query.get(mal_id)
        print(anime)
        listing = Listings(
            list_id=list_id,
            anime_id = anime.anime_id,
            listing_description = anime.anime_description
        )

        db.session.add(listing)
        db.session.commit()

    return redirect(f"/list/{list_id}")


@lists.route("/listing/<int:listing_id>/edit/", methods=["GET","POST"])
def edit_listing(listing_id):

    listing = Listings.query.get_or_404(listing_id)

    if not g.user:
        return redirect(f"/list/{listing.lists.list_id}")
    
    if request.method == "GET":
        return render_template("/list/edit_listing.html", listing=listing)

    if request.method == "POST":

        listing_description = request.form.get('listing-description')
        listing.listing_description = listing_description
        db.session.add(listing)
        db.session.commit()
        return redirect(f"/list/{listing.lists.list_id}")
    
@lists.route("/listing/<int:listing_id>/delete/", methods=["GET","POST"])
def delete_listing(listing_id):

    listing = Listings.query.get_or_404(listing_id)

    if not g.user:
        return redirect(f"/list/{listing.lists.list_id}")   
    
    db.session.delete(listing)
    db.session.commit()
    return redirect(f"/list/{listing.lists.list_id}")
