from . import user
from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db
from werkzeug.security import generate_password_hash, check_password_hash

@user.route("/", methods=['GET'])
def user_page():
    return render_template('user_profile.html')


@user.route("/profile/<int:user_id>", methods=['GET', 'POST', 'PUT'])
@jwt_required()
def user_profile(user_id):
    identity = get_jwt_identity()
    logged_in_user = User.query.filter_by(email=identity).first()

    if not logged_in_user or logged_in_user.id != user_id:
        if request.is_json:
            return jsonify({'message': 'You do not have permission to view this profile.'}), 403
        flash("You do not have permission to view this profile.", "danger")
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        if request.is_json:
            return jsonify({
                "data":{
                    'username': logged_in_user.username,
                    'email': logged_in_user.email,
                    'phone_number': logged_in_user.phone_number,
                    'created_at': logged_in_user.created_at
                },
                "message": 'Successfully GET data'
            })
        return render_template('user_profile.html', user=logged_in_user)
    
    elif request.method == 'POST':
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not check_password_hash(logged_in_user.password_hash, current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('user.user_profile', user_id=user_id))

        if email:
            logged_in_user.email = email
        if phone_number:
            logged_in_user.phone_number = phone_number
        if new_password:
            if new_password != confirm_new_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for('user.user_profile', user_id=user_id))
            logged_in_user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('user.user_profile', user_id=user_id))
    
    elif request.method == 'PUT' and request.is_json:       
        data = request.get_json()
        email = data.get('email')
        phone_number = data.get('phone_number')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')
        
        if not current_password:
            return jsonify({'message': 'Please enter your current password.'}), 400
        if not check_password_hash(logged_in_user.password_hash, current_password):
            return jsonify({'message': 'Current password is incorrect.'}), 403

        if email:
            logged_in_user.email = email
        if phone_number:
            logged_in_user.phone_number = phone_number
        if new_password:
            if new_password != confirm_new_password:
                return jsonify({'message': 'New passwords do not match.'}), 400
            logged_in_user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully.',
                        'data': {
                            'username': logged_in_user.username,
                            'email': logged_in_user.email,
                            'phone_number': logged_in_user.phone_number
                            }}), 200