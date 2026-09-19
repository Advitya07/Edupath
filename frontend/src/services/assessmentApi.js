import api from './api'
export const generateQuiz = data => api.post('/assessment/generate', data).then(r => r.data)
export const submitQuiz = data => api.post('/assessment/submit', data).then(r => r.data)
