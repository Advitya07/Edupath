import { create } from 'zustand'

const initial = JSON.parse(localStorage.getItem('edupath-roadmap') || 'null')
export const useRoadmapStore = create(set => ({
  roadmap: initial,
  scores: initial?.scores || {},
  setRoadmap: roadmap => { localStorage.setItem('edupath-roadmap', JSON.stringify(roadmap)); set({ roadmap }) },
  setScores: scores => set({ scores }),
  updateNode: (id, patch) => set(state => {
    if (!state.roadmap) return state
    const roadmap = { ...state.roadmap, nodes: state.roadmap.nodes.map(n => n.id === id ? { ...n, ...patch } : n) }
    localStorage.setItem('edupath-roadmap', JSON.stringify(roadmap)); return { roadmap }
  })
}))
