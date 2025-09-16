import React, { useState } from 'react'
import { searchDevices } from '../api'

export default function DeviceLookup() {
  const [name, setName] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setError(''); setLoading(true); setResults(null)
    try {
      const res = await searchDevices(name.trim())
      if (res.error) setError(res.error)
      else setResults(res.rows || [])
    } catch (err) {
      setError('Request failed')
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h2>Device Lookup</h2>
      <form onSubmit={onSubmit} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          placeholder="Enter device name"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <button type="submit" disabled={!name || loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {results && results.length === 0 && <p>No results.</p>}
      {results && results.length > 0 && (
        <table border="1" cellPadding="6" style={{ marginTop: 16 }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {results.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.name}</td>
                <td>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
