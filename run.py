import subprocess
import os
import sys
import time
import signal
import platform
import traceback

# Define colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.ENDC}")

# Store process references to terminate them later
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully stop all processes"""
    print_colored("\nShutting down all processes...", Colors.WARNING)
    for process in processes:
        if process.poll() is None:  # If process is still running
            if platform.system() == "Windows":
                process.send_signal(signal.CTRL_C_EVENT)
            else:
                process.terminate()
    print_colored("All processes terminated. Goodbye!", Colors.GREEN)
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def run_app():
    """Run both backend and frontend applications"""
    print_colored("=== Starting Stock Social Network Application ===", Colors.HEADER)
    
    # Check if required commands are available
    if not check_requirements():
        return

    # Setup model files for frontend to use (without modifying backend)
    setup_model_files()

    # Start backend server
    print_colored("\n[1/2] Starting backend server...", Colors.BLUE)
    backend_cmd = ["python", "backend/launcher.py"]
    backend_process = subprocess.Popen(
        backend_cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(backend_process)
    
    # Wait a bit for backend to initialize
    time.sleep(2)
    
    # Check if backend is still running
    if backend_process.poll() is not None:
        print_colored("Backend failed to start. Error output:", Colors.FAIL)
        output, _ = backend_process.communicate()
        print_colored(output, Colors.FAIL)
        return
    
    # Start frontend development server
    print_colored("\n[2/2] Starting frontend server...", Colors.BLUE)
    frontend_cmd = ["npm", "run", "dev"]
    
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(frontend_process)
    
    print_colored("\nBoth servers are starting up!", Colors.GREEN)
    print_colored("• Backend is running on http://localhost:5001", Colors.GREEN)
    print_colored("• Frontend will be available at http://localhost:3000", Colors.GREEN)
    print_colored("\nPress Ctrl+C to stop all servers", Colors.WARNING)
    
    # Monitor and print output from both processes
    try:
        # Start threads to read output from both processes
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_colored("Backend process stopped unexpectedly!", Colors.FAIL)
                # Get any remaining output
                output, _ = backend_process.communicate()
                if output:
                    print_colored("Backend output before stopping:", Colors.FAIL)
                    print_colored(output, Colors.FAIL)
                break
                
            if frontend_process.poll() is not None:
                print_colored("Frontend process stopped unexpectedly!", Colors.FAIL)
                # Get any remaining output
                output, _ = frontend_process.communicate()
                if output:
                    print_colored("Frontend output before stopping:", Colors.FAIL)
                    print_colored(output, Colors.FAIL)
                break
                
            # Read output from backend
            try:
                backend_output = backend_process.stdout.readline()
                if backend_output:
                    print(f"{Colors.BLUE}[Backend]{Colors.ENDC} {backend_output.strip()}")
            except Exception as e:
                print_colored(f"Error reading backend output: {str(e)}", Colors.WARNING)
                
            # Read output from frontend
            try:
                frontend_output = frontend_process.stdout.readline()
                if frontend_output:
                    print(f"{Colors.GREEN}[Frontend]{Colors.ENDC} {frontend_output.strip()}")
            except Exception as e:
                print_colored(f"Error reading frontend output: {str(e)}", Colors.WARNING)
                
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print_colored(f"Error in process monitoring: {str(e)}", Colors.FAIL)
        traceback.print_exc()
        signal_handler(None, None)

def setup_model_files():
    """Ensure necessary models are in place for frontend to use"""
    print_colored("Setting up model files for frontend...", Colors.BLUE)
    
    # Ensure models directory exists in frontend
    frontend_models_dir = os.path.join("frontend", "src", "models")
    if not os.path.exists(frontend_models_dir):
        print_colored("Creating frontend models directory...", Colors.WARNING)
        os.makedirs(frontend_models_dir)
    
    # Create .env.local file with API URL
    env_file_path = os.path.join("frontend", ".env.local")
    with open(env_file_path, 'w') as f:
        f.write("NEXT_PUBLIC_API_URL=http://localhost:5001\n")
    print_colored("Created .env.local with API URL", Colors.GREEN)
    
    # Create model files if needed
    model_files = [
        {
            'filename': 'StockModels.ts',
            'content': """// Stock data model
export interface Stock {
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
}

// Stock list model
export interface StockList {
  stocklist_id: number;
  list_name: string;
  creator_id: number;
  is_public: boolean;
  created_at: string;
  stocks?: StockListStock[];
}

// Stock in stock list
export interface StockListStock {
  symbol: string;
  num_shares: number;
}

// Stock prediction model
export interface StockPrediction {
  symbol: string;
  predicted_prices: Array<{
    date: string;
    price: number;
  }>;
  confidence: number;
}"""
        },
        {
            'filename': 'UserModels.ts',
            'content': """// User model
export interface User {
  user_id: number;
  username: string;
  email: string;
  created_at: string;
}

// Login information
export interface LoginInfo {
  email: string;
  password: string;
}

// Registration information
export interface RegisterInfo {
  username: string;
  email: string;
  password: string;
}

// Friend request model
export interface FriendRequest {
  request_id: number;
  sender_id: number;
  receiver_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  sender_name?: string;
}"""
        },
        {
            'filename': 'PortfolioModels.ts',
            'content': """// Portfolio model
export interface Portfolio {
  portfolio_id: number;
  portfolio_name: string;
  user_id: number;
  cash_balance: number;
  created_at: string;
  stocks?: PortfolioStock[];
}

// Portfolio stock item
export interface PortfolioStock {
  symbol: string;
  num_shares: number;
  current_price?: number;
  total_value?: number;
}

// Portfolio transaction
export interface PortfolioTransaction {
  transaction_id: number;
  portfolio_id: number;
  symbol: string;
  transaction_type: 'BUY' | 'SELL' | 'CASH';
  shares: number;
  price: number;
  cash_change: number;
  transaction_time: string;
}

// Portfolio statistics
export interface PortfolioStats {
  stocks: Array<{
    symbol: string;
    cov: number;  // Coefficient of variation
    beta: number; // Beta coefficient
  }>;
  correlation_matrix: Array<Array<number>>; // Correlation matrix
}"""
        },
        {
            'filename': 'ReviewModels.ts',
            'content': """// Review model
export interface Review {
  review_id: number;
  user_id: number;
  stocklist_id: number;
  review_text: string;
  created_at: string;
  updated_at: string;
  reviewer_name?: string; // Reviewer name
}"""
        }
    ]
    
    for model_file in model_files:
        file_path = os.path.join(frontend_models_dir, model_file['filename'])
        if not os.path.exists(file_path):
            print_colored(f"Creating {model_file['filename']}...", Colors.WARNING)
            with open(file_path, 'w') as f:
                f.write(model_file['content'])
        else:
            print_colored(f"{model_file['filename']} already exists.", Colors.GREEN)
    
    print_colored("Frontend model setup complete!", Colors.GREEN)

def check_requirements():
    """Check if all required software is installed"""
    requirements_met = True
    
    # Check Python version
    print("Checking Python version...")
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_colored("❌ Python 3.8 or higher is required.", Colors.FAIL)
        requirements_met = False
    else:
        print_colored("✅ Python version is compatible.", Colors.GREEN)
    
    # Check if npm is installed
    print("Checking if npm is installed...")
    try:
        subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_colored("✅ npm is installed.", Colors.GREEN)
    except FileNotFoundError:
        print_colored("❌ npm is not installed. Please install Node.js and npm.", Colors.FAIL)
        requirements_met = False
    
    # Check if frontend dependencies are installed
    print("Checking frontend dependencies...")
    if not os.path.exists("frontend/node_modules"):
        print_colored("⚠️ Frontend dependencies not installed. Installing now...", Colors.WARNING)
        try:
            subprocess.run(["npm", "install"], cwd="frontend", check=True)
            print_colored("✅ Frontend dependencies installed successfully.", Colors.GREEN)
        except subprocess.CalledProcessError:
            print_colored("❌ Failed to install frontend dependencies.", Colors.FAIL)
            requirements_met = False
    else:
        print_colored("✅ Frontend dependencies already installed.", Colors.GREEN)
    
    # Check backend dependencies
    print("Checking backend dependencies...")
    missing_deps = []
    try:
        # Attempt to import required modules
        try:
            import psycopg2
        except ImportError:
            missing_deps.append("psycopg2-binary")
            
        try:
            import flask
        except ImportError:
            missing_deps.append("flask")
            
        try:
            import numpy
        except ImportError:
            missing_deps.append("numpy")
            
        try:
            import pandas
        except ImportError:
            missing_deps.append("pandas")
        
        if missing_deps:
            raise ImportError("Missing required packages")
        else:
            print_colored("✅ Backend dependencies are installed.", Colors.GREEN)
            
    except ImportError:
        print_colored(f"❌ Missing backend dependencies: {', '.join(missing_deps)}", Colors.FAIL)
        print_colored("Running pip install to get required dependencies...", Colors.WARNING)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print_colored("✅ Backend dependencies installed successfully.", Colors.GREEN)
        except subprocess.CalledProcessError:
            print_colored("❌ Failed to install backend dependencies.", Colors.FAIL)
            requirements_met = False
    
    return requirements_met

if __name__ == "__main__":
    run_app() 