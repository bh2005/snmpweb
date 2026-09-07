import { defineStore } from 'pinia'
import axios from 'axios'

const STORAGE_KEY = 'snmpweb_auth'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null')
    return {
      username: saved?.username ?? null,
      role: saved?.role ?? null,
      authHeader: saved?.authHeader ?? null,
    }
  },

  getters: {
    isLoggedIn: (state) => !!state.authHeader,
    isAdmin: (state) => state.role === 'admin',
  },

  actions: {
    async login(username, password) {
      const authHeader = `Basic ${btoa(`${username}:${password}`)}`
      const res = await axios.get('/api/whoami', {
        headers: { Authorization: authHeader },
      })
      this.username = res.data.username
      this.role = res.data.role
      this.authHeader = authHeader
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ username: this.username, role: this.role, authHeader: this.authHeader })
      )
    },

    logout() {
      this.username = null
      this.role = null
      this.authHeader = null
      sessionStorage.removeItem(STORAGE_KEY)
    },
  },
})
