import React, { useState } from 'react'

const FolderManager = ({ onDataUpdate }) => {
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        icon: '📁'
    })

    const icons = ['📁', '💰', '🏦', '💳', '👜', '💼']

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const response = await fetch('/api/user1/folders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })

            if (response.ok) {
                setFormData({name: '', description: '', icon: '📁'})
                setShowForm(false)
                onDataUpdate()
            }
        } catch (error) {
            console.error('Error creating folder:', error)
        }
    }

    return (
        <div className="folder-manager">
            <div className="section-header">
                <h2>Manage Folders</h2>
                <button 
                    className="btn-primary"
                    onClick={() => setShowForm(true)}
                    >
                        + New Folder
                </button>
            </div>

            {showForm && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h3>Create New Folder</h3>
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label>Folder Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    value={formData.description}
                                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                                />
                            </div>

                            <div className="form-group">
                                <label>Icon</label>
                                <div className="icon-grid">
                                    {icons.map(icon => (
                                        <button
                                            key={icon}
                                            type="button"
                                            className={`icon-btn ${formData.icon === icon ? 'selected' : ''}`}
                                            onClick={() => setFormData({...formData, icon})}
                                        >
                                            {icon}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="form-actions">
                                <button type="button" onClick={() => setShowForm(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Create Folder
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default FolderManager