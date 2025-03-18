import psycopg2
from queries.setup import setup_queries
from flask import Flask, request

app = Flask(__name__)

app.config['POSTGRES_HOST'] = 'localhost'
app.config['POSTGRES_DB'] = 'postgres'
app.config['POSTGRES_USER'] = 'postgres'
app.config['POSTGRES_PASSWORD'] = '2357'

try:
    conn = psycopg2.connect(
        host=app.config['POSTGRES_HOST'],
        database=app.config['POSTGRES_DB'],
        user=app.config['POSTGRES_USER'],
        password=app.config['POSTGRES_PASSWORD']
    )
    print("✅ Connected to PostgreSQL!")

except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")

def setup_db(conn):
    try:
        cursor = conn.cursor()
        for query in setup_queries:
            cursor.execute(query)
        conn.commit()
        cursor.close()

        print("✅ Database setup complete!")

    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")

@app.route('/register', methods=['POST'])
def register():
    print(request.json)
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']


@app.route('/login', methods=['POST'])
def login():
    # Check if user exists in Users table
    # Return user_id
    pass
    

if __name__ == '__main__':
    setup_db(conn)
