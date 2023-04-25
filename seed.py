from app import db 
from models import User
from secret import WhichAniPW, WhichAniEmail

db.drop_all()
db.create_all()

user = User.signup(
                username = "WhichAni",
                password = WhichAniPW,
                email = WhichAniEmail,
                profile_image_url= User.profile_image_url.default.arg)

db.session.commit()