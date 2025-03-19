import psycopg2
from flask import Flask, request, jsonify
from queries.user import User

app = Flask(__name__)

app.config['POSTGRES_HOST'] = 'localhost'
app.config['POSTGRES_DB'] = 'postgres'
app.config['POSTGRES_USER'] = 'postgres'
app.config['POSTGRES_PASSWORD'] = '2357'

try:
    conn = psycopg2.connect(
        host=app.config['POSTGRES_HOST'],
        database=app.config['POSTGRES_DB'],
        user=app.config['POSTGRES_USER'],
        password=app.config['POSTGRES_PASSWORD']
    )
    print("✅ Connected to PostgreSQL!")

except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")

def setup_db(conn):
    try:
        cursor = conn.cursor()
        for query in setup_queries:
            cursor.execute(query)
        conn.commit()
        cursor.close()

        print("✅ Database setup complete!")

    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")

# Instantiate the User class
user = User()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    email = data['email']
    success = user.register(username, password, email)
    if success:
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"message": "Username or email already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    user_id = user.login(email, password)
    if user_id:
        return jsonify({"user_id": user_id}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

@app.route('/create_portfolio', methods=['POST'])
def create_portfolio():
    data = request.json
    user_id = data['user_id']
    initial_cash = data.get('initial_cash', 0)
    portfolio_id = user.create_portfolio(user_id, initial_cash)
    return jsonify({"portfolio_id": portfolio_id}), 201

@app.route('/delete_portfolio', methods=['DELETE'])
def delete_portfolio():
    data = request.json
    portfolio_id = data['portfolio_id']
    deleted_id = user.delete_portfolio(portfolio_id)
    if deleted_id:
        return jsonify({"message": "Portfolio deleted successfully"}), 200
    else:
        return jsonify({"message": "Portfolio not found"}), 404

@app.route('/update_cash_balance', methods=['POST'])
def update_cash_balance():
    data = request.json
    portfolio_id = data['portfolio_id']
    amount = data['amount']
    updated_balance = user.update_cash_balance(portfolio_id, amount)
    if updated_balance is not None:
        return jsonify({"updated_balance": updated_balance}), 200
    else:
        return jsonify({"message": "Insufficient funds"}), 400

@app.route('/buy_stock_shares', methods=['POST'])
def buy_stock_shares():
    data = request.json
    portfolio_id = data['portfolio_id']
    symbol = data['symbol']
    num_shares = data['num_shares']
    result = user.buy_stock_shares(portfolio_id, symbol, num_shares)
    if result:
        return jsonify({"message": "Stock purchased successfully"}), 200
    else:
        return jsonify({"message": "Purchase failed"}), 400

@app.route('/sell_stock_shares', methods=['POST'])
def sell_stock_shares():
    data = request.json
    portfolio_id = data['portfolio_id']
    symbol = data['symbol']
    num_shares = data['num_shares']
    result = user.sell_stock_shares(portfolio_id, symbol, num_shares)
    if result:
        return jsonify({"message": "Stock sold successfully"}), 200
    else:
        return jsonify({"message": "Sale failed"}), 400

@app.route('/view_portfolio', methods=['GET'])
def view_portfolio():
    portfolio_id = request.args.get('portfolio_id')
    portfolio_data = user.view_portfolio(portfolio_id)
    return jsonify(portfolio_data), 200

@app.route('/view_portfolio_transactions', methods=['GET'])
def view_portfolio_transactions():
    portfolio_id = request.args.get('portfolio_id')
    transactions = user.view_portfolio_transactions(portfolio_id)
    return jsonify(transactions), 200

if __name__ == '__main__':
    setup_db(conn)
    app.run(debug=True)