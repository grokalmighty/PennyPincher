import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import FolderManager from './components/FolderManager'
import AccountManager from './components/AccountManager'
import TransactionForm from './components/TransactionForm'
import './styles.css'

function App() {
    const [currentView, setCurrentView] = useState('dashboard')
    const [userData, setUserData] = useState(null)
    const [loading, setLoading] = userState(true)

    const userId = 'user1'

    useEffect(() => {
        loadDashboardData()
    }, [])

    const loadDashboardData = async () => {
        try {
            const response = await fetch('/api/${userId}/dashboard')
            const data = await response.json()
            setUserData(data)
        } catch (error) {
            console.error('Error loading dashboard:', error)
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
                <div className="loading-spinner"></div>
                <h2>Loading Penny Pincher...</h2>
            </div>
        )
    }

    return (
        <div className="app">
            <header className="app-header">
                <h1> Penny Pincher</h1>
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
                            Accounts
                        </button>
                        <button
                            className={currentView === 'transactions' ? 'active' : ''}
                            onClock={() => setCurrentView('transactions')}
                            >
                            Add Transaction
                        </button>
                </nav>
            </header>

            <main className="app-main">
                {currentView === 'dashboard' && (
                <Dashboard userData={userData} onDataUpdate={refreshData} />
                )}
                {currentView === 'folders' && (
                    <FolderManager onDataUpdate={refreshData} />
                )}
                {currentView === 'accounts' && (
                    <AccountManager onDataUpdate={refresData} />
                )}
                {currentView === 'transactions' && (
                    <TransactionForm onDataUpdate={refreshData} />
                    )}
            </main>
        </div>
    )
}

export default App