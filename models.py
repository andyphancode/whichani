from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

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
        nullable=False,
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
        db.Text
    )

    lists = db.relationship('List',
                            backref='users')
    
    ##Stretch feature
    likes = db.relationship('List',
                            secondary = 'likes')

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
    def authenticate(cls, username, password):
        """Authenticate a user based on inputted username and password. Returns user object if matching, returns False if not."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    

class Anime(db.Model):
    """For saving an anime entry."""

    __tablename__ = "anime"

    anime_id = db.Column(
        db.Integer,
        primary_key=True
    )

class List(db.Model):
    """List saving anime+description entries."""

    __tablename__ = "lists"

    list_id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    title = db.Column(
        db.Text,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='cascade')
    )

    anime = db.relationship(
        'Anime',
        secondary='listings',
        backref='lists'
    )

class Listings(db.Model):

    __tablename__ = "listings"

    listing_id = db.Column(
        db.Integer,
        primary_key=True
    )

    anime_id = db.Column(
        db.Integer,
        db.ForeignKey('anime.anime_id', ondelete='cascade')
    )

    list_id = db.Column(
        db.Integer,
        db.ForeignKey('lists.list_id', ondelete='cascade')
    )


## Stretch feature, saved code
class Likes(db.Model):
    """Mapping user likes to lists."""

    __tablename__ = 'likes'

    like_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='cascade')
    )

    list_id = db.Column(
        db.Integer,
        db.ForeignKey('lists.list_id', ondelete='cascade'),
        unique=True
    )

