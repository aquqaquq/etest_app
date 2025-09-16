import React, { useState } from 'react'
import { runCTask } from '../api'

export default function CTask() {
  const [a, setA] = useState('2')
  const [b, setB] = useState('3')
  const [out, setOut] = useState(null)

  async function onRun() {
    const res = await runCTask('sum', [a, b])
    setOut(res)
  }

  return (
    <div>
      <h2>C Task</h2>
      <input value={a} onChange={e => setA(e.target.value)} />
      <input value={b} onChange={e => setB(e.target.value)} />
      <button onClick={onRun}>Run</button>
      <pre>{out ? JSON.stringify(out, null, 2) : null}</pre>
    </div>
  )
}
