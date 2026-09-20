import { Handle, Position } from '@xyflow/react'
import { BookOpen, ExternalLink, Flag } from 'lucide-react'
import { getMasteryVisual } from './roadmapVisuals'

export function NodeHandles() {
  return (
    <>
      {[
        [Position.Top, 'w1'], [Position.Top, 'w2'],
        [Position.Bottom, 'x1'], [Position.Bottom, 'x2'],
        [Position.Left, 'y1'], [Position.Left, 'y2'],
        [Position.Right, 'z1'], [Position.Right, 'z2'],
      ].flatMap(([position, id]) => [
        <Handle key={`target-${id}`} type="target" position={position} id={id} className="!h-1 !w-1 !opacity-0" />,
        <Handle key={`source-${id}`} type="source" position={position} id={id} className="!h-1 !w-1 !opacity-0" />,
      ])}
    </>
  )
}

export function TopicNode({ data, width, height }) {
  const mastery = getMasteryVisual(data)
  const Icon = mastery.Icon
  const resourcesCount = data.resources?.length || 0
  const label = data.label || data.topic || ''
  const ui = data.__ui || {}
  const title = `${label} • ${mastery.label} (${mastery.mastery}% mastery). Click to view resources.`

  return (
    <div
      title={title}
      aria-label={title}
      role="button"
      tabIndex={0}
      className={`group relative h-full w-full min-w-0 rounded-xl border p-2 shadow-sm transition-[transform,opacity,box-shadow,border-color] duration-200 hover:-translate-y-0.5 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 ${mastery.node} ${
        ui.isActive
          ? 'z-20 -translate-y-0.5 !border-sky-300 ring-2 ring-sky-400 shadow-xl shadow-sky-500/25'
          : ui.isFocused
            ? 'z-10 -translate-y-0.5 !border-sky-300 ring-2 ring-sky-400/40 shadow-lg shadow-sky-500/15'
            : ''
      } ${ui.isRelated ? 'border-sky-400/70 ring-1 ring-sky-400/30' : ''} ${
        ui.isMuted ? 'opacity-35 saturate-50' : ''
      } ${ui.shouldReveal ? 'learning-node--reveal' : ''} ${ui.isReady ? 'learning-node--ready' : ''}`}
      style={ui.shouldReveal ? { animationDelay: `${ui.revealDelay || 0}ms` } : undefined}
    >
      <NodeHandles />
      <div className="flex min-w-0 items-start justify-between gap-1.5">
        <p className="min-w-0 flex-1 truncate text-[11px] font-semibold leading-tight tracking-[0.01em] text-slate-100 group-hover:text-white" title={label}>
          {label}
        </p>
        <div className="flex shrink-0 items-center gap-1">
          <span className={`inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-[8px] font-bold uppercase tracking-wider ${mastery.badge}`}>
            <Icon size={9} aria-hidden="true" />
            <span className="hidden min-[160px]:inline">{mastery.shortLabel}</span>
          </span>
        </div>
      </div>
      <div className="absolute inset-x-2 bottom-1.5 flex items-center gap-1.5">
        <div className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-slate-950/60" aria-hidden="true">
          <div
            className={`h-full rounded-full transition-all duration-300 ${mastery.progress}`}
            style={{ width: `${mastery.mastery}%` }}
          />
        </div>
        <span className="shrink-0 font-mono text-[9px] font-bold leading-none text-slate-300">{mastery.mastery}%</span>
        {resourcesCount > 0 && (
          <span
            className="inline-flex shrink-0 items-center gap-0.5 text-[9px] font-medium text-sky-300"
            title={`${resourcesCount} verified resources`}
          >
            <BookOpen size={10} />
            <span>{resourcesCount}</span>
          </span>
        )}
      </div>
      <span className="sr-only">{mastery.label}, {mastery.mastery}%</span>
    </div>
  )
}

export function SubtopicNode({ data, width, height }) {
  const mastery = getMasteryVisual(data)
  const Icon = mastery.Icon
  const resourcesCount = data.resources?.length || 0
  const label = data.label || data.topic || ''
  const ui = data.__ui || {}
  const title = `${label} • ${mastery.label} (${mastery.mastery}% mastery). Click to view resources.`

  return (
    <div
      title={title}
      aria-label={title}
      role="button"
      tabIndex={0}
      className={`group relative h-full w-full min-w-0 rounded-lg border px-2 py-1.5 shadow-sm transition-[transform,opacity,box-shadow,border-color] duration-200 hover:-translate-y-0.5 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 ${mastery.node} ${
        ui.isActive
          ? 'z-20 -translate-y-0.5 !border-sky-300 ring-2 ring-sky-400 shadow-xl shadow-sky-500/25'
          : ui.isFocused
            ? 'z-10 -translate-y-0.5 !border-sky-300 ring-2 ring-sky-400/40 shadow-lg shadow-sky-500/15'
            : ''
      } ${ui.isRelated ? 'border-sky-400/70 ring-1 ring-sky-400/30' : ''} ${
        ui.isMuted ? 'opacity-35 saturate-50' : ''
      } ${ui.shouldReveal ? 'learning-node--reveal' : ''} ${ui.isReady ? 'learning-node--ready' : ''}`}
      style={ui.shouldReveal ? { animationDelay: `${ui.revealDelay || 0}ms` } : undefined}
    >
      <NodeHandles />
      <div className="flex min-w-0 items-center justify-between gap-1.5">
        <span className="min-w-0 flex-1 truncate text-[10px] font-medium leading-tight text-slate-200 group-hover:text-white" title={label}>
          {label}
        </span>
        <div className="flex shrink-0 items-center gap-1">
          {resourcesCount > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[9px] font-semibold text-sky-300" title={`${resourcesCount} resources`}>
              <BookOpen size={9} />
              {resourcesCount}
            </span>
          )}
          <Icon className={mastery.icon} size={11} aria-hidden="true" />
        </div>
      </div>
      <div className="absolute inset-x-2 bottom-1 h-1 overflow-hidden rounded-full bg-slate-950/60" aria-hidden="true">
        <div
          className={`h-full rounded-full transition-all duration-300 ${mastery.progress}`}
          style={{ width: `${mastery.mastery}%` }}
        />
      </div>
      <span className="sr-only">{mastery.label}, {mastery.mastery}%</span>
    </div>
  )
}

export function CheckpointNode({ data, width, height }) {
  const mastery = getMasteryVisual(data)
  const resourcesCount = data.resources?.length || 0
  const label = data.label || data.topic || 'Checkpoint'
  const ui = data.__ui || {}
  const title = `Milestone Checkpoint: ${label} • ${mastery.label} (${mastery.mastery}% mastery). Click to view details.`

  return (
    <div
      title={title}
      aria-label={title}
      role="button"
      tabIndex={0}
      className={`group relative h-full w-full min-w-0 rounded-xl border-2 px-3 py-2 shadow-lg transition-[transform,opacity,box-shadow,border-color] duration-200 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-400 ${
        ui.isActive
          ? 'z-20 -translate-y-0.5 !border-amber-300 ring-2 ring-amber-400 shadow-xl shadow-amber-500/25 bg-gradient-to-r from-slate-900/95 via-amber-950/40 to-slate-900/95'
          : ui.isFocused
            ? 'z-10 -translate-y-0.5 !border-amber-400 ring-2 ring-amber-400/40 shadow-lg shadow-amber-500/20 bg-gradient-to-r from-slate-900/95 via-indigo-950/50 to-slate-900/95'
            : 'border-indigo-400/60 bg-gradient-to-r from-slate-900/95 via-[#162038] to-slate-900/95 shadow-indigo-950/40 ring-1 ring-indigo-400/25 hover:border-amber-400/80 hover:shadow-indigo-500/20'
      } ${ui.isRelated ? 'border-sky-400/80 ring-2 ring-sky-400/30' : ''} ${
        ui.isMuted ? 'opacity-35 saturate-50' : ''
      } ${ui.shouldReveal ? 'learning-node--reveal' : ''} ${ui.isReady ? 'learning-node--ready' : ''}`}
      style={ui.shouldReveal ? { animationDelay: `${ui.revealDelay || 0}ms` } : undefined}
    >
      <NodeHandles />
      <div className="flex min-w-0 items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5 flex-1">
          <span className="inline-flex shrink-0 items-center gap-1 rounded-md border border-amber-400/35 bg-amber-400/15 px-1.5 py-0.5 text-[8.5px] font-black uppercase tracking-wider text-amber-300 shadow-sm shadow-amber-950/30">
            <Flag size={10} className="text-amber-400 fill-amber-400/40" />
            <span>Milestone</span>
          </span>
          <p className="min-w-0 flex-1 truncate text-[11px] font-bold tracking-tight text-white group-hover:text-amber-200 transition-colors" title={label}>
            {label}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {resourcesCount > 0 && (
            <span
              className="inline-flex shrink-0 items-center gap-0.5 text-[9px] font-medium text-sky-300"
              title={`${resourcesCount} verified resources`}
            >
              <BookOpen size={10} />
              <span>{resourcesCount}</span>
            </span>
          )}
          <span className="font-mono text-[9px] font-bold leading-none text-slate-300">{mastery.mastery}%</span>
        </div>
      </div>
      <div className="absolute inset-x-2.5 bottom-1.5 h-1 overflow-hidden rounded-full bg-slate-950/70" aria-hidden="true">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            mastery.key === 'strong' ? 'bg-emerald-400' : mastery.key === 'medium' ? 'bg-sky-400' : mastery.key === 'weak' ? 'bg-amber-400' : 'bg-indigo-500/60'
          }`}
          style={{ width: `${Math.max(mastery.mastery, mastery.key === 'not_started' ? 10 : 0)}%` }}
        />
      </div>
      <span className="sr-only">Milestone Checkpoint: {label}, {mastery.label}</span>
    </div>
  )
}

export function SectionNode({ data, width, height }) {
  const label = data.label || ''
  return (
    <div
      style={{ width: width ? `${width}px` : 'auto', height: height ? `${height}px` : 'auto' }}
      className="relative rounded-2xl border border-dashed border-slate-700/60 bg-slate-800/15 p-3 pointer-events-none"
    >
      <NodeHandles />
      {label && (
        <span className="inline-block max-w-full truncate rounded-md border border-slate-700/50 bg-slate-800/90 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider text-slate-300 shadow-sm">
          {label}
        </span>
      )}
    </div>
  )
}

export function HorizontalBarNode({ data, width, height }) {
  const w = width || 80
  const h = height || 20
  const cy = h / 2
  const arrowSize = 6
  const lineEndX = Math.max(arrowSize, w - arrowSize)
  const id = data?.id || 'h-conn'

  return (
    <div
      style={{ width: `${w}px`, height: `${h}px` }}
      className="relative flex items-center justify-center pointer-events-none"
    >
      <NodeHandles />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
        <defs>
          <linearGradient id={`h-grad-${id}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="1" />
          </linearGradient>
          <filter id={`h-glow-${id}`} x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="1" dy="0" stdDeviation="2" floodColor="#38bdf8" floodOpacity="0.5" />
          </filter>
        </defs>
        <line
          x1={0}
          y1={cy}
          x2={lineEndX}
          y2={cy}
          stroke="#38bdf8"
          strokeWidth={5}
          strokeOpacity={0.2}
          strokeLinecap="round"
        />
        <line
          x1={0}
          y1={cy}
          x2={lineEndX}
          y2={cy}
          stroke={`url(#h-grad-${id})`}
          strokeWidth={2.4}
          strokeDasharray="4 4"
          strokeLinecap="round"
        />
        <polygon
          points={`${lineEndX - 1},${cy - 4.5} ${lineEndX - 1},${cy + 4.5} ${w},${cy}`}
          fill="#818cf8"
          filter={`url(#h-glow-${id})`}
        />
      </svg>
    </div>
  )
}

export function VerticalBarNode({ data, width, height }) {
  const w = width || 21
  const h = height || 64
  const cx = w / 2
  const arrowWidth = 5
  const arrowHeight = 7
  const lineEndY = Math.max(arrowHeight, h - arrowHeight)
  const id = data?.id || 'v-conn'

  return (
    <div
      style={{ width: `${w}px`, height: `${h}px` }}
      className="relative flex items-center justify-center pointer-events-none"
    >
      <NodeHandles />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
        <defs>
          <linearGradient id={`v-grad-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="1" />
          </linearGradient>
          <filter id={`v-glow-${id}`} x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#38bdf8" floodOpacity="0.5" />
          </filter>
        </defs>
        <line
          x1={cx}
          y1={0}
          x2={cx}
          y2={lineEndY}
          stroke="#38bdf8"
          strokeWidth={5}
          strokeOpacity={0.2}
          strokeLinecap="round"
        />
        <line
          x1={cx}
          y1={0}
          x2={cx}
          y2={lineEndY}
          stroke={`url(#v-grad-${id})`}
          strokeWidth={2.4}
          strokeDasharray="4 4"
          strokeLinecap="round"
          className="learning-edge__line--active"
        />
        <polygon
          points={`${cx - arrowWidth},${lineEndY - 1} ${cx + arrowWidth},${lineEndY - 1} ${cx},${h}`}
          fill="#818cf8"
          filter={`url(#v-glow-${id})`}
        />
      </svg>
    </div>
  )
}

export function LabelNode({ data }) {
  const fontSize = data?.style?.fontSize || 15
  return (
    <div
      className="relative max-w-xs sm:max-w-md break-words [overflow-wrap:anywhere] [word-break:break-word] font-bold text-slate-200"
      style={{ fontSize: `${fontSize}px` }}
    >
      <NodeHandles />
      {data.label}
    </div>
  )
}

export function ParagraphNode({ data }) {
  const label = (data?.label || '').trim().toLowerCase()
  if (
    label.includes('you can pick any backend programming language') ||
    label.includes('continue learning with following relevant tracks') ||
    label.includes('detailed version of this roadmap') ||
    label.includes('also visit the following related roadmaps') ||
    label.includes('scrimba is offering') ||
    label.includes('if you are already a full-stack developer') ||
    label.includes('pre-requisite') ||
    label.includes('prerequisite')
  ) {
    return null
  }
  return (
    <div
      className="relative max-w-xs sm:max-w-md break-words [overflow-wrap:anywhere] [word-break:break-word] text-xs leading-relaxed text-slate-300"
      style={{ fontSize: data?.style?.fontSize }}
    >
      <NodeHandles />
      {data.label}
    </div>
  )
}

export function ButtonNode({ data }) {
  const label = (data?.label || '').trim().toLowerCase()
  if (label === 'roadmap.sh' || label.includes('visit beginner') || label.includes('visit the beginner')) {
    return null
  }
  return (
    <div className="relative max-w-full min-w-0">
      <NodeHandles />
      <a
        href={data.href || '#'}
        target="_blank"
        rel="noreferrer"
        className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-sky-400/40 bg-sky-500/10 px-3 py-1.5 text-xs font-semibold text-sky-200 transition-colors hover:bg-sky-500/20 shadow-sm"
      >
        <span className="min-w-0 truncate [overflow-wrap:anywhere]">{data.label}</span>
        <ExternalLink className="shrink-0" size={12} />
      </a>
    </div>
  )
}

export function TitleNode({ data }) {
  return (
    <div className="relative max-w-full min-w-0 rounded-xl border border-sky-400/30 bg-gradient-to-r from-sky-500/20 to-indigo-500/20 px-5 py-3 shadow-xl backdrop-blur-sm">
      <NodeHandles />
      <h1 className="min-w-0 break-words [overflow-wrap:anywhere] text-xl font-extrabold tracking-tight text-white">{data.label}</h1>
    </div>
  )
}

export function LinksGroupNode({ data }) {
  return null
}

export default TopicNode
