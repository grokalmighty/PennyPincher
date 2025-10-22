import React from 'react'

const InsightsPanel = ({ insights }) => {
    if (!insights || insights.length === 0) {
        return (
            <div className="insights-panel">
                <p>No insights yet. Add more transactions to see patterns.</p>
            </div>
        )
    }

    const formatInsight = (accountName, insightData) => {
        if (insightData.time_patterns) {
            if (insightData.time_patterns.time_of_day) {
                const time = insightData.time_patterns.time_of_day
                return '${accountName}: ${time.percentage}% of spending happens in the ${time.dominant_period}'
            }

            if (insightData.time_patterns.days_of_week) {
                if (insightData.time_patterns.day_of_week.peak_day) {
                    const day = insightData.time_patterns.day_of_week.peak_day 
                    return '${accountNAme}: ${day.day} is your biggest spending (day (${day.percentage}%)'
                }
            }

            if (insightData.time_patterns.spending_velocity) {
                const velocity = insightData.time_patterns.spending_velocity
                return '${accountName}: ${velocity.message}'
            }
        }

        return '${accountName}: New spending pattern'
    }

    return (
        <div className="insights-panel">
            {insights.slice(0, 5).map((insightGroup, index) => (
                <div key={index} className="insight-item">
                    <div className="insight-icon">💡</div>
                    <div className="insight-content">
                        {formatInsight(insightGroup.account_name, insightGroup.insights)}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default InsightsPanel