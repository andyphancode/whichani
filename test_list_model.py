"""List model tests."""

# Run via this command:
# python -m unittest test_list_model.py

import os
from unittest import TestCase 

from models import db, User, List

os.environ['DATABASE_URL'] = "postgresql:///whichani-test"

from app import app

db.create_all()

class ListModelTestCase(TestCase):
    """Test for list models."""

    def setUp(self):

        db.drop_all()
        db.create_all()

        user = User.signup("testuser", "test@email.com", "testpw", None)
        user.user_id = 111111

        db.session.commit()

        self.user = User.query.get(111111)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_list_model(self):
        """Does basic model work?"""

        list = List(title="test", description="this is a test list.", user_id=111111)

        db.session.add(list)
        db.session.commit()

        self.assertEqual(self.user.lists[0].title, "test")
        self.assertEqual(self.user.lists[0].description, "this is a test list.")
        self.assertEqual(self.user.lists[0].user_id, 111111)
    
    def test_list_like(self):
        """Test liking a list."""

        list = List(title="test", description="this is a test list.", user_id=111111)

        user = User.signup("testuser2", "test2@email.com", "testpw2", None)

        user.id = 222222

        db.session.add_all([list, user])
        db.session.commit()

        list.liked_by.append(user)

        db.session.commit()

        likes = user.liked_lists
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].list_id, list.list_id)
    
    def test_delete_list(self):
        """Test deleting a list."""

        list = List(title="test", description="this is a test list.", user_id=111111)

        db.session.add(list)
        db.session.commit()

        db.session.delete(list)
        db.session.commit()

        retrieve_list = List.query.get(list.list_id)

        self.assertIsNone(retrieve_list)