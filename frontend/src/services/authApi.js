import api from './api'
export const register = data => api.post('/auth/register', data).then(r => r.data)
export const login = data => api.post('/auth/login', data).then(r => r.data)
export const saveProfile = (id, data) => api.post(`/auth/profile/${id}`, data).then(r => r.data)
export const parseResume = (file, context = {}) => { const form = new FormData(); form.append('file', file); if (context.user_id) form.append('user_id', context.user_id); if (context.career_target) form.append('career_target', context.career_target); return api.post('/resume/parse', form).then(r => r.data) }
