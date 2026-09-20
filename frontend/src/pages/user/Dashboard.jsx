import { ArrowRight, BookOpen, CircleAlert, Trophy, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../../components/layout/DashboardLayout'
import { useAuthStore } from '../../store/authStore'
import { useRoadmapStore } from '../../store/roadmapStore'
import { getUserRoadmap, generateRoadmap } from '../../services/roadmapApi'

export default function Dashboard() {
  const user = useAuthStore(s => s.user)
  const { roadmap, setRoadmap, setScores } = useRoadmapStore()
  const [loading, setLoading] = useState(!roadmap)

  useEffect(() => {
    if (!user?.id) return
    let isMounted = true

    async function loadDashboardRoadmap() {
      try {
        const data = await getUserRoadmap(user.id).catch(() =>
          generateRoadmap({
            user_id: user.id,
            career_target: user.career_target || 'Data Engineer',
            skills: user.skills || [],
          })
        )
        if (isMounted && data) {
          setRoadmap(data)
          if (data.scores) setScores(data.scores)
        }
      } catch (err) {
        console.error('Failed to load user roadmap for dashboard:', err)
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadDashboardRoadmap()
    return () => { isMounted = false }
  }, [user?.id, user?.career_target])

  const nodes = (roadmap?.nodes || []).filter(n => {
    const t = n.type
    return ['topic', 'subtopic', 'checkpoint', 'skill', 'todo'].includes(t) || !t
  })

  const getNodeStatus = n => n.data?.status || n.status || 'not_started'
  const getNodeTopic = n => (n.data?.label || n.data?.topic || n.topic || n.label || '').trim()

  const gaps = nodes.filter(n => getNodeStatus(n) === 'weak_gap')
  const inProgress = nodes.filter(n => getNodeStatus(n) === 'in_progress')
  const completed = nodes.filter(n => getNodeStatus(n) === 'completed')

  const completion = roadmap?.completion != null ? roadmap.completion : 0
  const activeTopic = inProgress[0] ? getNodeTopic(inProgress[0]) : (gaps[0] ? getNodeTopic(gaps[0]) : 'Choose next topic')
  const recommendTopic = gaps[0] ? getNodeTopic(gaps[0]) : (inProgress[0] ? getNodeTopic(inProgress[0]) : 'your next topic')

  return (
    <DashboardLayout>
      <p className="eyebrow">Your learning command center</p>
      <h1 className="mt-2 text-3xl font-bold text-white">
        Good to see you, {user?.name?.split(' ')[0] || 'Learner'}.
      </h1>
      <p className="mt-2 text-slate-400">
        {user?.career_target || 'Choose a destination'} · a focused path, updated as you learn.
      </p>

      {loading && !roadmap ? (
        <div className="card mt-8 grid h-48 place-items-center text-slate-400">
          <div className="text-center">
            <RefreshCw className="mx-auto animate-spin text-sky-400" size={24} />
            <p className="mt-2 text-sm font-medium">Calibrating your learning command center…</p>
          </div>
        </div>
      ) : !roadmap ? (
        <section className="card mt-8 bg-gradient-to-br from-sky-400/15 to-indigo-400/10 p-7">
          <BookOpen className="text-sky-300" />
          <h2 className="mt-4 text-xl font-bold text-white">Your roadmap is waiting for a signal.</h2>
          <p className="mt-2 max-w-xl text-slate-400">
            Take a confidence-aware diagnostic, then we’ll create a visual plan around your highest-leverage gaps.
          </p>
          <Link className="btn-primary mt-5" to="/assessment">
            Take the diagnostic <ArrowRight size={17} />
          </Link>
        </section>
      ) : (
        <>
          <section className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="card p-5">
              <Trophy className="text-emerald-300" />
              <p className="mt-4 text-3xl font-bold text-white">{completion}%</p>
              <p className="mt-1 text-sm text-slate-400">Calibrated mastery</p>
            </div>
            <div className="card p-5">
              <CircleAlert className="text-amber-300" />
              <p className="mt-4 text-3xl font-bold text-white">{gaps.length}</p>
              <p className="mt-1 text-sm text-slate-400">Priority skill gaps</p>
            </div>
            <div className="card p-5">
              <BookOpen className="text-sky-300" />
              <p className="mt-4 text-xl font-bold text-white truncate" title={activeTopic}>{activeTopic}</p>
              <p className="mt-1 text-sm text-slate-400">Currently in progress</p>
            </div>
          </section>

          <section className="card mt-5 p-6">
            <p className="eyebrow">Recommended next move</p>
            <h2 className="mt-2 text-xl font-bold text-white">Strengthen {recommendTopic}</h2>
            <p className="mt-2 text-sm text-slate-400">A short focused block will create the clearest gain in your path.</p>
            <Link to="/roadmap" className="btn-primary mt-5">
              Open learning path <ArrowRight size={17} />
            </Link>
          </section>
        </>
      )}
    </DashboardLayout>
  )
}
