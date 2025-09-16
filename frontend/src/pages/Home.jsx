import React, { useEffect, useState } from 'react'
import { health } from '../api'

export default function Home() {
  const [status, setStatus] = useState('checking...')
  const [db, setDb] = useState('checking...')
  useEffect(() => { (async () => {
    try { const h = await health(); setStatus(h.status); setDb(h.db) } catch {
      setStatus('backend unreachable')
    }
  })() }, [])
  return (
    <div>
      <h1>MyApp</h1>
      <p>Backend status: {status}</p>
      <p>DB status: {db}</p>
      <p>This is the homepage. Use the nav to try tasks.</p>
    </div>
  )
}
