from flask import Flask, request, render_template, redirect, flash, session, jsonify, g, Blueprint
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm, EditUserForm
from sqlalchemy.exc import IntegrityError


user = Blueprint('user', __name__, template_folder='routes')

######################################################
# User
######################################################
@user.route("/user/<int:user_id>/", methods=["GET","POST"])
def show_user(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        about_me = request.form.get('about_me')
        user.about_me = about_me
        db.session.add(user)
        db.session.commit()


    return render_template("/user/profile.html", user=user)
    


@user.route("/user/<int:user_id>/edit/", methods=["GET","POST"])
def edit_user(user_id):

    user = User.query.get_or_404(user_id)

    form = EditUserForm()

    if not g.user:
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

    user = User.query.get_or_404(user_id)

    if not g.user:
        return redirect(f"/user/{user_id}")
    
    db.session.delete(user)
    db.session.commit()
    return redirect("/")
