import psycopg2
import hashlib
import time
import os
import base64
# Define password hashing and verification directly in the User class

class User:
    def __init__(self):
        from flask import current_app
        self.app = current_app
    
    # Password hashing utility functions
    def hash_password(self, password):
        """Hash a password for storing"""
        salt = os.urandom(32)  # A new salt for this user
        key = hashlib.pbkdf2_hmac(
            'sha256',  # The hash digest algorithm
            password.encode('utf-8'),  # Convert the password to bytes
            salt,  # Salt
            100000  # 100,000 iterations
        )
        # Store the salt and key together
        return base64.b64encode(salt + key).decode('utf-8')
    
    def verify_password(self, provided_password, stored_password):
        """Verify a stored password against one provided by user"""
        try:
            # Convert the stored password from base64 to bytes
            stored_bytes = base64.b64decode(stored_password.encode('utf-8'))
            # Extract salt (first 32 bytes)
            salt = stored_bytes[:32]
            # Extract the stored key (remaining bytes)
            stored_key = stored_bytes[32:]
            
            # Hash the provided password with the extracted salt
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt,
                100000
            )
            
            # Compare the keys
            return new_key == stored_key
        except Exception as e:
            print(f"Error verifying password: {e}")
            # If there's an error (e.g., invalid base64), safely return False
            return False

    def register(self, username, password, email):
        """Register a new user"""
        try:
            from flask import current_app
            conn = psycopg2.connect(
                host=current_app.config['POSTGRES_HOST'],
                database=current_app.config['POSTGRES_DB'],
                user=current_app.config['POSTGRES_USER'],
                password=current_app.config['POSTGRES_PASSWORD']
            )
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT user_id FROM Users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                return False
            
            # Hash the password
            hashed_password = self.hash_password(password)
            
            # Insert new user
            cursor.execute(
                "INSERT INTO Users (username, password, email) VALUES (%s, %s, %s) RETURNING user_id",
                (username, hashed_password, email)
            )
            user_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error registering user: {e}")
            return False

    def login(self, email, password):
        """Login a user and return user_id if successful"""
        try:
            from flask import current_app
            conn = psycopg2.connect(
                host=current_app.config['POSTGRES_HOST'],
                database=current_app.config['POSTGRES_DB'],
                user=current_app.config['POSTGRES_USER'],
                password=current_app.config['POSTGRES_PASSWORD']
            )
            cursor = conn.cursor()
            
            # Get user by email
            cursor.execute("SELECT user_id, password FROM Users WHERE email = %s", (email,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                return None
                
            user_id, stored_password = result
            
            # Verify password
            if self.verify_password(password, stored_password):
                cursor.close()
                conn.close()
                return user_id
                
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error logging in: {e}")
            return None
    
    # Portfolio methods - delegated to imported functions
    def create_portfolio(self, user_id, initial_cash=0):
        try:
            from .portfolio import create_portfolio
            return create_portfolio(user_id, initial_cash)
        except Exception as e:
            print(f"Error creating portfolio: {e}")
            return None
        
    def delete_portfolio(self, portfolio_id):
        try:
            from .portfolio import delete_portfolio
            return delete_portfolio(portfolio_id)
        except Exception as e:
            print(f"Error deleting portfolio: {e}")
            return None
        
    def update_cash_balance(self, portfolio_id, amount):
        try:
            from .portfolio import update_cash_balance
            return update_cash_balance(portfolio_id, amount)
        except Exception as e:
            print(f"Error updating cash balance: {e}")
            return None
        
    def buy_stock_shares(self, portfolio_id, symbol, num_shares):
        try:
            from .portfolio import buy_stock_shares
            return buy_stock_shares(portfolio_id, symbol, num_shares)
        except Exception as e:
            print(f"Error buying stock shares: {e}")
            return False
        
    def sell_stock_shares(self, portfolio_id, symbol, num_shares):
        try:
            from .portfolio import sell_stock_shares
            return sell_stock_shares(portfolio_id, symbol, num_shares)
        except Exception as e:
            print(f"Error selling stock shares: {e}")
            return False
        
    def view_portfolio(self, portfolio_id):
        try:
            from .portfolio import view_portfolio
            return view_portfolio(portfolio_id)
        except Exception as e:
            print(f"Error viewing portfolio: {e}")
            return {}
        
    def view_portfolio_transactions(self, portfolio_id):
        try:
            from .portfolio import view_portfolio_transactions
            return view_portfolio_transactions(portfolio_id)
        except Exception as e:
            print(f"Error viewing portfolio transactions: {e}")
            return []
    
    # Stock list methods - delegated to imported functions
    def create_stock_list(self, creator_id, is_public=False):
        try:
            from .stock_list import create_stock_list
            return create_stock_list(creator_id, is_public)
        except Exception as e:
            print(f"Error creating stock list: {e}")
            return None
        
    def delete_stock_list(self, stocklist_id):
        try:
            from .stock_list import delete_stock_list
            return delete_stock_list(stocklist_id)
        except Exception as e:
            print(f"Error deleting stock list: {e}")
            return None
        
    def add_stock_to_list(self, stocklist_id, symbol, num_shares):
        try:
            from .stock_list import add_stock_to_list
            return add_stock_to_list(stocklist_id, symbol, num_shares)
        except Exception as e:
            print(f"Error adding stock to list: {e}")
            return False
        
    def remove_stock_from_list(self, stocklist_id, symbol, num_shares):
        try:
            from .stock_list import remove_stock_from_list
            return remove_stock_from_list(stocklist_id, symbol, num_shares)
        except Exception as e:
            print(f"Error removing stock from list: {e}")
            return False
        
    def view_stock_list(self, stocklist_id):
        try:
            from .stock_list import view_stock_list
            return view_stock_list(stocklist_id)
        except Exception as e:
            print(f"Error viewing stock list: {e}")
            return {}
    
    # Friend methods - delegated to imported functions
    def send_friend_request(self, sender_id, receiver_id):
        try:
            from .friends import send_friend_request
            return send_friend_request(sender_id, receiver_id)
        except Exception as e:
            print(f"Error sending friend request: {e}")
            return False
        
    def view_friends(self, user_id):
        try:
            from .friends import view_friends
            return view_friends(user_id)
        except Exception as e:
            print(f"Error viewing friends: {e}")
            return []
        
    def view_incoming_requests(self, user_id):
        try:
            from .friends import view_incoming_requests
            return view_incoming_requests(user_id)
        except Exception as e:
            print(f"Error viewing incoming requests: {e}")
            return []
        
    def view_outgoing_requests(self, user_id):
        try:
            from .friends import view_outgoing_requests
            return view_outgoing_requests(user_id)
        except Exception as e:
            print(f"Error viewing outgoing requests: {e}")
            return []
        
    def accept_friend_request(self, request_id):
        try:
            from .friends import accept_friend_request
            return accept_friend_request(request_id)
        except Exception as e:
            print(f"Error accepting friend request: {e}")
            return False
        
    def reject_friend_request(self, request_id):
        try:
            from .friends import reject_friend_request
            return reject_friend_request(request_id)
        except Exception as e:
            print(f"Error rejecting friend request: {e}")
            return False
        
    def delete_friend(self, user_id, friend_id):
        try:
            from .friends import delete_friend
            return delete_friend(user_id, friend_id)
        except Exception as e:
            print(f"Error deleting friend: {e}")
            return False
        
    def share_stock_list(self, stocklist_id, owner_id, friend_id):
        try:
            from .friends import share_stock_list
            return share_stock_list(stocklist_id, owner_id, friend_id)
        except Exception as e:
            print(f"Error sharing stock list: {e}")
            return False
        
    def view_accessible_stock_lists(self, user_id):
        try:
            from .friends import view_accessible_stock_lists
            return view_accessible_stock_lists(user_id)
        except Exception as e:
            print(f"Error viewing accessible stock lists: {e}")
            return []
    
    # Review methods - delegated to imported functions
    def create_review(self, user_id, stocklist_id, review_text):
        try:
            from .reviews import create_review
            return create_review(user_id, stocklist_id, review_text)
        except Exception as e:
            print(f"Error creating review: {e}")
            return None
        
    def update_review(self, review_id, user_id, new_text):
        try:
            from .reviews import update_review
            return update_review(review_id, user_id, new_text)
        except Exception as e:
            print(f"Error updating review: {e}")
            return False
        
    def delete_review(self, review_id, user_id):
        try:
            from .reviews import delete_review
            return delete_review(review_id, user_id)
        except Exception as e:
            print(f"Error deleting review: {e}")
            return False
        
    def view_reviews(self, stocklist_id, user_id):
        try:
            from .reviews import view_reviews
            return view_reviews(stocklist_id, user_id)
        except Exception as e:
            print(f"Error viewing reviews: {e}")
            return [] 