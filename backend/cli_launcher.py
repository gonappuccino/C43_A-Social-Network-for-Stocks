import psycopg2
from queries.auth import Auth
from queries.portfolio import Portfolio
from queries.stock_list import StockList
from queries.friends import Friends
from queries.stock_data import StockData
from queries.reviews import Reviews
from queries.setup import setup_queries, load_stock_history_from_local, load_stock_history_from_local_fast, load_stock_history_from_csv, copy_symbols
import os
import sys
from tabulate import tabulate 
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Database connection parameters
DB_HOST = '34.130.75.185'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '2357'

# Instantiate the classes
auth = Auth()
portfolio = Portfolio()
stock_list = StockList()
friends = Friends()
stock_data = StockData()
reviews = Reviews()

current_user_id = None
current_username = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    clear_screen()
    print("=" * 60)
    print(f"{title:^60}")
    print("=" * 60)
    print()

def pause():
    input("\nPress Enter to continue...")

def login_menu():
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
            
            result = auth.login(email, password)
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
            
            success = auth.register(username, password, email)
            if success:
                print(f"\n✅ Registration successful! Welcome {username}.")
                print("Please login with your new credentials.")
                pause()
            else:
                print("\n❌ Username or email already exists or invalid. Please try again.")
                pause()
                
        elif choice == '3':
            print("\nGoodbye!")
            sys.exit(0)
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 3.")
            pause()

def main_menu():
    global current_user_id, current_username  # Move this to the top of the function
    
    while True:
        print_header(f"Stock Social Network - Main Menu (User: {current_username})")
        print("1. Portfolio Management")
        print("2. Stock Lists")
        print("3. Friends")
        print("4. Stock Information")
        print("5. Delete Account")
        print("6. Log Out")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            portfolio_menu()
        elif choice == '2':
            stocklist_menu()
        elif choice == '3':
            friends_menu()
        elif choice == '4':
            stock_info_menu()
        elif choice == '5':
            delete_account_menu()
        elif choice == '6':
            current_user_id = None
            current_username = None
            print("\n✅ Logged out successfully.")
            pause()
            return
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 6.")
            pause()

def portfolio_menu():
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
        print("9. View Portfolio Analytics")
        print("10. View Portfolio History")
        print("11. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-11): ")
        
        if choice == '1':
            # View all portfolios for current user
            print_header("Your Portfolios")
            portfolios = portfolio.view_user_portfolios(current_user_id)
            if portfolios:
                # Assuming view_portfolio returns formatted data
                print(tabulate(portfolios, headers=["Portfolio ID", "Portfolio Name", "Cash Balance", "Total Shares", "Created At"]))
            else:
                print("You don't have any portfolios yet.")
            pause()
            
        elif choice == '2':
            # Create new portfolio
            try:
                portfolio_name = input("Enter portfolio name: ")
                initial_cash = float(input("Initial cash balance: $"))
                portfolio_id = portfolio.create_portfolio(current_user_id, portfolio_name, initial_cash)
                print(f"\n✅ Portfolio created successfully with ID: {portfolio_id}")
            except ValueError:
                print("\n❌ Invalid amount. Please enter a valid number.")
            pause()
            
        elif choice == '3':
            # Delete portfolio
            try:
                portfolio_id = int(input("Enter portfolio ID to delete: "))
                result = portfolio.delete_portfolio(portfolio_id, current_user_id)
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
                portfolio_data = portfolio.view_portfolio(current_user_id, portfolio_id)
                if portfolio_data:
                    portfolio_data_no_cash = [[x[2], x[3]] for x in portfolio_data]
                    cash = portfolio.get_cash_balance(portfolio_id, current_user_id)
                    print_header(f"Portfolio {portfolio_id} Details")
                    print(tabulate(portfolio_data_no_cash, headers=["Symbol", "Shares"]))
                    print(f"\nCash Balance: ${cash:.2f}")
                    value = portfolio.compute_portfolio_value(current_user_id, portfolio_id)
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
                result = portfolio.update_cash_balance(current_user_id, portfolio_id, amount)
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
                
                result = portfolio.buy_stock_shares(current_user_id, portfolio_id, symbol, num_shares)
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
                
                result = portfolio.sell_stock_shares(current_user_id, portfolio_id, symbol, num_shares)
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
                transactions = portfolio.view_portfolio_transactions(current_user_id, portfolio_id)
                
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
            view_portfolio_analytics()
            pause()
            
        elif choice == '10':
            # View portfolio history
            try:
                portfolio_id = int(input("Enter portfolio ID: "))
                period = input("Enter period (5d, 1mo, 6mo, 1y, 5y, all): ")
                # verify period
                if period not in ['5d', '1mo', '6mo', '1y', '5y', 'all']:
                    print("\n❌ Invalid period. Please enter a valid period.")
                    pause()
                    continue
                graph = input("Do you want to see a graph of the portfolio? (y/n): ")
                data = portfolio.view_portfolio_history(current_user_id, portfolio_id, period)
                if data:
                    print_header(f"Portfolio {portfolio_id} History")
                    print(tabulate(data, headers=["Date", "Total Value"]))
                else:
                    print(f"\nNo history data found for portfolio {portfolio_id}.")
                    pause()
                    continue

                if graph.lower() == 'y':
                    # Convert data to DataFrame for plotting
                    df = pd.DataFrame(data, columns=['Date', 'Value'])
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    
                    # Get period name for title
                    period_names = {
                        '5d': '5 Days', 
                        '1mo': '1 Month', 
                        '6mo': '6 Months', 
                        '1y': '1 Year', 
                        '5y': '5 Years', 
                        'all': 'All Time'
                    }
                    period_name = period_names.get(period, 'Custom Period')
                    
                    plt.figure(figsize=(12, 8))
                    plt.plot(df.index, df['Value'])
                    plt.title(f'Portfolio {portfolio_id} Value - {period_name}')
                    plt.xlabel('Date')
                    plt.ylabel('Value ($)')
                    plt.grid(True)
                    plt.show()
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '11':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 11.")
            pause()

def view_portfolio_analytics():
    """Display portfolio analytics including CV, Beta, and correlation/covariance matrices"""
    try:
        portfolio_id = int(input("Enter portfolio ID: "))
        
        # Get date range
        print("\nEnter date range for analysis (YYYY-MM-DD format)")
        print("Leave blank for maximum possible range based on available stock data")
        start_date_str = input("Start date: ").strip()
        end_date_str = input("End date: ").strip()
        
        # Parse dates if provided
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get analytics
        analytics = portfolio.compute_portfolio_analytics(current_user_id, portfolio_id, start_date, end_date)
        
        if not analytics:
            print("\n❌ No analytics available. Make sure the portfolio exists and contains stocks.")
            pause()
            return
            
        # Display stock analytics
        print_header("Portfolio Analytics")
        print("\nStock Analytics:")
        headers = ["Symbol", "Shares", "Coefficient of Variation", "Beta"]
        data = [[
            stock['symbol'],
            stock['shares'],
            f"{stock['coefficient_of_variation']:.4f}",
            f"{stock['beta']:.4f}"
        ] for stock in analytics['stock_analytics']]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
        # Display correlation matrix
        print("\nCorrelation Matrix:")
        symbols = sorted(analytics['correlation_matrix'].keys())
        headers = ["Symbol"] + symbols
        data = []
        for symbol in symbols:
            row = [symbol]
            for other_symbol in symbols:
                row.append(f"{analytics['correlation_matrix'][symbol].get(other_symbol, 0):.4f}")
            data.append(row)
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
        # Display covariance matrix
        print("\nCovariance Matrix:")
        data = []
        for symbol in symbols:
            row = [symbol]
            for other_symbol in symbols:
                row.append(f"{analytics['covariance_matrix'][symbol].get(other_symbol, 0):.4f}")
            data.append(row)
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
    except ValueError as e:
        print(f"\n❌ Invalid input: {e}")
    except Exception as e:
        print(f"\n❌ Error computing analytics: {e}")
    
    pause()
def stocklist_menu():
    while True:
        print_header("Stock Lists Management")
        print("1. View Accessible Stock Lists")
        print("2. Create New Stock List")
        print("3. Delete Stock List")
        print("4. View Stock List Details")
        print("5. Add Stock to List")
        print("6. Remove Stock from List")
        print("7. Share Stock List with Friend")
        print("8. Unshare Stock List with Friend")
        print("9. Review Stock List")
        print("10. View Reviews for Stock List")
        print("11. Delete Review")
        print("12. View Stock List History")
        print("13. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-13): ")
        
        if choice == '1':
            # View accessible stock lists
            stock_lists = stock_list.view_accessible_stock_lists(current_user_id)
            if stock_lists:
                print_header("Your Accessible Stock Lists")
                formatted_lists = []
                for sl in stock_lists:
                    formatted_lists.append([sl[0], sl[1], sl[2], sl[3], "Yes" if sl[4] else "No", sl[5]])
                print(tabulate(formatted_lists, headers=["List ID", "List Name", "Creator ID", "Creator Name", "Public", "Visibility"]))
            else:
                print("You don't have access to any stock lists.")
            pause()
            
        elif choice == '2':
            # Create new stock list
            stocklist_name = input("Enter stock list name: ")
            is_public_input = input("Make this list public? (y/n): ").lower()
            is_public = is_public_input == 'y'
            
            try:
                stocklist_id = stock_list.create_stock_list(current_user_id, stocklist_name, is_public)
                print(f"\n✅ Stock list created successfully with ID: {stocklist_id}")
            except Exception as e:
                print(f"\n❌ Error creating stock list: {e}")
            pause()
            
        elif choice == '3':
            # Delete stock list
            try:
                stocklist_id = int(input("Enter stock list ID to delete: "))
                result = stock_list.delete_stock_list(stocklist_id, current_user_id)
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
                stocklist_data = stock_list.view_stock_list(current_user_id, stocklist_id)
                if stocklist_data:
                    print_header(f"Stock List {stocklist_id} Details")
                    # Filter out None values and format the data
                    formatted_data = []
                    for row in stocklist_data:
                        if row[3] is not None:  # Only include rows with stock data
                            formatted_data.append([row[3], row[4]])  # Symbol and Shares
                    
                    if formatted_data:
                        print(tabulate(formatted_data, headers=["Symbol", "Shares"]))
                        # Calculate and display total value
                        total_value = stock_list.compute_stock_list_value(current_user_id, stocklist_id)
                        if total_value is not None:
                            print(f"\nTotal Stock List Value: ${total_value:.2f}")
                    else:
                        print("This stock list is empty.")
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
                
                result = stock_list.add_stock_to_list(current_user_id, stocklist_id, symbol, num_shares)
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
                
                result = stock_list.remove_stock_from_list(current_user_id, stocklist_id, symbol, num_shares)
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
                
                result = stock_list.share_stock_list(stocklist_id, current_user_id, friend_id)
                if result == 1:
                    print(f"\n✅ Stock list {stocklist_id} shared successfully with user {friend_id}.")
                elif result == -1:
                    print(f"\n❌ You do not own stock list {stocklist_id}.")
                elif result == -2:
                    print(f"\n❌ User {friend_id} is not your friend.")
                else:
                    print("\n❌ Failed to share stock list. Check that you own the list and the user is your friend.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
        elif choice == '8':
            # Unshare stock list with friend
            try:
                stocklist_id = int(input("Enter stock list ID to unshare: "))
                friend_id = int(input("Enter friend's user ID: "))
                
                result = stock_list.unshare_stock_list(stocklist_id, current_user_id, friend_id)
                if result:
                    print(f"\n✅ Stock list {stocklist_id} unshared successfully with user {friend_id}.")
                else:
                    print("\n❌ Failed to unshare stock list. Check that you own the list and the user is your friend.")
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
        elif choice == '9':
            # Review stock list
            try:
                stocklist_id = int(input("Enter stock list ID to review: "))
                review_text = input("Enter your review: ")
                
                review_id = reviews.create_review(current_user_id, stocklist_id, review_text)
                if review_id:
                    print(f"\n✅ Review submitted successfully with ID: {review_id}")
                else:
                    print("\n❌ Failed to submit review. You may have already reviewed this list or lack access.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()
            
        elif choice == '10':
            # View reviews for stock list
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                reviews_list = reviews.view_reviews(stocklist_id, current_user_id)
                if reviews_list:
                    print_header(f"Reviews for Stock List {stocklist_id}")
                    formatted_reviews = []
                    for r in reviews_list:
                        formatted_reviews.append([r[0], r[1], r[2], r[3], r[4]])
                    print(tabulate(formatted_reviews, headers=["Review ID", "User ID", "Text", "Created", "Updated"]))
                else:
                    print(f"\nNo reviews found for stock list {stocklist_id}.")
            except ValueError:
                print("\n❌ Invalid stock list ID. Please enter a valid number.")
            pause()

        elif choice == '11':
            # Delete review
            try:
                review_id = int(input("Enter review ID to delete: "))
                result = reviews.delete_review(review_id, current_user_id)
                if result:
                    print(f"\n✅ Review {review_id} deleted successfully.")
                else:
                    print(f"\n❌ Review {review_id} not found or you don't have permission to delete it.")
            except ValueError:
                print("\n❌ Invalid review ID. Please enter a valid number.")
            pause()
            
        elif choice == '12':
            # View stock list history
            try:
                stocklist_id = int(input("Enter stock list ID: "))
                period = input("Enter period (5d, 1mo, 6mo, 1y, 5y, all): ")
                # verify period
                if period not in ['5d', '1mo', '6mo', '1y', '5y', 'all']:
                    print("\n❌ Invalid period. Please enter a valid period.")
                    pause()
                    continue
                graph = input("Do you want to see a graph of the stock list? (y/n): ")
                data = stock_list.view_stock_list_history(current_user_id, stocklist_id, period)
                if data:
                    print_header(f"Stock List {stocklist_id} History")
                    print(tabulate(data, headers=["Date", "Total Value"]))
                else:
                    print(f"\nNo history data found for stock list {stocklist_id}.")

                if graph.lower() == 'y':
                    # Convert data to DataFrame for plotting
                    df = pd.DataFrame(data, columns=['Date', 'Value'])
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    
                    # Get period name for title
                    period_names = {
                        '5d': '5 Days', 
                        '1mo': '1 Month', 
                        '6mo': '6 Months', 
                        '1y': '1 Year', 
                        '5y': '5 Years', 
                        'all': 'All Time'
                    }
                    period_name = period_names.get(period, 'Custom Period')
                    
                    plt.figure(figsize=(12, 8))
                    plt.plot(df.index, df['Value'])
                    plt.title(f'Stock List {stocklist_id} Value - {period_name}')
                    plt.xlabel('Date')
                    plt.ylabel('Value ($)')
                    plt.grid(True)
                    plt.show()
            except ValueError:
                print("\n❌ Invalid input. Please enter valid numbers.")
            pause()
            
        elif choice == '13':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 13.")
            pause()

def friends_menu():
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
            friend_list = friends.view_friends(current_user_id)
            if friend_list:
                print_header("Your Friends")
                for friend_id, friend_name in friend_list:
                    print(f"User ID: {friend_id}, Username: {friend_name}")
            else:
                print("You don't have any friends yet.")
            pause()
            
        elif choice == '2':
            # Send friend request
            try:
                receiver_id = int(input("Enter user ID to send friend request: "))
                result = friends.send_friend_request(current_user_id, receiver_id)
                if result:
                    if result > 0:
                        print(f"\n✅ Friend request sent successfully to user {receiver_id}.")
                    elif result == -1: # Already friends or pending request
                        print("\n❌ You are already friends or have a pending request with this user.")
                    elif result == -2: # Less than 5 minutes since last request
                        print("\n❌ You can only send one request every 5 minutes.")
                    elif result == -3: # Request to self
                        print("\n❌ You can't send a friend request to yourself.")
                    else:
                        print("\n❌ Failed to send friend request. Check if the user exists.")
                else:
                    print("\n❌ Failed to send friend request. Check if the user exists.")
            except ValueError:
                print("\n❌ Invalid user ID. Please enter a valid number.")
            pause()
            
        elif choice == '3':
            # View incoming friend requests
            requests = friends.view_incoming_requests(current_user_id)
            if requests:
                print_header("Incoming Friend Requests")
                for req in requests:
                    print(f"Request ID: {req[0]}, From User ID: {req[1]}, Username: {req[2]}")
            else:
                print("You don't have any incoming friend requests.")
            pause()
            
        elif choice == '4':
            # View outgoing friend requests
            requests = friends.view_outgoing_requests(current_user_id)
            if requests:
                print_header("Outgoing Friend Requests")
                for req in requests:
                    print(f"Request ID: {req[0]}, To User ID: {req[1]}, Username: {req[2]}")
            else:
                print("You don't have any outgoing friend requests.")
            pause()
            
        elif choice == '5':
            # Accept friend request
            try:
                request_id = int(input("Enter request ID to accept: "))
                result = friends.accept_friend_request(request_id, current_user_id)
                if result:
                    print(f"\n✅ Friend request {request_id} accepted successfully.")
                else:
                    print(f"\n❌ Failed to accept friend request {request_id}. Check if this request exists or is a request to you")
            except ValueError:
                print("\n❌ Invalid request ID. Please enter a valid number.")
            pause()
            
        elif choice == '6':
            # Reject friend request
            try:
                request_id = int(input("Enter request ID to reject: "))
                result = friends.reject_friend_request(request_id, current_user_id)
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
                result = friends.delete_friend(current_user_id, friend_id)
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
    while True:
        print_header("Stock Information")
        print("1. View Stock Info")
        print("2. Fetch Latest Stock Info For an Individual Stock (Yahoo Finance)")
        print("3. Fetch Latest Stock Info For All Stocks (Yahoo Finance)")
        print("4. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            # View stock info
            symbol = input("Enter stock symbol: ").upper()
            period = input("Enter period (5d, 1mo, 6mo, 1y, 5y, all): ")
            # verify period
            if period not in ['5d', '1mo', '6mo', '1y', '5y', 'all']:
                print("\n❌ Invalid period. Please enter a valid period.")
                pause()
                continue
            graph = input("Do you want to see a graph of the stock? (y/n): ")
            data = stock_data.view_stock_info(symbol, period)
            if data:
                print_header(f"Stock Information for {symbol}")
                print(tabulate(data, headers=["Date", "Open", "High", "Low", "Close", "Volume"]))
            else:
                print(f"\nNo stock information found for {symbol}.")

            if graph.lower() == 'y':
                stock_data.display_stock_chart(symbol, period)
            pause()
            
        elif choice == '2':
            # Fetch latest stock info
            symbol = input("Enter stock symbol: ").upper()
            num_days = int(input("Enter number of days to fetch (1-365): "))
            result = stock_data.fetch_and_store_daily_info_yahoo(symbol, num_days)
            if result:
                print(f"\n✅ Successfully fetched and stored {num_days} days of data for {symbol}.")
            else:
                print(f"\n❌ Failed to fetch information for {symbol}. Make sure it's a valid symbol.")
            pause()

        elif choice == '3':
            # Fetch latest stock info for all stocks
            num_days = int(input("Enter number of days to fetch (1-365): "))
            result = stock_data.fetch_and_store_all_stocks_daily_info(num_days)
            if result:
                print(f"\n✅ Successfully fetched and stored {num_days} days of data for all stocks.")
            else:
                print(f"\n❌ Failed to fetch information for all stocks.")
            pause()
            
        elif choice == '4':
            return
            
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 4.")
            pause()

def delete_account_menu():
    """Handle account deletion with confirmation"""
    global current_user_id, current_username
    
    print_header("Delete Account")
    print("⚠️ WARNING: This action cannot be undone!")
    print("All your data will be permanently deleted, including:")
    print("- Your profile")
    print("- All your portfolios")
    print("- All your stock lists")
    print("- All your reviews")
    print("- All your friend connections")
    
    confirm = input("\nAre you sure you want to delete your account? (yes/no): ").lower()
    
    if confirm == 'yes':
        max_attempts = 3
        attempts = 0
        while attempts < max_attempts:
            password = input("Please enter your password to confirm: ")
            
            # Verify password
            result = auth.login(current_username, password)
            if result and result[0] == current_user_id:
                if auth.delete_account(current_user_id):
                    print("\n✅ Account deleted successfully.")
                    current_user_id = None
                    current_username = None
                else:
                    print("\n❌ Failed to delete account. Please try again later.")
                break
            else:
                attempts += 1
                if attempts < max_attempts:
                    print(f"\n❌ Incorrect password. {max_attempts - attempts} attempts remaining.")
                else:
                    print("\n❌ Too many incorrect attempts. Account deletion cancelled.")
    else:
        print("\nAccount deletion cancelled.")
    
    pause()

def setup_db(load_stock_history = False):
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
        print("✅ Initial Database setup complete!")
        
    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

    if not load_stock_history:
        return
    try:
        #cursor.execute(load_stock_history_from_csv)
        load_stock_history_from_local_fast(conn)
        cursor.execute(copy_symbols)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database setup complete!")
    except psycopg2.Error as e:
        print(f"❌ Loading stock history from VM has failed: {e}")
        print(f"Attemping to load stock history from local")
        conn.rollback()
        try:
            load_stock_history_from_local_fast(conn)
            cursor.execute(copy_symbols)
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database setup complete!")
        except Exception as e:
            conn.rollback()
            print(f"❌ Loading stock history from local has failed: {e}")
            sys.exit(1)


def main():

    setup_db(True)
    pause()
    
    print_header("Welcome to Stock Social Network - A CSCC43 Project")
    print("A command-line social network application for stock investors")
    
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
