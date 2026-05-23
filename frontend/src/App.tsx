import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { HashinalsWalletConnectSDK } from '@hashgraphonline/hashinal-wc'
import { TransferTransaction, AccountId, Hbar, LedgerId } from '@hashgraph/sdk'
import Confetti from './Confetti'
import { playSuccessSound, playDeclineSound } from './sounds'
import './App.css'
import { API_URL } from './config'


const IS_MOBILE = /android|iphone|ipad|ipod/i.test(
  typeof navigator !== 'undefined' ? navigator.userAgent : ''
)

// On mobile the SDK uses anchor.click() with target="_blank" which is blocked
// by browsers in async context. Intercept it and redirect via window.location.href instead.
function interceptMobileDeepLink(): () => void {
  const handler = (e: MouseEvent) => {
    const el = e.target as HTMLElement
    if (el.tagName !== 'A') return
    const href = el.getAttribute('href') ?? ''
    if (!href.includes('link.hashpack.app') && !href.includes('hashpack://')) return
    e.preventDefault()
    e.stopPropagation()
    // Store return URL so we can resume on page reload (Android case)
    sessionStorage.setItem('hbar_return_from_wallet', '1')
    window.location.href = href
    cleanup()
  }
  document.addEventListener('click', handler, true)
  const cleanup = () => document.removeEventListener('click', handler, true)
  return cleanup
}

// Smart HashPack download routing by device
function getHashPackDownload(): { url: string; label: string; hint: string } {
  const ua = navigator.userAgent
  if (/iPhone|iPad|iPod/i.test(ua)) return {
    url: 'https://apps.apple.com/ng/app/hashpack/id6444389849',
    label: 'Get HashPack on App Store',
    hint: 'iPhone / iPad detected',
  }
  if (/Android/i.test(ua)) return {
    url: 'https://play.google.com/store/apps/details?id=app.hashpack.wallet.twa',
    label: 'Get HashPack on Google Play',
    hint: 'Android detected',
  }
  return {
    url: 'https://chrome.google.com/webstore/detail/hashpack/gjagmgiddbbciopjhllkdnddhcglnemk',
    label: 'Install HashPack Extension',
    hint: 'Desktop browser detected',
  }
}

type MsgRole = 'hera' | 'user' | 'system' | 'receipt'

interface Msg {
  id: string
  role: MsgRole
  text: string
  txId?: string   // receipt only
  url?: string    // receipt only
}

const CHIPS = [
  { label: 'Espresso  1 HBAR',     order: 'Espresso' },
  { label: 'Flat White  2 HBAR',   order: 'Flat White' },
  { label: 'Cold Brew  3 HBAR',    order: 'Cold Brew' },
  { label: 'Matcha Latte  3 HBAR', order: 'Matcha Latte' },
  { label: 'Cappuccino  2 HBAR',   order: 'Cappuccino' },
  { label: 'Croissant  1 HBAR',    order: 'Croissant' },
]

let sdk: InstanceType<typeof HashinalsWalletConnectSDK> | null = null
function getSDK() {
  if (!sdk) sdk = HashinalsWalletConnectSDK.getInstance(undefined, LedgerId.TESTNET)
  return sdk
}

// Strip receipt formatting artefacts before rendering
function cleanReceiptText(text: string): string {
  return text
    .split('\n')
    .filter(l => !l.trim().startsWith('---') && !l.includes('TRANSACTION_ID:') && l.trim() !== '')
    .join('\n')
    .trim()
}

type Screen = 'connect' | 'chat'

export default function App() {
  const [screen, setScreen]         = useState<Screen>('connect')
  const [messages, setMessages]     = useState<Msg[]>([])
  const [balance, setBalance]       = useState<number | null>(null)
  const [balanceFlash, setFlash]    = useState(false)
  const [input, setInput]           = useState('')
  const [typing, setTyping]         = useState(false)
  const [error, setError]           = useState('')
  const [connecting, setConnecting] = useState(false)
  const [confetti, setConfetti]         = useState(false)
  const [showDownloadHint, setDownload] = useState(false)

  const ws = useRef<WebSocket | null>(null)
  const messagesEnd       = useRef<HTMLDivElement>(null)
  const downloadTimer     = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingReceiptMsg = useRef('')
  

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  // On mobile: detect return from HashPack and restore the WC session
  useEffect(() => {
    if (!IS_MOBILE) return
    if (!sessionStorage.getItem('hbar_return_from_wallet')) return
    sessionStorage.removeItem('hbar_return_from_wallet')

    const pendingProjectId = sessionStorage.getItem('hbar_pending_project_id')
    if (!pendingProjectId) return
    sessionStorage.removeItem('hbar_pending_project_id')

    setConnecting(true)
    const metadata = {
      name: 'HBAR Coffee Shop', description: 'AI barista — pay in HBAR',
      url: location.origin, icons: [] as string[],
    }
    ;(async () => {
      try {
        const s = getSDK()
        const result = await s.initAccount(pendingProjectId, metadata, LedgerId.TESTNET)
        if (result?.accountId) {
          clearDownloadTimer()
          openWs(result.accountId)
        } else {
          setError('Could not restore wallet session — please try connecting again.')
          setConnecting(false)
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e))
        setConnecting(false)
      }
    })()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const updateBalance = useCallback((hbar: number) => {
    setBalance(hbar)
    setFlash(true)
    setTimeout(() => setFlash(false), 700)
  }, [])

  const addMsg = useCallback((role: MsgRole, text: string, extra?: { txId?: string; url?: string }) =>
    setMessages(p => [...p, { id: crypto.randomUUID(), role, text, ...extra }]), [])

  const clearDownloadTimer = useCallback(() => {
    if (downloadTimer.current) { clearTimeout(downloadTimer.current); downloadTimer.current = null }
    setDownload(false)
  }, [])

  const handleConnect = useCallback(async () => {
    setError('')
    setDownload(false)
    setConnecting(true)

    // After 15 s with no wallet response, surface the download prompt
    downloadTimer.current = setTimeout(() => setDownload(true), 15_000)

    let projectId = ''
    try {
      projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID ?? ''
    } catch { /* ignore */ }

    if (!projectId) {
      clearDownloadTimer()
      setConnecting(false)
      return
    }
    const metadata = {
      name: 'HBAR Coffee Shop', description: 'AI barista — pay in HBAR',
      url: location.origin, icons: [] as string[],
    }

    // On mobile: install the deep-link interceptor BEFORE the SDK fires anchor.click()
    // so we can replace it with window.location.href (never blocked by browsers).
    let removeInterceptor: (() => void) | null = null
    if (IS_MOBILE) {
      sessionStorage.setItem('hbar_pending_project_id', projectId)
      removeInterceptor = interceptMobileDeepLink()
    }

    try {
      const s = getSDK()
      const result = await s.connectWallet(projectId, metadata, LedgerId.TESTNET)
      // Reaches here on iOS if universal link kept the page alive
      removeInterceptor?.()
      clearDownloadTimer()
      openWs(result.accountId)
    } catch (e: unknown) {
      removeInterceptor?.()
      clearDownloadTimer()
      // On Android the page navigated away — the error is expected; return flow handles it
      if (!IS_MOBILE) {
        setError(e instanceof Error ? e.message : String(e))
        setConnecting(false)
      }
    }
  }, [clearDownloadTimer])

  const openWs = useCallback((acctId: string) => {
	let wsUrl: string
	if (API_URL) {
	// production — point directly to Railway
	const proto = API_URL.startsWith('https') ? 'wss' : 'ws'
	wsUrl = `${proto}://${API_URL.replace(/^https?:\/\//, '')}/ws`
	} else {
	// local dev — use relative URL, Vite proxy handles it
	const proto = location.protocol === 'https:' ? 'wss' : 'ws'
	wsUrl = `${proto}://${location.host}/ws`
	}

	const socket = new WebSocket(wsUrl)
    socket.onopen = () => socket.send(JSON.stringify({ account_id: acctId }))

    socket.onmessage = async ({ data }: MessageEvent) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const msg: any = JSON.parse(data)

      if (msg.type === 'error')   { setError(msg.text); setConnecting(false); return }
      if (msg.type === 'balance') { updateBalance(Number(msg.hbar)); return }
      if (msg.type === 'typing')  { setTyping(true); return }

      if (msg.type === 'message') {
        setTyping(false); setConnecting(false); setScreen('chat')
        if (msg.text.includes('TRANSACTION_ID:')) {
          // Hold this — it will be merged into the receipt card
          pendingReceiptMsg.current = msg.text
        } else {
          addMsg('hera', msg.text)
        }
        return
      }

      if (msg.type === 'receipt') {
        // Merge agent's receipt text + on-chain details into ONE receipt card
        const receiptText = pendingReceiptMsg.current
        pendingReceiptMsg.current = ''
        addMsg('receipt', receiptText, { txId: msg.tx_id, url: msg.url })
        // Balance refresh after 5 s (mirror node needs time to index)
        setTimeout(async () => {
          try {
            const r = await fetch(`${API_URL}/api/balance/${acctId}`)
            const d = await r.json()
            if (d.hbar !== undefined) updateBalance(Number(d.hbar))
          } catch { /* ignore */ }
        }, 5000)
        return
      }

      // ── Payment request from agent ──────────────────────────────────────
      if (msg.type === 'pay') {
        const pendingId = crypto.randomUUID()
        setMessages(p => [...p, { id: pendingId, role: 'system', text: 'Waiting for wallet approval in HashPack...' }])
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const connector = (getSDK() as any).dAppConnector
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const signer = connector?.signers?.find((s: any) =>
            s.getAccountId().toString() === msg.from_account
          )
          if (!signer) throw new Error(`No signer for ${msg.from_account}. Is the wallet still connected?`)

          const tx = new TransferTransaction()
            .addHbarTransfer(AccountId.fromString(msg.from_account), new Hbar(-msg.amount_hbar))
            .addHbarTransfer(AccountId.fromString(msg.to_account),   new Hbar(msg.amount_hbar))
            .setTransactionMemo(msg.description ?? 'HBAR Coffee')

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const response: any = await signer.call(tx)
          const [a, t] = response.transactionId.toString().split('@')
          const [s2, n] = t.split('.')
          const txIdStr = `${a}-${s2}-${n}`

          setMessages(p => p.filter(m => m.id !== pendingId))
          playSuccessSound()
          setConfetti(true)
          socket.send(JSON.stringify({ type: 'payment_done', request_id: msg.request_id, tx_id: txIdStr }))
        } catch (e: unknown) {
          const reason = e instanceof Error ? e.message : String(e)
          setMessages(p => p.filter(m => m.id !== pendingId))
          playDeclineSound()
          addMsg('system', `Payment error: ${reason}`)
          socket.send(JSON.stringify({ type: 'payment_rejected', request_id: msg.request_id }))
        }
      }
    }

    socket.onclose = () => addMsg('system', 'Session ended. Refresh to reconnect.')
  }, [addMsg, updateBalance])

  const send = useCallback((text?: string) => {
    const t = text ?? input.trim()
    if (!t || !ws.current || ws.current.readyState !== WebSocket.OPEN) return
    addMsg('user', t)
    ws.current.send(JSON.stringify({ text: t }))
    if (!text) setInput('')
  }, [input, addMsg])

  /* ── Connect screen ── */
  if (screen === 'connect') return (
    <div className="connect-screen">
      <div className="connect-card">
        <div className="cup-wrap">
          <svg className="cup-svg" viewBox="0 0 72 72" fill="none">
            <path className="steam s1" d="M26 14 Q24 10 26 6 Q28 2 26 -1" strokeWidth="1.8"/>
            <path className="steam s2" d="M36 12 Q34 8 36 4 Q38 0 36 -3" strokeWidth="1.8"/>
            <path className="steam s3" d="M46 14 Q44 10 46 6 Q48 2 46 -1" strokeWidth="1.8"/>
            <path className="draw d1" strokeWidth="2.2" d="M16 20 L20 58 Q20 62 24 62 L48 62 Q52 62 52 58 L56 20 Z"/>
            <path className="draw d2" strokeWidth="2.2" d="M52 30 Q64 30 64 40 Q64 50 52 50"/>
            <path className="draw d3" strokeWidth="2"   d="M10 64 Q36 70 62 64"/>
          </svg>
          <div className="brand-name">HBAR Coffee Shop</div>
          <div className="brand-sub">Powered by Hedera</div>
        </div>
        <div className="divider"><span/><span/><span/></div>
        {connecting ? (
          <div className="spinner-wrap">
            <div className="spinner"/>
            <p>Opening wallet...</p>
            {showDownloadHint && (() => {
              const dl = getHashPackDownload()
              return (
                <div className="download-hint">
                  <p className="download-hint-text">
                    No wallet popup? You may not have HashPack installed.
                  </p>
                  <a
                    href={dl.url}
                    target="_blank"
                    rel="noopener"
                    className="download-btn"
                    onClick={clearDownloadTimer}
                  >
                    {dl.label}
                  </a>
                  <p className="download-device">{dl.hint}</p>
                </div>
              )
            })()}
          </div>
        ) : (
          <>
            <p className="connect-hint">Connect your Hedera wallet to order<br/>real coffee paid on-chain with HBAR.</p>
            <button className="connect-btn" onClick={handleConnect}>Connect Wallet</button>
            <p className="connect-sub">Works with HashPack · Testnet only</p>
          </>
        )}
        {error && <p className="connect-error">{error}</p>}
      </div>
    </div>
  )

  /* ── Chat screen ── */
  return (
    <div className="chat-screen">
      <Confetti active={confetti} onDone={() => setConfetti(false)} />

      <header className="chat-header">
        <div className="status-dot"/>
        <div className="header-info">
          <strong>Hera</strong>
          <span>Powered by Hedera</span>
        </div>
        {balance !== null && (
          <div className={`balance-badge${balanceFlash ? ' flash' : ''}`}>
            {balance.toFixed(2)} HBAR
          </div>
        )}
      </header>

      <div className="messages" style={{ position: 'relative' }}>
        <div className="chat-bg">
          <div className="latte-glow"/>
          {Array.from({ length: 20 }, (_, i) => <div key={i} className="bubble"/>)}
        </div>

        {messages.map((m: Msg) => {
          if (m.role === 'receipt') {
            const cleanText = cleanReceiptText(m.text)
            const shareText = encodeURIComponent(
              `Just bought coffee on-chain with HBAR! ${m.url} #Hedera #HBAR #HBARCoffeeShop`
            )
            return (
              <div key={m.id} className="receipt-card">
                <div className="receipt-title">Payment Confirmed</div>
                {cleanText && (
                  <div className="receipt-body">
                    <ReactMarkdown>{cleanText}</ReactMarkdown>
                  </div>
                )}
                <div className="receipt-divider"/>
                <div className="tx-id">{m.txId}</div>
                <div className="receipt-links">
                  <a href={m.url} target="_blank" rel="noopener" className="hashscan-btn">
                    View on Hashscan
                  </a>
                  <a
                    href={`https://twitter.com/intent/tweet?text=${shareText}`}
                    target="_blank" rel="noopener" className="share-btn"
                  >
                    Share on X
                  </a>
                </div>
              </div>
            )
          }
          return (
            <div key={m.id} className={`msg ${m.role}`}>
              {m.role === 'hera'
                ? <ReactMarkdown>{m.text}</ReactMarkdown>
                : m.text
              }
            </div>
          )
        })}

        {typing && <div className="msg hera typing"><span/><span/><span/></div>}
        <div ref={messagesEnd}/>
      </div>

      <div className="chips">
        {CHIPS.map(c => (
          <button key={c.label} className="chip" onClick={() => send(`I'd like a ${c.order}`)}>
            {c.label}
          </button>
        ))}
      </div>

      <div className="input-row">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="What can I get you?"
          enterKeyHint="send"
        />
        <button onClick={() => send()}>Send</button>
      </div>
    </div>
  )
}
