import { useEffect, useRef } from 'react'

interface Particle {
  x: number; y: number; vx: number; vy: number
  r: number; color: string; alpha: number; spin: number; rot: number
}

const COLORS = ['#b8711a','#d4892a','#f3e4cc','#3a7048','#7d5a38','#ede5d4','#e8c99a']

export default function Confetti({ active, onDone }: { active: boolean; onDone: () => void }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    if (!active) return
    const canvas = ref.current; if (!canvas) return
    const ctx = canvas.getContext('2d')!
    canvas!.width = window.innerWidth
    canvas!.height = window.innerHeight

    const particles: Particle[] = Array.from({ length: 80 }, () => ({
      x: canvas.width / 2 + (Math.random() - 0.5) * 200,
      y: canvas.height * 0.55,
      vx: (Math.random() - 0.5) * 12,
      vy: -(Math.random() * 10 + 6),
      r: Math.random() * 5 + 3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: 1,
      spin: (Math.random() - 0.5) * 0.3,
      rot: Math.random() * Math.PI * 2,
    }))

    let start = performance.now()

    function draw(now: number) {
      const elapsed = now - start
      ctx.clearRect(0, 0, canvas!.width, canvas!.height)
      particles.forEach(p => {
        p.vy += 0.25   // gravity
        p.x += p.vx
        p.y += p.vy
        p.rot += p.spin
        p.alpha = Math.max(0, 1 - elapsed / 1800)
        ctx.save()
        ctx.globalAlpha = p.alpha
        ctx.translate(p.x, p.y)
        ctx.rotate(p.rot)
        ctx.fillStyle = p.color
        ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r)
        ctx.restore()
      })
      if (elapsed < 1800) {
        rafRef.current = requestAnimationFrame(draw)
      } else {
        ctx.clearRect(0, 0, canvas!.width, canvas!.height)
        onDone()
      }
    }

    rafRef.current = requestAnimationFrame(draw)
    return () => { cancelAnimationFrame(rafRef.current) }
  }, [active, onDone])

  if (!active) return null
  return (
    <canvas
      ref={ref}
      style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        zIndex: 999,
      }}
    />
  )
}
