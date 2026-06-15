<template>
  <div class="teamlead-dashboard">
    <div class="header">
      <h2>Teamlead Monitor</h2>
      <button @click="logout" class="logout-btn">Logout</button>
    </div>
    
    <div class="content">
      <div class="stats-card">
        <h3>Online Chatters</h3>
        <table v-if="chatters.length > 0">
          <thead>
            <tr>
              <th>Chatter</th>
              <th>Active Dialogs</th>
              <th>Waiting Dialogs</th>
              <th>Silence Time (Max)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="chatter in chatters" :key="chatter.chatter_id" :class="{ 'has-overdue': chatter.overdue_dialogs > 0 }">
              <td>{{ chatter.chatter_name }}</td>
              <td>{{ chatter.active_dialogs }}</td>
              <td>{{ chatter.waiting_dialogs }}</td>
              <td class="overdue-cell">
                <span v-if="chatter.max_silence_start">{{ formatSilence(chatter.max_silence_start, now) }}</span>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="no-data">No chatters online currently.</p>
      </div>

      <div class="stats-card mt-4">
        <h3>Testing Tools</h3>
        <p class="test-desc">Use this to simulate a new message from a Fan to test real-time WebSocket updates and overdue metrics.</p>
        
        <div class="test-options">
          <label class="test-label">
            Target Chatter:
            <select v-model="emulateChatterId" class="emulate-select">
              <option :value="null">Any / Auto</option>
              <option v-for="c in chatters" :key="c.chatter_id" :value="c.chatter_id">
                {{ c.chatter_name }}
              </option>
            </select>
          </label>
          <label class="test-label checkbox-label">
            <input type="checkbox" v-model="emulateForceNew" />
            Create "New Chat" (Fresh Dialog)
          </label>
        </div>

        <div class="test-actions">
          <input type="text" v-model="emulateText" placeholder="Enter simulated message..." class="emulate-input" @keyup.enter="emulateFanMessage" />
          <button @click="emulateFanMessage" class="emulate-btn" :disabled="isEmulating">
            {{ isEmulating ? 'Sending...' : 'Emulate Fan Message' }}
          </button>
        </div>
        <p v-if="emulateSuccess" class="success-msg">Message sent successfully!</p>
        <p v-if="emulateError" class="error-msg">{{ emulateError }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const authStore = useAuthStore()

const chatters = ref([])
// We could fetch this from backend if we want, for UI display:
const overdueThreshold = ref(1) // Default or env matched

const emulateText = ref('')
const emulateChatterId = ref(null)
const emulateForceNew = ref(false)
const isEmulating = ref(false)
const emulateSuccess = ref(false)
const emulateError = ref('')

const now = ref(Date.now())

let ws = null
let reconnectTimer = null
let pollTimer = null
let clockTimer = null

const formatSilence = (isoStr, currentNow) => {
  if (!isoStr) return '-'
  const start = new Date(isoStr).getTime()
  const diff = Math.max(0, Math.floor((currentNow - start) / 1000))
  const m = Math.floor(diff / 60).toString().padStart(2, '0')
  const s = (diff % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const fetchOverview = async () => {
  try {
    const res = await api.get('/teamlead/overview/')
    chatters.value = res.data
  } catch (error) {
    console.error('Failed to fetch overview', error)
  }
}

const emulateFanMessage = async () => {
  if (isEmulating.value) return
  isEmulating.value = true
  emulateSuccess.value = false
  emulateError.value = ''
  
  try {
    await api.post('/emulate/incoming/', {
      text: emulateText.value || 'Hello, this is a simulated message.',
      chatter_id: emulateChatterId.value,
      force_new: emulateForceNew.value
    })
    emulateSuccess.value = true
    emulateText.value = ''
    setTimeout(() => { emulateSuccess.value = false }, 3000)
    fetchOverview() // immediately update active dialogs count
  } catch (err) {
    console.error('Emulation failed', err)
    emulateError.value = 'Failed to emulate message. Ensure chatters exist.'
  } finally {
    isEmulating.value = false
  }
}

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//localhost:8000/ws/crm/?token=${authStore.token}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('Teamlead WebSocket connected')
    if (reconnectTimer) clearTimeout(reconnectTimer)
    fetchOverview()
  }
  
  ws.onmessage = (event) => {
    // Whenever a chat message happens, or presence update, we can refresh the overview
    fetchOverview()
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected. Reconnecting in 3s...')
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }
}

const logout = () => {
  if (ws) ws.close()
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  fetchOverview()
  connectWebSocket()
  
  clockTimer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
  
  pollTimer = setInterval(() => {
    fetchOverview()
  }, 10000)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
.teamlead-dashboard {
  min-height: 100vh;
  background: var(--bg-color);
  font-family: var(--font-main);
}
.header {
  background: var(--panel-bg);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--panel-border);
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.logout-btn {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.logout-btn:hover {
  background: var(--danger-color);
  color: white;
}
.content {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}
.stats-card {
  background: var(--panel-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--panel-border);
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}
.stats-card h3 {
  margin-top: 0;
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
  font-weight: 600;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  text-align: left;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--panel-border);
  color: var(--text-primary);
}
th {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
  tbody tr {
    transition: background-color 0.2s ease;
  }
  tbody tr:hover {
    background: rgba(255, 255, 255, 0.03);
  }
.has-overdue {
  background: rgba(239, 68, 68, 0.1);
  animation: bg-pulse 2s infinite alternate;
}
@keyframes bg-pulse {
  from { background: rgba(239, 68, 68, 0.05); }
  to { background: rgba(239, 68, 68, 0.15); }
}
.overdue-cell {
  font-weight: 600;
}
.has-overdue .overdue-cell {
  color: var(--danger-color);
  text-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}
.warning-icon {
  margin-right: 0.5rem;
  display: inline-block;
  animation: shake 0.5s infinite;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}
.no-data {
  color: var(--text-secondary);
  text-align: center;
  padding: 3rem;
  font-size: 1.125rem;
}
.mt-4 {
  margin-top: 1.5rem;
}
.test-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}
.test-options {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  align-items: center;
}
.test-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}
.emulate-select {
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--panel-border);
  background: rgba(15, 23, 42, 0.5);
  color: white;
  font-family: inherit;
  font-size: 0.875rem;
}
.emulate-select:focus {
  outline: none;
  border-color: var(--accent-color);
}
.checkbox-label {
  cursor: pointer;
}
.checkbox-label input {
  cursor: pointer;
}
.test-actions {
  display: flex;
  gap: 1rem;
}
.emulate-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--panel-border);
  background: rgba(15, 23, 42, 0.5);
  color: white;
  font-size: 1rem;
  font-family: inherit;
}
.emulate-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
.emulate-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}
.emulate-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.emulate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.success-msg {
  color: #10b981;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
.error-msg {
  color: var(--danger-color);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
