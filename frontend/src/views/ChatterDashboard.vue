<template>
  <div class="chatter-dashboard">
    <div class="sidebar glass-panel" style="border-radius: 0; border-right: 1px solid var(--border-glass);">
      <div class="header">
        <h2>Dialogs</h2>
        <button @click="logout" class="btn" style="background: var(--danger); box-shadow: 0 4px 15px var(--danger-glow); padding: 5px 10px; font-size: 0.8rem;">Logout</button>
      </div>
      <div class="dialog-list">
        <div 
          v-for="dialog in dialogs" 
          :key="dialog.id" 
          class="dialog-item"
          :class="{ active: selectedDialog?.id === dialog.id }"
          @click="selectDialog(dialog)"
        >
          <div class="dialog-content">
            <div class="dialog-info">
              <strong>{{ dialog.model.name }} & {{ dialog.fan.name }}</strong>
              <span class="time">{{ formatTime(dialog.last_message_at) }}</span>
            </div>
          </div>
          <div class="dialog-actions">
            <button @click.stop="promptDeleteDialog(dialog)" class="delete-btn" title="Delete Chat">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
            <div v-if="dialog.unread_count > 0" class="badge">
              {{ dialog.unread_count }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-area">
      <div v-if="selectedDialog" class="chat-container">
        <div class="chat-header glass-panel" style="border-radius: 0; border-bottom: 1px solid var(--border-glass);">
          <h3>Chatting as {{ selectedDialog.model.name }} with {{ selectedDialog.fan.name }}</h3>
        </div>
        
        <div class="messages" ref="messagesContainer" @scroll="handleScroll">
          <div v-if="loadingMore" class="loading-more">
            <div class="spinner"></div>
            <span>Loading older messages...</span>
          </div>
          <div 
            v-for="msg in messages" 
            :key="msg.id" 
            class="message"
            :class="msg.sender_type"
          >
            <div class="message-bubble glass-panel">
              <div v-if="msg.is_ppv" class="ppv-badge">PPV: ${{ msg.price }}</div>
              {{ msg.text }}
            </div>
            <div class="message-meta">
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
        
        <div class="chat-input glass-panel" style="border-radius: 0; border-top: 1px solid var(--border-glass);">
          <textarea v-model="newMessageText" @keyup.enter.exact="sendMessage" placeholder="Type a message..." class="input-glass" style="height: 60px; resize: none;"></textarea>
          <div class="actions">
            <div class="ppv-toggle">
              <label><input type="checkbox" v-model="isPpv" /> PPV</label>
              <input v-if="isPpv" type="number" v-model.number="ppvPrice" placeholder="Price $" step="0.01" class="input-glass" style="width: 100px; padding: 5px 10px;" />
            </div>
            <button @click="sendMessage" :disabled="!newMessageText.trim()" class="btn">Send</button>
          </div>
        </div>
      </div>
      <div v-else class="no-dialog">
        <p>Select a dialog to start chatting</p>
      </div>
    </div>

    <!-- Custom Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay">
      <div class="modal-content glass-panel">
        <h3>Delete Chat</h3>
        <p>Are you sure you want to delete this chat with {{ dialogToDelete?.fan.name }}? This action cannot be undone.</p>
        <div class="modal-actions">
          <button class="btn" style="background: transparent; border: 1px solid var(--text-muted); color: var(--text-main); box-shadow: none;" @click="cancelDelete">Cancel</button>
          <button class="btn" style="background: var(--danger); box-shadow: 0 4px 15px var(--danger-glow);" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const authStore = useAuthStore()

const dialogs = ref([])
const selectedDialog = ref(null)
const messages = ref([])
const newMessageText = ref('')
const isPpv = ref(false)
const ppvPrice = ref(null)

const messagesContainer = ref(null)
const loadingMore = ref(false)
const nextCursor = ref(null)

const showDeleteModal = ref(false)
const dialogToDelete = ref(null)

let ws = null
let reconnectTimer = null

const fetchDialogs = async () => {
  try {
    const res = await api.get('/dialogs/')
    dialogs.value = res.data.results || (Array.isArray(res.data) ? res.data : [])
    if (dialogs.value.length > 0 && !selectedDialog.value) {
      selectDialog(dialogs.value[0])
    }
  } catch (error) {
    console.error('Failed to fetch dialogs', error)
  }
}

const fetchMessages = async (dialogId, cursor = null) => {
  try {
    const url = cursor ? `/dialogs/${dialogId}/messages/?cursor=${cursor}` : `/dialogs/${dialogId}/messages/`
    const res = await api.get(url)
    
    const fetchedMessages = res.data.results.reverse()
    
    if (cursor) {
      messages.value = [...fetchedMessages, ...messages.value]
    } else {
      messages.value = fetchedMessages
    }
    nextCursor.value = res.data.next ? new URL(res.data.next).searchParams.get('cursor') : null
    
    if (!cursor) {
      scrollToBottom()
    }
  } catch (error) {
    console.error('Failed to fetch messages', error)
  }
}

  const selectDialog = async (dialog) => {
    selectedDialog.value = dialog
    messages.value = [] // clear before load
    nextCursor.value = null

    
    // clear unread locally immediately
    if (dialog.unread_count > 0) {
      dialog.unread_count = 0
      api.post(`/dialogs/${dialog.id}/read/`).catch(console.error)
    }
    
    await fetchMessages(dialog.id)
  }

  const promptDeleteDialog = (dialog) => {
    dialogToDelete.value = dialog
    showDeleteModal.value = true
  }

  const cancelDelete = () => {
    showDeleteModal.value = false
    dialogToDelete.value = null
  }

  const confirmDelete = async () => {
    if (!dialogToDelete.value) return
    const id = dialogToDelete.value.id
    
    try {
      await api.delete(`/dialogs/${id}/`)
      dialogs.value = dialogs.value.filter(d => d.id !== id)
      if (selectedDialog.value && selectedDialog.value.id === id) {
        selectedDialog.value = null
        messages.value = []
      }
    } catch (error) {
      console.error('Failed to delete dialog', error)
      alert('Failed to delete chat.')
    } finally {
      showDeleteModal.value = false
      dialogToDelete.value = null
    }
  }

const handleScroll = async () => {
  if (!messagesContainer.value || !nextCursor.value || loadingMore.value) return
  
  if (messagesContainer.value.scrollTop === 0) {
    loadingMore.value = true
    const oldHeight = messagesContainer.value.scrollHeight
    
    await fetchMessages(selectedDialog.value.id, nextCursor.value)
    
    await nextTick()
    // Maintain scroll position
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight - oldHeight
    loadingMore.value = false
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = () => {
  if (!newMessageText.value.trim() || !ws || ws.readyState !== WebSocket.OPEN) return
  
  const payload = {
    action: 'send_message',
    dialog_id: selectedDialog.value.id,
    text: newMessageText.value.trim(),
    is_ppv: isPpv.value,
    price: isPpv.value ? ppvPrice.value : null
  }
  
  ws.send(JSON.stringify(payload))
  
  newMessageText.value = ''
  isPpv.value = false
  ppvPrice.value = null
}

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBaseUrl = import.meta.env.VITE_WS_URL || `${wsProtocol}//localhost:8000`
  const wsUrl = `${wsBaseUrl}/ws/crm/?token=${authStore.token}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket connected')
    if (reconnectTimer) clearTimeout(reconnectTimer)
    
    // On reconnect, fetch dialogs to get updated unread counts
    fetchDialogs()
    if (selectedDialog.value) {
       // Ideally we'd fetch only missed messages, but re-fetching current page is simpler for now
       // Or we can rely on REST call to get latest
       // For reliability:
       fetchMessages(selectedDialog.value.id)
    }
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'chat_message') {
      const msg = data.message
      
      // Update dialog list (move to top, update unread count)
      const dialogIdx = dialogs.value.findIndex(d => d.id === data.dialog_id)
      if (dialogIdx !== -1) {
        const dialog = dialogs.value[dialogIdx]
        dialog.last_message_at = msg.created_at
        
        if (selectedDialog.value && selectedDialog.value.id === data.dialog_id) {
           if (msg.sender_type === 'fan') {
               api.post(`/dialogs/${dialog.id}/read/`)
               dialog.unread_count = 0
           }
           
           // Deduplicate messages
           const exists = messages.value.find(m => m.id === msg.id)
           if (!exists) {
             messages.value.push(msg)
             nextTick(scrollToBottom)
           }
        } else {
           if (data.unread_count !== undefined) {
               dialog.unread_count = data.unread_count
           } else if (msg.sender_type === 'fan') {
               dialog.unread_count++
           }
        }
        
        // Move to top
        const [d] = dialogs.value.splice(dialogIdx, 1)
        dialogs.value.unshift(d)
      } else {
        // Dialog not in the list (brand new), refresh the list
        fetchDialogs()
      }
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected. Reconnecting in 3s...')
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const logout = () => {
  if (ws) ws.close()
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  fetchDialogs()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
})
</script>

<style scoped>
.chatter-dashboard {
  display: flex;
  height: 100vh;
  background: transparent;
}
.sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  z-index: 10;
}
.header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.5px;
}
.dialog-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}
.dialog-item {
  padding: 1rem;
  margin-bottom: 0.5rem;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}
.dialog-item:hover {
  background: hsla(210, 40%, 98%, 0.05);
  transform: scale(1.02);
}
.dialog-item.active {
  background: var(--accent-glow);
  border-color: var(--accent);
}
.dialog-content {
  flex: 1;
  min-width: 0;
}
.dialog-info {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.dialog-info strong {
  font-weight: 500;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}
.time {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.dialog-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
  min-width: 24px;
}
.delete-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  opacity: 0;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dialog-item:hover .delete-btn {
  opacity: 1;
}
.delete-btn:hover {
  color: var(--danger);
}
.badge {
  background: var(--danger);
  color: white;
  border-radius: 12px;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  box-shadow: 0 0 10px var(--danger-glow);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 var(--danger-glow); }
  70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}
.no-dialog {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--text-muted);
  font-size: 1.125rem;
}
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.chat-header {
  padding: 1.5rem;
  z-index: 5;
}
.chat-header h3 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--text-main);
}
.messages {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  color: var(--accent);
  font-size: 0.875rem;
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--accent-glow);
  border-radius: 50%;
  border-top-color: var(--accent);
  animation: spin 1s ease-in-out infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.message {
  max-width: 75%;
  animation: slideIn 0.3s ease-out forwards;
  opacity: 0;
  transform: translateY(10px);
}
@keyframes slideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.message.fan {
  align-self: flex-start;
}
.message.chatter {
  align-self: flex-end;
}
.message-bubble {
  padding: 0.875rem 1.25rem;
  color: var(--text-main);
  line-height: 1.5;
  background: hsla(222, 47%, 16%, 0.6);
  border: 1px solid var(--border-glass);
}
.message.fan .message-bubble {
  border-bottom-left-radius: 4px;
}
.message.chatter .message-bubble {
  background: var(--accent-glow);
  border-color: var(--accent);
  border-bottom-right-radius: 4px;
}
.message-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.375rem;
  margin-left: 0.5rem;
  margin-right: 0.5rem;
}
.message.chatter .message-meta {
  text-align: right;
}
.ppv-badge {
  background: hsla(330, 80%, 60%, 0.2);
  color: hsl(330, 80%, 75%);
  border: 1px solid hsla(330, 80%, 60%, 0.5);
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  display: inline-block;
  font-weight: 600;
  box-shadow: 0 0 8px hsla(330, 80%, 60%, 0.2);
}
.chat-input {
  padding: 1.5rem;
}
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}
.ppv-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-muted);
}
.actions button:disabled {
  background: var(--bg-glass);
  color: var(--text-muted);
  box-shadow: none;
  cursor: not-allowed;
  border: 1px solid var(--border-glass);
}

/* Custom Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  text-align: center;
}
.modal-content h3 {
  margin-top: 0;
  color: var(--text-main);
  margin-bottom: 1rem;
}
.modal-content p {
  color: var(--text-muted);
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
  line-height: 1.4;
}
.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
