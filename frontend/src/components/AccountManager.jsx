import React, { useState, useEffect } from 'react'
import axios from 'axios'

const AccountManager = ({ onDataUpdate, userId }) => {
  const [showForm, setShowForm] = useState(false)
  const [folders, setFolders] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    type: 'expense',
    folder_id: '',
    monthly_budget: '',
    target_amount: '',
    deadline: '',
    current_balance: '0'
  })

  const accountTypes = [
    { value: 'checking', label: '💰 Checking Account' },
    { value: 'bill', label: '📅 Bill Account' },
    { value: 'expense', label: '💸 Expense Account' },
    { value: 'goal', label: '🎯 Goal Account' },
    { value: 'savings', label: '🏦 Savings Account' },
    { value: 'investment', label: '📈 Investment Account' }
  ]

  useEffect(() => {
    loadFolders()
  }, [])

  const loadFolders = async () => {
    try {
      const response = await axios.get(`/api/${userId}/folders`)
      setFolders(response.data.folders)
      if (response.data.folders.length > 0) {
        setFormData(prev => ({ ...prev, folder_id: response.data.folders[0].id }))
      }
    } catch (error) {
      console.error('Error loading folders:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        monthly_budget: parseFloat(formData.monthly_budget) || 0,
        target_amount: parseFloat(formData.target_amount) || 0,
        current_balance: parseFloat(formData.current_balance) || 0
      }

      await axios.post(`/api/${userId}/accounts`, payload)
      setFormData({
        name: '',
        type: 'expense',
        folder_id: folders[0]?.id || '',
        monthly_budget: '',
        target_amount: '',
        deadline: '',
        current_balance: '0'
      })
      setShowForm(false)
      onDataUpdate()
    } catch (error) {
      console.error('Error creating account:', error)
      alert('Error creating account')
    }
  }

  return (
    <div className="account-manager">
      <div className="section-header">
        <h2>Manage Accounts</h2>
        <button 
          className="btn-primary"
          onClick={() => setShowForm(true)}
        >
          + New Account
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Create New Account</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Account Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Account Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                >
                  {accountTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Folder</label>
                <select
                  value={formData.folder_id}
                  onChange={(e) => setFormData({...formData, folder_id: e.target.value})}
                  required
                >
                  {folders.map(folder => (
                    <option key={folder.id} value={folder.id}>
                      {folder.icon} {folder.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Monthly Budget (optional)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.monthly_budget}
                  onChange={(e) => setFormData({...formData, monthly_budget: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>Target Amount (for goals)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.target_amount}
                  onChange={(e) => setFormData({...formData, target_amount: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>Deadline (for goals)</label>
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({...formData, deadline: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Current Balance</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.current_balance}
                  onChange={(e) => setFormData({...formData, current_balance: e.target.value})}
                  required
                />
              </div>

              <div className="form-actions">
                <button type="button" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountManager