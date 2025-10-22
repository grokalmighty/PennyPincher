from datetime import datetime, timedelta
from enum import Enum

class AccountType(Enum):
    CHECKING = "checking"
    BILL = "bill"
    EXPENSE = "expense"
    GOAL = "goal"
    SAVINGS = "savings"
    INVESTMENT = "investment"

class Account:
    def __init__(self, account_id, name, account_type, folder_id, 
                 monthly_budget=0, target_amount=0, deadline=None,
                 current_balance=0):
        self.id = account_id
        self.name = name
        self.type = AccountType(account_type)
        self.folder_id = folder_id
        self.monthly_budget = float(monthly_budget)
        self.target_amount = float(target_amount)
        self.deadline = deadline
        self.current_balance = float(current_balance)
        self.created_at = datetime.now().isoformat()
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        # Update balance based on transaction type
        if transaction.amount < 0: # Expense
            self.current_balance += transaction.amount
        else: # Income or transfer in
            self.current_balance += transaction.amount
    
    def get_budget_utilization(self):
        if self.monthly_budget == 0:
            return 0
        monthly_spending = self.get_monthly_spending()
        return (monthly_spending / self.monthly_budget) * 100
    
    def get_monthly_spending(self):
        """Calculate spending for current month"""
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        monthly_transactions = [
            t for t in self.transactions 
            if t.amount < 0 and datetime.formisoformat(t.date) >= current_month_start
        ]

        return abs(sum(t.amount for t in monthly_transactions))
    
    def get_health_status(self):
        utilization = self.get_budget_utilizations()
        if utilization > 100:
            return "over_bugget"
        elif utilization > 80:
            return "warning"
        else:
            return "healthy"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'folder_id': self.folder_id,
            'monthly_budget': self.monthly_budget,
            'target_amount': self.target_amount,
            'deadline': self.deadline,
            'current_balance': self.current_balance,
            'budget_utilization': self.get_budget_utilization(),
            'health_status': self.get_health_Status(),
            'transaction_count': len(self.transactions)
        }