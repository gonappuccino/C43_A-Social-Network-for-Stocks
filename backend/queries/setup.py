
create_users = '''
    CREATE TABLE Users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''

create_friend_requests = '''
    CREATE TABLE FriendRequest (
        request_id SERIAL PRIMARY KEY,
        sender_id INT REFERENCES Users(user_id),
        receiver_id INT REFERENCES Users(user_id),
        status VARCHAR(20) CHECK (status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (sender_id, receiver_id)
    );
    '''

create_stock_lists = '''
    CREATE TABLE StockLists (
        stocklist_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id),
        is_public BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''

create_stocks = '''
    CREATE TABLE Stocks (
        symbol VARCHAR(10) PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    '''


create_stock_list_stocks = '''
    CREATE TABLE StockListStocks (
        list_entry_id SERIAL PRIMARY KEY,
        stocklist_id INT REFERENCES StockLists(stocklist_id),
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
        num_shares INT NOT NULL,
        UNIQUE (stocklist_id, symbol)
    );
'''

# Combines portfolios and user_portfolios tables as portfolios itself it redundant
create_portfolios = '''
    CREATE TABLE Portfolios (
        portfolio_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id),
        cash_balance DECIMAL(15,2) DEFAULT 0.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
'''

create_portfolio_stocks = '''
    CREATE TABLE PortfolioStocks (
        portfolio_entry_id SERIAL PRIMARY KEY,
        portfolio_id INT REFERENCES Portfolios(portfolio_id),
        symbol VARCHAR(10) REFERENCES Stocks(symbol),
        num_shares INT NOT NULL,
        UNIQUE (portfolio_id, symbol)
    );
''' 

create_reviews = '''
    CREATE TABLE Reviews (
        review_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id),
        stocklist_id INT REFERENCES StockLists(stocklist_id),
        review_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''

setup_queries = [
    create_users,
    create_friend_requests,
    create_stock_lists,
    create_stocks,
    create_stock_list_stocks,
    create_portfolios,
    create_portfolio_stocks,
    create_reviews
]