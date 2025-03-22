
import psycopg2
from queries.user import User
from queries.setup import setup_queries
import os
import sys
from tabulate import tabulate 

# Database connection parameters
DB_HOST = '34.130.75.185'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '2357'

# Instantiate the User class
user = User()

# Global variables
current_user_id = None
current_username = None

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a formatted header."""
    clear_screen()
    print("=" * 60)
    print(f"{title:^60}")
    print("=" * 60)
    print()

def pause():
    """Wait for user to press Enter before continuing."""
    input("\nPress Enter to continue...")

def login_menu():
    """Display login/register menu and handle authentication."""
    global current_user_id, current_username
    
    while True:
        print_header("Stock Social Network - Authentication")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            email = input("Email: ")
            password = input("Password: ")
            
            result = user.login(email, password)
            if result:
                current_user_id = result[0]
                current_username = email  # You might want to fetch the actual username
                print(f"\n✅ Login successful! Welcome back.")
                pause()
                return True
            else:
                print("\n❌ Invalid email or password. Please try again.")
                pause()
                
        elif choice == '2':
            username = input("Username: ")
            email = input("Email: ")
            password = input("Password: ")
            
            success = user.register(username, password, email)
            if success:
                print(f"\n✅ Registration successful! Welcome {username}.")
                print("Please login with your new credentials.")
                pause()
            else:
                print("\n❌ Username or email already exists. Please try again.")
                pause()
                
        elif choice == '3':
            print("\nGoodbye!")
            sys.exit(0)
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 3.")
            pause()

def main_menu():
    """Display the main menu and handle navigation."""
    global current_user_id, current_username  # Move this to the top of the function
    
    while True:
        print_header(f"Stock Social Network - Main Menu (User: {current_username})")
        print("1. Portfolio Management")
        print("2. Stock Lists")
        print("3. Friends")
        print("4. Stock Information")
        print("5. Log Out")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            portfolio_menu()
        elif choice == '2':
            stocklist_menu()
        elif choice == '3':
            friends_menu()
        elif choice == '4':
            stock_info_menu()
        elif choice == '5':
            current_user_id = None
            current_username = None
            print("\n✅ Logged out successfully.")
            pause()
            return
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 5.")
            pause()

def portfolio_menu():
    """Handle portfolio-related operations."""
    while True:
        print_header("Portfolio Management")
        print("1. View All Portfolios")
        print("2. Create New Portfolio")
        print("3. Delete Portfolio")
        print("4. View Portfolio Details")
        print("5. Update Cash Balance")
        print("6. Buy Stock Shares")
        print("7. Sell Stock Shares")
        print("8. View Portfolio Transactions")
        print("9. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-9): ")
        
        if choice == '1':
            # View all portfolios for current user
            print_header("Your Portfolios")
            portfolios = user.view_user_portfolios(current_user_id)
            if portfolios:
                # Assuming view_portfolio returns formatted data
                print(tabulate(portfolios, headers=["Portfolio ID", "Cash Balance", "Total Shares", "Created At"]))
            else:
                print("You don't have any portfolios yet.")
            pause()
            
        elif choice == '2':
            # Create new portfolio
            try:
                initial_cash = float(input("Initial cash balance: $"))
                portfolio_id = user.create_portfolio(current_user_id, initial_cash)
                print(f"\n✅ Portfolio created successfully with ID: {portfolio_id}")
            except ValueError:
                print("\n❌ Invalid amount. Please enter a valid number.")
            pause()
            
        elif choice == '3':
            # Delete portfolio
            try:
                portfolio_id = int(input("Enter portfolio ID to delete: "))
                result = user.delete_portfolio(portfolio_id)
                if result:
                    print(f"\n✅ Portfolio {portfolio_id} deleted successfully.")
                else:
                    print(f"\n❌ Portfolio {portfolio_id} not found or you don't have permission to delete it.")
            except ValueError:
                print("\n❌ Invalid portfolio ID. Please enter a valid number.")
            pause()
            
        elif choice == '4':
            # View portfolio details
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                portfolio_data = user.view_portfolio(portfolio_id)
                if portfolio_data:
                    print_header(f"Portfolio {portfolio_id} Details")
                    print(tabulate(portfolio_data, headers=["Portfolio ID", "Cash Balance", "Symbol", "Shares"]))
                    value = user.compute_portfolio_value(portfolio_id)
                    print(f"\nTotal Portfolio Value: ${value:.2f}")
                else:
                    print(f"\n❌ Portfolio {portfolio_id} not found or you don't have permission to view it.")
            except ValueError:
                print("\n❌ Invalid portfolio ID. Please enter a valid number.")
            pause()
            
        elif choice == '5':
            # Update cash balance
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                amount = float(input("Enter amount (positive to deposit, negative to withdraw): $"))
                result = user.update_cash_balance(portfolio_id, amount)
                if result is not None:
                    print(f"\n✅ Cash balance updated successfully. New balance: ${result:.2f}")
                else:
                    print("\n❌ Insufficient funds or invalid portfolio ID.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '6':
            # Buy stock shares
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                symbol = input("Enter stock symbol: ").upper()
                num_shares = int(input("Enter number of shares to buy: "))
                
                result = user.buy_stock_shares(portfolio_id, symbol, num_shares)
                if result:
                    print(f"\n✅ Successfully purchased {num_shares} shares of {symbol}.")
                else:
                    print("\n❌ Purchase failed. Insufficient funds or invalid inputs.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '7':
            # Sell stock shares
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                symbol = input("Enter stock symbol: ").upper()
                num_shares = int(input("Enter number of shares to sell: "))
                
                result = user.sell_stock_shares(portfolio_id, symbol, num_shares)
                if result:
                    print(f"\n✅ Successfully sold {num_shares} shares of {symbol}.")
                else:
                    print("\n❌ Sale failed. Insufficient shares or invalid inputs.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '8':
            # View portfolio transactions
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                transactions = user.view_portfolio_transactions(portfolio_id)
                
                if transactions:
                    print_header(f"Portfolio {portfolio_id} Transactions")
                    headers = ["ID", "Portfolio", "Symbol", "Type", "Shares", "Price", "Cash Change", "Time"]
                    print(tabulate(transactions, headers=headers))
                else:
                    print(f"\nNo transactions found for portfolio {portfolio_id}.")
            except ValueError:
                print("\n❌ Invalid portfolio ID. Please enter a valid number.")
            pause()
            
        elif choice == '9':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 9.")
            pause()

def stocklist_menu():
    """Handle stock list operations."""
    while True:
        print_header("Stock Lists Management")
        print("1. View Accessible Stock Lists")
        print("2. Create New Stock List")
        print("3. Delete Stock List")
        print("4. View Stock List Details")
        print("5. Add Stock to List")
        print("6. Remove Stock from List")
        print("7. Share Stock List with Friend")
        print("8. Review Stock List")
        print("9. View Reviews for Stock List")
        print("10. Delete Review")
        print("11. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-10): ")
        
        if choice == '1':
            # View accessible stock lists
            stock_lists = user.view_accessible_stock_lists(current_user_id)
            if stock_lists:
                print_header("Your Accessible Stock Lists")
                formatted_lists = []
                for sl in stock_lists:
                    formatted_lists.append([sl[0], sl[1], "Yes" if sl[2] else "No", sl[3]])
                print(tabulate(formatted_lists, headers=["List ID", "Creator ID", "Public", "Visibility"]))
            else:
                print("You don't have access to any stock lists.")
            pause()
            
        elif choice == '2':
            # Create new stock list
            is_public_input = input("Make this list public? (y/n): ").lower()
            is_public = is_public_input == 'y'
            
            try:
                stocklist_id = user.create_stock_list(current_user_id, is_public)
                print(f"\n✅ Stock list created successfully with ID: {stocklist_id}")
            except Exception as e:
                print(f"\n❌ Error creating stock list: {e}")
            pause()
            
        elif choice == '3':
            # Delete stock list
            try:
                stocklist_id = int(input("Enter stock list ID to delete: "))
                result = user.delete_stock_list(stocklist_id)
                if result:
                    print(f"\n✅ Stock list {stocklist_id} deleted successfully.")
                else:
                    print(f"\n❌ Stock list {stocklist_id} not found or you don't have permission to delete it.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()
            
        elif choice == '4':
            # View stock list details
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                stocklist_data = user.view_stock_list(stocklist_id)
                if stocklist_data:
                    print_header(f"Stock List {stocklist_id} Details")
                    print(tabulate(stocklist_data, headers=["List ID", "Public", "Creator ID", "Symbol", "Shares"]))
                else:
                    print(f"\n❌ Stock list {stocklist_id} not found or you don't have permission to view it.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()
            
        elif choice == '5':
            # Add stock to list
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                symbol = input("Enter stock symbol: ").upper()
                num_shares = int(input("Enter number of shares: "))
                
                result = user.add_stock_to_list(stocklist_id, symbol, num_shares)
                if result:
                    print(f"\n✅ Successfully added {num_shares} shares of {symbol} to stock list {stocklist_id}.")
                else:
                    print("\n❌ Failed to add stock to list. Check your permissions and inputs.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '6':
            # Remove stock from list
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                symbol = input("Enter stock symbol: ").upper()
                num_shares = int(input("Enter number of shares to remove: "))
                
                result = user.remove_stock_from_list(stocklist_id, symbol, num_shares)
                if result:
                    print(f"\n✅ Successfully removed {num_shares} shares of {symbol} from stock list {stocklist_id}.")
                else:
                    print("\n❌ Failed to remove stock from list. Check your permissions and inputs.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '7':
            # Share stock list with friend
            try:
                stocklist_id = int(input("Enter stock list ID to share: "))
                friend_id = int(input("Enter friend's user ID: "))
                
                result = user.share_stock_list(stocklist_id, current_user_id, friend_id)
                if result:
                    print(f"\n✅ Stock list {stocklist_id} shared successfully with user {friend_id}.")
                else:
                    print("\n❌ Failed to share stock list. Check that you own the list and the user is your friend.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '8':
            # Review stock list
            try:
                stocklist_id = int(input("Enter stock list ID to review: "))
                review_text = input("Enter your review: ")
                
                review_id = user.create_review(current_user_id, stocklist_id, review_text)
                if review_id:
                    print(f"\n✅ Review submitted successfully with ID: {review_id}")
                else:
                    print("\n❌ Failed to submit review. You may have already reviewed this list or lack access.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()
            
        elif choice == '9':
            # View reviews for stock list
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                reviews = user.view_reviews(stocklist_id, current_user_id)
                if reviews:
                    print_header(f"Reviews for Stock List {stocklist_id}")
                    formatted_reviews = []
                    for r in reviews:
                        formatted_reviews.append([r[0], r[1], r[2], r[3], r[4]])
                    print(tabulate(formatted_reviews, headers=["Review ID", "User ID", "Text", "Created", "Updated"]))
                else:
                    print(f"\nNo reviews found for stock list {stocklist_id}.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()

        elif choice == '10':
            # Delete review
            try:
                review_id = int(input("Enter review ID to delete: "))
                result = user.delete_review(review_id, current_user_id)
                if result:
                    print(f"\n✅ Review {review_id} deleted successfully.")
                else:
                    print(f"\n❌ Review {review_id} not found or you don't have permission to delete it.")
            except ValueError:
                print("\n❌ Invalid review ID. Please enter a valid number.")
            pause()
            
        elif choice == '11':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 10.")
            pause()

def friends_menu():
    """Handle friend-related operations."""
    while True:
        print_header("Friends Management")
        print("1. View Friends")
        print("2. Send Friend Request")
        print("3. View Incoming Friend Requests")
        print("4. View Outgoing Friend Requests")
        print("5. Accept Friend Request")
        print("6. Reject Friend Request")
        print("7. Delete Friend")
        print("8. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            # View friends
            friends = user.view_friends(current_user_id)
            if friends:
                print_header("Your Friends")
                for friend_id in friends:
                    print(f"User ID: {friend_id}")
            else:
                print("You don't have any friends yet.")
            pause()
            
        elif choice == '2':
            # Send friend request
            try:
                receiver_id = int(input("Enter user ID to send friend request: "))
                result = user.send_friend_request(current_user_id, receiver_id)
                if result:
                    print(f"\n✅ Friend request sent successfully to user {receiver_id}.")
                else:
                    print("\n❌ Failed to send friend request. You may already have a pending request or be friends.")
            except ValueError:
                print("\n❌ Invalid user ID. Please enter a valid number.")
            pause()
            
        elif choice == '3':
            # View incoming friend requests
            requests = user.view_incoming_requests(current_user_id)
            if requests:
                print_header("Incoming Friend Requests")
                for req in requests:
                    print(f"Request ID: {req[0]}, From User ID: {req[1]}")
            else:
                print("You don't have any incoming friend requests.")
            pause()
            
        elif choice == '4':
            # View outgoing friend requests
            requests = user.view_outgoing_requests(current_user_id)
            if requests:
                print_header("Outgoing Friend Requests")
                for req in requests:
                    print(f"Request ID: {req[0]}, To User ID: {req[1]}")
            else:
                print("You don't have any outgoing friend requests.")
            pause()
            
        elif choice == '5':
            # Accept friend request
            try:
                request_id = int(input("Enter request ID to accept: "))
                result = user.accept_friend_request(request_id)
                if result:
                    print(f"\n✅ Friend request {request_id} accepted successfully.")
                else:
                    print(f"\n❌ Failed to accept friend request {request_id}.")
            except ValueError:
                print("\n❌ Invalid request ID. Please enter a valid number.")
            pause()
            
        elif choice == '6':
            # Reject friend request
            try:
                request_id = int(input("Enter request ID to reject: "))
                result = user.reject_friend_request(request_id)
                if result:
                    print(f"\n✅ Friend request {request_id} rejected successfully.")
                else:
                    print(f"\n❌ Failed to reject friend request {request_id}.")
            except ValueError:
                print("\n❌ Invalid request ID. Please enter a valid number.")
            pause()
            
        elif choice == '7':
            # Delete friend
            try:
                friend_id = int(input("Enter user ID of friend to delete: "))
                result = user.delete_friend(current_user_id, friend_id)
                if result:
                    print(f"\n✅ Friend {friend_id} deleted successfully.")
                else:
                    print(f"\n❌ Failed to delete friend {friend_id}. Check if this user is actually your friend.")
            except ValueError:
                print("\n❌ Invalid user ID. Please enter a valid number.")
            pause()
            
        elif choice == '8':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 8.")
            pause()

def stock_info_menu():
    """Handle stock information operations."""
    while True:
        print_header("Stock Information")
        print("1. View Stock Info")
        print("2. Fetch Latest Stock Info (Yahoo Finance)")
        print("3. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            # View stock info
            symbol = input("Enter stock symbol: ").upper()
            data = user.view_stock_info(symbol)
            if data:
                print_header(f"Stock Information for {symbol}")
                print(tabulate(data, headers=["Date", "Open", "High", "Low", "Close", "Volume"]))
            else:
                print(f"\nNo stock information found for {symbol}.")
            pause()
            
        elif choice == '2':
            # Fetch latest stock info
            symbol = input("Enter stock symbol: ").upper()
            result = user.fetch_and_store_daily_info_yahoo(symbol)
            if result:
                print(f"\n✅ Successfully fetched and stored latest information for {symbol}.")
            else:
                print(f"\n❌ Failed to fetch information for {symbol}. Make sure it's a valid symbol.")
            pause()
            
        elif choice == '3':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 3.")
            pause()

def setup_db():
    """Set up the database tables if they don't exist."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        for query in setup_queries:
            cursor.execute(query)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database setup complete!")
        
    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

def main():
    """Main entry point for the CLI app."""
    # Ensure database is set up
    setup_db()
    
    print_header("Welcome to Stock Social Network")
    print("A command-line social network for stock investors")
    
    while True:
        # If not logged in, show login menu
        if not current_user_id:
            if not login_menu():
                break
        
        # If logged in, show main menu
        else:
            main_menu()

if __name__ == "__main__":
    main()
