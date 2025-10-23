import React, { useState, useEffect } from 'react'
import axios from 'axios'
import InsightsPanel from './InsightsPanel'
import ProjectionsPanel from './ProjectionsPanel'

const Dashboard = ({ userData, onDataUpdate, userId }) => {
  const [accountInsights, setAccountInsights] = useState({})

  useEffect(() => {
    loadAccountInsights()
  }, [userData])

  const loadAccountInsights = async () => {
    const insights = {}
    if (userData && userData.accounts) {
      for (const account of userData.accounts.slice(0, 5)) {
        try {
          const response = await axios.get(`/api/${userId}/accounts/${account.id}/insights`)
          insights[account.id] = response.data.insights
        } catch (error) {
          console.error(`Error loading insights for account ${account.id}:`, error)
        }
      }
      setAccountInsights(insights)
    }
  }

  if (!userData) {
    return <div>No data available</div>
  }

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return '✅'
      case 'warning': return '⚠️'
      case 'over_budget': return '❌'
      default: return '🔵'
    }
  }

  const getProgressBar = (utilization) => {
    const width = Math.min(100, utilization)
    let color = '#10b981'
    if (utilization > 80) color = '#f59e0b'
    if (utilization > 100) color = '#ef4444'
    
    return (
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${width}%`, backgroundColor: color }}
        ></div>
        <span className="progress-text">{utilization.toFixed(1)}%</span>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Financial Overview</h2>
        <button onClick={onDataUpdate} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      <div className="folders-grid">
        {userData.folders.map(folder => (
          <div key={folder.id} className="folder-card">
            <div className="folder-header">
              <span className="folder-icon">{folder.icon}</span>
              <h3>{folder.name}</h3>
              <span className="account-count">{folder.accounts.length} accounts</span>
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
                  
                  {account.monthly_budget > 0 && (
                    <div className="account-budget">
                      <div className="budget-info">
                        <span>Budget: ${account.monthly_budget}</span>
                        {getHealthIcon(account.health_status)}
                      </div>
                      {getProgressBar(account.budget_utilization)}
                    </div>
                  )}

                  {account.target_amount > 0 && account.deadline && (
                    <div className="account-goal">
                      <div className="goal-progress">
                        <span>Goal: ${account.target_amount}</span>
                        <span>{((account.current_balance / account.target_amount) * 100).toFixed(1)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ 
                            width: `${(account.current_balance / account.target_amount) * 100}%`,
                            backgroundColor: '#3b82f6'
                          }}
                        ></div>
                      </div>
                      {accountInsights[account.id]?.goal_progress && (
                        <div className="goal-status">
                          {accountInsights[account.id].goal_progress.on_track ? '🎯 On track' : '⚠️ Needs attention'}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="insights-grid">
        <div className="insights-column">
          <h3>Recent Insights</h3>
          <InsightsPanel insights={userData.total_insights} />
        </div>
        
        <div className="projections-column">
          <h3>1-Month Projections</h3>
          <ProjectionsPanel accounts={userData.accounts} accountInsights={accountInsights} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard