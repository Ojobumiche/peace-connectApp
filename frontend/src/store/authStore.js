import { create } from 'zustand'

// Zustand v5 — persist is loaded manually for compatibility
function loadState() {
  try {
    const raw = localStorage.getItem('peacecda-auth')
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

const saved = loadState()

const useAuthStore = create((set) => ({
  user: saved.user ?? null,
  isAuthenticated: saved.isAuthenticated ?? false,

  login: (userData, access, refresh) => {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    const next = { user: userData, isAuthenticated: true }
    localStorage.setItem('peacecda-auth', JSON.stringify(next))
    set(next)
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('peacecda-auth')
    set({ user: null, isAuthenticated: false })
  },
}))

export default useAuthStore
