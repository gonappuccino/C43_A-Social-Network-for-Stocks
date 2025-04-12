import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import sys
from queries.setup import setup_queries, load_stock_history_from_local, load_stock_history_from_local_fast, load_stock_history_from_csv, copy_symbols


try:
    from queries.auth import Auth
    from queries.portfolio import Portfolio
    from queries.stock_list import StockList
    from queries.friends import Friends
    from queries.stock_data import StockData
    from queries.reviews import Reviews
    print("Backend modules imported successfully.")
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Please ensure gui_launcher.py is in the 'backend' directory or adjust import paths.")
    exit() # Exit if backend cannot be imported

def setup_db(load_stock_history = False):
    try:
        conn = psycopg2.connect(
            host='34.130.75.185',
            database='postgres',
            user='postgres',
            password='2357'
        )
        cursor = conn.cursor()
        
        for query in setup_queries:
            cursor.execute(query)
        
        conn.commit()
        print("✅ Initial Database setup complete!")
        
        if load_stock_history:
            try:
                # Clear existing stock data
                cursor.execute("DELETE FROM stockshistory")
                cursor.execute("DELETE FROM stocks")
                conn.commit()
                print("✅ Cleared existing stock data")
                
                success = load_stock_history_from_local_fast(conn)
                if success:
                    cursor.execute(copy_symbols)
                    conn.commit()
                    print("✅ Stock history loaded successfully!")
                else:
                    print("❌ Failed to load stock history from local file")
            except Exception as e:
                print(f"❌ Error loading stock history: {e}")
                conn.rollback()
                
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Social Network")
        self.geometry("800x600") # Adjusted starting size

        # Initialize backend instances
        self.auth = Auth()
        self.portfolio = Portfolio()
        self.stock_list = StockList()
        self.friends = Friends()
        self.stock_data = StockData()
        self.reviews = Reviews()

        self.current_user_id = None
        self.current_username = None # Store username for display

        # Container frame to switch between login and main app
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.login_frame = LoginFrame(self.container, self)
        self.main_app_frame = None # Will be created after login

        self.show_login_frame()

    def show_login_frame(self):
        if self.main_app_frame:
            self.main_app_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.title("Stock Social Network - Login") # Update title

    def show_main_app_frame(self):
        self.login_frame.pack_forget()
        if not self.main_app_frame:
            self.main_app_frame = MainAppFrame(self.container, self)
        self.main_app_frame.pack(fill="both", expand=True)
        self.title(f"Stock Social Network - Welcome {self.current_username}")  # Update title with username
        
        # Refresh portfolio list immediately after showing main frame
        self.main_app_frame.refresh_portfolio_list()
        self.main_app_frame.refresh_portfolio()

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        if self.main_app_frame:
            self.main_app_frame.destroy() # Destroy the main frame to clear state
            self.main_app_frame = None
        self.show_login_frame()
        messagebox.showinfo("Logout", "You have been logged out.")

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding="20")
        self.controller = controller

        ttk.Label(self, text="Stock Social Network", font=("Arial", 24)).pack(pady=20)

        # Login Section
        login_group = ttk.LabelFrame(self, text="Login", padding="10")
        login_group.pack(pady=10, padx=20, fill="x")

        ttk.Label(login_group, text="Email:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.login_email_entry = ttk.Entry(login_group, width=30)
        self.login_email_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(login_group, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.login_password_entry = ttk.Entry(login_group, show="*", width=30)
        self.login_password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(login_group, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

        # Registration Section
        register_group = ttk.LabelFrame(self, text="Register", padding="10")
        register_group.pack(pady=10, padx=20, fill="x")

        ttk.Label(register_group, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.reg_username_entry = ttk.Entry(register_group, width=30)
        self.reg_username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(register_group, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reg_email_entry = ttk.Entry(register_group, width=30)
        self.reg_email_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(register_group, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.reg_password_entry = ttk.Entry(register_group, show="*", width=30)
        self.reg_password_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(register_group, text="Register", command=self.register).grid(row=3, column=0, columnspan=2, pady=10)

        # Exit Button
        ttk.Button(self, text="Exit", command=self.controller.quit).pack(pady=20)


    def login(self):
        email = self.login_email_entry.get()
        password = self.login_password_entry.get()

        if not email or not password:
            messagebox.showerror("Login Error", "Please enter both email and password.")
            return

        try:
            result = self.controller.auth.login(email, password)
            if result and isinstance(result, tuple) and len(result) > 0:
                self.controller.current_user_id = result[0]
                self.controller.current_username = email # Fetch username if needed later
                messagebox.showinfo("Login Success", "Login successful!")
                self.controller.show_main_app_frame()
            else:
                messagebox.showerror("Login Error", "Invalid email or password.")
        except Exception as e:
            messagebox.showerror("Login Error", f"An error occurred during login: {e}")
            print(f"Login exception: {e}") # Log error


    def register(self):
        username = self.reg_username_entry.get()
        email = self.reg_email_entry.get()
        password = self.reg_password_entry.get()

        if not username or not email or not password:
            messagebox.showerror("Registration Error", "Please fill in all fields.")
            return

        try:
            success = self.controller.auth.register(username, password, email)
            if success:
                messagebox.showinfo("Registration Success", "Registration successful! Please login.")
                # Clear registration fields
                self.reg_username_entry.delete(0, tk.END)
                self.reg_email_entry.delete(0, tk.END)
                self.reg_password_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Registration Error", "Username or email already exists, or input is invalid.")
        except Exception as e:
             messagebox.showerror("Registration Error", f"An error occurred during registration: {e}")
             print(f"Registration exception: {e}") # Log error


class MainAppFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top frame for logout and user info (optional)
        top_frame = ttk.Frame(self)
        top_frame.pack(side="top", fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text=f"User: {self.controller.current_username} (ID: {self.controller.current_user_id})").pack(side="left")
        ttk.Button(top_frame, text="Logout", command=self.controller.logout).pack(side="right")

        # Notebook for different sections
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Create tabs
        self.portfolio_tab = ttk.Frame(self.notebook, padding="10")
        self.stocklist_tab = ttk.Frame(self.notebook, padding="10")
        self.friends_tab = ttk.Frame(self.notebook, padding="10")
        self.stockinfo_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.portfolio_tab, text='Portfolio')
        self.notebook.add(self.stocklist_tab, text='Stock Lists')
        self.notebook.add(self.friends_tab, text='Friends')
        self.notebook.add(self.stockinfo_tab, text='Stock Info')

        # Initialize Portfolio Tab
        self.setup_portfolio_tab()

        # Initialize Stock List Tab
        self.setup_stocklist_tab()

        # Initialize Friends Tab
        self.setup_friends_tab()

        # Initialize Stock Info Tab
        self.setup_stockinfo_tab()

        # Add delete account button
        ttk.Button(self, text="Delete Account", command=self.delete_account).pack(side="bottom", pady=10)

    def setup_portfolio_tab(self):
        # Portfolio Management Frame
        management_frame = ttk.Frame(self.portfolio_tab)
        management_frame.pack(fill="x", padx=5, pady=5)

        # Create Portfolio Button
        ttk.Button(management_frame, text="Create New Portfolio", command=self.create_portfolio).pack(side="left", padx=5)
        
        # Portfolio Selection
        ttk.Label(management_frame, text="Select Portfolio:").pack(side="left", padx=5)
        self.portfolio_var = tk.StringVar()
        self.portfolio_combo = ttk.Combobox(management_frame, textvariable=self.portfolio_var, state="readonly")
        self.portfolio_combo.pack(side="left", padx=5)
        self.portfolio_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_portfolio())

        # Portfolio Details Frame
        self.details_frame = ttk.LabelFrame(self.portfolio_tab, text="Portfolio Details", padding="10")
        self.details_frame.pack(fill="x", padx=5, pady=5)

        # Create labels for portfolio details
        self.portfolio_name_label = ttk.Label(self.details_frame, text="Portfolio Name: -")
        self.portfolio_name_label.pack(side="left", padx=10)
        
        self.cash_balance_label = ttk.Label(self.details_frame, text="Cash Balance: $0.00")
        self.cash_balance_label.pack(side="left", padx=10)
        
        self.total_shares_label = ttk.Label(self.details_frame, text="Total Shares: 0")
        self.total_shares_label.pack(side="left", padx=10)
        
        self.total_value_label = ttk.Label(self.details_frame, text="Total Value: $0.00")
        self.total_value_label.pack(side="left", padx=10)
        
        # Portfolio Holdings Frame
        holdings_frame = ttk.LabelFrame(self.portfolio_tab, text="Holdings", padding="10")
        holdings_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Treeview for holdings
        columns = ('Symbol', 'Shares')
        self.holdings_tree = ttk.Treeview(holdings_frame, columns=columns, show='headings')
        
        # Configure column headings
        for col in columns:
            self.holdings_tree.heading(col, text=col)
            self.holdings_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(holdings_frame, orient="vertical", command=self.holdings_tree.yview)
        self.holdings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.holdings_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons Frame
        buttons_frame = ttk.Frame(self.portfolio_tab)
        buttons_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(buttons_frame, text="Add Stock", command=self.add_stock).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Remove Stock", command=self.remove_stock).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_portfolio).pack(side="right", padx=5)

        # Graph Frame
        graph_frame = ttk.LabelFrame(self.portfolio_tab, text="Portfolio Performance", padding="10")
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create matplotlib figure for portfolio performance
        self.figure = plt.Figure(figsize=(6, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Initial portfolio load
        self.refresh_portfolio()

    def setup_stocklist_tab(self):
        # Stock List Management Frame
        management_frame = ttk.Frame(self.stocklist_tab)
        management_frame.pack(fill="x", padx=5, pady=5)

        # Create Stock List Button
        ttk.Button(management_frame, text="Create New Stock List", command=self.create_stocklist).pack(side="left", padx=5)
        
        # Stock List Selection
        ttk.Label(management_frame, text="Select Stock List:").pack(side="left", padx=5)
        self.stocklist_var = tk.StringVar()
        self.stocklist_combo = ttk.Combobox(management_frame, textvariable=self.stocklist_var, state="readonly")
        self.stocklist_combo.pack(side="left", padx=5)
        self.stocklist_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_stocklist())

        # Stock List Details Frame
        self.stocklist_details_frame = ttk.LabelFrame(self.stocklist_tab, text="Stock List Details", padding="10")
        self.stocklist_details_frame.pack(fill="x", padx=5, pady=5)

        # Create labels for stock list details
        self.stocklist_name_label = ttk.Label(self.stocklist_details_frame, text="List Name: -")
        self.stocklist_name_label.pack(side="left", padx=10)
        
        self.stocklist_creator_label = ttk.Label(self.stocklist_details_frame, text="Creator: -")
        self.stocklist_creator_label.pack(side="left", padx=10)
        
        self.stocklist_public_label = ttk.Label(self.stocklist_details_frame, text="Public: -")
        self.stocklist_public_label.pack(side="left", padx=10)
        
        self.stocklist_value_label = ttk.Label(self.stocklist_details_frame, text="Total Value: $0.00")
        self.stocklist_value_label.pack(side="left", padx=10)

        # Stock List Holdings Frame
        holdings_frame = ttk.LabelFrame(self.stocklist_tab, text="Stocks", padding="10")
        holdings_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Treeview for holdings
        columns = ('Symbol', 'Shares')
        self.stocklist_tree = ttk.Treeview(holdings_frame, columns=columns, show='headings')
        
        # Configure column headings
        for col in columns:
            self.stocklist_tree.heading(col, text=col)
            self.stocklist_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(holdings_frame, orient="vertical", command=self.stocklist_tree.yview)
        self.stocklist_tree.configure(yscrollcommand=scrollbar.set)
        
        self.stocklist_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons Frame
        buttons_frame = ttk.Frame(self.stocklist_tab)
        buttons_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(buttons_frame, text="Add Stock", command=self.add_stock_to_list).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Remove Stock", command=self.remove_stock_from_list).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Share List", command=self.share_stocklist).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Unshare List", command=self.unshare_stocklist).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Delete List", command=self.delete_stocklist).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_stocklist).pack(side="right", padx=5)

        # Reviews Frame
        reviews_frame = ttk.LabelFrame(self.stocklist_tab, text="Reviews", padding="10")
        reviews_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Treeview for reviews
        columns = ('Review ID', 'User ID', 'Text', 'Created', 'Updated')
        self.reviews_tree = ttk.Treeview(reviews_frame, columns=columns, show='headings', height=4)
        
        # Configure column headings
        for col in columns:
            self.reviews_tree.heading(col, text=col)
            self.reviews_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(reviews_frame, orient="vertical", command=self.reviews_tree.yview)
        self.reviews_tree.configure(yscrollcommand=scrollbar.set)
        
        self.reviews_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Review Buttons Frame
        review_buttons_frame = ttk.Frame(self.stocklist_tab)
        review_buttons_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(review_buttons_frame, text="Add Review", command=self.add_review).pack(side="left", padx=5)
        ttk.Button(review_buttons_frame, text="Delete Review", command=self.delete_review).pack(side="left", padx=5)

        # Initial stock list load
        self.refresh_stocklist_list()
        self.refresh_stocklist()

    def setup_friends_tab(self):
        # Create main container for friends tab
        friends_container = ttk.Frame(self.friends_tab)
        friends_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Left side - Friends List
        left_frame = ttk.LabelFrame(friends_container, text="My Friends", padding="10")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Create Treeview for friends list
        columns = ('User ID', 'Username')
        self.friends_tree = ttk.Treeview(left_frame, columns=columns, show='headings')
        for col in columns:
            self.friends_tree.heading(col, text=col)
            self.friends_tree.column(col, width=100)

        # Add scrollbar to friends list
        friends_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.friends_tree.yview)
        self.friends_tree.configure(yscrollcommand=friends_scrollbar.set)
        
        self.friends_tree.pack(side="left", fill="both", expand=True)
        friends_scrollbar.pack(side="right", fill="y")

        # Right side - Friend Requests
        right_frame = ttk.Frame(friends_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Incoming Requests
        incoming_frame = ttk.LabelFrame(right_frame, text="Incoming Friend Requests", padding="10")
        incoming_frame.pack(fill="both", expand=True, pady=(0, 5))

        columns = ('Request ID', 'From User', 'Username')
        self.incoming_tree = ttk.Treeview(incoming_frame, columns=columns, show='headings', height=5)
        for col in columns:
            self.incoming_tree.heading(col, text=col)
            self.incoming_tree.column(col, width=100)

        incoming_scrollbar = ttk.Scrollbar(incoming_frame, orient="vertical", command=self.incoming_tree.yview)
        self.incoming_tree.configure(yscrollcommand=incoming_scrollbar.set)
        
        self.incoming_tree.pack(side="left", fill="both", expand=True)
        incoming_scrollbar.pack(side="right", fill="y")

        # Outgoing Requests
        outgoing_frame = ttk.LabelFrame(right_frame, text="Outgoing Friend Requests", padding="10")
        outgoing_frame.pack(fill="both", expand=True, pady=5)

        columns = ('Request ID', 'To User', 'Username')
        self.outgoing_tree = ttk.Treeview(outgoing_frame, columns=columns, show='headings', height=5)
        for col in columns:
            self.outgoing_tree.heading(col, text=col)
            self.outgoing_tree.column(col, width=100)

        outgoing_scrollbar = ttk.Scrollbar(outgoing_frame, orient="vertical", command=self.outgoing_tree.yview)
        self.outgoing_tree.configure(yscrollcommand=outgoing_scrollbar.set)
        
        self.outgoing_tree.pack(side="left", fill="both", expand=True)
        outgoing_scrollbar.pack(side="right", fill="y")

        # Buttons Frame
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.pack(fill="x", pady=5)

        ttk.Button(buttons_frame, text="Send Friend Request", command=self.send_friend_request).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Accept Request", command=self.accept_friend_request).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Reject Request", command=self.reject_friend_request).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Delete Friend", command=self.delete_friend).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_friends).pack(side="right", padx=5)

        # Initial load of friends data
        self.refresh_friends()

    def setup_stockinfo_tab(self):
        # Stock Info Management Frame
        management_frame = ttk.Frame(self.stockinfo_tab)
        management_frame.pack(fill="x", padx=5, pady=5)

        # Stock Symbol Entry
        ttk.Label(management_frame, text="Stock Symbol:").pack(side="left", padx=5)
        self.stock_symbol_var = tk.StringVar()
        self.stock_symbol_entry = ttk.Entry(management_frame, textvariable=self.stock_symbol_var)
        self.stock_symbol_entry.pack(side="left", padx=5)

        # Period Selection
        ttk.Label(management_frame, text="Period:").pack(side="left", padx=5)
        self.period_var = tk.StringVar(value="5d")
        period_combo = ttk.Combobox(management_frame, textvariable=self.period_var, values=["5d", "1mo", "6mo", "1y", "5y", "all"], state="readonly", width=5)
        period_combo.pack(side="left", padx=5)

        # Buttons Frame
        buttons_frame = ttk.Frame(self.stockinfo_tab)
        buttons_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(buttons_frame, text="View Stock Info", command=self.view_stock_info).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Fetch Latest Data", command=self.fetch_stock_info).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Fetch All Stocks", command=self.fetch_all_stocks).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Predict Price", command=self.predict_stock_price).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Show Graph", command=self.show_stock_graph).pack(side="left", padx=5)

        # Stock Data Frame
        data_frame = ttk.LabelFrame(self.stockinfo_tab, text="Stock Data", padding="10")
        data_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Treeview for stock data
        columns = ("Date", "Open", "High", "Low", "Close", "Volume")
        self.stock_tree = ttk.Treeview(data_frame, columns=columns, show='headings')
        
        # Configure column headings
        for col in columns:
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scrollbar.set)
        
        self.stock_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Graph Frame
        self.graph_frame = ttk.LabelFrame(self.stockinfo_tab, text="Stock Price Chart", padding="10")
        self.graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.stock_figure = plt.Figure(figsize=(6, 4))
        self.stock_ax = self.stock_figure.add_subplot(111)
        self.stock_canvas = FigureCanvasTkAgg(self.stock_figure, self.graph_frame)
        self.stock_canvas.get_tk_widget().pack(fill="both", expand=True)

    def view_stock_info(self):
        symbol = self.stock_symbol_var.get().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        period = self.period_var.get()
        try:
            data = self.controller.stock_data.view_stock_info(symbol, period)
            if data:
                # Clear existing items
                for item in self.stock_tree.get_children():
                    self.stock_tree.delete(item)

                # Insert new data
                for row in data:
                    self.stock_tree.insert('', 'end', values=row)
            else:
                messagebox.showinfo("Info", f"No data found for {symbol}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch stock data: {str(e)}")

    def fetch_stock_info(self):
        symbol = self.stock_symbol_var.get().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        days = simpledialog.askinteger("Fetch Data", "Enter number of days to fetch (1-365):", initialvalue=5, minvalue=1, maxvalue=365)
        if days is None:  # User cancelled
            return

        try:
            result = self.controller.stock_data.fetch_and_store_daily_info_yahoo(symbol, days)
            if result:
                messagebox.showinfo("Success", f"Successfully fetched {days} days of data for {symbol}")
                self.view_stock_info()  # Refresh display
            else:
                messagebox.showerror("Error", f"Failed to fetch data for {symbol}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def fetch_all_stocks(self):
        days = simpledialog.askinteger("Fetch All Stocks", "Enter number of days to fetch (1-365):", initialvalue=5, minvalue=1, maxvalue=365)
        if days is None:  # User cancelled
            return

        try:
            result = self.controller.stock_data.fetch_and_store_all_stocks_daily_info(days)
            if result:
                messagebox.showinfo("Success", f"Successfully fetched {days} days of data for all stocks")
            else:
                messagebox.showerror("Error", "Failed to fetch data for all stocks")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def predict_stock_price(self):
        symbol = self.stock_symbol_var.get().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        days = simpledialog.askinteger("Predict Price", "Enter number of days to predict:", initialvalue=30, minvalue=1)
        if days is None:  # User cancelled
            return

        try:
            predictions, confidence = self.controller.stock_data.predict_stock_price(symbol, days)
            if predictions:
                # Create a new window for predictions
                pred_window = tk.Toplevel(self)
                pred_window.title(f"Price Predictions for {symbol}")
                pred_window.geometry("600x400")

                # Create a frame for the prediction data
                pred_frame = ttk.Frame(pred_window, padding="10")
                pred_frame.pack(fill="both", expand=True)

                # Add confidence label
                ttk.Label(pred_frame, text=f"Prediction Confidence: {confidence:.2%}").pack(pady=5)

                # Create Treeview for predictions
                columns = ("Date", "Predicted Value")
                pred_tree = ttk.Treeview(pred_frame, columns=columns, show='headings')
                for col in columns:
                    pred_tree.heading(col, text=col)
                    pred_tree.column(col, width=150)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(pred_frame, orient="vertical", command=pred_tree.yview)
                pred_tree.configure(yscrollcommand=scrollbar.set)
                
                pred_tree.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                # Insert prediction data
                df = pd.DataFrame(predictions)
                for _, row in df.iterrows():
                    pred_tree.insert('', 'end', values=(row['date'], f"${row['value']:.2f}"))

                # Add a graph
                graph_frame = ttk.Frame(pred_window, padding="10")
                graph_frame.pack(fill="both", expand=True)

                fig = plt.Figure(figsize=(8, 4))
                ax = fig.add_subplot(111)
                ax.plot(df['date'], df['value'], marker='o')
                ax.set_title(f'Stock Price Predictions for {symbol}')
                ax.set_xlabel('Date')
                ax.set_ylabel('Price ($)')
                ax.grid(True)

                canvas = FigureCanvasTkAgg(fig, graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)

            else:
                messagebox.showinfo("Info", "No predictions available for this stock")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_stock_graph(self):
        symbol = self.stock_symbol_var.get().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        period = self.period_var.get()
        try:
            # Clear previous plot
            self.stock_ax.clear()
            
            # Get the data
            data = self.controller.stock_data.view_stock_info(symbol, period)
            if data:
                # Convert data for plotting
                df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Plot the data
                self.stock_ax.plot(df['Date'], df['Close'], label='Close Price')
                self.stock_ax.set_title(f'{symbol} Stock Price - {period}')
                self.stock_ax.set_xlabel('Date')
                self.stock_ax.set_ylabel('Price ($)')
                self.stock_ax.grid(True)
                self.stock_ax.legend()
                
                # Rotate x-axis labels for better readability
                plt.setp(self.stock_ax.get_xticklabels(), rotation=45)
                
                # Adjust layout to prevent label cutoff
                self.stock_figure.tight_layout()
                
                # Refresh canvas
                self.stock_canvas.draw()
            else:
                messagebox.showinfo("Info", f"No data found for {symbol}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display graph: {str(e)}")

    def refresh_portfolio_list(self):
        try:
            portfolios = self.controller.portfolio.view_user_portfolios(self.controller.current_user_id)
            if portfolios:
                # Format: "Portfolio Name (ID: x) - $y"
                portfolio_list = [f"{p[1]} (ID: {p[0]}) - ${float(p[2]):.2f}" for p in portfolios]
                self.portfolio_combo['values'] = portfolio_list
                if not self.portfolio_var.get() and portfolio_list:
                    self.portfolio_combo.set(portfolio_list[0])
            else:
                self.portfolio_combo['values'] = []
                self.portfolio_var.set('')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh portfolio list: {str(e)}")

    def get_selected_portfolio_id(self):
        selected = self.portfolio_var.get()
        if selected:
            # Extract ID from the format "Portfolio Name (ID: x) - $y"
            import re
            match = re.search(r'ID: (\d+)', selected)
            if match:
                return int(match.group(1))
        return None

    def create_portfolio(self):
        portfolio_name = simpledialog.askstring("Create Portfolio", "Enter portfolio name:")
        if not portfolio_name:
            return
            
        initial_cash = simpledialog.askfloat("Create Portfolio", "Enter initial cash balance:", initialvalue=10000.0)
        if initial_cash is None:  # User cancelled
            return
            
        try:
            portfolio_id = self.controller.portfolio.create_portfolio(
                self.controller.current_user_id,
                portfolio_name,
                initial_cash
            )
            
            if portfolio_id:
                messagebox.showinfo("Success", f"Created new portfolio '{portfolio_name}' with ${initial_cash:.2f}")
                self.refresh_portfolio_list()
                self.refresh_portfolio()
            else:
                messagebox.showerror("Error", "Failed to create portfolio")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_stock(self, event=None):
        # Get portfolio ID
        portfolio_id = self.get_selected_portfolio_id()
        if not portfolio_id:
            messagebox.showerror("Error", "Please select a portfolio first")
            return
            
        # Get stock symbol
        symbol = simpledialog.askstring("Add Stock", "Enter stock symbol:")
        if not symbol:
            return
        symbol = symbol.upper()
        
        try:
            # First fetch stock data
            self.controller.stock_data.fetch_and_store_daily_info_yahoo(symbol, num_days=5)
            
            # Get number of shares
            shares = simpledialog.askfloat("Add Stock", "Enter number of shares:")
            if shares is None:  # User cancelled
                return
            if shares < 1 or shares > 10000:
                messagebox.showerror("Error", "Please enter a number between 1 and 10000")
                return
                
            # Try to buy shares
            success = self.controller.portfolio.buy_stock_shares(
                self.controller.current_user_id,
                portfolio_id,
                symbol,
                shares
            )
            
            if success:
                messagebox.showinfo("Success", f"Successfully purchased {shares} shares of {symbol}!")
                self.refresh_portfolio()
            else:
                cash_balance = self.controller.portfolio.get_cash_balance(portfolio_id, self.controller.current_user_id)
                messagebox.showerror("Error", f"Purchase failed. Current cash balance: ${cash_balance:.2f}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error purchasing stock: {str(e)}")

    def remove_stock(self):
        # Get selected item from treeview
        selected_item = self.holdings_tree.selection()
        if not selected_item:
            messagebox.showwarning("Remove Stock", "Please select a stock to remove")
            return

        symbol = self.holdings_tree.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Remove Stock", f"Are you sure you want to remove {symbol} from your portfolio?"):
            try:
                success = self.controller.portfolio.remove_stock(
                    self.controller.current_user_id,
                    symbol
                )
                
                if success:
                    messagebox.showinfo("Success", f"Removed {symbol} from portfolio")
                    self.refresh_portfolio()
                else:
                    messagebox.showerror("Error", "Failed to remove stock from portfolio")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def refresh_portfolio(self):
        try:
            portfolio_id = self.get_selected_portfolio_id()
            if not portfolio_id:
                print("No portfolio selected")
                # Clear the treeview if no portfolio is selected
                for item in self.holdings_tree.get_children():
                    self.holdings_tree.delete(item)
                self.portfolio_name_label.config(text="Portfolio Name: -")
                self.cash_balance_label.config(text="Cash Balance: $0.00")
                self.total_shares_label.config(text="Total Shares: 0")
                self.total_value_label.config(text="Total Value: $0.00")
                return

            print(f"Fetching portfolio data for portfolio_id: {portfolio_id}")
            # Get portfolio data
            portfolio_data = self.controller.portfolio.view_portfolio(
                self.controller.current_user_id, portfolio_id)
            
            print(f"Portfolio data received: {portfolio_data}")
            
            if not portfolio_data:
                print("No portfolio data found")
                messagebox.showinfo("Info", "No portfolio data found.")
                return

            # Clear existing items
            for item in self.holdings_tree.get_children():
                self.holdings_tree.delete(item)

            # Update holdings
            total_value = 0
            total_shares = 0
            cash_balance = portfolio_data[0][1] if portfolio_data else 0

            # Get portfolio name from the combo box
            selected = self.portfolio_var.get()
            portfolio_name = selected.split(" (ID:")[0] if selected else "-"
            self.portfolio_name_label.config(text=f"Portfolio Name: {portfolio_name}")

            # Process portfolio data - only stocks (no cash)
            for holding in portfolio_data:
                try:
                    symbol = holding[2]
                    if not symbol:  # Skip if no symbol (cash balance row)
                        continue

                    shares = float(holding[3]) if holding[3] is not None else 0
                    total_shares += shares
                    
                    # Get current price from stock data to calculate total value
                    try:
                        stock_info = self.controller.stock_data.view_stock_info(symbol, period='1d')
                        if stock_info and len(stock_info) > 0:
                            current_price = float(stock_info[0][4])  # close price
                            value = shares * current_price
                            total_value += value

                            self.holdings_tree.insert('', 'end', values=(
                                symbol,
                                f"{shares:.2f}"
                            ))
                        else:
                            print(f"No stock info available for {symbol}")
                    except Exception as e:
                        print(f"Error getting stock info for {symbol}: {str(e)}")
                        continue
                except Exception as e:
                    print(f"Error processing holding {holding}: {str(e)}")
                    continue

            # Add cash to total value but don't show in holdings
            total_value += cash_balance

            # Update summary labels
            self.cash_balance_label.config(text=f"Cash Balance: ${cash_balance:.2f}")
            self.total_shares_label.config(text=f"Total Shares: {total_shares:.2f}")
            self.total_value_label.config(text=f"Total Value: ${total_value:.2f}")

            # Refresh the performance graph
            self.update_performance_graph()

        except Exception as e:
            print(f"Failed to refresh portfolio: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to refresh portfolio data: {str(e)}")

    def update_performance_graph(self):
        try:
            portfolio_id = self.get_selected_portfolio_id()
            if not portfolio_id:
                return

            # Get historical portfolio value data using view_portfolio_history
            historical_data = self.controller.portfolio.view_portfolio_history(
                self.controller.current_user_id,
                portfolio_id,
                period='1mo'  # Show last month of data
            )
            
            if not historical_data:
                return
            
            # Clear previous plot
            self.ax.clear()
            
            # Convert data for plotting
            dates = [entry[0] for entry in historical_data]  # timestamp
            values = [float(entry[1]) for entry in historical_data]  # total_value
            
            self.ax.plot(dates, values, '-b')
            self.ax.set_title('Portfolio Value Over Time')
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('Value ($)')
            self.ax.grid(True)
            
            # Rotate x-axis labels for better readability
            plt.setp(self.ax.get_xticklabels(), rotation=45)
            
            # Adjust layout to prevent label cutoff
            self.figure.tight_layout()
            
            # Refresh canvas
            self.canvas.draw()

        except Exception as e:
            print(f"Error updating performance graph: {str(e)}")

    def delete_account(self):
        if messagebox.askyesno("Delete Account", "WARNING: This action is permanent and cannot be undone. Are you sure you want to delete your account?"):
            password = simpledialog.askstring("Password Confirmation", "Enter your password to confirm deletion:", show='*')
            if password:
                try:
                    success = self.controller.auth.delete_account(
                        self.controller.current_user_id,
                        password
                    )
                    if success:
                        messagebox.showinfo("Account Deleted", "Your account has been successfully deleted.")
                        self.controller.logout()
                    else:
                        messagebox.showerror("Error", "Failed to delete account. Please check your password and try again.")
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred while deleting account: {str(e)}")

    def refresh_friends(self):
        # Clear existing items
        for tree in [self.friends_tree, self.incoming_tree, self.outgoing_tree]:
            for item in tree.get_children():
                tree.delete(item)

        try:
            # Load friends list
            friends_list = self.controller.friends.view_friends(self.controller.current_user_id)
            if friends_list:
                for friend_id, friend_name in friends_list:
                    self.friends_tree.insert('', 'end', values=(friend_id, friend_name))

            # Load incoming requests
            incoming_requests = self.controller.friends.view_incoming_requests(self.controller.current_user_id)
            if incoming_requests:
                for req in incoming_requests:
                    self.incoming_tree.insert('', 'end', values=(req[0], req[1], req[2]))

            # Load outgoing requests
            outgoing_requests = self.controller.friends.view_outgoing_requests(self.controller.current_user_id)
            if outgoing_requests:
                for req in outgoing_requests:
                    self.outgoing_tree.insert('', 'end', values=(req[0], req[1], req[2]))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh friends data: {str(e)}")

    def send_friend_request(self):
        receiver_id = simpledialog.askinteger("Send Friend Request", "Enter user ID to send friend request:")
        if receiver_id is not None:
            try:
                result = self.controller.friends.send_friend_request(self.controller.current_user_id, receiver_id)
                if result:
                    if result > 0:
                        messagebox.showinfo("Success", f"Friend request sent successfully to user {receiver_id}.")
                    elif result == -1:
                        messagebox.showwarning("Warning", "You are already friends or have a pending request with this user.")
                    elif result == -2:
                        messagebox.showwarning("Warning", "You can only send one request every 5 minutes.")
                    elif result == -3:
                        messagebox.showwarning("Warning", "You can't send a friend request to yourself.")
                    self.refresh_friends()
                else:
                    messagebox.showerror("Error", "Failed to send friend request. Check if the user exists.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def accept_friend_request(self):
        selected = self.incoming_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a friend request to accept.")
            return

        request_id = self.incoming_tree.item(selected[0])['values'][0]
        try:
            result = self.controller.friends.accept_friend_request(request_id, self.controller.current_user_id)
            if result:
                messagebox.showinfo("Success", "Friend request accepted successfully.")
                self.refresh_friends()
            else:
                messagebox.showerror("Error", "Failed to accept friend request.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def reject_friend_request(self):
        selected = self.incoming_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a friend request to reject.")
            return

        request_id = self.incoming_tree.item(selected[0])['values'][0]
        try:
            result = self.controller.friends.reject_friend_request(request_id, self.controller.current_user_id)
            if result:
                messagebox.showinfo("Success", "Friend request rejected successfully.")
                self.refresh_friends()
            else:
                messagebox.showerror("Error", "Failed to reject friend request.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_friend(self):
        selected = self.friends_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a friend to delete.")
            return

        friend_id = self.friends_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to remove this friend?"):
            try:
                result = self.controller.friends.delete_friend(self.controller.current_user_id, friend_id)
                if result:
                    messagebox.showinfo("Success", "Friend removed successfully.")
                    self.refresh_friends()
                else:
                    messagebox.showerror("Error", "Failed to remove friend.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def refresh_stocklist_list(self):
        try:
            stocklists = self.controller.stock_list.view_accessible_stock_lists(self.controller.current_user_id)
            if stocklists:
                # Format: "List Name (ID: x) - Creator: y"
                stocklist_list = [f"{sl[1]} (ID: {sl[0]}) - Creator: {sl[3]}" for sl in stocklists]
                self.stocklist_combo['values'] = stocklist_list
                if not self.stocklist_var.get() and stocklist_list:
                    self.stocklist_combo.set(stocklist_list[0])
            else:
                self.stocklist_combo['values'] = []
                self.stocklist_var.set('')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh stock list list: {str(e)}")

    def get_selected_stocklist_id(self):
        selected = self.stocklist_var.get()
        if selected:
            # Extract ID from the format "List Name (ID: x) - Creator: y"
            import re
            match = re.search(r'ID: (\d+)', selected)
            if match:
                return int(match.group(1))
        return None

    def create_stocklist(self):
        stocklist_name = simpledialog.askstring("Create Stock List", "Enter stock list name:")
        if not stocklist_name:
            return
            
        is_public = messagebox.askyesno("Create Stock List", "Make this list public?")
        
        try:
            stocklist_id = self.controller.stock_list.create_stock_list(
                self.controller.current_user_id,
                stocklist_name,
                is_public
            )
            
            if stocklist_id:
                messagebox.showinfo("Success", f"Created new stock list '{stocklist_name}'")
                self.refresh_stocklist_list()
                self.refresh_stocklist()
            else:
                messagebox.showerror("Error", "Failed to create stock list")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_stock_to_list(self):
        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return
            
        symbol = simpledialog.askstring("Add Stock", "Enter stock symbol:")
        if not symbol:
            return
        symbol = symbol.upper()
        
        shares = simpledialog.askfloat("Add Stock", "Enter number of shares:")
        if shares is None:  # User cancelled
            return
        if shares < 1:
            messagebox.showerror("Error", "Please enter a positive number of shares")
            return
            
        try:
            success = self.controller.stock_list.add_stock_to_list(
                self.controller.current_user_id,
                stocklist_id,
                symbol,
                shares
            )
            
            if success:
                messagebox.showinfo("Success", f"Added {shares} shares of {symbol} to stock list")
                self.refresh_stocklist()
            else:
                messagebox.showerror("Error", "Failed to add stock to list")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding stock: {str(e)}")

    def remove_stock_from_list(self):
        selected_item = self.stocklist_tree.selection()
        if not selected_item:
            messagebox.showwarning("Remove Stock", "Please select a stock to remove")
            return

        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return

        symbol = self.stocklist_tree.item(selected_item[0])['values'][0]
        shares = simpledialog.askfloat("Remove Stock", f"Enter number of shares of {symbol} to remove:")
        if shares is None:  # User cancelled
            return
        if shares < 1:
            messagebox.showerror("Error", "Please enter a positive number of shares")
            return

        try:
            success = self.controller.stock_list.remove_stock_from_list(
                self.controller.current_user_id,
                stocklist_id,
                symbol,
                shares
            )
            
            if success:
                messagebox.showinfo("Success", f"Removed {shares} shares of {symbol} from stock list")
                self.refresh_stocklist()
            else:
                messagebox.showerror("Error", "Failed to remove stock from list")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def share_stocklist(self):
        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return

        friend_id = simpledialog.askinteger("Share Stock List", "Enter friend's user ID:")
        if friend_id is None:  # User cancelled
            return

        try:
            result = self.controller.stock_list.share_stock_list(stocklist_id, self.controller.current_user_id, friend_id)
            if result == 1:
                messagebox.showinfo("Success", f"Stock list shared with user {friend_id}")
            elif result == -1:
                messagebox.showerror("Error", "You do not own this stock list")
            elif result == -2:
                messagebox.showerror("Error", "User is not your friend")
            else:
                messagebox.showerror("Error", "Failed to share stock list")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def unshare_stocklist(self):
        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return

        friend_id = simpledialog.askinteger("Unshare Stock List", "Enter friend's user ID:")
        if friend_id is None:  # User cancelled
            return

        try:
            success = self.controller.stock_list.unshare_stock_list(stocklist_id, self.controller.current_user_id, friend_id)
            if success:
                messagebox.showinfo("Success", f"Stock list unshared with user {friend_id}")
            else:
                messagebox.showerror("Error", "Failed to unshare stock list")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_stocklist(self):
        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return

        if messagebox.askyesno("Delete Stock List", "Are you sure you want to delete this stock list?"):
            try:
                success = self.controller.stock_list.delete_stock_list(stocklist_id, self.controller.current_user_id)
                if success:
                    messagebox.showinfo("Success", "Stock list deleted successfully")
                    self.refresh_stocklist_list()
                    self.refresh_stocklist()
                else:
                    messagebox.showerror("Error", "Failed to delete stock list")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_review(self):
        stocklist_id = self.get_selected_stocklist_id()
        if not stocklist_id:
            messagebox.showerror("Error", "Please select a stock list first")
            return

        review_text = simpledialog.askstring("Add Review", "Enter your review:")
        if not review_text:
            return

        try:
            review_id = self.controller.reviews.create_review(
                self.controller.current_user_id,
                stocklist_id,
                review_text
            )
            
            if review_id:
                messagebox.showinfo("Success", "Review added successfully")
                self.refresh_stocklist()
            else:
                messagebox.showerror("Error", "Failed to add review")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_review(self):
        selected_item = self.reviews_tree.selection()
        if not selected_item:
            messagebox.showwarning("Delete Review", "Please select a review to delete")
            return

        review_id = self.reviews_tree.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Delete Review", "Are you sure you want to delete this review?"):
            try:
                success = self.controller.reviews.delete_review(review_id, self.controller.current_user_id)
                if success:
                    messagebox.showinfo("Success", "Review deleted successfully")
                    self.refresh_stocklist()
                else:
                    messagebox.showerror("Error", "Failed to delete review")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def refresh_stocklist(self):
        try:
            stocklist_id = self.get_selected_stocklist_id()
            if not stocklist_id:
                # Clear the treeviews if no stock list is selected
                for tree in [self.stocklist_tree, self.reviews_tree]:
                    for item in tree.get_children():
                        tree.delete(item)
                self.stocklist_name_label.config(text="List Name: -")
                self.stocklist_creator_label.config(text="Creator: -")
                self.stocklist_public_label.config(text="Public: -")
                self.stocklist_value_label.config(text="Total Value: $0.00")
                return

            # Get stock list data
            stocklist_data = self.controller.stock_list.view_stock_list(
                self.controller.current_user_id, stocklist_id)
            
            if not stocklist_data:
                messagebox.showinfo("Info", "No stock list data found.")
                return

            # Clear existing items
            for tree in [self.stocklist_tree, self.reviews_tree]:
                for item in tree.get_children():
                    tree.delete(item)

            # Get stock list name and creator from the combo box
            selected = self.stocklist_var.get()
            stocklist_name = selected.split(" (ID:")[0] if selected else "-"
            creator = selected.split("Creator: ")[1] if selected else "-"

            # Update details labels
            self.stocklist_name_label.config(text=f"List Name: {stocklist_name}")
            self.stocklist_creator_label.config(text=f"Creator: {creator}")
            
            # Process stock list data
            for item in stocklist_data:
                if item[3]:  # Only process items with a symbol
                    self.stocklist_tree.insert('', 'end', values=(
                        item[3],  # symbol
                        f"{float(item[4]):.2f}"  # shares
                    ))

            # Get total value
            total_value = self.controller.stock_list.compute_stock_list_value(
                self.controller.current_user_id,
                stocklist_id
            )
            self.stocklist_value_label.config(text=f"Total Value: ${total_value:.2f}")

            # Get public status
            stocklists = self.controller.stock_list.view_accessible_stock_lists(self.controller.current_user_id)
            for sl in stocklists:
                if sl[0] == stocklist_id:
                    self.stocklist_public_label.config(text=f"Public: {'Yes' if sl[4] else 'No'}")
                    break

            # Load reviews
            reviews_list = self.controller.reviews.view_reviews(stocklist_id, self.controller.current_user_id)
            if reviews_list:
                for review in reviews_list:
                    self.reviews_tree.insert('', 'end', values=review)

        except Exception as e:
            print(f"Failed to refresh stock list: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh stock list data: {str(e)}")


if __name__ == "__main__":
    # Setup database and load stock history
    setup_db(True)
    
    # Basic DB Connection Check (Optional but recommended)
    try:
        conn = psycopg2.connect(
            host='34.130.75.185',
            database='postgres',
            user='postgres',
            password='2357'
        )
        print("✅ Database connection successful.")
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure the database server is running and accessible.")

    app = StockApp()
    app.mainloop() 