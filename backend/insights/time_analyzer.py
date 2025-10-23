from datetime import datetime, timedelta
import statistics
from collections import defaultdict

class TimeAnalyzer:
    def __init__(self):
        self.time_buckets = {
            'early_morning': (5 ,9),
            'midday': (9, 16),
            'evening': (16, 21),
            'late_night': (21, 5)
        }
    
    def analyze_account_patterns(self, account):
        """Analyze time and day patterns for an account"""
        if not account.transactions:
            return None

        transactions = [t for t in account.transactions if t.amount < 0] # Only expenses

        if not transactions:
            return None
        
        insights = {}

        # Time of day analysis 
        time_insight = self._analyze_time_of_day(transactions)
        if time_insight:
            insights['time_of_day'] = time_insight 
        
        # Day of week analysis
        day_insight = self._analyze_day_of_week(transactions)
        if day_insight:
            insights['day_of_week'] = day_insight
        
        # Spending velocity
        velocity_insight = self._analyze_spending_velocity(transactions)
        if velocity_insight:
            insights['spending_velocity'] = velocity_insight
        
        return insights if insights else None

    def _analyze_time_of_day(self, transactions):
        time_totals = {bucket: 0 for bucket in self.time_buckets}
        time_counts = {bucket: 0 for bucket in self.time_buckets}

        for t in transactions:
            hour = datetime.fromisoformat(t.date).hour
            for bucket, (start, end) in self.time_buckets.items():
                if start <= hour < end or (start > end and (hour >= start or hour < end)):
                    time_totals[bucket] += abs(t.amount)
                    time_counts[bucket] += 1

        # Find dominant time bucket
        if sum(time_totals.values()) > 0:
            dominant_bucket = max(time_totals, key=time_totals.get)
            percentage = (time_totals[dominant_bucket] / sum(time_totals.values())) * 100
            
            if percentage > 60: # Significant pattern
                time_names = {
                    'early_morning': 'Early morning (5 - 9 AM)',
                    'midday': 'Midday (9 AM - 4 PM)',
                    'evening': 'Evening (4 - 9 PM)',
                    'late_night': 'Late night (9 PM - 5 AM)'
                }

                return {
                    'dominant_period': time_names[dominant_bucket],
                    'percentage': round(percentage, 1),
                    'average_amount': time_totals[dominant_bucket] / max(1, time_counts[dominant_bucket]),
                    'impact_score': min(0.9, percentage / 100)
                }
            
            return None 
    
    def _analyze_day_of_week(self, transactions):
        day_totals = {day: 0 for day in range(7)}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for t in transactions:
            day = datetime.fromisoformat(t.date).weekday()
            day_totals[day] += abs(t.amount)
        
        # Calculate weekend vs weekday
        weekday_total = sum(day_totals[day] for day in range(5)) # Mon-Fri
        weekend_total = sum(day_totals[day] for day in range(5, 7)) # Sat- Sun

        total_spending = weekday_total + weekend_total
        if total_spending == 0:
            return None
        
        weekend_ratio = weekend_total / total_spending

        # Find peak day
        peak_day = max(day_totals, key=day_totals.get)
        peak_percentage = (day_totals[peak_day] / total_spending) * 100

        insights = {}

        if weekend_ratio > 0.6:
            insights['weekend_focus'] = {
                'day': day_names[peak_day],
                'percentage': round(peak_percentage, 1),
                'message': f"{day_names[peak_day]} is your biggest spending day"
            }
        
        return insights if insights else None 
    
    def _analyze_spending_velocity(self, transactions):
        if len(transactions) < 3:
            return None

        # Sort by date and calculate intervals 
        sorted_transactions = sorted(transactions, key=lambda x: x.date)
        dates = [datetime.fromisoformat(t.date) for t in sorted_transactions]

        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)

        avg_interval = statistics.mean(intervals)
        interval_std = statistics.stdev(intervals) if len(intervals) > 1 else 0

        consistency = 1 - (interval_std / avg_interval) if avg_interval > 0 else 0

        if avg_interval <= 2:
            pattern = "frequent"
        elif avg_interval <= 7:
            pattern = "regular"
        else:
            pattern = "occasional"
        
        return {
            'average_days_between': round(avg_interval, 1),
            'consistency': round(consistency, 2),
            'pattern': pattern,
            'message': f"{pattern.capitalize()} spending (every {avg_interval:.1f} days)"
        }