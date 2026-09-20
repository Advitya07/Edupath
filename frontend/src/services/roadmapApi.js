import api from './api'

export const getRoadmaps = () => api.get('/roadmaps').then(r => r.data)
export const getRoadmapBySlug = (slug, userId) =>
  api.get(`/roadmaps/${slug}`, { params: userId ? { user_id: userId } : {} }).then(r => r.data)
export const getUserRoadmap = userId => api.get(`/roadmap/user/${userId}`).then(r => r.data)
export const generateRoadmap = data => api.post('/roadmap/generate', data).then(r => r.data)
export const getResources = data => api.post('/roadmap/resources', data).then(r => r.data)
