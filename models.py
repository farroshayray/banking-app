from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(255), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.0)
    pin_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.Enum('withdrawal', 'transfer', 'deposit'), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def apply_transaction(self):
        if self.type == 'deposit' and self.to_account_id:
            to_account = Account.query.get(self.to_account_id)
            if to_account:
                print(f"Depositing {self.amount} to account {self.to_account_id}")
                to_account.balance += Decimal(self.amount)
                db.session.add(to_account)
                
        elif self.type == 'withdrawal' and self.from_account_id:
            from_account = Account.query.get(self.from_account_id)
            if from_account and from_account.balance >= Decimal(self.amount):
                print(f"Withdrawing {self.amount} from account {self.from_account_id}")
                from_account.balance -= Decimal(self.amount)
                db.session.add(from_account)
            else:
                raise ValueError('Insufficient funds')
        
        elif self.type == 'transfer':
            from_account = Account.query.get(self.from_account_id)
            to_account = Account.query.get(self.to_account_id)

            if from_account and to_account:
                if from_account.balance >= Decimal(self.amount):
                    print(f"Transferring {self.amount} from {self.from_account_id} to {self.to_account_id}")
                    from_account.balance -= Decimal(self.amount)
                    to_account.balance += Decimal(self.amount)
                    db.session.add(from_account)
                    db.session.add(to_account)
                else:
                    raise ValueError("Insufficient funds for transfer")
        print('wadaaaw')
            
        # db.session.add(self)
        db.session.commit()
            