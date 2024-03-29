import os
# from secret import API_KEY_CONFIG
import jwt
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# for production, API_KEY_CONFIG as 2nd argument
SECRET_KEY = os.environ.get("SECRET_KEY")

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)

class User(db.Model):
    """User model."""

    __tablename__ = 'users'

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.Text,
        unique=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    profile_image_url = db.Column(
        db.Text,
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
    )

    about_me = db.Column(
        db.Text,
        default="I love anime!"
    )

    lists = db.relationship('List',
                            backref='users',
                            lazy=True,
                            cascade='all, delete-orphan')
    
    ##Stretch feature
    liked_lists = db.relationship('List',
                            secondary = 'likes',
                            backref='liked_by')

    @classmethod
    def signup(cls, username, password, email, profile_image_url):
        """Sign up user. Hash password."""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
            email=email,
            profile_image_url=profile_image_url,
        )

        db.session.add(user)
        return user
    
    @classmethod
    def update_password(cls, username, new_password):
        """Update user with new password"""

        user = cls.query.filter_by(username=username).first()

        hashed_pwd = bcrypt.generate_password_hash(new_password).decode('UTF-8')

        user.password = hashed_pwd

        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Authenticate a user based on inputted username and password. Returns user object if matching, returns False if not."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
    @classmethod
    def get_reset_token(cls, self):

        payload = {
            'user_id': self.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        reset_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return reset_token
    
    @staticmethod
    def verify_token(token):
        try:
            user_id = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])['user_id']
        except:
            return None
        return User.query.get_or_404(user_id)


class List(db.Model):
    """List saving anime+description entries."""

    __tablename__ = "lists"

    list_id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    title = db.Column(
        db.Text,
        default="Untitled"
    )

    description = db.Column(
        db.Text,
        default="No description."
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id')
    )

    listings = db.relationship('Listings',
                               backref='lists',
                               lazy=True,
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        """Show info on list."""

        l = self
        return f"<List {l.list_id} {l.title} {l.description} {l.user_id}>"

class Listings(db.Model):
    "Individual listings on a list."

    __tablename__ = "listings"

    listing_id = db.Column(
        db.Integer,
        primary_key=True
    )

    anime_id = db.Column(
        db.Integer,
        db.ForeignKey('anime.anime_id')
    )

    list_id = db.Column(
        db.Integer,
        db.ForeignKey('lists.list_id')
    )
    
    listing_description = db.Column(
        db.Text
    )

    def __repr__(self):
        """Show info on listing."""

        l = self
        return f"<Listing {l.listing_id} {l.anime_id} {l.list_id} {l.listing_description}>"

class Anime(db.Model):
    """For saving an anime entry."""

    __tablename__ = "anime"

    anime_id = db.Column(
        db.Integer,
        primary_key=True
    )
    anime_image_url = db.Column(
        db.Text,
        default="No image found"
    )
    anime_description = db.Column(
        db.Text
    )
    anime_title = db.Column(
        db.Text,
        nullable=False
    )

    listings = db.relationship('Listings',
                               backref='anime',
                               lazy=True)
    
    def __repr__(self):
        """Show info on anime."""

        a = self
        return f"<Anime {a.anime_id} {a.anime_image_url} {a.anime_description} {a.anime_title}>"


# likes table for many-to-many relationship
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True),
    db.Column('list_id', db.Integer, db.ForeignKey('lists.list_id'), primary_key=True)
)

