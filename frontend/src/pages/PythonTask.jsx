import React, { useState } from 'react'
import { runPythonTask } from '../api'

export default function PythonTask() {
  const [name, setName] = useState('World')
  const [out, setOut] = useState(null)

  async function onRun() {
    const res = await runPythonTask({ task: 'hello', params: { name } })
    setOut(res)
  }

  return (
    <div>
      <h2>Python Task</h2>
      <input value={name} onChange={e => setName(e.target.value)} />
      <button onClick={onRun}>Run</button>
      <pre>{out ? JSON.stringify(out, null, 2) : null}</pre>
    </div>
  )
}
