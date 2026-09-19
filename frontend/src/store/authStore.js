import { create } from 'zustand'

const saved = JSON.parse(localStorage.getItem('edupath-user') || 'null')
export const useAuthStore = create(set => ({
  user: saved,
  login: ({ token, user }) => { localStorage.setItem('edupath-token', token); localStorage.setItem('edupath-user', JSON.stringify(user)); set({ user }) },
  updateUser: user => { localStorage.setItem('edupath-user', JSON.stringify(user)); set({ user }) },
  logout: () => { localStorage.removeItem('edupath-token'); localStorage.removeItem('edupath-user'); set({ user: null }) }
}))
