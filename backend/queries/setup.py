
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
        user_id INT REFERENCES Users(user_id),      -- Owner of this list
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
        symbol VARCHAR(10) PRIMARY KEY
    );
    '''


create_stock_list_stocks = '''
    CREATE TABLE IF NOT EXISTS StockListStocks (
        list_entry_id SERIAL PRIMARY KEY,
        stocklist_id INT REFERENCES StockLists(stocklist_id),
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
        num_shares INT NOT NULL,
        UNIQUE (stocklist_id, symbol)
    );
'''

# Combines portfolios and user_portfolios tables as portfolios itself it redundant
create_portfolios = '''
    CREATE TABLE IF NOT EXISTS Portfolios (
        portfolio_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id),
        cash_balance DECIMAL(15,2) DEFAULT 0.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
'''

create_portfolio_stocks = '''
    CREATE TABLE IF NOT EXISTS PortfolioStocks (
        portfolio_entry_id SERIAL PRIMARY KEY,
        portfolio_id INT REFERENCES Portfolios(portfolio_id),
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
        num_shares INT NOT NULL,
        UNIQUE (portfolio_id, symbol)
    );
''' 

create_portfolio_transactions = '''
    CREATE TABLE IF NOT EXISTS PortfolioTransactions (
        transaction_id SERIAL PRIMARY KEY,
        portfolio_id INT REFERENCES Portfolios(portfolio_id) ON DELETE CASCADE,
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
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
        user_id INT REFERENCES Users(user_id),
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

load_stock_history_from_csv = '''COPY StocksHistory(timestamp, open, high,low, close, volume, symbol) 
    FROM '/data/SP500History.csv' DELIMITER ',' CSV HEADER;
'''

# Now copy symbols from StocksHistory to Stocks
copy_symbols = '''
    INSERT INTO Stocks (symbol)
    SELECT DISTINCT symbol
    FROM StocksHistory;
'''

create_daily_stock_info = '''
    CREATE TABLE IF NOT EXISTS DailyStockInfo (
        daily_info_id SERIAL PRIMARY KEY,
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
        date DATE NOT NULL DEFAULT CURRENT_DATE,
        open NUMERIC(15,2),
        high NUMERIC(15,2),
        low NUMERIC(15,2),
        close NUMERIC(15,2),
        volume INT
    );
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

    # Set up stock history and stocks table
    #load_stock_history_from_csv,
    #copy_symbols,
    create_daily_stock_info,
    
]