import psycopg2
from queries.utils import decimal_to_float as d2f

class Auth:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='postgres',
        user='postgres',
        password='2357'
    )

    def register(self, username, password, email):
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