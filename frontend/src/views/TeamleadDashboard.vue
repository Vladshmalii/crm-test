<template>
  <div class="teamlead-dashboard">
    <div class="header glass-panel" style="border-radius: 0; border-bottom: 1px solid var(--border-glass);">
      <h2>Teamlead Monitor</h2>
      <button @click="logout" class="btn" style="background: var(--danger); box-shadow: 0 4px 15px var(--danger-glow); padding: 5px 10px; font-size: 0.8rem;">Logout</button>
    </div>
    
    <div class="content">
      <div class="stats-card glass-panel">
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

      <div class="stats-card glass-panel mt-4">
        <h3>Testing Tools</h3>
        <p class="test-desc">Use this to simulate a new message from a Fan to test real-time WebSocket updates and overdue metrics.</p>
        
        <div class="test-options">
          <label class="test-label">
            Target Chatter:
            <select v-model="emulateChatterId" class="input-glass" style="width: auto; padding: 5px 10px;">
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
          <input type="text" v-model="emulateText" placeholder="Enter simulated message..." class="input-glass" @keyup.enter="emulateFanMessage" />
          <button @click="emulateFanMessage" class="btn" :disabled="isEmulating" style="white-space: nowrap;">
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
  const wsBaseUrl = import.meta.env.VITE_WS_URL || `${wsProtocol}//localhost:8000`
  const wsUrl = `${wsBaseUrl}/ws/crm/?token=${authStore.token}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    fetchOverview()
  }
  
  ws.onmessage = () => {
    fetchOverview()
  }
  
  ws.onclose = () => {
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
  font-family: var(--font-family);
}
.header {
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.5px;
}
.content {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}
.stats-card {
  padding: 2rem;
}
.stats-card h3 {
  margin-top: 0;
  border-bottom: 1px solid var(--border-glass);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
  color: var(--text-main);
  font-weight: 600;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  text-align: left;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--border-glass);
  color: var(--text-main);
}
th {
  color: var(--text-muted);
  font-weight: 500;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
  tbody tr {
    transition: background-color 0.2s ease;
  }
  tbody tr:hover {
    background: hsla(210, 40%, 98%, 0.03);
  }
.has-overdue {
  background: hsla(348, 83%, 55%, 0.1);
  animation: bg-pulse 2s infinite alternate;
}
@keyframes bg-pulse {
  from { background: hsla(348, 83%, 55%, 0.05); }
  to { background: hsla(348, 83%, 55%, 0.15); }
}
.overdue-cell {
  font-weight: 600;
}
.has-overdue .overdue-cell {
  color: var(--danger);
  text-shadow: 0 0 8px var(--danger-glow);
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
  color: var(--text-muted);
  text-align: center;
  padding: 3rem;
  font-size: 1.125rem;
}
.mt-4 {
  margin-top: 1.5rem;
}
.test-desc {
  color: var(--text-muted);
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
  color: var(--text-muted);
  font-size: 0.875rem;
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
.success-msg {
  color: var(--success);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
.error-msg {
  color: var(--danger);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
