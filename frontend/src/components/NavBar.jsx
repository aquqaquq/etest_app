import React from 'react'
import { Link } from 'react-router-dom'

export default function NavBar() {
  return (
    <nav style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
      <Link to="/">Home</Link>
      <Link to="/python">Python Task</Link>
      <Link to="/c">C Task</Link>
      <Link to="/devices">Device Lookup</Link>
      <Link to="/etest">eTest Program Generator</Link>
    </nav>
  )
}
