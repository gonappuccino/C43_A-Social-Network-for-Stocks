
import psycopg2
from queries.user import User
import random
import datetime
from tabulate import tabulate

# Database connection parameters
DB_HOST = '34.130.75.185'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '2357'

# Initialize User class
user = User()

# Stock symbols to use in demo
STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NFLX', 'NVDA', 'AMD', 'INTC']

# Demo users
DEMO_USERS = [
    {"username": "johndoe", "password": "password123", "email": "john@example.com"},
    {"username": "janedoe", "password": "password123", "email": "jane@example.com"},
    {"username": "bobsmith", "password": "password123", "email": "bob@example.com"},
    {"username": "alicejones", "password": "password123", "email": "alice@example.com"},
    {"username": "mikebrown", "password": "password123", "email": "mike@example.com"},
]

# Demo stock list names
STOCK_LIST_NAMES = [
    "Tech Giants", "Green Energy", "Dividend Kings", "Growth Stocks", 
    "Value Picks", "Blue Chips", "Small Caps", "Crypto Related", 
    "Healthcare", "Entertainment"
]

# Demo portfolio names
PORTFOLIO_NAMES = [
    "Retirement Fund", "College Savings", "Aggressive Growth", 
    "Dividend Income", "Long-term Investments", "Short-term Trades"
]

# Demo reviews
DEMO_REVIEWS = [
    "Great collection of stocks! I've been following these for months.",
    "Solid picks, but I would add a few more tech stocks for diversification.",
    "Not sure about some of these choices, but overall a decent list.",
    "These stocks have been performing well for me. Thanks for sharing!",
    "I like the combination of growth and value in this list.",
    "Perfect selection for beginners looking to invest in this sector.",
    "I've been investing in most of these stocks with good returns.",
    "Interesting mix of established companies and emerging players.",
    "Thanks for putting this together! Very helpful for my research.",
    "Would be better with some international exposure, but good US picks."
]

def clear_existing_data():
    """
    Optionally clear all existing data from the database
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Disable foreign key constraints temporarily
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Clear tables in reverse order of dependencies
        tables = [
            "Reviews",
            "PortfolioTransactions",
            "PortfolioStocks",
            "Portfolios",
            "StockListStocks",
            "StockListAccess",
            "StockLists",
            "FriendRequest",
            "DailyStockInfo"
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table};")
            print(f"Cleared table: {table}")
        
        # Re-enable foreign key constraints
        cursor.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database cleared successfully!")
        
    except psycopg2.Error as e:
        print(f"❌ Error clearing database: {e}")
        return False
    
    return True

def create_demo_users():
    """
    Create demo users
    """
    print("Creating demo users...")
    user_ids = []
    
    for demo_user in DEMO_USERS:
        # Check if user already exists
        cursor = user.conn.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (demo_user["email"],))
        existing = cursor.fetchone()
        cursor.close()
        
        if existing:
            print(f"User {demo_user['username']} already exists with ID: {existing[0]}")
            user_ids.append(existing[0])
        else:
            success = user.register(demo_user["username"], demo_user["password"], demo_user["email"])
            if success:
                cursor = user.conn.cursor()
                cursor.execute("SELECT user_id FROM Users WHERE email = %s", (demo_user["email"],))
                user_id = cursor.fetchone()[0]
                cursor.close()
                print(f"Created user {demo_user['username']} with ID: {user_id}")
                user_ids.append(user_id)
            else:
                print(f"Failed to create user {demo_user['username']}")
    
    return user_ids

def create_friend_relationships(user_ids):
    """
    Create friend relationships between users
    """
    print("Creating friend relationships...")
    
    # Create some accepted friend relationships
    friendship_pairs = []
    for i in range(len(user_ids)):
        for j in range(i+1, len(user_ids)):
            # 70% chance of friendship
            if random.random() < 0.7:
                friendship_pairs.append((user_ids[i], user_ids[j]))
    
    # Add the friend relationships
    for sender_id, receiver_id in friendship_pairs:
        # Send request
        request_id = user.send_friend_request(sender_id, receiver_id)
        
        # Accept it (if it's a valid request ID)
        if isinstance(request_id, int) and request_id > 0:
            user.accept_friend_request(request_id)
            print(f"Created friendship between users {sender_id} and {receiver_id}")
    
    # Create some pending friend requests
    pending_pairs = []
    for i in range(len(user_ids)):
        for j in range(len(user_ids)):
            if i != j and (user_ids[i], user_ids[j]) not in friendship_pairs and (user_ids[j], user_ids[i]) not in friendship_pairs:
                # 30% chance of pending request
                if random.random() < 0.3:
                    pending_pairs.append((user_ids[i], user_ids[j]))
    
    # Add the pending requests
    for sender_id, receiver_id in pending_pairs:
        request_id = user.send_friend_request(sender_id, receiver_id)
        if isinstance(request_id, int) and request_id > 0:
            print(f"Created pending friend request from user {sender_id} to {receiver_id}")

def create_portfolios(user_ids):
    """
    Create portfolios for users
    """
    print("Creating portfolios...")
    portfolio_ids = []
    
    for user_id in user_ids:
        # Create 1-3 portfolios for each user
        num_portfolios = random.randint(1, 3)
        for i in range(num_portfolios):
            portfolio_name = random.choice(PORTFOLIO_NAMES) + f" {i+1}"
            initial_cash = random.randint(10000, 100000)
            
            try:
                portfolio_id = user.create_portfolio(user_id, portfolio_name, initial_cash)
                portfolio_ids.append((user_id, portfolio_id))
                print(f"Created portfolio '{portfolio_name}' for user {user_id} with ID: {portfolio_id}")
            except Exception as e:
                print(f"Failed to create portfolio for user {user_id}: {e}")
    
    return portfolio_ids

def buy_stocks_for_portfolios(portfolio_ids):
    """
    Buy stocks for the created portfolios
    """
    print("Buying stocks for portfolios...")
    
    for user_id, portfolio_id in portfolio_ids:
        # Buy 3-6 different stocks for each portfolio
        num_stocks = random.randint(3, 6)
        selected_stocks = random.sample(STOCK_SYMBOLS, num_stocks)
        
        for symbol in selected_stocks:
            # Buy between 5 and 50 shares
            num_shares = random.randint(5, 50)
            
            try:
                result = user.buy_stock_shares(portfolio_id, symbol, num_shares)
                if result:
                    print(f"Bought {num_shares} shares of {symbol} for portfolio {portfolio_id}")
                else:
                    print(f"Failed to buy {symbol} for portfolio {portfolio_id}")
            except Exception as e:
                print(f"Error buying stocks: {e}")

def create_stock_lists(user_ids):
    """
    Create stock lists for users
    """
    print("Creating stock lists...")
    stock_list_ids = []
    
    for user_id in user_ids:
        # Create 1-3 stock lists for each user
        num_lists = random.randint(1, 3)
        for i in range(num_lists):
            list_name = random.choice(STOCK_LIST_NAMES) + f" {i+1}"
            is_public = random.choice([True, False])
            
            try:
                stock_list_id = user.create_stock_list(user_id, list_name, is_public)
                stock_list_ids.append((user_id, stock_list_id, is_public))
                print(f"Created {'public' if is_public else 'private'} stock list '{list_name}' for user {user_id} with ID: {stock_list_id}")
            except Exception as e:
                print(f"Failed to create stock list for user {user_id}: {e}")
    
    return stock_list_ids

def add_stocks_to_lists(stock_list_ids):
    """
    Add stocks to the created stock lists
    """
    print("Adding stocks to stock lists...")
    
    for user_id, stock_list_id, is_public in stock_list_ids:
        # Add 4-8 different stocks to each list
        num_stocks = random.randint(4, 8)
        selected_stocks = random.sample(STOCK_SYMBOLS, num_stocks)
        
        for symbol in selected_stocks:
            # Add between 10 and 100 shares
            num_shares = random.randint(10, 100)
            
            try:
                result = user.add_stock_to_list(stock_list_id, symbol, num_shares)
                if result:
                    print(f"Added {num_shares} shares of {symbol} to stock list {stock_list_id}")
                else:
                    print(f"Failed to add {symbol} to stock list {stock_list_id}")
            except Exception as e:
                print(f"Error adding stocks to list: {e}")

def share_stock_lists(user_ids, stock_list_ids):
    """
    Share private stock lists between friends
    """
    print("Sharing stock lists...")
    
    # Only share private lists
    private_lists = [(user_id, list_id) for user_id, list_id, is_public in stock_list_ids if not is_public]
    
    for owner_id, list_id in private_lists:
        # Get friends of this user
        friends = user.view_friends(owner_id)
        
        if friends:
            # Share with 1-2 random friends
            num_friends = min(len(friends), random.randint(1, 2))
            selected_friends = random.sample(friends, num_friends)
            
            for friend_id in selected_friends:
                try:
                    result = user.share_stock_list(list_id, owner_id, friend_id)
                    if result:
                        print(f"Shared stock list {list_id} from user {owner_id} with friend {friend_id}")
                    else:
                        print(f"Failed to share stock list {list_id} with friend {friend_id}")
                except Exception as e:
                    print(f"Error sharing stock list: {e}")

def create_reviews(user_ids, stock_list_ids):
    """
    Create reviews for stock lists
    """
    print("Creating reviews...")
    
    # Get public lists and lists shared with friends
    public_lists = [(user_id, list_id) for user_id, list_id, is_public in stock_list_ids if is_public]
    
    for reviewer_id in user_ids:
        # Review 2-4 random public lists
        num_reviews = min(len(public_lists), random.randint(2, 4))
        selected_lists = random.sample(public_lists, num_reviews)
        
        for owner_id, list_id in selected_lists:
            # Don't review your own lists
            if reviewer_id != owner_id:
                review_text = random.choice(DEMO_REVIEWS)
                
                try:
                    review_id = user.create_review(reviewer_id, list_id, review_text)
                    if review_id:
                        print(f"Created review from user {reviewer_id} for stock list {list_id}")
                    else:
                        print(f"Failed to create review for stock list {list_id}")
                except Exception as e:
                    print(f"Error creating review: {e}")

def fetch_stock_data():
    """
    Fetch current stock data for demo symbols
    """
    print("Fetching current stock data...")
    
    for symbol in STOCK_SYMBOLS:
        try:
            result = user.fetch_and_store_daily_info_yahoo(symbol)
            if result:
                print(f"Fetched and stored stock data for {symbol}")
            else:
                print(f"Failed to fetch stock data for {symbol}")
        except Exception as e:
            print(f"Error fetching stock data: {e}")

def print_summary(user_ids):
    """
    Print a summary of the created demo data
    """
    print("\n=== DEMO DATA SUMMARY ===\n")
    
    # Print users
    print("Users:")
    cursor = user.conn.cursor()
    cursor.execute("SELECT user_id, username, email FROM Users WHERE user_id IN %s ORDER BY user_id", (tuple(user_ids),))
    users = cursor.fetchall()
    print(tabulate(users, headers=["User ID", "Username", "Email"]))
    print()
    
    # Print friendships
    print("Friendships:")
    all_friendships = []
    for u_id in user_ids:
        friends = user.view_friends(u_id)
        if friends:
            for friend_id in friends:
                # Only show each friendship once
                if u_id < friend_id:
                    all_friendships.append((u_id, friend_id))
    
    print(tabulate(all_friendships, headers=["User ID", "Friend ID"]))
    print()
    
    # Print portfolios
    print("Portfolios:")
    all_portfolios = []
    for u_id in user_ids:
        portfolios = user.view_user_portfolios(u_id)
        if portfolios:
            for p in portfolios:
                all_portfolios.append(p)
    
    print(tabulate(all_portfolios, headers=["Portfolio ID", "Name", "Cash Balance", "Total Stocks", "Created At"]))
    print()
    
    # Print stock lists
    print("Stock Lists:")
    all_stock_lists = []
    for u_id in user_ids:
        stock_lists = user.view_accessible_stock_lists(u_id)
        if stock_lists:
            for sl in stock_lists:
                # Only show each list once
                if sl[2] == u_id:  # creator_id matches current user
                    all_stock_lists.append(sl)
    
    print(tabulate(all_stock_lists, headers=["List ID", "Name", "Creator ID", "Public", "Visibility"]))
    print()

def prepare_demo_data():
    """
    Main function to prepare all demo data
    """
    print("=== PREPARING DEMO DATA ===")
    
    # Optionally clear existing data - uncomment if needed
    # clear_existing_data()
    
    # Create users
    user_ids = create_demo_users()
    
    # Create friend relationships
    create_friend_relationships(user_ids)
    
    # Create portfolios and buy stocks
    portfolio_ids = create_portfolios(user_ids)
    buy_stocks_for_portfolios(portfolio_ids)
    
    # Create stock lists and add stocks
    stock_list_ids = create_stock_lists(user_ids)
    add_stocks_to_lists(stock_list_ids)
    
    # Share stock lists
    share_stock_lists(user_ids, stock_list_ids)
    
    # Create reviews
    create_reviews(user_ids, stock_list_ids)
    
    # Fetch stock data
    fetch_stock_data()
    
    # Print summary
    print_summary(user_ids)
    
    print("\n=== DEMO DATA PREPARATION COMPLETE ===")
    print("You can now use these users, portfolios, and stock lists for your demo")
    
    # Return demo credentials for convenience
    return {
        "users": DEMO_USERS,
        "user_ids": user_ids,
        "stock_symbols": STOCK_SYMBOLS
    }

if __name__ == "__main__":
    demo_data = prepare_demo_data()
    print("\nDemo User Credentials:")
    for u in demo_data["users"]:
        print(f"Username: {u['username']}, Email: {u['email']}, Password: {u['password']}")
