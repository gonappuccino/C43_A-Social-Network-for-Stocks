import os
import csv
import psycopg2
create_users = '''
    CREATE TABLE IF NOT EXISTS Users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''

create_friend_requests = '''
    CREATE TABLE IF NOT EXISTS FriendRequest (
        request_id SERIAL PRIMARY KEY,
        sender_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        receiver_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        status VARCHAR(20) CHECK (status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (sender_id, receiver_id)
    );
    '''

# Combines StockLists and Created
create_stock_lists = '''
    CREATE TABLE IF NOT EXISTS StockLists (
        stocklist_id SERIAL PRIMARY KEY,
        list_name VARCHAR(100) NOT NULL,
        creator_id INT REFERENCES Users(user_id) ON DELETE CASCADE,      -- Owner of this list
        is_public BOOLEAN DEFAULT FALSE,               -- If True, all users can see it
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''

create_stock_list_access = '''
    CREATE TABLE IF NOT EXISTS StockListAccess (
        access_id SERIAL PRIMARY KEY,
        stocklist_id INT REFERENCES StockLists(stocklist_id) ON DELETE CASCADE,
        user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,       -- User who can access this list
        access_role VARCHAR(20) CHECK (access_role IN ('owner', 'shared')),
        UNIQUE (stocklist_id, user_id)
    );
    '''

# Stocks should reference the stock history table
create_stocks = '''
    CREATE TABLE IF NOT EXISTS Stocks (
        symbol VARCHAR(5) PRIMARY KEY
    );
    '''


create_stock_list_stocks = '''
    CREATE TABLE IF NOT EXISTS StockListStocks (
        list_entry_id SERIAL PRIMARY KEY,
        stocklist_id INT REFERENCES StockLists(stocklist_id) ON DELETE CASCADE,
        symbol VARCHAR(10) REFERENCES Stocks(symbol) ON DELETE CASCADE,
        num_shares INT NOT NULL,
        UNIQUE (stocklist_id, symbol)
    );
'''

# Combines portfolios and user_portfolios tables as portfolios itself it redundant
create_portfolios = '''
    CREATE TABLE IF NOT EXISTS Portfolios (
        portfolio_id SERIAL PRIMARY KEY,
        portfolio_name VARCHAR(100) NOT NULL,
        user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        cash_balance DECIMAL(15,2) DEFAULT 0.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
'''

create_portfolio_stocks = '''
    CREATE TABLE IF NOT EXISTS PortfolioStocks (
        portfolio_entry_id SERIAL PRIMARY KEY,
        portfolio_id INT REFERENCES Portfolios(portfolio_id) ON DELETE CASCADE,
        symbol VARCHAR(10) REFERENCES Stocks(symbol) ON DELETE CASCADE,
        num_shares INT NOT NULL,
        UNIQUE (portfolio_id, symbol)
    );
''' 

create_portfolio_transactions = '''
    CREATE TABLE IF NOT EXISTS PortfolioTransactions (
        transaction_id SERIAL PRIMARY KEY,
        portfolio_id INT REFERENCES Portfolios(portfolio_id) ON DELETE CASCADE,
        symbol VARCHAR(10) REFERENCES Stocks(symbol) ON DELETE CASCADE,
        transaction_type VARCHAR(4) CHECK (transaction_type IN ('BUY', 'SELL', 'CASH')),
        shares INT NOT NULL,
        price NUMERIC(15,2) NOT NULL,        -- price per share
        cash_change NUMERIC(15,2) NOT NULL,  -- total cash impact (+ or -)
        transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
'''

create_reviews = '''
    CREATE TABLE IF NOT EXISTS Reviews (
        review_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        stocklist_id INT REFERENCES StockLists(stocklist_id) ON DELETE CASCADE,
        review_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, stocklist_id)
    );
    '''

create_stock_history = '''CREATE TABLE IF NOT EXISTS StocksHistory (
    timestamp DATE, 
    open REAL,
    high REAL, 
    low REAL, 
    close REAL, 
    volume INT, 
    symbol VARCHAR(5),
    PRIMARY KEY(symbol, timestamp)
    );
    '''

create_daily_stock_info = '''
    CREATE TABLE IF NOT EXISTS DailyStockInfo (
        timestamp DATE,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INT,
        symbol VARCHAR(5),
        PRIMARY KEY (symbol, timestamp)
    );
'''

load_stock_history_from_csv = '''COPY StocksHistory(timestamp, open, high,low, close, volume, symbol) 
    FROM 'data/pg17/data/sp500history.csv' DELIMITER ',' CSV HEADER;
'''

def load_stock_history_from_local(conn):
    """
    Load stock history data from a local CSV file and insert it into the database
    """
    cursor = conn.cursor()
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            '../data', 'SP500History.csv')
    
    print(f"Reading CSV from local path: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return False
    
    # Count for progress reporting
    row_count = 0
    success_count = 0
    
    try:
        # Read and insert data row by row
        with open(csv_path, 'r') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)  # Skip header row
            
            for row in csv_reader:
                row_count += 1
                
                if len(row) != 7:
                    print(f"⚠️ Skipping invalid row {row_count}: {row}")
                    continue
                
                timestamp, open_price, high, low, close, volume, symbol = row
                open_price = float(open_price) ; high = float(high) ; low = float(low) ; close = float(close) ; volume = int(volume)

                try:
                    insert_query = """
                        INSERT INTO StocksHistory(timestamp, open, high, low, close, volume, symbol)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timestamp) DO NOTHING;
                    """
                    cursor.execute(insert_query, (timestamp, open_price, high, low, close, volume, symbol))
                    success_count += 1
                    
                    # Commit periodically to avoid huge transactions
                    if success_count % 1000 == 0:
                        conn.commit()
                        print(f"✅ Processed {success_count} rows...")
                        
                except psycopg2.Error as e:
                    conn.rollback()
                    print(f"⚠️ Error inserting row {row_count}: {e}")
        
        # Final commit
        conn.commit()
        
        print(f"✅ Successfully loaded {success_count} out of {row_count} rows")
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Failed to load stock history: {e}")
        return False
    finally:
        cursor.close()


def load_stock_history_from_local_fast(conn):
    """
    Load stock history data from a local CSV file using efficient batching
    """
    cursor = conn.cursor()
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            '..\data', 'SP500History.csv')
    
    print(f"Reading CSV from local path: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return False
    
    try:

        with open(csv_path, 'r') as f:
            # first row is header
            next(f)
            
            cursor.copy_from(
                file=f,
                table='stockshistory', #for some reason this needs to be lower case
                sep=',',
                columns=('timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol'), 
                null=''
            )
        
        conn.commit()
        print(f"✅ Successfully loaded stock history data")
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Failed to load stock history: {e}")
    finally:
        cursor.close()


# Now copy symbols from StocksHistory to Stocks + spy for stock analytics 
copy_symbols = '''
    INSERT INTO Stocks (symbol)
    (SELECT DISTINCT symbol
    FROM StocksHistory)
    UNION
    (SELECT 'SPY' AS symbol)
    ON CONFLICT (symbol) DO NOTHING;
'''



setup_queries = [
    create_users,
    create_friend_requests,
    create_stock_history,
    create_stocks,
    create_stock_lists,
    create_stock_list_access,
    create_stock_list_stocks,
    create_portfolios,
    create_portfolio_stocks,
    create_portfolio_transactions,
    create_reviews,
    create_daily_stock_info,
]
