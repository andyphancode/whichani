from flask import request, render_template, redirect, flash, g, Blueprint
from models import db, User, List, likes
from forms import EditUserForm, EditAboutMeForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

user = Blueprint('user', __name__, template_folder='routes')

######################################################
# User
######################################################
@user.route("/user/<int:user_id>/", methods=["GET","POST"])
def show_user(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    form = EditAboutMeForm()
    # prepopulate about_me form
    form.about_me.data = user.about_me

    # generate 10 lists made by user ranked by likes
    top_lists = (List.query
                 .filter_by(user_id=user_id)  
                 .outerjoin(likes) 
                 .group_by(List.list_id)
                 .order_by(desc(db.func.count(likes.c.user_id)))
                 .limit(10)
                 .all())
    
    # save like counts of each list in top lists
    like_counts = {}

    for list in top_lists:
        like_count = db.session.query(likes).filter_by(list_id=list.list_id).count()
        like_counts[list.list_id] = like_count

    # generate 10 lists liked by user ranked by likes
    liked_lists = (List.query
                    .join(likes, List.list_id == likes.c.list_id)
                    .filter(likes.c.user_id == user_id)
                    .group_by(List.list_id)
                    .order_by(desc(db.func.count(likes.c.user_id)))
                    .limit(10)
                    .all())

    # if built in about me form is submitted
    if request.method == "POST":
        about_me = request.form.get('about_me')
        user.about_me = about_me
        db.session.add(user)
        db.session.commit()


    return render_template("/user/profile.html", user=user, top_lists=top_lists, like_counts=like_counts, liked_lists=liked_lists, form=form)
    
@user.route("/user/<int:user_id>/lists")
def show_user_lists(user_id):
    """Show lists made by user."""

    user = User.query.get_or_404(user_id)


    lists = (List.query
                .filter_by(user_id=user_id)  
                .outerjoin(likes) 
                .group_by(List.list_id)
                .order_by(desc(db.func.count(likes.c.user_id)))
                .all())

    like_counts = {}

    for list in lists:
        like_count = db.session.query(likes).filter_by(list_id=list.list_id).count()
        like_counts[list.list_id] = like_count

    # list_type to indicate which type of list
    return render_template("/user/user_list.html", user=user, lists=lists, like_counts=like_counts, list_type=1)

@user.route("/user/<int:user_id>/likes")
def show_user_likes(user_id):
    """Show lists liked by user."""

    user = User.query.get_or_404(user_id)

    if g.user.user_id != user_id:
        return redirect(f"/user/{user_id}")

    lists = (List.query
            .join(likes)  # Join with the likes association table
            .filter(likes.c.user_id == user.user_id)  # Filter by the user's ID
            .all())
    
    like_counts = {}
    
    for list in lists:
        like_count = db.session.query(likes).filter_by(list_id=list.list_id).count()
        like_counts[list.list_id] = like_count

    return render_template("/user/user_list.html", user=user, lists=lists, like_counts=like_counts, list_type=2)


@user.route("/user/<int:user_id>/edit/", methods=["GET","POST"])
def edit_user(user_id):
    """Edit user account details."""

    user = User.query.get_or_404(user_id)

    form = EditUserForm()

    if not g.user:
        return redirect(f"/user/{user_id}")
    
    if g.user.user_id != user_id:
        return redirect(f"/user/{user_id}")

    if request.method == "POST":

        email = form.email.data
        profile_image_url = form.profile_image_url.data
        old_password = form.old_password.data
        new_password = form.new_password.data
        new_password_confirm = form.new_password_confirm.data

        if profile_image_url == "":
            profile_image_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"

        if new_password != new_password_confirm:
            flash("New passwords do not match!", "danger")
            return redirect(f"/user/{user_id}/edit")
        
        user_edit = User.authenticate(g.user.username, old_password)

        if user_edit:
            try:
                user_edit.email = email
                user_edit.profile_image_url = profile_image_url

                db.session.add(user_edit)
                db.session.commit()
                flash("Settings successfully changed.","success")
                if new_password != "":
                    success = User.update_password(user_edit.username, new_password)
                    if success:
                        flash("Password successfully changed.","success")
            except IntegrityError:
                flash("Email already in use!", "danger")
                return redirect(f"/user/{user_id}/edit") 

        else: 
            flash("Incorrect credentials.", "danger")
        

        return redirect(f"/user/{user_id}/edit")
       
    return render_template("/user/edit_profile.html", form=form, user=user)    

@user.route("/user/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """Delete user."""

    user = User.query.get_or_404(user_id)

    if g.user.user_id != user_id:
        return redirect(f"/user/{user_id}")

    if not g.user:
        return redirect(f"/user/{user_id}")
    
    db.session.delete(user)
    db.session.commit()
    return redirect("/")
