import psycopg2

DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "2357"  # Your password

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    print("✅ Connected to PostgreSQL!")
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")