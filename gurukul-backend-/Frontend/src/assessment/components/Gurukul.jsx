import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabaseClient'
import { CLERK_ENABLED } from '../config/auth'
import { assessmentQuestions, knowledgebase, syllabus } from '../data/gurukul'

function ProgressBar({ label, value }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm text-white/80">
        <span>{label}</span>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="h-2 w-full rounded bg-white/10">
        <div
          className="h-2 rounded bg-orange-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  )
}

function TierCard({ tier, items, onComplete }) {
  return (
    <div className="rounded-xl border border-white/20 bg-white/10 p-4">
      <h3 className="text-lg font-semibold mb-2">{tier} Tier</h3>
      <ul className="space-y-2">
        {items.map((l) => (
          <li key={l.lesson_id} className="rounded-lg border border-white/10 bg-white/5 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-medium">{l.title}</div>
                <div className="text-sm text-white/70">{l.description}</div>
                <div className="mt-1 text-xs text-white/60">
                  Type: {l.content_type} · Vedic link: {l.vedic_link}
                </div>
              </div>
              {onComplete && (
                <button
                  onClick={() => onComplete(tier, l.lesson_id)}
                  className="shrink-0 rounded-md border border-white/30 px-3 py-1 text-xs hover:bg-white/10"
                >
                  Mark Complete
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Gurukul() {
  const [stage, setStage] = useState('landing')
  const [progress, setProgress] = useState(() => {
    const saved = localStorage.getItem('gurukul_progress')
    return saved ? JSON.parse(saved) : { Seed: 0, Tree: 0, Sky: 0 }
  })
  const [answers, setAnswers] = useState({})
  const [assessmentDone, setAssessmentDone] = useState(() => {
    return Boolean(localStorage.getItem('gurukul_assessment'))
  })
  const [query, setQuery] = useState('')
  const filteredKb = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return knowledgebase
    return knowledgebase.filter((k) =>
      [k.title, k.description, k.category, k.modern_application]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    )
  }, [query])

  useEffect(() => {
    // Keep: if later we want to link Supabase row-level data with Clerk
    const { data } = supabase.auth.onAuthStateChange(() => {})
    return () => {
      data.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('gurukul_progress', JSON.stringify(progress))
  }, [progress])

  // Auth handled by Clerk; Supabase auth UI removed for simplicity.

  function updateAnswer(qId, choice) {
    setAnswers((a) => ({ ...a, [qId]: choice }))
  }

  function submitAssessment() {
    const detail = assessmentQuestions.map((q) => {
      const selected = answers[q.id]
      const is_correct = selected === q.correct_answer
      return {
        question_id: q.id,
        selected_option: selected ?? null,
        is_correct,
        explanation: '',
        ai_score: is_correct ? 1 : 0,
      }
    })
    const score = detail.reduce((s, d) => s + (d.ai_score || 0), 0)
    const result = {
      id: crypto.randomUUID(),
      questions: assessmentQuestions,
      user_responses: detail,
      total_score: score,
      max_score: assessmentQuestions.length,
      created_at: new Date().toISOString(),
    }
    localStorage.setItem('gurukul_assessment', JSON.stringify(result))
    setAssessmentDone(true)
    // naive progress mapping
    const pct = Math.round((score / assessmentQuestions.length) * 100)
    setProgress({ Seed: Math.min(100, pct), Tree: Math.max(0, pct - 30), Sky: Math.max(0, pct - 60) })
    setStage('dashboard')
  }

  function onCompleteLesson(tier) {
    // simple +10% per completion
    setProgress((p) => ({ ...p, [tier]: Math.min(100, (p[tier] || 0) + 10) }))
  }

  return (
    <div className="text-white">
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Gurukul Learning</h2>
          <p className="text-white/70 text-sm">Seed → Tree → Sky learning path</p>
        </div>
          <div className="flex items-center gap-2" />
      </div>

      {stage === 'landing' && (
        <div className="rounded-2xl border border-white/20 bg-white/10 p-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <h3 className="text-2xl font-semibold">Welcome to Gurukul</h3>
              <p className="mt-2 text-white/80">
                Learn through the Seed → Tree → Sky journey with coding, logic, math, language, culture, and Vedic wisdom.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button onClick={() => setStage('assessment')} className="rounded-md bg-orange-500 px-4 py-2 text-sm hover:bg-orange-600">Start Assessment</button>
                <button onClick={() => setStage('dashboard')} className="rounded-md border border-white/30 px-4 py-2 text-sm hover:bg-white/10">Go to Dashboard</button>
                <button onClick={() => setStage('syllabus')} className="rounded-md border border-white/30 px-4 py-2 text-sm hover:bg-white/10">View Syllabus</button>
                <button onClick={() => setStage('knowledge')} className="rounded-md border border-white/30 px-4 py-2 text-sm hover:bg-white/10">Vedic Knowledgebase</button>
              </div>
            </div>
            <div className="space-y-3">
              <ProgressBar label="Seed" value={progress.Seed} />
              <ProgressBar label="Tree" value={progress.Tree} />
              <ProgressBar label="Sky" value={progress.Sky} />
            </div>
          </div>
        </div>
      )}

      {stage === 'assessment' && (
        <div className="rounded-2xl border border-white/20 bg-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Initial Assessment</h3>
            <button onClick={() => setStage('landing')} className="rounded-md border border-white/30 px-3 py-1 text-sm hover:bg-white/10">Back</button>
          </div>
          <div className="space-y-5">
            {assessmentQuestions.map((q, idx) => (
              <div key={q.id} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium">{idx + 1}. {q.question_text}</div>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {q.options.map((opt) => (
                    <label key={opt} className="flex items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        value={opt}
                        checked={answers[q.id] === opt}
                        onChange={() => updateAnswer(q.id, opt)}
                      />
                      <span>{opt}</span>
                    </label>
                  ))}
                </div>
                <div className="mt-2 text-xs text-white/60">Category: {q.category} · Difficulty: {q.difficulty}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-end gap-2">
            <button onClick={() => setStage('landing')} className="rounded-md border border-white/30 px-4 py-2 text-sm hover:bg-white/10">Cancel</button>
            <button onClick={submitAssessment} className="rounded-md bg-orange-500 px-4 py-2 text-sm hover:bg-orange-600">Submit</button>
          </div>
          {assessmentDone && (
            <div className="mt-3 text-xs text-white/60">Previous assessment saved locally.</div>
          )}
        </div>
      )}

      {stage === 'dashboard' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Personalized Dashboard</h3>
            <button onClick={() => setStage('landing')} className="rounded-md border border-white/30 px-3 py-1 text-sm hover:bg-white/10">Back</button>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <ProgressBar label="Seed" value={progress.Seed} />
            <ProgressBar label="Tree" value={progress.Tree} />
            <ProgressBar label="Sky" value={progress.Sky} />
          </div>
          <div className="rounded-xl border border-white/20 bg-white/10 p-4">
            <div className="font-medium">AI Recommendations</div>
            <ul className="mt-2 list-disc pl-5 text-sm text-white/80">
              <li>Complete the first 3 Seed lessons to unlock Tree tier tips.</li>
              <li>Try the daily logic challenge in Seed tier.</li>
            </ul>
          </div>
        </div>
      )}

      {stage === 'syllabus' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Syllabus</h3>
            <button onClick={() => setStage('landing')} className="rounded-md border border-white/30 px-3 py-1 text-sm hover:bg-white/10">Back</button>
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <TierCard tier="Seed" items={syllabus.Seed} onComplete={onCompleteLesson} />
            <TierCard tier="Tree" items={syllabus.Tree} onComplete={onCompleteLesson} />
            <TierCard tier="Sky" items={syllabus.Sky} onComplete={onCompleteLesson} />
          </div>
        </div>
      )}

      {stage === 'knowledge' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Vedic Knowledgebase</h3>
            <button onClick={() => setStage('landing')} className="rounded-md border border-white/30 px-3 py-1 text-sm hover:bg-white/10">Back</button>
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search (e.g., Arthashastra, leadership)"
            className="w-full rounded-md bg-white/10 border border-white/20 px-3 py-2 text-sm placeholder-white/60 text-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
          />
          <div className="grid gap-3 md:grid-cols-2">
            {filteredKb.map((k) => (
              <div key={k.id} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium">{k.title}</div>
                <div className="text-sm text-white/80 mt-1">{k.description}</div>
                <div className="text-xs text-white/60 mt-2">Category: {k.category}</div>
                <div className="text-xs text-white/60">Modern application: {k.modern_application}</div>
                {k.related_lessons?.length > 0 && (
                  <div className="text-xs text-white/60 mt-1">Related lessons: {k.related_lessons.join(', ')}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


