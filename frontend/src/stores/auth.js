import { defineStore } from 'pinia'
import api from '../api'

function decodeJwtPayload(token) {
  try {
    const base64 = token.split('.')[1]
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    role: localStorage.getItem('role') || null,
    username: localStorage.getItem('username') || null,
  }),
  actions: {
    async login(username, password) {
      try {
        const response = await api.post('/auth/login/', { username, password })
        this.token = response.data.access
        this.refreshToken = response.data.refresh

        localStorage.setItem('token', this.token)
        if (this.refreshToken) {
          localStorage.setItem('refreshToken', this.refreshToken)
        }

        const payload = decodeJwtPayload(this.token)
        this.role = payload.role || 'chatter'
        this.username = payload.username || username

        localStorage.setItem('role', this.role)
        localStorage.setItem('username', this.username)
        return true
      } catch (error) {
        console.error('Login failed', error)
        return false
      }
    },
    logout() {
      this.token = null
      this.refreshToken = null
      this.role = null
      this.username = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('role')
      localStorage.removeItem('username')
    },
  },
})
