import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Maximize2 } from 'lucide-react'
import {
  TopicNode,
  SubtopicNode,
  CheckpointNode,
  SectionNode,
  HorizontalBarNode,
  VerticalBarNode,
  LabelNode,
  ParagraphNode,
  ButtonNode,
  TitleNode,
  LinksGroupNode,
} from './CustomSkillNode'
import LearningPathEdge from './LearningPathEdge'
import { getMasteryVisual, getExcludedRoadmapNodeIds, findMatchingScore } from './roadmapVisuals'
import { useRoadmapStore } from '../../store/roadmapStore'

const nodeTypes = {
  topic: TopicNode,
  subtopic: SubtopicNode,
  checkpoint: CheckpointNode,
  section: SectionNode,
  horizontal: HorizontalBarNode,
  vertical: VerticalBarNode,
  label: LabelNode,
  paragraph: ParagraphNode,
  button: ButtonNode,
  resourceButton: ButtonNode,
  title: TitleNode,
  linksgroup: LinksGroupNode,
  todo: SubtopicNode,
  skill: TopicNode,
}

const edgeTypes = { learningPath: LearningPathEdge }
const focusableNodeTypes = new Set(['topic', 'subtopic', 'todo', 'skill', 'checkpoint'])

function SkillGraphContent({ roadmap, onNodeClick }) {
  const { fitView } = useReactFlow()
  const [activeNodeId, setActiveNodeId] = useState(null)
  const [hoveredNodeId, setHoveredNodeId] = useState(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    setActiveNodeId(null)
    setHoveredNodeId(null)
    setIsReady(false)
    const frame = requestAnimationFrame(() => setIsReady(true))
    return () => cancelAnimationFrame(frame)
  }, [roadmap?.id, roadmap?.slug, roadmap?.last_synced_at])

  const focusedNodeId = hoveredNodeId || activeNodeId
  const allRawNodes = roadmap?.nodes || []
  const allRawEdges = roadmap?.edges || []

  // Cleanly exclude promotional links, prerequisite boxes/links, related roadmaps, and dangling arrows
  const excludedNodeIds = useMemo(() => getExcludedRoadmapNodeIds(allRawNodes), [allRawNodes])

  const rawNodes = useMemo(() => allRawNodes.filter(n => !excludedNodeIds.has(n.id)), [allRawNodes, excludedNodeIds])
  const rawEdges = useMemo(
    () => allRawEdges.filter(e => !excludedNodeIds.has(e.source) && !excludedNodeIds.has(e.target)),
    [allRawEdges, excludedNodeIds]
  )

  const storeScores = useRoadmapStore(s => s.scores) || {}
  const allScores = useMemo(() => ({
    ...(roadmap?.scores || {}),
    ...storeScores,
  }), [roadmap?.scores, storeScores])

  const nodeDataMap = useMemo(() => {
    const map = new Map()
    for (const n of rawNodes) {
      const label = (n.data?.label || n.data?.topic || n.label || n.topic || '').trim()
      let mastery = n.data?.mastery ?? n.mastery ?? 0
      let status = n.data?.status ?? n.status ?? 'not_started'
      if (allScores && Object.keys(allScores).length > 0) {
        const foundScore = findMatchingScore(label, allScores)
        if (foundScore !== undefined) {
          mastery = Math.round(Number(foundScore))
          status = mastery >= 80 ? 'completed' : mastery >= 55 ? 'in_progress' : mastery > 0 ? 'weak_gap' : 'not_started'
        }
      }
      map.set(n.id, { ...(n.data || n), id: n.id, mastery, status })
    }
    return map
  }, [rawNodes, allScores])

  const relatedNodeIds = useMemo(() => {
    if (!focusedNodeId) return new Set()
    return new Set(
      rawEdges
        .filter(edge => edge.source === focusedNodeId || edge.target === focusedNodeId)
        .flatMap(edge => [edge.source, edge.target])
    )
  }, [focusedNodeId, rawEdges])

  const nodes = useMemo(() => {
    return rawNodes.map((n, index) => {
      const isCheckpoint = (n.data?.label || n.data?.topic || n.label || '').trim().toLowerCase().startsWith('checkpoint')
      const nType = isCheckpoint ? 'checkpoint' : (nodeTypes[n.type] ? n.type : 'subtopic')
      const isFocusable = focusableNodeTypes.has(nType)
      const isFocused = n.id === focusedNodeId
      const isActive = n.id === activeNodeId
      const isRelated = relatedNodeIds.has(n.id) && n.id !== focusedNodeId
      const isMuted = Boolean(focusedNodeId) && isFocusable && n.id !== focusedNodeId && !relatedNodeIds.has(n.id)

      const resolvedData = nodeDataMap.get(n.id) || (n.data || n)

      return {
        id: n.id,
        type: nType,
        position: n.position || { x: 0, y: 0 },
        data: {
          ...resolvedData,
          id: n.id,
          __ui: {
            isFocused,
            isActive,
            isRelated,
            isMuted,
            isReady,
            shouldReveal: n.type === 'section' || index < 72,
            revealDelay: n.type === 'section' ? 80 : 140 + (index % 10) * 26,
          },
        },
        width: n.width,
        height: n.height,
        zIndex: isActive ? 60 : isFocused ? 50 : isRelated ? 25 : (isCheckpoint ? 15 : (n.type === 'section' ? -1 : 1)),
        style: n.style,
      }
    })
  }, [activeNodeId, focusedNodeId, isReady, nodeDataMap, rawNodes, relatedNodeIds])

  const edges = useMemo(() => {
    return rawEdges.map(e => {
      const isSourceFocused = e.source === focusedNodeId
      const isTargetFocused = e.target === focusedNodeId
      const isRelated = Boolean(focusedNodeId) && (isSourceFocused || isTargetFocused)
      const isActive = Boolean(activeNodeId) && (e.source === activeNodeId || e.target === activeNodeId)
      const isMuted = Boolean(focusedNodeId) && !isRelated

      const sourceData = nodeDataMap.get(e.source)
      const targetData = nodeDataMap.get(e.target)
      const sourceMastery = sourceData ? getMasteryVisual(sourceData) : null
      const targetMastery = targetData ? getMasteryVisual(targetData) : null
      const isCompletedPath = sourceMastery?.key === 'strong' && (targetMastery?.key === 'strong' || targetMastery?.key === 'medium')

      let markerColor = '#6483a8'
      if (isActive || isRelated) {
        markerColor = '#38bdf8'
      } else if (isCompletedPath) {
        markerColor = '#34d399'
      } else if (isMuted) {
        markerColor = '#415a77'
      }

      return {
        ...e,
        type: 'learningPath',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: markerColor,
          width: 12,
          height: 12,
        },
        data: {
          ...e.data,
          edgeStyle: e.data?.edgeStyle,
          isRelated,
          isActive,
          isMuted,
          isCompletedPath,
          isVisible: isReady,
        },
        style: {
          ...e.style,
        },
      }
    })
  }, [activeNodeId, focusedNodeId, isReady, nodeDataMap, rawEdges])

  const handleNodeClick = (_, node) => {
    if (focusableNodeTypes.has(node.type)) {
      setActiveNodeId(node.id)
      onNodeClick?.(node.data)
    }
  }

  const handleFitView = () => {
    fitView?.({ duration: 0, padding: 0.16 })
  }

  return (
    <div
      className={`learning-graph relative h-[min(70vh,760px)] min-h-[440px] w-full overflow-hidden rounded-2xl border border-line bg-slate-900/60 shadow-xl shadow-slate-950/25 sm:h-[620px] lg:h-[720px] ${
        isReady ? 'learning-graph--ready' : ''
      }`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center justify-between gap-3 border-b border-white/[0.08] bg-slate-900/70 px-3 py-2 text-[11px] font-medium text-slate-300 backdrop-blur-md sm:px-4">
        <span className="truncate">Select any skill block to explore verified resources</span>
        <div className="pointer-events-auto flex items-center gap-2.5 shrink-0">
          <span className="hidden text-slate-400 sm:inline text-[10px]">Scroll to zoom · drag to pan</span>
          <button
            type="button"
            onClick={handleFitView}
            className="inline-flex items-center gap-1 rounded-md border border-line bg-slate-800/80 px-2 py-0.5 text-[10px] font-semibold text-slate-300 hover:border-sky-400/60 hover:text-white transition-colors"
            title="Fit roadmap to screen"
          >
            <Maximize2 size={11} />
            <span>Fit view</span>
          </button>
        </div>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={(_, node) => focusableNodeTypes.has(node.type) && setHoveredNodeId(node.id)}
        onNodeMouseLeave={() => setHoveredNodeId(null)}
        onPaneClick={() => setActiveNodeId(null)}
        fitView
        fitViewOptions={{ padding: 0.16, duration: 0 }}
        minZoom={0.15}
        maxZoom={2}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        defaultEdgeOptions={{ type: 'learningPath' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} color="#385170" gap={24} size={1.25} />
        <Controls
          className="!border-line !bg-slate-900/90 !fill-slate-300 !shadow-lg [&>button]:!border-line [&>button]:!bg-slate-900 [&>button:hover]:!bg-slate-800"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={n => {
            if (n.type === 'section') return '#1b2a41'
            if (focusableNodeTypes.has(n.type)) return getMasteryVisual(n.data).accent
            return 'transparent'
          }}
          className="!hidden !border-line !bg-slate-900/90 sm:!block"
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  )
}

export default function SkillGraph({ roadmap, onNodeClick }) {
  return (
    <ReactFlowProvider>
      <SkillGraphContent roadmap={roadmap} onNodeClick={onNodeClick} />
    </ReactFlowProvider>
  )
}
