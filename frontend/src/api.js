const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080'

export async function runPythonTask(payload) {
  const res = await fetch(`${API_BASE}/api/run-python`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return res.json()
}

export async function runCTask(taskName, args) {
  const res = await fetch(`${API_BASE}/api/run-c/${encodeURIComponent(taskName)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ args })
  })
  return res.json()
}

export async function searchDevices(name) {
  const res = await fetch(`${API_BASE}/api/devices/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  })
  return res.json()
}

export async function health() {
  const res = await fetch(`${API_BASE}/api/health`)
  return res.json()
}
