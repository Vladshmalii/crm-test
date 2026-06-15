import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      // Don't retry on the refresh endpoint itself to prevent infinite loop
      if (originalRequest.url === '/auth/refresh/') {
        return Promise.reject(error)
      }
      
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          const res = await axios.post('http://localhost:8000/api/auth/refresh/', { refresh: refreshToken })
          const newAccessToken = res.data.access
          localStorage.setItem('token', newAccessToken)
          
          // Update the failed request and retry it
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh token failed, fall through to logout
        console.error('Token refresh failed:', refreshError)
      }
      
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('role')
      localStorage.removeItem('username')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
