import { LoaderCircle, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import QuestionCard from '../../components/assessment/QuestionCard'
import QuizResult from '../../components/assessment/QuizResult'
import { generateQuiz, submitQuiz } from '../../services/assessmentApi'
import { generateRoadmap } from '../../services/roadmapApi'
import { useAuthStore } from '../../store/authStore'
import { useRoadmapStore } from '../../store/roadmapStore'

export default function DiagnosticQuiz() {
  const user = useAuthStore(s => s.user)
  const { scores, setScores, setRoadmap } = useRoadmapStore()
  const nav = useNavigate()
  const location = useLocation()

  const topic = location.state?.topic
  const previousTopics = location.state?.previous_topics || []
  const nodeId = location.state?.node_id
  const careerTarget = location.state?.career_target || user?.career_target || 'Data Engineer'

  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let isMounted = true
    async function loadQuiz() {
      try {
        const data = await generateQuiz({
          user_id: user?.id,
          career_target: careerTarget,
          skills: user?.skills || [],
          topic,
          node_id: nodeId,
          previous_topics: previousTopics,
        })
        if (isMounted) setQuiz(data)
      } catch {
        if (isMounted) setError('The local AI service is unavailable. Start Ollama and try again.')
      }
    }
    loadQuiz()
    return () => { isMounted = false }
  }, [user?.id, careerTarget, topic])

  const setAnswer = (id, value) =>
    setAnswers(all => ({ ...all, [id]: { question_id: id, ...value } }))

  const finish = async () => {
    if (
      Object.keys(answers).length !== quiz.questions.length ||
      Object.values(answers).some(a => a.selected_index === undefined || !a.confidence)
    ) {
      setError('Answer every question and add your confidence for a calibrated result.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const scored = await submitQuiz({
        user_id: user?.id,
        quiz_id: quiz.id,
        answers: Object.values(answers),
        previous_scores: scores,
      })
      setResult(scored)
      const combined = scored.skill_scores || { ...scores, ...scored.topic_scores }
      setScores(combined)
      if (scored.roadmap) {
        setRoadmap({ ...scored.roadmap, scores: combined })
      }
    } catch {
      setError('The assessment could not be scored. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const makePath = async () => {
    try {
      const combined = result.skill_scores || { ...scores, ...result.topic_scores }
      const updatedRoadmap = await generateRoadmap({
        user_id: user?.id,
        career_target: careerTarget,
        scores: combined,
        skills: user?.skills || [],
      })
      setRoadmap({ ...updatedRoadmap, scores: combined })
      nav(topic ? '/roadmap' : '/dashboard')
    } catch {
      nav(topic ? '/roadmap' : '/dashboard')
    }
  }

  if (result) {
    return (
      <main className="min-h-screen bg-ink p-5 sm:p-10">
        <QuizResult result={result} onContinue={makePath} />
      </main>
    )
  }

  if (!quiz) {
    return (
      <main className="grid min-h-screen place-items-center bg-ink text-slate-400">
        <div className="text-center px-4 max-w-md">
          <LoaderCircle className="mx-auto animate-spin text-sky-300" size={32} />
          <p className="mt-3 font-semibold text-slate-200">
            Crafting your {topic ? `${topic} ` : ''}diagnostic…
          </p>
          {previousTopics.length > 0 && (
            <p className="mt-1 text-xs text-slate-400">
              Including foundational prerequisites: {previousTopics.slice(0, 3).join(', ')}
            </p>
          )}
          {error && <p className="mt-2 text-sm text-rose-300">{error}</p>}
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-ink p-5 sm:p-10">
      <div className="mx-auto max-w-2xl">
        <div className="flex justify-between items-start gap-3">
          <div>
            <p className="eyebrow">
              {topic
                ? `Focused assessment · ${topic}`
                : 'Adaptive diagnostic'}
            </p>
            <h1 className="mt-1 text-2xl font-bold text-white">
              {topic ? `Mastery check: ${topic}` : 'How well do you know the fundamentals?'}
            </h1>
            <p className="mt-1.5 text-sm text-slate-400">
              {previousTopics.length > 0
                ? `Assessing ${topic} and continuity from: ${previousTopics.slice(0, 3).join(', ')}.`
                : 'Your confidence matters as much as the answer.'}
            </p>
          </div>
          <span className="shrink-0 rounded-full border border-sky-400/30 bg-sky-500/10 px-3 py-1 text-xs font-semibold text-sky-300">
            {Object.keys(answers).length} / {quiz.questions.length} answered
          </span>
        </div>

        <div className="mt-7 space-y-4">
          {quiz.questions.map((question, i) => (
            <QuestionCard
              key={question.id}
              question={question}
              index={i}
              answer={answers[question.id]}
              onAnswer={value => setAnswer(question.id, value)}
            />
          ))}
        </div>

        {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

        <button
          onClick={finish}
          disabled={busy}
          className="btn-primary mt-6 w-full flex items-center justify-center gap-2"
        >
          {busy ? (
            'Calibrating your path…'
          ) : (
            <>
              See my calibrated result <Sparkles size={17} />
            </>
          )}
        </button>
      </div>
    </main>
  )
}
