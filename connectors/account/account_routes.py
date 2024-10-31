from . import account
import random
from flask import render_template, request, flash, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db, Account, User
from werkzeug.security import generate_password_hash, check_password_hash

@account.route("/", methods=['GET'])
@jwt_required()
def account_page():
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first() if identity else None
    username = user.username if user else None
    accounts = Account.query.filter_by(user_id=user.id).all() if user else None
    return render_template('account.html', username=username, accounts=accounts)

@account.route("/create_account", methods=['GET', 'POST'])
@jwt_required()
def create_account():
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first() if identity else None
    username = user.username if user else None

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        account_name = data.get('account_name', '').strip()
        account_type = data.get('account_type', '').strip()
        pin_hash = data.get('pin_hash', '').strip()
        repin_hash = data.get('repin_hash', '').strip()
        
        if not account_name or not account_type or not pin_hash or not repin_hash:
            return jsonify({'message': 'All fields are required'}), 400
        
        if len(pin_hash) != 6 or len(repin_hash) != 6 or not pin_hash.isdigit() or not repin_hash.isdigit():
            return jsonify({'message': 'PIN must be 6 digits and numeric only'}), 400
        
        if pin_hash != repin_hash:
            if request.is_json:
                return jsonify({'message': 'PINs do not match'}), 400
            flash('PINs do not match')
            return render_template('create_account.html', username=username)
            
        
        hashed_pin = generate_password_hash(pin_hash)
        
        account_number = None
        while True:
            account_number = str(random.randint(1000000000, 9999999999))  # Generate 10-digit number
            existing_account = Account.query.filter_by(account_number=account_number).first()
            if not existing_account:
                break 
        
        new_account = Account(
            user_id=user.id,
            account_name=account_name,
            account_type=account_type,
            account_number=account_number,
            pin_hash=hashed_pin,
        )
        db.session.add(new_account)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'message': 'Account created successfully!',
                'account_number': account_number,
                'account_type': account_type,
                'account_name': account_name
            }), 201

        flash('Account created successfully!')
        return redirect(url_for('account.account_page'))
    
    return render_template('create_account.html', username=username)

@account.route("/account_detail/<int:account_id>", methods=['GET','POST','PUT'])
@jwt_required()
def account_detail(account_id):
    identity = get_jwt_identity()
    logged_in_user = User.query.filter_by(email=identity).first()
    account = Account.query.filter_by(id=account_id).first()
    if not logged_in_user or logged_in_user.id != account.user_id:
        if request.is_json:
            return jsonify({'message': 'You do not have permission to view this account.'}), 403
        flash("You do not have permission to view this account.", "danger")
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        if request.is_json:
            return jsonify({
                "data": {
                    "account_number": account.account_number,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "balance": account.balance
                },
                "message": "GET account data success"
            })
        return render_template('account_detail.html', account=account)
    
    elif request.method == 'POST':
        account_name = request.form.get('account_name')
        current_pin = request.form.get('current_pin')
        new_pin = request.form.get('new_pin')
        confirm_new_pin = request.form.get('confirm_new_pin')
        
        if not check_password_hash(account.pin_hash, current_pin):
            if request.is_json:
                return jsonify({'message': 'Current PIN is incorrect.'}), 400
            flash('Current PIN is incorrect.', 'danger')
            return redirect(url_for('account.account_detail', account_id=account_id))
        
        if account_name:
            account.account_name = account_name
        
        if new_pin:
            if new_pin != confirm_new_pin:
                if request.is_json:
                    return jsonify({'message': 'New PINs do not match.'}), 400
                flash('New PINs do not match.', 'danger')
                return redirect(url_for('account.account_detail', account_id=account_id))

            if len(new_pin) != 6 or not new_pin.isdigit():
                if request.is_json:
                    return jsonify({'message': 'New PIN must be 6 digits and numeric only.'}), 400
                flash('New PIN must be 6 digits and numeric only.', 'danger')
                return redirect(url_for('account.account_detail', account_id=account_id))

            account.pin_hash = generate_password_hash(new_pin)

        db.session.commit()
               
        if request.is_json:
            return jsonify({
                'message': 'Account details updated successfully!',
                'account_name': account.account_name
            }), 201

        flash('Account details updated successfully!', 'success')
        return redirect(url_for('account.account_detail', account_id=account_id))
    
    if request.method == 'PUT' and request.is_json:
        data = request.get_json()
        account_name = data.get('account_name')
        current_pin = data.get('current_pin')
        new_pin = data.get('new_pin')
        confirm_new_pin = data.get('confirm_new_pin')
        
        if not current_pin:
            return jsonify({'message': 'Current PIN is required.'}), 400

        if not check_password_hash(account.pin_hash, current_pin):
            return jsonify({'message': 'Current PIN is incorrect.'}), 400

        if account_name:
            account.account_name = account_name

        if new_pin:
            if new_pin != confirm_new_pin:
                return jsonify({'message': 'New PINs do not match.'}), 400

            if len(new_pin) != 6 or not new_pin.isdigit():
                return jsonify({'message': 'New PIN must be 6 digits and numeric only.'}), 400

            account.pin_hash = generate_password_hash(new_pin)

        db.session.commit()

        return jsonify({
            'message': 'Account details updated successfully!',
            'account_name': account.account_name,
            'account_number': account.account_number
        }), 201
        
@account.route('/account_detail/delete/<int:account_id>', methods=['POST', 'DELETE'])
@jwt_required()
def delete_account(account_id):
    identity = get_jwt_identity()
    logged_in_user = User.query.filter_by(email=identity).first()
    account = Account.query.filter_by(id=account_id).first()
    if not logged_in_user or logged_in_user.id != account.user_id:
        if request.is_json:
            return jsonify({'message': 'You do not have permission to delete this account.'}), 403
        flash("You do not have permission to delete this account.", "danger")
        return redirect(url_for('home'))
    db.session.delete(account)
    db.session.commit()
    if request.is_json:
        return jsonify({'message': 'Account deleted successfully!'}), 200
    return redirect(url_for('account.account_page'))

@account.route('/account_detail/confirm_delete/<int:account_id>', methods=['GET', 'POST'])
@jwt_required()
def confirm_delete_account(account_id):
    identity = get_jwt_identity()
    logged_in_user = User.query.filter_by(email=identity).first()
    account = Account.query.filter_by(id=account_id).first()

    if not logged_in_user or logged_in_user.id != account.user_id:
        flash("You do not have permission to delete this account.", "danger")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        pin = request.form.get('pin_hash', '').strip()
        
        if not check_password_hash(account.pin_hash, pin):
            flash("Incorrect PIN. Please try again.", "danger")
            return redirect(url_for('account.confirm_delete_account', account_id=account_id))
        
        if account.balance >= 50000:
            flash("Cannot delete account with balance more than Rp. 50.000,-.", "danger")
            return redirect(url_for('account.confirm_delete_account', account_id=account_id))

        db.session.delete(account)
        db.session.commit()
        
        flash("Account deleted successfully!", "success")
        return redirect(url_for('account.account_page'))
    
    return render_template('confirm_delete_account.html', account=account)