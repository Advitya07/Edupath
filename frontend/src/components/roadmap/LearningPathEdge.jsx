import { BaseEdge, getSmoothStepPath } from '@xyflow/react'

export default function LearningPathEdge({
  id,
  sourceX,
  sourceY,
  sourcePosition,
  targetX,
  targetY,
  targetPosition,
  markerEnd,
  style,
  data,
}) {
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
    offset: 20,
  })

  const isRelated = Boolean(data?.isRelated)
  const isActive = Boolean(data?.isActive)
  const isMuted = Boolean(data?.isMuted)
  const isCompletedPath = Boolean(data?.isCompletedPath)
  const isVisible = data?.isVisible !== false
  const isDashed = data?.edgeStyle === 'dashed'

  let stroke = '#557396'
  let strokeWidth = 1.45
  let opacity = isVisible ? 0.75 : 0

  if (isActive) {
    stroke = '#38bdf8'
    strokeWidth = 2.6
    opacity = 1
  } else if (isRelated) {
    stroke = '#5bc8ff'
    strokeWidth = 2.2
    opacity = 1
  } else if (isCompletedPath) {
    stroke = '#34d399'
    strokeWidth = 1.6
    opacity = isMuted ? 0.25 : 0.65
  } else if (isMuted) {
    opacity = 0.2
    stroke = '#415a77'
  }

  const sharedStyle = {
    opacity,
    transition: 'opacity 260ms ease, stroke 180ms ease, stroke-width 180ms ease',
  }

  return (
    <>
      {(isRelated || isActive) && (
        <BaseEdge
          id={`${id}-halo`}
          path={edgePath}
          className="learning-edge__halo pointer-events-none"
          style={{
            ...sharedStyle,
            stroke: isActive ? '#38bdf8' : '#0ea5e9',
            strokeWidth: isActive ? 9 : 6,
            opacity: isActive ? 0.35 : 0.22,
          }}
        />
      )}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        className={`learning-edge__line${isActive ? ' learning-edge__line--active' : ''}`}
        style={{
          ...style,
          ...sharedStyle,
          stroke,
          strokeWidth,
          strokeDasharray: isActive ? '6 8' : isDashed ? '2 7' : undefined,
        }}
      />
    </>
  )
}
