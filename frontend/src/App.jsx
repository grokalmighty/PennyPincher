import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Dashboard from './components/Dashboard'
import FolderManager from './components/FolderManager'
import AccountManager from './components/AccountManager'
import TransactionForm from './components/TransactionForm'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [userData, setUserData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const userId = 'user1'

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`/api/${userId}/dashboard`)
      setUserData(response.data)
    } catch (error) {
      console.error('Error loading dashboard:', error)
      setError('Failed to load data. Make sure the backend is running on port 5000.')
    } finally {
      setLoading(false)
    }
  }

  const refreshData = () => {
    loadDashboardData()
  }

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner">💰</div>
        <h2>Loading Money Mentor...</h2>
        <p>Starting up the application</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app-error">
        <h2>🚨 Connection Error</h2>
        <p>{error}</p>
        <p>Make sure you're running the backend with: <code>python backend/app.py</code></p>
        <button onClick={loadDashboardData} className="btn-primary">
          Retry Connection
        </button>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>💰 Money Mentor</h1>
        <nav className="app-nav">
          <button 
            className={currentView === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentView('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={currentView === 'folders' ? 'active' : ''}
            onClick={() => setCurrentView('folders')}
          >
            Folders
          </button>
          <button 
            className={currentView === 'accounts' ? 'active' : ''}
            onClick={() => setCurrentView('accounts')}
          >
            Accounts
          </button>
          <button 
            className={currentView === 'transactions' ? 'active' : ''}
            onClick={() => setCurrentView('transactions')}
          >
            Add Transaction
          </button>
        </nav>
      </header>

      <main className="app-main">
        {currentView === 'dashboard' && (
          <Dashboard userData={userData} onDataUpdate={refreshData} userId={userId} />
        )}
        {currentView === 'folders' && (
          <FolderManager onDataUpdate={refreshData} userId={userId} />
        )}
        {currentView === 'accounts' && (
          <AccountManager onDataUpdate={refreshData} userId={userId} />
        )}
        {currentView === 'transactions' && (
          <TransactionForm onDataUpdate={refreshData} userId={userId} />
        )}
      </main>
    </div>
  )
}

export default App