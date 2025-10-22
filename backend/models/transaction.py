from datetime import datetime

class Transaction:
    def __init__(self, transaction_id, amount, description, account_id, category="", date=None):
        self.id = transaction_id
        self.amount = float(amount)
        self.description = description
        self.account_id = account_id
        self.category = category
        self.date = date or datetime.now().isoformat()
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'account_id': self.account_id,
            'category': self.category,
            'date': self.date,
            'created_at': self.created_at
        }