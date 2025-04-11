import psycopg2
from queries.setup import (
    create_users, create_friend_requests, create_stock_lists, create_stock_list_access,
    create_stocks, create_stock_list_stocks, create_portfolios, create_portfolio_stocks,
    create_portfolio_transactions, create_reviews, create_stock_history, create_daily_stock_info
)

# Database connection parameters
DB_HOST = '34.130.75.185'
DB_NAME = 'template1'
DB_USER = 'postgres'
DB_PASSWORD = '2357'

def drop_tables(cursor):
    """Drop all tables in the correct order to respect foreign key constraints"""
    drop_queries = [
        "DROP TABLE IF EXISTS Reviews CASCADE;",
        "DROP TABLE IF EXISTS PortfolioTransactions CASCADE;",
        "DROP TABLE IF EXISTS PortfolioStocks CASCADE;",
        "DROP TABLE IF EXISTS Portfolios CASCADE;",
        "DROP TABLE IF EXISTS StockListStocks CASCADE;",
        "DROP TABLE IF EXISTS StockListAccess CASCADE;",
        "DROP TABLE IF EXISTS StockLists CASCADE;",
        "DROP TABLE IF EXISTS FriendRequest CASCADE;",
        "DROP TABLE IF EXISTS DailyStockInfo CASCADE;",
        "DROP TABLE IF EXISTS StocksHistory CASCADE;",
        "DROP TABLE IF EXISTS Stocks CASCADE;",
        "DROP TABLE IF EXISTS Users CASCADE;"
    ]
    
    for query in drop_queries:
        cursor.execute(query)

def create_tables(cursor):
    """Create all tables in the correct order"""
    create_queries = [
        create_users,
        create_friend_requests,
        create_stocks,
        create_stock_lists,
        create_stock_list_access,
        create_stock_list_stocks,
        create_portfolios,
        create_portfolio_stocks,
        create_portfolio_transactions,
        create_reviews,
        create_stock_history,
        create_daily_stock_info
    ]
    
    for query in create_queries:
        cursor.execute(query)

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print("Starting database reset")
        
        # Drop all tables
        print("Dropping all tables")
        drop_tables(cursor)
        
        # Create all tables
        print("Creating all tables")
        create_tables(cursor)
        
        # Commit the changes
        conn.commit()
        print("Database reset complete")
        
    except psycopg2.Error as e:
        print(f"Database reset failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_database() 