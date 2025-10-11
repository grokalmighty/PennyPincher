import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os 

class SpendingPersonalityClassifier:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = [
            'savings_rate', 'spending_volatility', 'discretionary_ratio',
            'essential_ratio', 'recurring_expense_ratio'
        ]
        self.personality_types = {
            0: 'Frugal', 
            1: 'Balanced', 
            2: 'Spender', 
            3: 'Big Spender'}
    
    def generate_training_data(self, n_samples=1000):
        """Generate training data for the 3 spending types above."""
        np.random.seed(42)
        data = []

        for i in range(n_samples):
            if i < n_samples // 4:
                # Frugal: High savings, low spending
                savings_rate = np.random.normal(0.35, 0.05)
                discretionary_ratio = np.random.normal(0.15, 0.03)
                spending_type = 0
            elif i < n_samples // 2:
                # Balanced: Moderate savings, balanced spending
                savings_rate = np.random.normal(0.20, 0.04)
                discretionary_ratio = np.random.normal(0.30, 0.05)
                spending_type = 1
            elif i < 3 * n_samples // 4:
                # Spender: Low savings, high spending 
                savings_rate = np.random.normal(0.10, 0.05)
                discretionary_ratio = np.random.normal(0.45, 0.06)
                spending_type = 2
            else:
                # Big spender: Very low savings, very high spending
                savings_rate = np.random.normal(0.05, 0.03)
                discretionary_ratio = np.random.normal(0.60, 0.07)
                spending_type = 3
            
            row = {
                'savings_rate': max(0.01, savings_rate),
                'spending_volatility': np.random.normal(0.2, 0.1),
                'discretionary_ratio': max(0.01, min(0.8, discretionary_ratio)),
                'essential_ratio': np.random.normal(0.6, 0.1),
                'recurring_expense_ratio': np.random.normal(0.25, 0.08),
                'spending_type': spending_type
            }
            data.append(row)
        
        return pd.DataFrame(data)

    def calculate_features(self, transactions):
        """Calculate features that determine spending type."""
        if not transactions:
            return {feature: 0 for feature in self.feature_names}
        
        df = pd.DataFrame(transactions)
        df['amount'] = pd.to_numeric(df['amount'])

        # Calculate total income and expenses
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expenses = abs(df[df['amount'] < 0]['amount'].sum())

        # Savings rate
        savings_rate = (total_income - total_expenses) / total_income if total_income > 0 else 0.05

        # Discretionary vs essential spending
        discretionary_categories = ['dining', 'entertainment',' shopping', 'hobbies', 'travel']
        essential_categories = ['rent', 'utilities', 'groceries', 'transportation', 'healthcare']
        discretionary_spending = abs(df[df['category'].str.lower().isin([cat.lower() for cat in discretionary_categories]) & (df['amount'] < 0)]['amount'].sum())
        essential_spending = abs(df[df['category'].str.lower().isin([cat.lower() for cat in essential_categories]) & (df['amount'] < 0)]['amount'].sum())
        discretionary_ratio = discretionary_spending / total_expenses if total_expenses > 0 else 0.3
        essential_ratio = essential_spending / total_expenses if total_expenses > 0 else 0.6

        # Spending volatility 
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            monthly_spending = df[df['amount'] < 0].groupby(df['date'].dt.to_period('M'))['amount'].sum().abs()
            spending_volatility = monthly_spending.std() / monthly_spending.mean() if len(monthly_spending) > 1 else 0.2
        else:
            spending_volatility = 0.2
        
        # Recurring expense ratio
        recurring_categories = ['subscriptions', 'memberships', 'loan_payments']
        recurring_expenses = abs(df[df['category'].str.lower().isin([cat.lower() for cat in recurring_categories]) & (df['amount'] < 0)]['amount'].sum())
        recurring_ratio = recurring_expenses / total_expenses if total_expenses > 0 else 0.2
        return {
            'savings_rate': max(0.01, min(0.5, savings_rate)),
            'spending_volatility': max(0.1, min(0.8, spending_volatility)),
            'discretionary_ratio': max(0.1, min(0.8, discretionary_ratio)),
            'essential_ratio': max(0.3, min(0.9, essential_ratio)),
            'recurring_expense_ratio': max(0.1, min(0.5, recurring_ratio))
        }

    def predict_personality(self, transactions):
        """Predict spending personality from transactions."""
        if not self.model:
            if not self.load_model():
                self.train()
        
        features = self.calculate_features(transactions)
        feature_vector = [features[feature] for feature in self.feature_names]
        prediction = self.model.predict([feature_vector])[0]
        personality_type = self.personality_types[prediction]
        return {
            'personality_type': personality_type,
            'features': features,
            'confidence': max(self.model.predict_proba([feature_vector])[0])
        }