import { AlertTriangle, CheckCircle2, CircleDotDashed, ChevronDown, ExternalLink, PlayCircle, RefreshCw, Search, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/layout/DashboardLayout'
import SkillGraph from '../../components/roadmap/SkillGraph'
import ResourceDrawer from '../../components/roadmap/ResourceDrawer'
import { getMasteryVisual, getExcludedRoadmapNodeIds, getPreviousTopics, findMatchingScore } from '../../components/roadmap/roadmapVisuals'
import { getRoadmaps, getRoadmapBySlug, getUserRoadmap, generateRoadmap, getResources } from '../../services/roadmapApi'
import { useAuthStore } from '../../store/authStore'
import { useRoadmapStore } from '../../store/roadmapStore'

export default function RoadmapPage() {
  const user = useAuthStore(s => s.user)
  const updateUser = useAuthStore(s => s.updateUser)
  const { roadmap, scores, setRoadmap } = useRoadmapStore()
  const nav = useNavigate()

  const [roles, setRoles] = useState([])
  const [currentRoleSlug, setCurrentRoleSlug] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [resources, setResources] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [roleSearch, setRoleSearch] = useState('')
  const [isSelectorOpen, setIsSelectorOpen] = useState(false)

  // 1. Fetch all roles on mount
  useEffect(() => {
    async function loadRoles() {
      try {
        const availableRoles = await getRoadmaps()
        setRoles(availableRoles)

        // Determine initial role
        const userTarget = user?.career_target || 'Data Engineer'
        const matched = availableRoles.find(
          r => r.name.toLowerCase() === userTarget.toLowerCase() || r.roadmap_slug === userTarget.toLowerCase()
        )
        const initialSlug = matched ? matched.roadmap_slug : 'data-engineer'
        setCurrentRoleSlug(initialSlug)
      } catch (err) {
        console.error('Failed to load roles list:', err)
        setError('Could not connect to backend API.')
      }
    }
    loadRoles()
  }, [])

  // 2. Fetch or generate roadmap when role changes
  const loadActiveRoadmap = async slug => {
    if (!slug) return
    setLoading(true)
    setError('')
    try {
      const userTarget = user?.career_target || 'Data Engineer'
      const matchedRole = roles.find(
        r => r.roadmap_slug === slug || r.name.toLowerCase() === slug.toLowerCase()
      )
      const roleName = matchedRole ? matchedRole.name : slug
      const isUserCareer = userTarget.toLowerCase() === roleName.toLowerCase() || userTarget.toLowerCase() === slug.toLowerCase()

      let data = null
      // 1. If this is user's active career target, load their saved personalized roadmap with real scores
      if (user?.id && isUserCareer) {
        data = await getUserRoadmap(user.id).catch(() => null)
      }

      // 2. Otherwise load via slug passing user.id to overlay scores from backend
      if (!data) {
        data = await getRoadmapBySlug(slug, user?.id).catch(() => null)
      }

      // 3. Fallback to generateRoadmap
      if (!data && user?.id) {
        data = await generateRoadmap({
          user_id: user.id,
          career_target: roleName,
          scores: scores || {},
          skills: user.skills || [],
        }).catch(() => null)
      }

      // 4. Raw slug fallback
      if (!data) {
        data = await getRoadmapBySlug(slug)
      }

      const combinedScores = data.scores || scores || {}
      setRoadmap({ ...data, scores: combinedScores })
    } catch (err) {
      console.error(`Failed to load roadmap for ${slug}:`, err)
      setError('Could not load roadmap data. Please verify the API is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (currentRoleSlug) {
      loadActiveRoadmap(currentRoleSlug)
    }
  }, [currentRoleSlug, user?.id])

  const selectRole = role => {
    setCurrentRoleSlug(role.roadmap_slug)
    setIsSelectorOpen(false)
    if (user && updateUser) {
      updateUser({ ...user, career_target: role.name })
    }
  }

  // Filter roles for dropdown
  const filteredRoles = useMemo(() => {
    if (!roleSearch.trim()) return roles
    const q = roleSearch.toLowerCase()
    return roles.filter(r => r.name.toLowerCase().includes(q) || r.roadmap_slug.includes(q))
  }, [roles, roleSearch])

  const currentRole = useMemo(() => {
    return roles.find(r => r.roadmap_slug === currentRoleSlug) || {
      name: roadmap?.title || 'Data Engineer',
      roadmap_slug: currentRoleSlug || 'data-engineer',
      source_url: `https://roadmap.sh/${currentRoleSlug || 'data-engineer'}`,
    }
  }, [roles, currentRoleSlug, roadmap?.title])

  const stats = useMemo(() => {
    const excludedIds = getExcludedRoadmapNodeIds(roadmap?.nodes || [])
    const rawNodes = (roadmap?.nodes || []).filter(n => !excludedIds.has(n.id))
    const focusable = rawNodes.filter(n => {
      const isCheckpoint = (n.data?.label || n.data?.topic || n.label || '').trim().toLowerCase().startsWith('checkpoint')
      return isCheckpoint || n.type === 'topic' || n.type === 'subtopic' || n.type === 'skill' || n.type === 'todo'
    })
    let strong = 0
    let medium = 0
    let weak = 0
    let notStarted = 0
    let totalMastery = 0

    const allScores = { ...(roadmap?.scores || {}), ...(scores || {}) }

    for (const n of focusable) {
      const ndata = { ...(n.data || n) }
      const label = (ndata.label || ndata.topic || n.label || n.topic || '').trim()
      if (allScores && Object.keys(allScores).length > 0) {
        const found = findMatchingScore(label, allScores)
        if (found !== undefined) {
          ndata.mastery = Math.round(Number(found))
          ndata.status = ndata.mastery >= 80 ? 'completed' : ndata.mastery >= 55 ? 'in_progress' : ndata.mastery > 0 ? 'weak_gap' : 'not_started'
        }
      }
      totalMastery += (Number(ndata.mastery) || 0)
      const v = getMasteryVisual(ndata)
      if (v.key === 'strong') strong++
      else if (v.key === 'medium') medium++
      else if (v.key === 'weak') weak++
      else notStarted++
    }

    const calculatedCompletion = focusable.length ? Math.round((totalMastery / focusable.length) * 10) / 10 : 0
    return {
      total: focusable.length,
      strong,
      medium,
      weak,
      notStarted,
      completion: roadmap?.completion ?? calculatedCompletion,
    }
  }, [roadmap?.nodes, roadmap?.completion, roadmap?.scores, scores])

  // Handle node click to open resources
  const openNodeDrawer = async nodeData => {
    setSelectedNode(nodeData)
    // If node already has embedded resources, use them immediately
    if (nodeData.resources && nodeData.resources.length > 0) {
      setResources({
        topic: nodeData.label || nodeData.topic,
        description: nodeData.description,
        resources: nodeData.resources,
        paid_resources: nodeData.paid_resources || [],
        source_url: currentRole.source_url,
        practice_task: `Build a practical exercise demonstrating ${nodeData.label || nodeData.topic}.`,
      })
    } else {
      setResources(null)
    }

    // Also fetch from API to ensure fresh data
    try {
      const fetched = await getResources({
        topic: nodeData.label || nodeData.topic,
        career_target: currentRole.name,
        node_id: nodeData.id,
      })
      setResources(fetched)
    } catch {
      if (!nodeData.resources || nodeData.resources.length === 0) {
        setResources({
          resources: [],
          description: nodeData.description || '',
          practice_task: `Build an example demonstrating ${nodeData.label || nodeData.topic}.`,
        })
      }
    }
  }

  return (
    <DashboardLayout>
      {/* Top Header & Role Selector */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line/80 pb-6">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="eyebrow">Interactive Learning Path</span>
            <span className="text-slate-500">•</span>
            <span className="text-xs text-slate-400">
              Source:{' '}
              <a
                href={currentRole.source_url || 'https://roadmap.sh'}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-sky-400 hover:underline inline-flex items-center gap-1"
              >
                roadmap.sh <ExternalLink size={11} />
              </a>
            </span>
          </div>

          {/* Role Title & Selector Trigger */}
          <div className="relative mt-2">
            <button
              onClick={() => setIsSelectorOpen(!isSelectorOpen)}
              className="flex flex-wrap items-center gap-3 text-left group"
            >
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white group-hover:text-sky-300 transition-colors break-words min-w-0">
                {currentRole.name}
              </h1>
              <div className="flex items-center gap-1 rounded-lg border border-line/80 bg-slate-900/80 px-2.5 py-1 text-xs font-semibold text-slate-300 group-hover:border-sky-400 shrink-0">
                <span>Change Role ({roles.length})</span>
                <ChevronDown size={14} className={`transition-transform ${isSelectorOpen ? 'rotate-180' : ''}`} />
              </div>
            </button>

            {/* Dropdown Menu for all 29 roles */}
            {isSelectorOpen && (
              <div className="absolute left-0 top-full z-40 mt-2 w-[calc(100vw-2.5rem)] sm:w-96 max-w-sm rounded-2xl border border-line bg-slate-900/95 p-3 shadow-2xl shadow-black/80 backdrop-blur-md">
                <div className="relative">
                  <Search size={15} className="absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search 29 roles..."
                    value={roleSearch}
                    onChange={e => setRoleSearch(e.target.value)}
                    className="w-full rounded-xl border border-line bg-slate-900/90 py-2 pl-9 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-400 focus:outline-none"
                    autoFocus
                  />
                </div>

                <div className="mt-2 max-h-72 overflow-y-auto space-y-1 pr-1">
                  {filteredRoles.map(r => (
                    <button
                      key={r.roadmap_slug}
                      onClick={() => selectRole(r)}
                      className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs font-medium transition-colors ${
                        r.roadmap_slug === currentRoleSlug
                          ? 'bg-sky-500/20 text-sky-200 font-bold border border-sky-500/40'
                          : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                      }`}
                    >
                      <span className="truncate">{r.name}</span>
                      {r.node_count > 0 && (
                        <span className="text-[10px] text-slate-500 shrink-0 ml-2">{r.node_count} nodes</span>
                      )}
                    </button>
                  ))}
                  {filteredRoles.length === 0 && (
                    <p className="p-3 text-center text-xs text-slate-500">No matching roles found.</p>
                  )}
                </div>
              </div>
            )}
          </div>

          <p className="mt-2 text-sm text-slate-400">
            Authoritative curriculum from roadmap.sh. Click any topic or skill block to explore verified resources.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => loadActiveRoadmap(currentRoleSlug)}
            className="btn-ghost flex items-center gap-1.5 text-xs font-semibold"
          >
            <RefreshCw size={14} /> Refresh Graph
          </button>
        </div>
      </div>

      {/* Calibration & Stats Bar */}
      <div className="mt-5 rounded-2xl border border-line/80 bg-slate-900/50 p-3 shadow-sm backdrop-blur-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-semibold">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-emerald-300">
              <CheckCircle2 size={13} className="text-emerald-400" />
              <span>Strong ({stats.strong})</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-sky-300">
              <PlayCircle size={13} className="text-sky-400" />
              <span>Developing ({stats.medium})</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-amber-300">
              <AlertTriangle size={13} className="text-amber-400" />
              <span>Needs focus ({stats.weak})</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/60 px-3 py-1 text-slate-300">
              <CircleDotDashed size={13} className="text-slate-400" />
              <span>Not started ({stats.notStarted})</span>
            </span>
            <span className="hidden sm:inline-flex items-center rounded-full border border-line/70 bg-slate-800/40 px-3 py-1 text-slate-400">
              {stats.total} total skills
            </span>
          </div>

          <div className="flex items-center gap-2.5 rounded-xl border border-line bg-slate-900/90 px-3.5 py-1.5 text-slate-300">
            <span className="text-slate-400">Overall calibration:</span>
            <strong className="font-bold text-sky-300">{stats.completion}%</strong>
          </div>
        </div>
      </div>

      {/* Main Graph Area */}
      {loading ? (
        <div className="card mt-6 grid h-[600px] place-items-center text-slate-400">
          <div className="text-center">
            <RefreshCw className="mx-auto animate-spin text-sky-400" size={32} />
            <p className="mt-3 font-semibold text-slate-200">Loading {currentRole.name} roadmap…</p>
            <p className="mt-1 text-xs text-slate-500">Retrieving interactive structure from roadmap.sh</p>
          </div>
        </div>
      ) : error ? (
        <div className="card mt-6 p-8 text-rose-300 text-center">
          <p className="font-semibold">{error}</p>
          <button className="btn-primary mt-4" onClick={() => loadActiveRoadmap(currentRoleSlug)}>
            Try again
          </button>
        </div>
      ) : (
        <div className="mt-4">
          <SkillGraph roadmap={roadmap} onNodeClick={openNodeDrawer} />
        </div>
      )}

      {/* Resource Drawer */}
      <ResourceDrawer
        topic={selectedNode}
        resourceData={resources}
        close={() => setSelectedNode(null)}
        reevaluate={topicTitle => {
          const prevTopics = getPreviousTopics(selectedNode, roadmap)
          nav('/assessment', {
            state: {
              topic: topicTitle,
              node_id: selectedNode?.id,
              previous_topics: prevTopics,
              career_target: currentRole.name,
            },
          })
        }}
      />
    </DashboardLayout>
  )
}
