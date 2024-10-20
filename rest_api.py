import sys
import json
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

transactions = []
balances = {}

@app.route('/add', methods=['POST'])
def add_points():
    data = request.get_json()

    payer = data.get("payer")
    points = data.get("points")
    timestamp = datetime.strptime(data.get("timestamp"), "%Y-%m-%dT%H:%M:%SZ")

    # Add transaction
    transactions.append({"payer": payer, "points": points, "timestamp": timestamp})

    # Update balances
    if payer not in balances:
        balances[payer] = 0
    balances[payer] += points

    return '', 200

@app.route('/spend', methods=['POST'])
def spend_points():
    data = request.get_json()
    points_to_spend = data.get("points")

    # Calculate total points available
    total_points = sum(balances.values())
    if points_to_spend > total_points:
        return "Not enough points", 400

    # Sort transactions by oldest timestamp (FIFO)
    sorted_transactions = sorted(transactions, key=lambda x: x["timestamp"])
    
    # Track points spent by payer
    points_spent = []
    points_deducted = {}

    # Process spending
    for transaction in sorted_transactions:
        if points_to_spend == 0:
            break

        payer = transaction["payer"]
        available_points = transaction["points"]

        if available_points <= 0:
            continue  # Ignore transactions with negative points

        points_to_use = min(available_points, points_to_spend)

        # Deduct points from balances and points to spend
        balances[payer] -= points_to_use
        points_to_spend -= points_to_use
        transaction["points"] -= points_to_use

        # Record points spent for each payer
        if payer not in points_deducted:
            points_deducted[payer] = 0
        points_deducted[payer] -= points_to_use

    for payer, points in points_deducted.items():
        points_spent.append({"payer": payer, "points": points})

    return jsonify(points_spent), 200

@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify(balances), 200

# Function to process JSON data passed via command-line argument
def process_json_file(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        # Assume the JSON contains an array of transactions
        for transaction in data:
            payer = transaction.get("payer")
            points = transaction.get("points")
            timestamp = transaction.get("timestamp")
            print(f"Processing: {payer} adds {points} points on {timestamp}")
            # Simulate sending a POST request to /add
            transactions.append({"payer": payer, "points": points, "timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")})
            if payer not in balances:
                balances[payer] = 0
            balances[payer] += points

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
        process_json_file(json_file_path)
    app.run(port=8000, debug=True)
