import api from './api'
export const askMentor = data => api.post('/chat', data).then(r => r.data)
