import { BookOpen, ExternalLink, GraduationCap, Sparkles, Video, FileText, Globe, X } from 'lucide-react'
import { useEffect } from 'react'
import { getMasteryVisual } from './roadmapVisuals'

const typeIcons = {
  Book: BookOpen,
  Article: FileText,
  Video: Video,
  Course: GraduationCap,
  Documentation: Globe,
  'Open Source': Globe,
  'Roadmap Guide': Sparkles,
}

export default function ResourceDrawer({ resourceData, topic, close, reevaluate }) {
  useEffect(() => {
    if (!topic) return undefined

    const handleKeyDown = event => {
      if (event.key === 'Escape') close()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [close, topic])

  if (!topic) return null

  const freeResources = resourceData?.resources || topic.resources || []
  const paidResources = resourceData?.paid_resources || topic.paid_resources || []
  const description = resourceData?.description || topic.description || ''
  const topicTitle = topic.label || topic.topic || 'Skill Topic'
  const sourceUrl = resourceData?.source_url || 'https://roadmap.sh'
  const mastery = getMasteryVisual(topic)

  return (
    <div className="resource-drawer fixed inset-0 z-50 flex justify-end bg-slate-950/65 backdrop-blur-sm" role="presentation">
      <section className="resource-drawer__panel flex h-full w-full max-w-full sm:max-w-lg flex-col overflow-y-auto overscroll-contain border-l border-line/80 bg-slate-900/95 p-4 shadow-2xl shadow-slate-950/70 sm:p-6 backdrop-blur-xl" role="dialog" aria-modal="true" aria-labelledby="resource-drawer-title">
        {/* Header */}
        <div className="flex min-w-0 items-start justify-between gap-3 border-b border-line pb-5">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-semibold uppercase tracking-wider text-sky-300">
              <span>Focused skill block</span>
              <span className="text-slate-600">•</span>
              <span className={mastery.icon}>{mastery.label}</span>
              <span className="text-slate-400">{mastery.mastery}% mastery</span>
            </div>
            <h2 id="resource-drawer-title" className="mt-1 break-words [overflow-wrap:anywhere] [word-break:break-word] text-2xl font-bold leading-tight text-white">{topicTitle}</h2>
            <div className="mt-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-slate-400">
              <span>Roadmap source:</span>
              <a
                href={sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-sky-400 hover:underline"
              >
                roadmap.sh
              </a>
            </div>
          </div>
          <button
            className="shrink-0 rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
            onClick={close}
            aria-label="Close topic resources"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mt-5 min-w-0 flex-1 space-y-6">
          {/* Topic Description */}
          {description && (
            <div className="rounded-xl border border-line bg-slate-900/50 p-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">About this topic</h3>
              <div className="mt-2 break-words [overflow-wrap:anywhere] [word-break:break-word] whitespace-pre-line text-sm leading-relaxed text-slate-300">
                {description.replace(/^#\s+[^\n]+\n+/, '')}
              </div>
            </div>
          )}

          {/* FREE RESOURCES */}
          <div>
            <div className="flex min-w-0 items-center justify-between gap-3">
              <h3 className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Free Resources ({freeResources.length})
              </h3>
              <span className="shrink-0 text-[11px] text-slate-400">Roadmap.sh Verified</span>
            </div>

            {freeResources.length === 0 ? (
              <p className="mt-3 rounded-xl border border-line/60 bg-slate-900/30 p-4 text-xs text-slate-400">
                No external resources currently linked for this specific topic on roadmap.sh.
              </p>
            ) : (
              <div className="mt-3 space-y-2.5">
                {freeResources.map((item, idx) => {
                  const Icon = typeIcons[item.type] || FileText
                  return (
                    <a
                      key={idx}
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="group block min-w-0 rounded-xl border border-line bg-slate-800/50 p-3.5 transition-[border-color,background-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-sky-400/80 hover:bg-slate-800 hover:shadow-lg hover:shadow-sky-500/10"
                    >
                      <div className="flex min-w-0 items-center justify-between gap-3">
                        <span className="inline-flex min-w-0 items-center gap-1.5 rounded-md bg-sky-500/10 px-2 py-0.5 text-[11px] font-bold text-sky-300">
                          <Icon size={12} />
                          {item.type}
                        </span>
                        <ExternalLink size={14} className="shrink-0 text-slate-500 group-hover:text-sky-300" />
                      </div>
                      <p className="mt-2 break-words [overflow-wrap:anywhere] [word-break:break-word] font-medium leading-snug text-slate-200 group-hover:text-white">{item.title}</p>
                      {item.description && (
                        <p className="mt-1 break-words [overflow-wrap:anywhere] [word-break:break-word] text-xs leading-relaxed text-slate-400">{item.description}</p>
                      )}
                    </a>
                  )
                })}
              </div>
            )}
          </div>

          {/* PAID / PREMIUM RESOURCES */}
          {paidResources.length > 0 && (
            <div>
              <div className="flex min-w-0 items-center justify-between gap-3">
                <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  Premium / Partner Courses ({paidResources.length})
                </h3>
              </div>
              <div className="mt-3 space-y-2.5">
                {paidResources.map((item, idx) => (
                  <a
                    key={idx}
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="group block min-w-0 rounded-xl border border-line bg-slate-800/35 p-3.5 transition-[border-color,background-color,transform] hover:-translate-y-0.5 hover:border-amber-400/60 hover:bg-slate-800/60"
                  >
                    <div className="flex min-w-0 items-center justify-between gap-3">
                      <span className="min-w-0 break-words rounded-md bg-amber-500/10 px-2 py-0.5 text-[11px] font-bold text-amber-300">
                        {item.partner || 'Premium'} • {item.type}
                      </span>
                      <ExternalLink size={14} className="shrink-0 text-slate-500 group-hover:text-amber-300" />
                    </div>
                    <p className="mt-2 break-words [overflow-wrap:anywhere] [word-break:break-word] font-medium leading-snug text-slate-200">{item.title}</p>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Practice Task */}
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
            <p className="text-xs font-bold uppercase tracking-wider text-indigo-300">Practice Task</p>
            <p className="mt-2 text-sm text-slate-300 break-words [overflow-wrap:anywhere] [word-break:break-word]">
              {resourceData?.practice_task ||
                `Build a practical project or exercise demonstrating ${topicTitle} and write down key architectural trade-offs.`}
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 border-t border-line pt-4">
          <button
            onClick={() => reevaluate(topicTitle)}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Sparkles size={16} /> Take a focused diagnostic quiz
          </button>
        </div>
      </section>
    </div>
  )
}
