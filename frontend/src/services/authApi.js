import api from './api'
export const register = data => api.post('/auth/register', data).then(r => r.data)
export const login = data => api.post('/auth/login', data).then(r => r.data)
export const saveProfile = (id, data) => api.post(`/auth/profile/${id}`, data).then(r => r.data)
export const parseResume = file => { const form = new FormData(); form.append('file', file); return api.post('/resume/parse', form).then(r => r.data) }
