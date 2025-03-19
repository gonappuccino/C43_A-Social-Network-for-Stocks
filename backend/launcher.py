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

@app.route('/create_stock_list', methods=['POST'])
def create_stock_list():
    data = request.json
    creator_id = data['creator_id']
    is_public = data.get('is_public', False)
    stocklist_id = user.create_stock_list(creator_id, is_public)
    return jsonify({"stocklist_id": stocklist_id}), 201

@app.route('/delete_stock_list', methods=['DELETE'])
def delete_stock_list():
    data = request.json
    stocklist_id = data['stocklist_id']
    deleted_id = user.delete_stock_list(stocklist_id)
    if deleted_id:
        return jsonify({"message": "Stock list deleted successfully"}), 200
    else:
        return jsonify({"message": "Stock list not found"}), 404

@app.route('/add_stock_to_list', methods=['POST'])
def add_stock_to_list():
    data = request.json
    stocklist_id = data['stocklist_id']
    symbol = data['symbol']
    num_shares = data['num_shares']
    result = user.add_stock_to_list(stocklist_id, symbol, num_shares)
    if result:
        return jsonify({"message": "Stock added to list successfully"}), 200
    else:
        return jsonify({"message": "Failed to add stock to list"}), 400

@app.route('/remove_stock_from_list', methods=['POST'])
def remove_stock_from_list():
    data = request.json
    stocklist_id = data['stocklist_id']
    symbol = data['symbol']
    num_shares = data['num_shares']
    result = user.remove_stock_from_list(stocklist_id, symbol, num_shares)
    if result:
        return jsonify({"message": "Stock removed from list successfully"}), 200
    else:
        return jsonify({"message": "Failed to remove stock from list"}), 400

@app.route('/view_stock_list', methods=['GET'])
def view_stock_list():
    stocklist_id = request.args.get('stocklist_id')
    stocklist_data = user.view_stock_list(stocklist_id)
    return jsonify(stocklist_data), 200

@app.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    data = request.json
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    result = user.send_friend_request(sender_id, receiver_id)
    if result:
        return jsonify({"message": "Friend request sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send friend request"}), 400

@app.route('/view_friends', methods=['GET'])
def view_friends():
    user_id = request.args.get('user_id')
    friends = user.view_friends(user_id)
    return jsonify(friends), 200

@app.route('/view_incoming_requests', methods=['GET'])
def view_incoming_requests():
    user_id = request.args.get('user_id')
    incoming_requests = user.view_incoming_requests(user_id)
    return jsonify(incoming_requests), 200

@app.route('/view_outgoing_requests', methods=['GET'])
def view_outgoing_requests():
    user_id = request.args.get('user_id')
    outgoing_requests = user.view_outgoing_requests(user_id)
    return jsonify(outgoing_requests), 200

@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request():
    data = request.json
    request_id = data['request_id']
    result = user.accept_friend_request(request_id)
    if result:
        return jsonify({"message": "Friend request accepted successfully"}), 200
    else:
        return jsonify({"message": "Failed to accept friend request"}), 400

@app.route('/reject_friend_request', methods=['POST'])
def reject_friend_request():
    data = request.json
    request_id = data['request_id']
    result = user.reject_friend_request(request_id)
    if result:
        return jsonify({"message": "Friend request rejected successfully"}), 200
    else:
        return jsonify({"message": "Failed to reject friend request"}), 400

@app.route('/delete_friend', methods=['POST'])
def delete_friend():
    data = request.json
    user_id = data['user_id']
    friend_id = data['friend_id']
    result = user.delete_friend(user_id, friend_id)
    if result:
        return jsonify({"message": "Friend deleted successfully"}), 200
    else:
        return jsonify({"message": "Failed to delete friend"}), 400

@app.route('/share_stock_list', methods=['POST'])
def share_stock_list():
    data = request.json
    stocklist_id = data['stocklist_id']
    owner_id = data['owner_id']
    friend_id = data['friend_id']
    result = user.share_stock_list(stocklist_id, owner_id, friend_id)
    if result:
        return jsonify({"message": "Stock list shared successfully"}), 200
    else:
        return jsonify({"message": "Failed to share stock list"}), 400

@app.route('/view_accessible_stock_lists', methods=['GET'])
def view_accessible_stock_lists():
    user_id = request.args.get('user_id')
    stock_lists = user.view_accessible_stock_lists(user_id)
    return jsonify(stock_lists), 200

@app.route('/create_review', methods=['POST'])
def create_review():
    data = request.json
    user_id = data['user_id']
    stocklist_id = data['stocklist_id']
    review_text = data['review_text']
    review_id = user.create_review(user_id, stocklist_id, review_text)
    if review_id:
        return jsonify({"review_id": review_id}), 201
    else:
        return jsonify({"message": "Failed to create review"}), 400

@app.route('/update_review', methods=['POST'])
def update_review():
    data = request.json
    review_id = data['review_id']
    user_id = data['user_id']
    new_text = data['new_text']
    result = user.update_review(review_id, user_id, new_text)
    if result:
        return jsonify({"message": "Review updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update review"}), 400

@app.route('/delete_review', methods=['DELETE'])
def delete_review():
    data = request.json
    review_id = data['review_id']
    user_id = data['user_id']
    result = user.delete_review(review_id, user_id)
    if result:
        return jsonify({"message": "Review deleted successfully"}), 200
    else:
        return jsonify({"message": "Failed to delete review"}), 400

@app.route('/view_reviews', methods=['GET'])
def view_reviews():
    stocklist_id = request.args.get('stocklist_id')
    user_id = request.args.get('user_id')
    reviews = user.view_reviews(stocklist_id, user_id)
    return jsonify(reviews), 200

if __name__ == '__main__':
    setup_db(conn)
    app.run(debug=True)