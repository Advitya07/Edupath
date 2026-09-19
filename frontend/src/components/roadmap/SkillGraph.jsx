import { Background, Controls, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import CustomSkillNode from './CustomSkillNode'
const nodeTypes = { skill: CustomSkillNode }
export default function SkillGraph({ roadmap, onNodeClick }) { const nodes=(roadmap?.nodes || []).map(n => ({ id:n.id, type:'skill', position:n.position, data:n })); return <div className="h-[570px] overflow-hidden rounded-2xl border border-line bg-slate-950/35"><ReactFlow nodes={nodes} edges={roadmap?.edges || []} nodeTypes={nodeTypes} onNodeClick={(_,node) => onNodeClick(node.data)} fitView minZoom={0.5}><Background color="#23354e" gap={22}/><Controls/></ReactFlow></div> }
