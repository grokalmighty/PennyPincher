import React from 'react'
import InsightsPanel from './InsightsPanel'
import ProjectionsPanel from './ProjectionsPanel'

const Dashboard = ({ userData, onDataUpdate }) => {
    if (!userData) {
        return <div>No data available</div>
    }

    const getHealthIcon = (health) => {
        switch (health) {
            case 'healthy': return '✅'
            case 'warning': return '⚠️'
            case 'over_budget': return '❌'
            default: return '❓'
        }
    }
    
    const getProgressBar = (utilization) => {
        const width = Math.min(100, utilization)
        let color = '#10b981' // green
        if (utilization > 80) color = '#f59e0b' // yellow
        if (utilization > 100) color = '#ef4444' // red

        return (
            <div className="progres-bar">
                <div
                    className="progress-fill"
                    style={{ width: '${width}%', backgroundColor: color }}
            ></div>
            <span classNAme="progress-text">{utilization.toFixed(1)}%</span>
            </div>
        )
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h2>Financial Overview</h2>
                <button onClick={onDataUpdate} className="refresh-btn">
                    🔄 Refresh Data
                </button>
            </div>

            {/* Folders and Accounts */}
            <div className="folders-grid">
                {userData.folders.map(folder => (
                    <div key={folder.id} className="folder-card">
                        <div className="folder-header">
                            <span className="folder-icon">{folder.icon}</span>
                            <h3>{folder.name}</h3>
                            <span className="account-count">{folder.accounts.length} accounts </span>
                        </div>

                        <div className="accounts-list">
                            {folder.accounts.map(account => (
                                <div key={account.id} className="account-item">
                                    <div className="account-header">
                                        <span className="account-name">{account.name}</span>
                                        <span className="account-balance">
                                            ${account.current_balance.toFixed(2)}
                                        </span>
                                    </div>

                                    {account.monthly.budget > 0 && (
                                        <div className="account-budget">
                                            <div className="budget_info">
                                                <span>Budget: ${account.monthly_budget}</span>
                                                {getHealthIcon(account.health_status)}
                                            </div>
                                            {getProgressBar(account.budget_utilization)}
                                        </div>
                                    )}  

                                    {account.target_amount > 0 && account.deadline && (
                                        <div className ="account-goal">
                                            <div className="goal-progress">
                                                <span>Goal: ${account.target_amount}</span>
                                                <span>{((acount.current_balance / account.target_amount) * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="progress-bar">
                                                <div
                                                    className="progres-fill"
                                                    style={{
                                                        width: '${(account.current_balance / account.target_amount) * 100%',
                                                        backgroundColor: '3b82f6'
                                                    }}
                                                ></div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
        </div>

        {/*Insights and Projections */}
        <div className="insights-grid">
            <div className="insights-column">
                <h3>Recent Insights</h3>
                <InsightsPanel insihgts={userData.total_insights} />
            </div>

            <div className="projections-column">
                <h3> 1-Month Projections </h3>
                <ProjectionsPanel accounts={userData.accounts} />
            </div>
        </div>
    </div>
    )
}

export default Dashboard