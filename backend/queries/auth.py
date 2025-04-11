import psycopg2
from queries.utils import decimal_to_float as d2f
import re
class Auth:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )

    def register(self, username, password, email):
        # Verify username, password and email are valid
        if not username or len(username) == 0:
            return False
        if not password or len(password) == 0:
            return False
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        
        # Check if username and email are unique
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=%s OR email=%s", (username, email))
        if cursor.fetchone():
            cursor.close()
            return False
        
        cursor.execute("INSERT INTO Users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
        self.conn.commit()
        cursor.close()
        return True

    def login(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE email=%s AND password=%s", (email, password))
        user_id = cursor.fetchone()
        cursor.close()
        return user_id
    
    def logout(self):
        return True

    def delete_account(self, user_id):

        try:
            cursor = self.conn.cursor()
            # Delete the user (cascade will handle related data)
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except psycopg2.Error as e:
            print(f"Error deleting account: {e}")
            self.conn.rollback()
            return False 