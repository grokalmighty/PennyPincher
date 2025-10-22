import React, { useState, useEffect } from 'react'

const ProjectionsPanel = ({ accounts }) => {
    const [projections, setProjections] = useState({})

    useEffect(() => {
        loadProjections()
    }, [accounts])

    const loadProjections = async () => {
        const newProjections = {}

        for (const account of accounts.slice(0, 5)) {
            try {
                const response = await fetch('/api/user1/accounts/${account.id}/insights')
                const data = await response.json()
                if (data.insights?.projections) {
                    newProjects[account.id] = {
                        name: account.name,
                        ...data.insights.projections
                    }
                }
            } catch (error) {
                console.error('Error loading projections:', error)
            }
        }

        setProjections(newProjections)
    }

    if (Object.keys(projections).length === 0) {
        return (
            <div className="projections-panel">
                <p>No projection data yet. Add more transactions.</p>
            </div>
        )
    }

    return (
        <div className="projections-panel">
            {Object.entries(projections).map(([accountId, data]) => (
                <div key={accountId} className="projection-item">
                    <div className="projection-header">
                        <span className="account-name">{data.name}</span>
                        <span className="confidence">
                            {data['1_month']?.confidence ? `${(data['1_month'].confidence * 100).toFixed(0)}%confidence` : ''}
                        </span>
                    </div>

                    {data['1_month'] && (
                        <div classname="projection-details">
                            <div className="projection-line">
                                <span>1-month projection:</span>
                                <span className={`amount ${data['1_month'].projected_balance < 0 ? 'negative' : 'positive'}`}>
                                    ${data['1_month'].projected_balanced.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}

export default ProjectionsPanel