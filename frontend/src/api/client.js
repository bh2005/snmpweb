import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.authHeader) {
    config.headers.Authorization = auth.authHeader
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore().logout()
    }
    return Promise.reject(error)
  }
)

export function apiErrorMessage(error) {
  return error.response?.data?.detail || error.message || 'Unbekannter Fehler'
}

export default client
