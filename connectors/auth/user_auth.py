from . import auth
from flask import Flask, request, flash, make_response, render_template, jsonify, redirect, url_for
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, unset_jwt_cookies, jwt_required, get_jwt_identity

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            phone_number = data.get('phone_number', '').strip()
            password = data.get('password', '').strip()
            repassword = data.get('repassword', '').strip()
        else:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            password = request.form.get('password', '').strip()
            repassword = request.form.get('repassword', '').strip()

        if not all([username, email, password, repassword, phone_number]):
            return jsonify({'message': 'All fields are required!'}), 400

        if password != repassword:
            if request.is_json:
                return jsonify({'message': 'Passwords do not match!'}), 400
            flash('Please input the same password', 'danger')
            return make_response(render_template('register.html')), 400
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'message': 'Email already exists!'}), 400
            flash('Email already exists', 'danger')
            return make_response(render_template('register.html')), 400
        
        if User.query.filter_by(phone_number=phone_number).first():
            if request.is_json:
                return jsonify({'message': 'Phone number already exists!'}), 400
            flash('Phone number already exists', 'danger')
            return make_response(render_template('register.html')), 400
                

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, email=email, password_hash=hashed_password, phone_number=phone_number)

        db.session.add(user)
        db.session.commit()

        if request.is_json:
            return jsonify({
                'data': {'username': user.username, 'email': user.email},
                'message': 'User registered successfully!'
            }), 201

        flash('User registered successfully!', 'success')
        return redirect(url_for('auth.login'))

    return make_response(render_template('register.html')), 200


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

        if not email or not password:
            return jsonify({'message': 'Email and password are required!'}), 400

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=email)
            if request.is_json:
                return jsonify({
                    'access_token': access_token,
                    'user': {'username':user.username, 'email': user.email, 'id': user.id},
                    'message': 'Login successful!'
                }), 200
            
            response = make_response(redirect(url_for('home')))
            response.set_cookie('access_token_cookie', access_token, httponly=True)
            return response

        if request.is_json:
            return jsonify({'message': 'Invalid credentials!'}), 403
        flash('Invalid credentials!', 'danger')
    return make_response(render_template('login.html')), 200

@auth.route('/logout')
@jwt_required()
def logout():
    response = jsonify({'message': 'Logout successful!'})

    unset_jwt_cookies(response)

    if not request.is_json:
        flash("You have been logged out.", "success")
        response = make_response(redirect(url_for('home')))
        response.set_cookie('access_token_cookie', '', expires=0)
    return response