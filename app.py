import os
from flask import Flask, render_template, session, g
from routes.list import list
from routes.auth import auth
from routes.user import user
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, List, likes
from flask_cors import CORS, cross_origin

# from secret import API_KEY_CONFIG

from sqlalchemy import desc, func

CURR_USER_KEY = "curr_user"

app = Flask(__name__) 

with app.app_context():

    cors = CORS(app, origins=["whichani.me","whichani.onrender.com"])
    app.register_blueprint(list)
    app.register_blueprint(auth)
    app.register_blueprint(user)
    # for production, API_KEY_CONFIG as 2nd argument
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    # debug = DebugToolbarExtension(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///whichani')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SESSION_COOKIE_SECURE'] = True


connect_db(app)
 

######################################################
# Session handler
######################################################

@app.before_request
def add_user_to_g():
    """If logged in, add user to g."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


######################################################
# Home
######################################################

@app.route('/', methods=["GET"])
def home():
    """Render homepage based on login status. Also load top liked lists."""

    list_alias = db.aliased(List)
    likes_alias = db.aliased(likes)

    top_lists = (db.session.query(list_alias) 
                .join(likes_alias, list_alias.list_id == likes_alias.c.list_id)
                .group_by(list_alias.list_id)
                .order_by(desc(db.func.count(likes_alias.c.user_id)))
                .limit(10)
                .all())

    top_list_with_likes = []

    for list in top_lists:
        tmp = []
        if len(list.listings) != 0:
            like_count = db.session.query(func.count(likes.c.user_id)).filter(likes.c.list_id == list.list_id).scalar()
            first_listing = list.listings
            tmp.append(list)
            tmp.append(like_count)
            tmp.append(first_listing)
            top_list_with_likes.append(tmp)

    return render_template('home.html', top_list_with_likes=top_list_with_likes)

######################################################
# Error page
######################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 page."""

    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()