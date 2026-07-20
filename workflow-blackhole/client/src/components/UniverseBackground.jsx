"use client"

import { useEffect, useRef } from "react"
import { useTheme } from "./theme-provider"

function rand(min, max) { return Math.random() * (max - min) + min }

function createParticle(w, h) {
  const maxOrbit = Math.hypot(w, h) * 0.45
  return {
    angle: Math.random() * Math.PI * 2,
    // slightly faster and varied speeds for more dynamic motion
    speed: rand(0.3, 1.6) * 0.28,
    orbit: rand(Math.min(w, h) * 0.05, maxOrbit),
    eccentric: rand(0.6, 1.0),
    // larger sizes for better visibility
    size: rand(0.9, 3.2),
    // brighter particles on average
    alpha: rand(0.12, 1.0),
  }
}

export default function UniverseBackground() {
  const { theme } = useTheme()
  const ref = useRef(null)

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (theme !== 'universe') return
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    if (window.innerWidth < 640) return // skip on small screens

    const canvas = ref.current
    const ctx = canvas.getContext('2d')
    let dpr = window.devicePixelRatio || 1

    function resize() {
      const w = window.innerWidth
      const h = window.innerHeight
      canvas.style.width = w + 'px'
      canvas.style.height = h + 'px'
      canvas.width = Math.max(1, Math.floor(w * dpr))
      canvas.height = Math.max(1, Math.floor(h * dpr))
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      return { w, h }
    }

    let { w, h } = resize()
    // Increase particle density significantly for a richer starfield
    // New formula: more particles per area, min 300, max 2000
    const particles = Array.from({ length: Math.ceil(Math.max(300, Math.min(2000, (w * h) / 20000))) }, () => createParticle(w, h))

    let rafId
    let last = performance.now()

    function draw(now) {
      const dt = (now - last) / 1000
      last = now
      ctx.clearRect(0, 0, w, h)

      const cx = w / 2
      const cy = h / 2

      particles.forEach(p => {
        p.angle += p.speed * dt
        const x = cx + Math.cos(p.angle) * p.orbit
        const y = cy + Math.sin(p.angle) * p.orbit * p.eccentric

        const brightness = Math.min(1, 0.25 + (1 - (p.orbit / (Math.hypot(w, h) * 0.45))) * 0.9)
        ctx.beginPath()
        ctx.fillStyle = `rgba(255,255,255,${p.alpha * brightness})`
        ctx.arc(x, y, p.size, 0, Math.PI * 2)
        ctx.fill()
      })

      rafId = requestAnimationFrame(draw)
    }

    rafId = requestAnimationFrame(draw)

    function onResize() {
      const dims = resize()
      w = dims.w; h = dims.h
      particles.length = 0
      const count = Math.ceil(Math.max(300, Math.min(2000, (w * h) / 20000)))
      for (let i = 0; i < count; i++) particles.push(createParticle(w, h))
    }

    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('resize', onResize)
    }
  }, [theme])

  return (
    <canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed inset-0"
      style={{ zIndex: 5 }}
    />
  )
}
