import { useCallback, useEffect, useRef, useState } from 'react'

const DEFAULT_CONFIG = {
  pack: 'debate',
  provider: 'openai',
  model: 'gpt-4o',
  settings: { rounds: 2, synthesis: 'single' },
}

function useWebSocket(sessionId, onMessage) {
  const wsRef = useRef(null)

  const connect = useCallback(() => {
    if (!sessionId) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = import.meta.env.DEV ? 'localhost:8000' : window.location.host
    const ws = new WebSocket(`${protocol}://${host}/ws/${sessionId}`)
    ws.onmessage = (e) => onMessage(JSON.parse(e.data))
    wsRef.current = ws
  }, [sessionId, onMessage])

  const send = useCallback((query) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ query }))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  return { send }
}

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [configText, setConfigText] = useState(JSON.stringify(DEFAULT_CONFIG, null, 2))
  const [query, setQuery] = useState('')
  const [turns, setTurns] = useState([])
  const [finalResponse, setFinalResponse] = useState('')
  const [usage, setUsage] = useState(null)
  const [packs, setPacks] = useState([])
  const [providers, setProviders] = useState([])
  const [status, setStatus] = useState('Configure the council to begin.')

  useEffect(() => {
    fetch('/api/packs').then((r) => r.json()).then((d) => setPacks(d.packs || []))
    fetch('/api/providers').then((r) => r.json()).then((d) => setProviders(d.providers || []))
  }, [])

  const onWsMessage = useCallback((msg) => {
    if (msg.type === 'turn') {
      setTurns((prev) => [...prev, msg])
    } else if (msg.type === 'final') {
      setFinalResponse(msg.content)
      setUsage({ items: msg.usage, total: msg.total_cost_usd })
      setStatus('Deliberation complete.')
    } else if (msg.type === 'error') {
      setStatus(`Error: ${msg.message}`)
    }
  }, [])

  const { send } = useWebSocket(sessionId, onWsMessage)

  const configure = async () => {
    try {
      const config = JSON.parse(configText)
      const res = await fetch('/api/council/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config }),
      })
      const data = await res.json()
      setSessionId(data.session_id)
      setTurns([])
      setFinalResponse('')
      setUsage(null)
      setStatus(`Session ${data.session_id.slice(0, 8)}… ready.`)
    } catch (e) {
      setStatus(`Config error: ${e.message}`)
    }
  }

  const exportConfig = () => {
    const blob = new Blob([configText], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'council-config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const importConfig = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setConfigText(reader.result)
    reader.readAsText(file)
  }

  const submit = () => {
    if (!query.trim() || !sessionId) return
    setTurns([])
    setFinalResponse('')
    setUsage(null)
    setStatus('Deliberating…')
    send(query)
  }

  return (
    <div className="flex h-screen">
      {/* Config panel */}
      <aside className="w-80 border-r border-slate-800 p-4 flex flex-col gap-3 overflow-y-auto">
        <h1 className="text-xl font-bold text-blue-400">🏛️ Council AI</h1>
        <p className="text-sm text-slate-400">Configure your council panel</p>

        <div className="text-xs text-slate-500">
          <p className="font-semibold mb-1">Packs</p>
          {packs.map((p) => (
            <button
              key={p.name}
              className="block text-left w-full hover:text-blue-300 py-0.5"
              onClick={() => setConfigText(JSON.stringify({ ...DEFAULT_CONFIG, pack: p.name }, null, 2))}
            >
              {p.name}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-500">
          <p className="font-semibold mb-1">Providers</p>
          <p>{providers.join(', ') || 'loading…'}</p>
        </div>

        <textarea
          className="flex-1 min-h-48 bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono"
          value={configText}
          onChange={(e) => setConfigText(e.target.value)}
        />
        <div className="flex gap-2">
          <button onClick={configure} className="flex-1 bg-blue-600 hover:bg-blue-500 rounded px-3 py-2 text-sm">
            Apply Config
          </button>
          <button onClick={exportConfig} className="bg-slate-700 hover:bg-slate-600 rounded px-2 py-2 text-xs">
            Export
          </button>
          <label className="bg-slate-700 hover:bg-slate-600 rounded px-2 py-2 text-xs cursor-pointer">
            Import
            <input type="file" accept=".json" className="hidden" onChange={importConfig} />
          </label>
        </div>
      </aside>

      {/* Chat center */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {finalResponse && (
            <div className="bg-blue-950 border border-blue-800 rounded-lg p-4">
              <h2 className="font-semibold text-blue-300 mb-2">Council Response</h2>
              <p className="whitespace-pre-wrap">{finalResponse}</p>
            </div>
          )}
          {!finalResponse && !turns.length && (
            <p className="text-slate-500 text-center mt-20">{status}</p>
          )}
        </div>
        <footer className="border-t border-slate-800 p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-900 border border-slate-700 rounded px-4 py-2"
              placeholder="Ask the council…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
            />
            <button onClick={submit} className="bg-blue-600 hover:bg-blue-500 rounded px-6 py-2">
              Send
            </button>
          </div>
          {usage && (
            <p className="text-xs text-slate-500 mt-2">
              Total cost: ${usage.total?.toFixed(4)} · {usage.items?.length} counselors tracked
            </p>
          )}
        </footer>
      </main>

      {/* Deliberation drawer */}
      <aside className="w-96 border-l border-slate-800 p-4 overflow-y-auto">
        <h2 className="font-semibold text-slate-300 mb-3">Deliberation</h2>
        {turns.length === 0 && <p className="text-sm text-slate-500">Turns appear here in real time.</p>}
        {turns.map((t, i) => (
          <div key={i} className="mb-3 bg-slate-900 rounded p-3 border border-slate-800">
            <p className="text-xs text-slate-400">
              Round {t.round} · {t.counselor_name} · {t.model}
            </p>
            <p className="text-sm mt-1 whitespace-pre-wrap">{t.content}</p>
          </div>
        ))}
      </aside>
    </div>
  )
}
