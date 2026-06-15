import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    role: localStorage.getItem('role') || null,
    username: localStorage.getItem('username') || null
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
        
        // Decode JWT payload (simple approach)
        const payload = JSON.parse(atob(this.token.split('.')[1]))
        this.role = payload.role || 'chatter' // fallback
        
        // In a real app we might have a /me endpoint, but for now we just hardcode based on username 
        // or extend token payload. Let's assume username is available
        this.username = username
        if (username === 'teamlead') this.role = 'teamlead'
        else this.role = 'chatter'

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
    }
  }
})
