from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

from models.folder import Folder
from models.account import Account, AccountType
from models.transaction import Transaction
from insights.time_analyzer import TimeAnalyzer
from insights.projection_engine import ProjectionEngine
from insights.goal_tracker import GoalTracker

app = Flask(__name__)
CORS(app)

# In-memory storage 
users_data = {}

def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            'folders': {},
            'accounts': {},
            'transactions': {},
            'next_folder_id': 1,
            'next_account_id': 1,
            'next_transaction_id': 1
        }
        _initialize_default_data(user_id)
    return users_data[user_id]

def _initialize_default_data(user_id):
    """Initialize with some default folders and accounts"""
    user_data = users_data[user_id]

    # Create default folders 
    default_folders = [
        {"name": "Essentials", "description": "Basic living expenses", "icon": "🏠"},
        {"name": "Goals", "description": "Savings goals and targets", "icon": "🎯"},
        {"name": "Lifestyle", "description": "Discretionary spending", "icon": "🍽️"},
        {"name": "Investments", "description": "Long-term savings", "icon": "📈"}
    ]

    for folder_data in default_folders:
        folder_id = user_data['next_folder_id']
        folder = Folder(folder_id, folder_data['name'], folder_data['description'], folder_data['icon'])
        user_data['folders'][folder_id] = folder
        user_data['next_folder_id'] += 1

    # Create some default accounts
    default_accounts = [
        {"name": "Groceries", "type": AccountType.EXPENSE, "folder_id": 1, "monthly_budget": 500},
        {"name": "Emergency Fund", "type": AccountType.GOAL, "folder_id": 2, "target_amount": 10000},
        {"name": "Dining Out", "type": AccountType.EXPENSE, "folder_id": 3, "monthly_budget": 200},
    ]
    
    for account_data in default_accounts:
        account_id = user_data['next_account_id']
        account = Account(
            account_id=account_id,
            name=account_data['name'],
            account_type=account_data['type'],
            folder_id=account_data['folder_id'],
            monthly_budget=account_data.get('monthly_budget', 0),
            target_amount=account_data.get('target_amount', 0)
        )
        user_data['accounts'][account_id] = account
        user_data['folders'][account_data['folder_id']].add_account(account)
        user_data['next_account_id'] += 1

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():  # FIXED: was health_checl
    return jsonify({"status": "healthy", "message": "Money Mentor API is running"})

# Folder endpoints
@app.route('/api/<user_id>/folders', methods=['GET'])
def get_folders(user_id):
    user_data = get_user_data(user_id)
    folders = [folder.to_dict() for folder in user_data['folders'].values()]
    return jsonify({"folders": folders})

@app.route('/api/<user_id>/folders', methods=['POST'])
def create_folder(user_id):
    user_data = get_user_data(user_id)
    data = request.json

    folder_id = user_data['next_folder_id']
    folder = Folder(
        folder_id=folder_id,
        name=data['name'],
        description=data.get('description', ''),
        icon=data.get('icon', '📁')
    )

    user_data['folders'][folder_id] = folder
    user_data['next_folder_id'] += 1

    return jsonify({"status": "success", "folder": folder.to_dict()})

# Account endpoints
@app.route('/api/<user_id>/accounts', methods=['POST'])
def create_account(user_id):
    user_data = get_user_data(user_id)
    data = request.json

    # Validate folder exists
    folder_id = data['folder_id']
    if folder_id not in user_data['folders']:
        return jsonify({"error": "Folder not found"}), 404
    
    account_id = user_data['next_account_id']  # FIXED: was user_id['next_account_id']
    account = Account(
        account_id=account_id,
        name=data['name'],
        account_type=data['type'],
        folder_id=folder_id,
        monthly_budget=data.get('monthly_budget', 0),
        target_amount=data.get('target_amount', 0),
        deadline=data.get('deadline'),
        current_balance=data.get('current_balance', 0)
    )

    user_data['accounts'][account_id] = account
    user_data['folders'][folder_id].add_account(account)
    user_data['next_account_id'] += 1

    return jsonify({"status": "success", "account": account.to_dict()})

@app.route('/api/<user_id>/accounts', methods=['GET'])  # FIXED: added missing /
def get_accounts(user_id):  # FIXED: was get_users
    user_data = get_user_data(user_id)
    accounts = [account.to_dict() for account in user_data['accounts'].values()]
    return jsonify({"accounts": accounts})

@app.route('/api/<user_id>/accounts/<int:account_id>', methods=['GET'])
def get_account(user_id, account_id):
    user_data = get_user_data(user_id)
    account = user_data['accounts'].get(account_id)

    if not account:
        return jsonify({"error": "Account not found"}), 404
    
    return jsonify({"account": account.to_dict()})

# Transaction endpoints
@app.route('/api/<user_id>/transactions', methods=['POST'])
def create_transaction(user_id):
    user_data = get_user_data(user_id)
    data = request.json

    # Validate account exists
    account_id = data['account_id']
    if account_id not in user_data['accounts']:
        return jsonify({"error": "Account not found"}), 404

    transaction_id = user_data['next_transaction_id']  # FIXED: was user_id['next_transaction_id']
    transaction = Transaction(
        transaction_id=transaction_id,
        amount=data['amount'],
        description=data['description'],
        account_id=account_id,
        category=data.get('category', ''),
        date=data.get('date')
    )

    # Add to account
    account = user_data['accounts'][account_id]
    account.add_transaction(transaction)

    # Store in transactions list
    user_data['transactions'][transaction_id] = transaction
    user_data['next_transaction_id'] += 1

    return jsonify({"status": "success", "transaction": transaction.to_dict()})

@app.route('/api/<user_id>/accounts/<int:account_id>/transactions', methods=['GET'])
def get_account_transactions(user_id, account_id):
    user_data = get_user_data(user_id)
    account = user_data['accounts'].get(account_id)

    if not account:
        return jsonify({"error": "Account not found"}), 404
    
    transactions = [t.to_dict() for t in account.transactions]
    return jsonify({"transactions": transactions})

# Insights endpoints
@app.route('/api/<user_id>/accounts/<int:account_id>/insights', methods=['GET'])
def get_account_insights(user_id, account_id):
    user_data = get_user_data(user_id)
    account = user_data['accounts'].get(account_id)

    if not account:
        return jsonify({"error": "Account not found"}), 404
    
    insights = {}

    # Time-based insights
    time_analyzer = TimeAnalyzer()
    time_insights = time_analyzer.analyze_account_patterns(account)
    if time_insights:
        insights['time_patterns'] = time_insights

    # Projections
    projection_engine = ProjectionEngine()
    projections = projection_engine.generate_account_projections(account)
    if projections:
        insights['projections'] = projections
    
    # Goal tracking 
    if account.type.value == 'goal' and account.deadline:
        goal_tracker = GoalTracker()
        goal_progress = goal_tracker.calculate_goal_progress(account)
        if goal_progress:
            insights['goal_progress'] = goal_progress

    return jsonify({"insights": insights})

@app.route('/api/<user_id>/dashboard', methods=['GET'])
def get_dashboard(user_id):
    user_data = get_user_data(user_id)

    dashboard_data = {
        'folders': [],
        'accounts': [],
        'total_insights': []  # FIXED: was total_insights (typo)
    }

    # Add folders with their accounts
    for folder in user_data['folders'].values():
        folder_data = folder.to_dict()
        folder_data['accounts'] = [account.to_dict() for account in folder.accounts]
        dashboard_data['folders'].append(folder_data)

        # Add accounts to flat list
        dashboard_data['accounts'].extend(folder_data['accounts'])

    # Generate insights for a few key accounts
    time_analyzer = TimeAnalyzer()
    for account in list(user_data['accounts'].values())[:5]:
        insights = time_analyzer.analyze_account_patterns(account)
        if insights:
            dashboard_data['total_insights'].append({
                'account_name': account.name,
                'account_icon': '📊', 
                'insights': insights,
            })
    
    return jsonify(dashboard_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)