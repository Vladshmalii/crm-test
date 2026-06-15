<template>
  <div class="login-container">
    <div class="login-card glass-panel">
      <div class="glow-orb"></div>
      <h2>Login to CRM</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" type="text" required class="input-glass" placeholder="Enter your username" />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input v-model="password" type="password" required class="input-glass" placeholder="Enter your password" />
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <button type="submit" class="btn" :disabled="loading" style="width: 100%; margin-top: 1rem;">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const success = await authStore.login(username.value, password.value)
    if (success) {
      if (authStore.role === 'teamlead') {
        router.push('/teamlead')
      } else {
        router.push('/')
      }
    } else {
      error.value = 'Invalid credentials'
    }
  } catch (err) {
    error.value = 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

.login-card {
  padding: 2.5rem;
  width: 100%;
  max-width: 400px;
  position: relative;
  z-index: 10;
}

.glow-orb {
  position: absolute;
  top: -50px;
  right: -50px;
  width: 150px;
  height: 150px;
  background: var(--accent);
  border-radius: 50%;
  filter: blur(80px);
  z-index: -1;
  opacity: 0.5;
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.5px;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-bottom: 1rem;
  text-align: center;
  font-size: 0.875rem;
}
</style>
