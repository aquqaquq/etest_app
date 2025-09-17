import React from 'react'
import { Link } from 'react-router-dom'

export default function NavBar() {
  return (
    <header className="app-header">
      <div className="container">
        <div className="brand">ETest Program Generator</div>
        <nav className="nav-links">
          <Link className="nav-link" to="/">Home</Link>
          <Link className="nav-link" to="/python">Python Task</Link>
          <Link className="nav-link" to="/c">C Task</Link>
          <Link className="nav-link" to="/devices">Device Lookup</Link>
          <Link className="nav-link" to="/etest">eTest</Link>
        </nav>
      </div>
    </header>
  )
}
