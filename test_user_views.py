"""User View tests."""

# Run test with:K
# FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, User, List

os.environ['DATABASE_URL'] = "postgresql:///whichani-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):

        db.drop_all()
        db.create_all()

        user1 = User.signup("testuser1", "testpw1", "test1@email.com", None)
        user2 = User.signup("testuser2", "testpw2", "test2@email.com", None)

        user1.user_id = 111111
        user2.user_id = 222222

        db.session.commit()

        self.user1 = user1
        self.user2 = user2

        list1 = List(title="this is list from user1", description="test list.", user_id=111111)
        list2 = List(title="this is list from user2", description="test list.", user_id=222222)

        db.session.add_all([list1, list2])
        db.session.commit()

        list1.liked_by.append(self.user1)
        list1.liked_by.append(self.user2)
        list2.liked_by.append(self.user1)

        db.session.commit()

        self.client = app.test_client()

    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_show_user_lists(self):
        """Test showing a user's lists."""

        with self.client as c:
            
            resp = c.get(f"/user/{self.user1.user_id}/lists")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("this is list from user1", str(resp.data))
            self.assertNotIn("this is list from user2", str(resp.data))
    

    def test_show_user_likes_unauthorized(self):
        """Test showing a user's likes but not as identical user."""

        with self.client as c:
            
            resp = c.get(f"/user/{self.user2.user_id}/likes")
            self.assertEqual(resp.status_code, 302)
    
    def test_show_user_likes(self):
        """Test showing a user's likes as user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id
                                
            resp = c.get(f"/user/{self.user1.user_id}/likes")
            self.assertIn("this is list from user1", str(resp.data))
            self.assertIn("2 Likes", str(resp.data))
            self.assertIn("this is list from user2", str(resp.data))

    def test_show_edit_user(self):
        """Test showing user edit page as user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id
                                
            resp = c.get(f"/user/{self.user1.user_id}/edit", follow_redirects=True)
            self.assertIn("Edit your account details.", str(resp.data))

    def test_show_edit_user_unauthorized(self):
        """Test showing user edit page as unauthorized user."""

        with self.client as c:
            
            resp = c.get(f"/user/{self.user2.user_id}/edit", follow_redirects=True)
            self.assertIn("About testuser2", str(resp.data))
