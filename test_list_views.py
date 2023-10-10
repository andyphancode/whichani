"""List View tests."""

# Run test with:
# FLASK_ENV=production python -m unittest test_list_views.py


import os
from unittest import TestCase

from models import db, User, List, Listings, Anime

os.environ['DATABASE_URL'] = "postgresql:///whichani-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class ListViewTestCase(TestCase):
    """Test views for lists."""

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

        list1.list_id = 111111
        list2.list_id = 222222


        db.session.add_all([list1, list2])
        db.session.commit()

        new_anime = Anime(anime_image_url="", anime_description="", anime_title="Cowboy Bebop")
        new_anime.anime_id = 1

        db.session.add(new_anime)
        db.session.commit()

        listing1 = Listings(anime_id=1, listing_description="this is a test description")
        listing1.listing_id = 1000

        db.session.commit()

        list2.listings.append(listing1)

        list1.liked_by.append(self.user1)
        list1.liked_by.append(self.user2)
        list2.liked_by.append(self.user1)

        db.session.commit()

        self.client = app.test_client()

    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_new_list(self):
        """Test showing a user's lists."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id
            
            resp = c.get(f"/new_list", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Untitled", str(resp.data))
    
    def test_show_recommend_list(self):
        """Test showing recommend list interface."""

        with self.client as c:
            resp = c.get(f"/recommend", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Generate some recommendations!", str(resp.data))

    def test_recommend_list(self):
        "Test recommendation feature."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id

            resp = c.post('/recommend/', data={
                    'type': 'TV',
                    'status': 'airing',
                    'genre': ['action', 'adventure'],
                    })
            self.assertEqual(resp.status_code, 302)

            resp2 = c.post('/recommend/', data={
                    'type': 'TV',
                    'status': 'airing',
                    'genre': ['action', 'adventure'],
                    }, follow_redirects = True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn("WhichAni Recommendations", str(resp2.data))
            
    def test_show_list(self):
        "Test showing a list."

        with self.client as c:
            resp = c.get(f"/list/111111", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("this is list from user1", str(resp.data))
            resp2 = c.get(f"/list/222222", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Cowboy Bebop", str(resp2.data))
    
    def test_edit_listing(self):
        "Test editing a listing as user."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.user_id

            resp = c.post(f"/edit-listing/1000/", data={'listing_description': 'new changed description'}, follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("new changed description", str(resp.data))
    
    def test_edit_listing_unauthorized(self):
        "Test editing a listing as non-owner."

        with self.client as c:

            resp = c.post(f"/edit-listing/1000/", data={'listing_description': 'new changed description'}, follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("this is a test description", str(resp.data))

    def test_delete_listing(self):
        "Test deleting listing as user."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.user_id

            resp = c.post(f"/listing/1000/delete/", follow_redirects = True)
            print(resp.data)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("this is a test description", str(resp.data))

    def test_delete_listing_unauthorized(self):
        "Test deleting listing as non-owner."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id

            resp = c.post(f"/listing/1000/delete", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("this is a test description", str(resp.data))

    def test_like_list(self):
        "Test like feature."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.user_id\
            
            resp = c.post(f'/list/111111/like', follow_redirects = True)
            print(resp.data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""Likes <span class="badge rounded-pill mx-2">1</span>""", str(resp.data))

    def test_search(self):
        "Test search feature."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id
            resp = c.get(f"/list/111111/search", follow_redirects = True, query_string={'search_input': 'Bocchi The Rock'})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Bocchi The Rock", str(resp.data))
    
    def test_search_unauthorized(self):
        "Test search feature as unauthorized user."
         
        with self.client as c:
            resp = c.get(f"/list/111111/search", query_string={'search_input': 'Bocchi The Rock'}, follow_redirects = True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("this is list from user1", str(resp.data))

    def test_add_to_list(self):
        "Test adding anime to list as user."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.user_id
            resp = c.get(f"/list/111111/add", follow_redirects = True, data={'mal_id': '30276'})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("One Punch Man", str(resp.data))

    def test_add_to_list_unauthorized(self):
        "Test adding anime to list as unauthorized user."

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.user_id
            resp = c.get(f"/list/111111/add", follow_redirects = True, data={'mal_id': '30276'})
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("One Punch Man", str(resp.data))




    
