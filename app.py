from flask import Flask, jsonify, render_template, make_response, redirect, url_for, flash, request
from models import db, User, Account, Transaction
from config import Config
from connectors.auth import auth as auth_blueprint
from connectors.account import account as account_blueprint
from connectors.user import user as user_blueprint
from connectors.transaction import transaction as transaction_blueprint
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, unset_jwt_cookies
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(account_blueprint, url_prefix='/account')
app.register_blueprint(user_blueprint,url_prefix='/user')
app.register_blueprint(transaction_blueprint,url_prefix='/transaction')

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    if request.is_json:
        response = jsonify({"msg": "Token has expired"})
        unset_jwt_cookies(response)
        return response, 401
    else:
        flash("Your session has expired. Please log in again.", "warning")
        response = make_response(redirect(url_for('auth.login')))
        unset_jwt_cookies(response)
        return response
    
@jwt.unauthorized_loader
def missing_jwt_callback(error):
    if request.is_json:
        return jsonify({"msg": "unauthorized, please login first"}), 401
    else:
        return render_template('unauthorized.html'), 401
    
@app.errorhandler(403)
def forbidden_error_handler(error):
    if request.is_json:
        return jsonify({"message": "forbidden, please login as Admin"}), 403
    else:
        return render_template('forbidden.html'), 403

@app.route("/")
@jwt_required(optional=True)
def home():
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first() if identity else None
    username = user.username if user else None
    accounts = Account.query.filter_by(user_id=user.id).all() if user else None
    print(user)
    if request.is_json:
        return jsonify({'message': 'welcome to Ros Bank'})
    return render_template('home.html', username=username, accounts=accounts)

if __name__ == "__main__":
    app.run(debug=True)