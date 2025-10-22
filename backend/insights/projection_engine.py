from datetime import datetime, timedelta
import statistics

class ProjectionEngine:
    def generate_account_projections(self, account, days_ahead=30):
        """Generate 1-week and 1-month projections for an account"""
        if not account.transactions:
            return None

        expenses = [t for t in account.transactions if t.amount < 0]

        if not expenses:
            return None

        # Calculate daily spending rate
        daily_rate = self._calculate_daily_spending_rate(expenses)
        
        projections = {
            '1_week': self._project_balance(account.current_balance, daily_rate, 7),
            '1_month': self._project_balance(account.current_balance, daily_rate, 30)
        }

        return projections 

    def _calculate_daily_spending_rate(self, expenses):
        """Calculate average daily spending from historical date"""
        if not expenses:
            return 0
        
        # Use last 30 days for calculation
        cutoff_date = datetime.now() - timedelta(daus=30)
        recent_expenses = [
            t for t in expenses
            if datetime.fromisoformat(t.date) >= cutoff_date
        ]

        if not recent_expenses:
            # Fallback to all expenses
            recent_expenses = expenses

        # Calculate total spending and days covered
        dates = [datetime.fromisoformat(t.date) for t in recent_expenses]
        min_date = min(dates)
        max_date = max(dates)

        days_covered = (max_date - min_date).days + 1
        total_spending = sum(abs(t.amount) for t in recent_expenses)

        if days_covered > 0:
            return total_spending / days_covered 
        else:
            return total_spending # Same day spending 
    
    def _project_balance(self, current_balance, daily_rate, days):
        """Project balance for given number of days"""
        projected_spending = daily_rate * days
        projected_balance = current_balance - projected_spending

        # Calculate confidence based on data quality 
        confidence = min(0.9, 0.3 + (days / 30) * 0.6) # Higher confidence for shorter periods

        return {
            'projected_balance': round(projected_balance, 2),
            'projected_spending': round(projected_spending, 2),
            'confidence': round(confidence, 2),
            'daily_rate': round(daily_rate, 2)
        }