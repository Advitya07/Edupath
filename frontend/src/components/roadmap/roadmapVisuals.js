import { AlertTriangle, CheckCircle2, CircleDotDashed, PlayCircle } from 'lucide-react'

export const masteryVisuals = {
  strong: {
    key: 'strong',
    label: 'Strong',
    shortLabel: 'Strong',
    detail: 'Mastered (80–100%)',
    Icon: CheckCircle2,
    accent: '#10b981',
    node: 'border-emerald-400/55 bg-gradient-to-br from-emerald-500/15 via-emerald-950/10 to-slate-900/80 text-emerald-100 shadow-sm shadow-emerald-950/20 ring-1 ring-emerald-500/20',
    progress: 'bg-emerald-400',
    icon: 'text-emerald-300',
    badge: 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/35',
    chip: 'bg-emerald-400/10 text-emerald-300 border-emerald-500/30',
  },
  medium: {
    key: 'medium',
    label: 'Developing',
    shortLabel: 'Medium',
    detail: 'In progress (55–79%)',
    Icon: PlayCircle,
    accent: '#38bdf8',
    node: 'border-sky-400/50 bg-gradient-to-br from-sky-500/12 via-sky-950/10 to-slate-900/80 text-sky-100 shadow-sm shadow-sky-950/20 ring-1 ring-sky-500/20',
    progress: 'bg-sky-400',
    icon: 'text-sky-300',
    badge: 'bg-sky-400/15 text-sky-300 border border-sky-400/35',
    chip: 'bg-sky-400/10 text-sky-300 border-sky-500/30',
  },
  weak: {
    key: 'weak',
    label: 'Needs focus',
    shortLabel: 'Focus',
    detail: 'Skill gap (<55%)',
    Icon: AlertTriangle,
    accent: '#fbbf24',
    node: 'border-amber-400/55 bg-gradient-to-br from-amber-500/15 via-amber-950/10 to-slate-900/80 text-amber-100 shadow-sm shadow-amber-950/20 ring-1 ring-amber-400/30',
    progress: 'bg-amber-400',
    icon: 'text-amber-300',
    badge: 'bg-amber-400/15 text-amber-300 border border-amber-400/35',
    chip: 'bg-amber-400/10 text-amber-300 border-amber-500/30',
  },
  not_started: {
    key: 'not_started',
    label: 'Not started',
    shortLabel: 'New',
    detail: 'Not started (0%)',
    Icon: CircleDotDashed,
    accent: '#64748b',
    node: 'border-slate-600/70 border-dashed bg-slate-900/65 text-slate-300 shadow-sm shadow-slate-950/15',
    progress: 'bg-slate-700/80',
    icon: 'text-slate-400',
    badge: 'bg-slate-800/80 text-slate-400 border border-slate-700/60',
    chip: 'bg-slate-800/40 text-slate-400 border-slate-700/40',
  },
}

export function getMasteryValue(data = {}) {
  const value = Number(data.mastery)
  return Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value))) : 0
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function findMatchingScore(label, scores = {}) {
  if (!label || !scores || typeof scores !== 'object') return undefined
  const l = label.trim().toLowerCase()

  // 1. Exact case-insensitive match
  for (const [k, v] of Object.entries(scores)) {
    if (k.trim().toLowerCase() === l) return Number(v)
  }

  // 2. Clean punctuation match
  const cleanL = l.replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()
  for (const [k, v] of Object.entries(scores)) {
    const cleanK = k.trim().toLowerCase().replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()
    if (cleanK && cleanK === cleanL) return Number(v)
  }

  // 3. Word boundary match for keys with length >= 3 (avoids 'go' matching 'algorithms')
  let bestMatch = undefined
  let bestLen = 0
  for (const [k, v] of Object.entries(scores)) {
    const kLow = k.trim().toLowerCase()
    if (kLow.length >= 3) {
      const regex = new RegExp(`\\b${escapeRegExp(kLow)}\\b`, 'i')
      if (regex.test(l) && kLow.length > bestLen) {
        bestLen = kLow.length
        bestMatch = Number(v)
      }
    } else if (l.length >= 4) {
      const regex = new RegExp(`\\b${escapeRegExp(l)}\\b`, 'i')
      if (regex.test(kLow) && l.length > bestLen) {
        bestLen = l.length
        bestMatch = Number(v)
      }
    }
  }

  return bestMatch
}

// This is a presentation-only mapping of the existing score and status fields.
export function getMasteryVisual(data = {}) {
  const mastery = getMasteryValue(data)
  const status = data.status
  const key = mastery === 0
    ? 'not_started'
    : status === 'completed' || mastery >= 80
      ? 'strong'
      : status === 'in_progress' || mastery >= 55
        ? 'medium'
        : 'weak'

  return { key, mastery, ...masteryVisuals[key] }
}

export function getExcludedRoadmapNodeIds(nodes = []) {
  const ids = new Set()
  const titleNode = nodes.find(n => n.type === 'title')
  const titleY = titleNode?.position?.y ?? null

  // 1. Linksgroup nodes are always external 'Related Roadmaps' promotional cards
  for (const n of nodes) {
    if (n.type === 'linksgroup') {
      ids.add(n.id)
    }
  }

  // 2. Promotional, roadmap.sh, and cross-roadmap phrases
  const promoPhrases = [
    'detailed version of this roadmap',
    'roadmap.sh',
    'also visit the following related roadmaps',
    'continue learning with following relevant tracks',
    'you can pick any backend programming language',
    'scrimba is offering',
    'scrimba - ai engineer path',
    'visit beginner friendly version',
    'visit the beginner version',
    'visit devops roadmap',
    'visit the data analyst roadmap',
    'visit his blog',
    'visit his github',
    'visit his linkedin',
    'visit their website',
    'if you are already a full-stack developer you should visit the following tracks',
  ]

  for (const n of nodes) {
    const lbl = (n.data?.label || n.data?.topic || n.label || '').trim().toLowerCase()
    if (promoPhrases.some(p => lbl.includes(p))) {
      ids.add(n.id)
    }
  }

  // 3. Pre-requisites header / box at the top of the map
  const prereqNodes = nodes.filter(n => {
    const lbl = (n.data?.label || n.label || '').trim().toLowerCase()
    const isPrereqText = lbl.includes('pre-requisite') || lbl.includes('prerequisite')
    const isTopHeader = titleY === null || (n.position?.y ?? 9999) < titleY + 100
    return isPrereqText && (n.type === 'label' || n.type === 'paragraph' || n.type === 'section') && isTopHeader
  })

  for (const pr of prereqNodes) {
    ids.add(pr.id)
    const px = pr.position?.x ?? 0
    const py = pr.position?.y ?? 0
    for (const n of nodes) {
      const nx = n.position?.x ?? 0
      const ny = n.position?.y ?? 0
      if (['section', 'button', 'vertical', 'horizontal', 'label'].includes(n.type)) {
        if (Math.abs(nx - px) <= 350 && Math.abs(ny - py) <= 300) {
          ids.add(n.id)
        }
      }
    }
  }

  // 4. Buttons at or above the title node
  if (titleY !== null) {
    for (const n of nodes) {
      if (n.type === 'button' || n.type === 'resourceButton') {
        if ((n.position?.y ?? 9999) <= titleY + 5) {
          ids.add(n.id)
        }
      }
    }
  }

  // 5. Dangling vertical nodes above title
  if (titleY !== null) {
    for (const n of nodes) {
      if (n.type === 'vertical' && (n.position?.y ?? 9999) < titleY) {
        ids.add(n.id)
      }
    }
  }

  // 6. Bottom trailing sections
  const bottomHeaders = nodes.filter(n => {
    const lbl = (n.data?.label || n.label || '').trim().toLowerCase()
    return (
      lbl.includes('continue learning with following relevant tracks') ||
      lbl.includes('also visit the following related roadmaps')
    )
  })

  for (const bh of bottomHeaders) {
    ids.add(bh.id)
    const cy = bh.position?.y ?? 0
    const cx = bh.position?.x ?? 0
    for (const n of nodes) {
      const ny = n.position?.y ?? 0
      const nx = n.position?.x ?? 0
      if (
        ['button', 'vertical', 'horizontal', 'resourceButton'].includes(n.type) &&
        ny >= cy - 20 &&
        Math.abs(nx - cx) <= 800
      ) {
        ids.add(n.id)
      }
    }
  }

  return ids
}

export function getPreviousTopics(targetNode, roadmap) {
  if (!targetNode || !roadmap) return []
  const targetId = targetNode.id || targetNode.data?.id
  const nodes = roadmap.nodes || []
  const edges = roadmap.edges || []
  const nodesById = new Map(nodes.map(n => [n.id, n]))
  const prevTopics = []
  const seen = new Set([targetId])

  // 1. Direct and indirect predecessors via incoming edges
  const queue = [targetId]
  while (queue.length > 0 && prevTopics.length < 4) {
    const curr = queue.shift()
    for (const e of edges) {
      if (e.target === curr && !seen.has(e.source)) {
        seen.add(e.source)
        queue.push(e.source)
        const sNode = nodesById.get(e.source)
        if (sNode) {
          const lbl = (sNode.data?.label || sNode.data?.topic || sNode.label || sNode.topic || '').trim()
          const t = sNode.type
          if (['topic', 'subtopic', 'checkpoint', 'skill', 'todo'].includes(t) && lbl && !prevTopics.includes(lbl)) {
            prevTopics.push(lbl)
          }
        }
      }
    }
  }

  // 2. Sequential earlier topics in layout flow
  const focusable = nodes
    .filter(n => ['topic', 'subtopic', 'checkpoint', 'skill', 'todo'].includes(n.type))
    .sort((a, b) => (a.position?.y || 0) - (b.position?.y || 0) || (a.position?.x || 0) - (b.position?.x || 0))

  const targetIdx = focusable.findIndex(n => n.id === targetId)
  if (targetIdx > 0) {
    const currentLabel = (targetNode.label || targetNode.topic || targetNode.data?.label || targetNode.data?.topic || '').trim().toLowerCase()
    for (let i = targetIdx - 1; i >= 0 && prevTopics.length < 5; i--) {
      const lbl = (focusable[i].data?.label || focusable[i].data?.topic || focusable[i].label || '').trim()
      if (lbl && !prevTopics.includes(lbl) && lbl.toLowerCase() !== currentLabel) {
        prevTopics.push(lbl)
      }
    }
  }

  return prevTopics.slice(0, 4)
}


