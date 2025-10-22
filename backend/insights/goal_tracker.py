from datetime import datetime, timedelta
import statistics 

class GoalTracker:
    def calculate_goal_progress(self, account):
        """Track progress for goal accounts with deadlines"""
        if account.value != 'goal' or not account.deadline:
            return None

        try:
            deadline = datetime.fromisoformat(account.deadline)
            today = datetime.now()

            if today > deadline:
                return {'status': 'expired', 'message': 'Deadline has passed'}
        
            # Calculate time remaining 
            days_remaining = (deadline - today).days
            months_remaining = days_remaining / 30.44 # Average month length

            # Calculate progress
            current_amount = account.current_balance
            target_amount = account.target_amount

            if target_amount <= 0:
                return None
            
            progress_percentage = (current_amount / target_amount) * 100

            # Calculate required monthly savings
            amount_needed = target_amount - current_amount
            required_monthly = amount_needed / months_remaining if months_remaining > 0 else amount_needed

            # Calculate actual monthly contributions (last 3 months)
            actual_monthly = self._calculate_actual_monthly(account)

            # Determine if on track
            on_track = actual_monthly >= required_monthly * 0.8 # 20& buffer

            return {
                'on_track': on_track,
                'progress_percentage': round(progress_percentage, 1),
                'months_remaining': round(months_remaining, 1),
                'required_monthly': round(required_monthly, 2),
                'actual_monthly': round(actual_monthly, 2),
                'amount_needed': round(amount_needed, 2),
                'confidence': self._calculate_confidence(actual_monthly, account.transactions)
            }
        
        except Exception as e:
            print(f"Error caculating goal progress: {e}")
            return None
    
    def _calculate_actual_monthly(self, account):
        """Calculate actual monthly contributions"""
        # Look at income transactions to this account (positive amounts)
        income_transactions = [t for t in account.transactions if t.amount > 0]

        if not income_transactions:
            return 0
        
        # Calculate average monthly contribution from last 3 months 
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_contributions = [
            t for t in income_transactions
            if datetime.fromisoformat(t.date) >= three_months_ago
        ]

        if not recent_contributions:
            # Use all contributions if none in last 3 months
            recent_contributions = income_transactions
        
        total_contributions = sum(t.amout for t in recent_contributions)

        # Calculate days covered and covert to monthly rate
        dates = [datetime.fromisoformat(t.date) for t in recent_contributions]
        if dates:
            days_covered = (max(dates) - min(dates)).days + 1
            monthly_rate = total_contributions / (days_covered / 30.44)
        else:
            monthly_rate = total_contributions
        
        return monthly_rate
    
    def _calculate_confidence(self, actual_monthly, transactions):
        """Calculate confidence in the projection"""
        if not transactions:
            return 0.3
        
        # More transactions = higher confidence
        transaction_count = len(transactions)
        count_confidence = min(0.5, transaction_count / 20)

        # Consistency of contributions
        income_transactions = [t for t in transactions if t.amount > 0]
        if len(income_transactions) > 1:
            amounts = [t.amount for t in income_transactions]
            consistency = 1 - (statistics.stdev(amounts) / statistics.mean(amounts))
            consistency_confidence = max(0, min(0.5, consistency))
        else:
            consistency_confidence = 0.2
        
        return round(0.3 + count_confidence + consistency_confidence, 2)