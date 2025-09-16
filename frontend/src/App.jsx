import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PythonTask from './pages/PythonTask'
import CTask from './pages/CTask'
import DeviceLookup from './pages/DeviceLookup'
import EtestProgramGenerator from './pages/EtestProgramGenerator'
import NavBar from './components/NavBar'

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', margin: 16 }}>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/python" element={<PythonTask />} />
        <Route path="/c" element={<CTask />} />
        <Route path="/devices" element={<DeviceLookup />} />
        <Route path="/etest" element={<EtestProgramGenerator />} />
        <Route path="*" element={<div>Not found</div>} />
      </Routes>
    </div>
  )
}
