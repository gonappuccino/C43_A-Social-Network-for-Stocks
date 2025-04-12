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
            database='template1',
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

        # Placeholder labels for other tabs (will be implemented later)
        ttk.Label(self.stocklist_tab, text="Stock List Management Content Here").pack()
        ttk.Label(self.friends_tab, text="Friends Management Content Here").pack()
        ttk.Label(self.stockinfo_tab, text="Stock Information Content Here").pack()

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
            self.holdings_tree.column(col, width=100)  # Adjust width as needed

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