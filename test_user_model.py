"""User model tests."""

# Run via this command:
# python -m unittest test_user_model.py


import os
from unittest import TestCase 
from sqlalchemy import exc
from models import db, User, List

os.environ['DATABASE_URL'] = "postgresql:///whichani-test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup("test1", "testpw1", "email1@email.com", None)
        user2 = User.signup("test2", "testpw2", "email2@email.com", None)

        user1.user_id = 111111
        user2.user_id = 222222

        db.session.commit()

        user1 = User.query.get(111111)
        user2 = User.query.get(222222)

        self.user1 = user1
        self.user2 = user2

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no liked lists or lists
        self.assertEqual(len(u.liked_lists), 0)
        self.assertEqual(len(u.lists), 0)

    ########################################
    # Authenticating

    def test_wrong_username(self):
        self.assertFalse(User.authenticate("wrongusername", "testpw1"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate("test1", "wrongpassword"))
    
    def test_authentication(self):
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)

    #############################
    # Signup 

    def test_signup(self):

        user = User.signup("testuser",  "testpassword", "testemail@email.com", None)
        user.user_id = 333333
        db.session.commit()

        user = User.query.get(333333)

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testemail@email.com")
        # checks that pw is encrypted
        self.assertNotEqual(user.password, "testpassword")

    def test_invalid_username(self):
        user = User.signup(None,  "testpassword", "testemail@email.com", None)
        user.user_id = 333333
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            user = User.signup("testuser",  None, "testemail@email.com", None)
        with self.assertRaises(ValueError) as context:
            user = User.signup("testuser",  "", "testemail@email.com", None)

    #############################
    # Updating password

    def test_update_password(self):
        """Test updating user password."""
        user = User.signup('testuser', 'password', 'test@example.com', None)
        db.session.commit()
        user = User.update_password('testuser', 'newpassword')
        db.session.commit()
        user = User.authenticate('testuser','newpassword')
        self.assertTrue(user)