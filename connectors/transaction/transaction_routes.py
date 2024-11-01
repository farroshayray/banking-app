from . import transaction
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Account, Transaction, db
from werkzeug.security import check_password_hash
from decimal import Decimal
from sqlalchemy import or_

@transaction.app_template_filter('currency')
def currency_format(value):
    return f"Rp. {value:,.0f},-"

@transaction.route('/', methods=['GET'])
@jwt_required()
def transaction_page():
    return render_template('transaction.html')

@transaction.route('transaction_detail/<int:account_id>/<int:transaction_id>', methods=['GET'])
@jwt_required()
def transaction_detail(account_id, transaction_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first()
    account = Account.query.filter_by(id=account_id).first()
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    transfer_to = Account.query.filter_by(id=transaction.to_account_id).first()
    transfer_from = Account.query.filter_by(id=transaction.from_account_id).first()
    transfer_from_user = User.query.filter_by(id=transfer_from.user_id).first() if transfer_from else None
    transfer_to_user = User.query.filter_by(id=transfer_to.user_id).first() if transfer_to else None
    return render_template('transaction_detail.html', user=user, account=account, transaction=transaction, transfer_from_user=transfer_from_user, transfer_from=transfer_from, transfer_to=transfer_to, transfer_to_user=transfer_to_user)

@transaction.route('/transaction_list/<int:account_id>', methods=['GET'])
@jwt_required()
def transaction_list(account_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first()
    username = user.username if user else None
    account = Account.query.filter_by(id=account_id).first()

    if not account:
        if request.is_json:
            return jsonify({'message': 'Invalid account'}), 400
        flash('Invalid account', 'danger')
        return render_template('transaction.html', username=username, account=account)

    if account.user_id != user.id:
        if request.is_json:
            return jsonify({'message': 'You do not have permission to view transactions for this account.'}), 403
        flash("You do not have permission to view transactions for this account.", "danger")
        return redirect(url_for('home'))

    transactions = Transaction.query.filter(
        or_(
            Transaction.from_account_id == account_id,
            Transaction.to_account_id == account_id
        )
    ).all()

    if request.is_json:
        return jsonify({
            'transactions': [
                {
                    'id': transaction.id,
                    'type': transaction.type,
                    'amount': float(transaction.amount),
                    'description': transaction.description,
                    'from_account_id': transaction.from_account_id,
                    'to_account_id': transaction.to_account_id,
                    'created_at': transaction.created_at
                }
                for transaction in transactions
            ]
        })

    return render_template('transaction_list.html', username=username, account=account, transactions=transactions)

@transaction.route('/make_transaction/<int:account_id>', methods=['GET','POST'])
@jwt_required()
def make_transaction(account_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first() if identity else None
    username = user.username if user else None
    account = Account.query.filter_by(id=account_id).first()
    from_account_number = account.account_number if account else None
    
    # get all transactions by account id
    get_transactions = Transaction.query.filter(
        or_(
            Transaction.from_account_id == account_id,
            Transaction.to_account_id == account_id
        )
    ).all()

    if request.is_json:
        return jsonify({
            'transactions': [
                {
                    'id': get_transaction.id,
                    'type': get_transaction.type,
                    'amount': float(get_transaction.amount),
                    'description': get_transaction.description,
                    'from_account_id': get_transaction.from_account_id,
                    'to_account_id': get_transaction.to_account_id,
                    'created_at': get_transaction.created_at
                }
                for get_transaction in get_transactions
            ]
        })
    
    if not account:
        if request.is_json:
            return jsonify({'message': 'Invalid account'}), 400
        flash('Invalid account', 'danger')
        return render_template('transaction.html', username=username, account=account)

    if not account.user_id:
        if request.is_json:
            return jsonify({'message': 'Account not found'}), 404
        flash('Account not found', 'danger')
        return render_template('transaction.html', username=username, account=account)
    
    if account.user_id != user.id:
        if request.is_json:
            return jsonify({'message': 'You do not have permission to make a transaction for this account.'}), 403
        flash("You do not have permission to make a transaction for this account.", "danger")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            from_account_id = account.id
            to_account_number = str(data.get('to_account_number'))
            amount = data.get('amount')
            description = data.get('description')
            type = data.get('type').lower()
            account_pin = data.get('account_pin')
        else:
            from_account_id = account.id
            to_account_number = request.form.get('to_account_number')
            amount = request.form.get('amount')
            description = request.form.get('description')
            type = request.form.get('type')
            account_pin = request.form.get('account_pin')
        
        to_account_id = None
        
        if check_password_hash(account.pin_hash, account_pin):
            if type == 'transfer':
                to_account = Account.query.filter_by(account_number=to_account_number).first()
                if not to_account:
                    if request.is_json:
                        return jsonify({'message': 'Invalid recipient account'}), 400
                    flash('Invalid recipient account', 'danger')
                    return render_template('transaction.html', username=username, account=account)
                to_account_id = to_account.id
                
                if float(amount) > account.balance:
                    if request.is_json:
                        return jsonify({'message': 'Insufficient funds'}), 400
                    flash('Insufficient funds', 'danger')
                    return render_template('transaction.html', username=username, account=account)
            
            if type == 'withdrawal':
                if float(amount) > account.balance:
                    if request.is_json:
                        return jsonify({'message': 'Insufficient funds'}), 400
                    flash('Insufficient funds', 'danger')
                    return render_template('transaction.html', username=username, account=account)

            
            if type == 'deposit':
                if float(amount) <= 0:
                    if request.is_json:
                        return jsonify({'message': 'Invalid amount'}), 400
                    flash('Invalid amount', 'danger')
                    return render_template('transaction.html', username=username, account=account)
                from_account_id = None
                from_account_number = None
                to_account = Account.query.filter_by(id=account.id).first()
                to_account_id = account.id
                    
            
            try:
                amount = float(amount)
                if amount <= 0:
                    if request.is_json:
                        return jsonify({'message': 'Invalid amount'}), 400
                    flash('Invalid amount', 'danger')
            except ValueError:
                if request.is_json:
                    return jsonify({'message': 'Invalid amount'}), 400
                flash('Invalid amount', 'danger')
                return render_template('transaction.html', username=username, account=account)
            
            transaction = Transaction(
                from_account_id=from_account_id, 
                to_account_id=to_account_id, 
                amount=amount, 
                description=description, 
                type=type
            )
            
            to_user = User.query.filter_by(id=to_account.user_id).first() if to_account_id else None
            to_user_name = to_user.username if to_user else None
            
            db.session.add(transaction)
            try:
                transaction.apply_transaction()
                db.session.commit()
                if request.is_json:
                    return jsonify({
                    'message': 'Transaction successful!',
                    'data': {
                        'transfer_to': to_account_number if to_account_id else 'N/A',
                        'transfer_from': from_account_number,
                        'amount': amount,
                        'description': description,
                        'type': type,
                        'created_at': transaction.created_at,
                        'id': transaction.id,
                        'to_user_name': to_user_name
                    }
                }), 200
            
                flash('Transaction successful!')
                return render_template('transaction.html', username=username, account=account)
            except ValueError as e:
                db.session.rollback()
                if request.is_json:
                    return jsonify({'message': str(e)}), 400
                flash(str(e), 'danger')
                return render_template('transaction.html', username=username, account=account)

        else:
            if request.is_json:
                return jsonify({'message': 'Invalid account pin'}), 403
            flash('invalid credentials!', 'danger')
        
        if request.is_json:
            return jsonify({'message': 'Invalid account pin'}), 403
        flash('invalid credentials!', 'danger')
    
    return render_template('transaction.html', username=username, account=account, get_transactions=get_transactions)
