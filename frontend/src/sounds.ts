type AudioCtx = AudioContext & { state: string }

function ctx(): AudioCtx | null {
  try {
    return new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)() as AudioCtx
  } catch { return null }
}

export function playSuccessSound() {
  const ac = ctx(); if (!ac) return
  // Brewing bubbles: short filtered noise burst
  const buf = ac.createBuffer(1, ac.sampleRate * 0.25, ac.sampleRate)
  const d = buf.getChannelData(0)
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1
  const noise = ac.createBufferSource()
  noise.buffer = buf
  const bp = ac.createBiquadFilter()
  bp.type = 'bandpass'; bp.frequency.value = 500; bp.Q.value = 0.6
  const ng = ac.createGain()
  ng.gain.setValueAtTime(0.12, ac.currentTime)
  ng.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.25)
  noise.connect(bp); bp.connect(ng); ng.connect(ac.destination)
  noise.start(); noise.stop(ac.currentTime + 0.25)

  // Ascending chime: C5 E5 G5 C6
  ;[523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    const t = ac.currentTime + 0.3 + i * 0.11
    gain.gain.setValueAtTime(0, t)
    gain.gain.linearRampToValueAtTime(0.22, t + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.55)
    osc.connect(gain); gain.connect(ac.destination)
    osc.start(t); osc.stop(t + 0.6)
  })
}

export function playDeclineSound() {
  const ac = ctx(); if (!ac) return
  // Soft descending G4 -> Eb4 — gentle, not harsh
  ;[392, 311.13].forEach((freq, i) => {
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    const t = ac.currentTime + i * 0.2
    gain.gain.setValueAtTime(0, t)
    gain.gain.linearRampToValueAtTime(0.18, t + 0.03)
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.45)
    osc.connect(gain); gain.connect(ac.destination)
    osc.start(t); osc.stop(t + 0.5)
  })
}
