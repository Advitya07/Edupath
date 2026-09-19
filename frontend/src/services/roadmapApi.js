import api from './api'
export const generateRoadmap = data => api.post('/roadmap/generate', data).then(r => r.data)
export const getResources = data => api.post('/roadmap/resources', data).then(r => r.data)
