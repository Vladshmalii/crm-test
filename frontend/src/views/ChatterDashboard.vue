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
              <strong>{{ dialog.persona.name }} & {{ dialog.fan.name }}</strong>
              <span class="time">{{ formatTime(dialog.last_message_at) }}</span>
            </div>
            <div v-if="dialog.last_message" class="last-message-preview">
              <span class="sender-name">{{ dialog.last_message.sender_type === 'fan' ? dialog.fan.name : dialog.persona.name }}: </span>
              <span class="msg-text">{{ dialog.last_message.text }}</span>
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
          <h3>Chatting as {{ selectedDialog.persona.name }} with {{ selectedDialog.fan.name }}</h3>
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
            <div 
              class="message-bubble glass-panel"
              :class="{ 'is-ppv-bubble': msg.is_ppv }"
            >
              <template v-if="msg.is_ppv">
                <div class="ppv-header">
                  <div class="ppv-icon-wrap">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                  </div>
                  <span class="ppv-title">Locked Content</span>
                  <span class="ppv-price">${{ msg.price }}</span>
                </div>
                <div class="ppv-content">
                  {{ msg.text }}
                </div>
              </template>
              <template v-else>
                {{ msg.text }}
              </template>
            </div>
            <div class="message-meta">
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
        
        <div class="chat-input glass-panel" style="border-radius: 0; border-top: 1px solid var(--border-glass);">
          <textarea v-model="newMessageText" @keyup.enter.exact="sendMessage" placeholder="Type a message..." class="input-glass" style="height: 60px; resize: none;"></textarea>
          <div class="actions">
            <div class="ppv-toggle-container">
              <label class="ppv-switch-label" :class="{ 'is-active': isPpv }">
                <input type="checkbox" v-model="isPpv" class="hidden-checkbox" />
                <div class="ppv-switch-track">
                  <div class="ppv-switch-knob">
                    <svg v-if="isPpv" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>
                  </div>
                </div>
                <span class="ppv-switch-text">Paid Message</span>
              </label>
              
              <transition name="fade-slide">
                <div v-if="isPpv" class="price-input-wrapper">
                  <span class="currency-symbol">$</span>
                  <input type="number" v-model.number="ppvPrice" placeholder="0.00" step="0.01" class="price-input" />
                </div>
              </transition>
            </div>
            <button @click="sendMessage" :disabled="!newMessageText.trim()" class="btn send-btn">
              <span>Send</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="no-dialog">
        <p>Select a dialog to start chatting</p>
      </div>
    </div>


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
const drafts = ref({})
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
    // Save draft for previous dialog
    if (selectedDialog.value) {
      drafts.value[selectedDialog.value.id] = newMessageText.value
    }
    
    selectedDialog.value = dialog
    messages.value = [] // clear before load
    nextCursor.value = null
    
    // Restore draft for new dialog
    newMessageText.value = drafts.value[dialog.id] || ''

    
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
  if (selectedDialog.value) {
    drafts.value[selectedDialog.value.id] = ''
  }
  isPpv.value = false
  ppvPrice.value = null
}

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBaseUrl = import.meta.env.VITE_WS_URL || `${wsProtocol}//localhost:8000`
  const wsUrl = `${wsBaseUrl}/ws/crm/?token=${authStore.token}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    fetchDialogs()
    if (selectedDialog.value) {
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
        dialog.last_message = {
          text: msg.text,
          sender_type: msg.sender_type
        }
        
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
.last-message-preview {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}
.last-message-preview .sender-name {
  font-weight: 600;
  color: var(--text-main);
  opacity: 0.8;
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
.is-ppv-bubble {
  background: linear-gradient(135deg, hsla(330, 80%, 15%, 0.8), hsla(280, 80%, 15%, 0.8)) !important;
  border: 1px solid hsla(330, 80%, 50%, 0.4) !important;
  box-shadow: 0 4px 20px hsla(330, 80%, 50%, 0.15), inset 0 0 0 1px hsla(330, 80%, 60%, 0.2) !important;
  padding: 1rem 1.25rem;
}
.ppv-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid hsla(330, 80%, 60%, 0.2);
}
.ppv-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, hsl(330, 80%, 60%), hsl(280, 80%, 60%));
  border-radius: 50%;
  color: white;
  box-shadow: 0 0 10px hsla(330, 80%, 60%, 0.5);
}
.ppv-icon-wrap svg {
  width: 12px;
  height: 12px;
}
.ppv-title {
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: linear-gradient(to right, hsl(330, 80%, 75%), hsl(280, 80%, 75%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.ppv-price {
  margin-left: auto;
  font-weight: 800;
  font-size: 0.9rem;
  color: hsl(330, 80%, 85%);
  background: hsla(330, 80%, 60%, 0.2);
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  border: 1px solid hsla(330, 80%, 60%, 0.3);
}
.ppv-content {
  color: hsl(330, 20%, 95%);
  font-size: 0.95rem;
  line-height: 1.6;
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
.ppv-toggle-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.hidden-checkbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.ppv-switch-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;
}
.ppv-switch-track {
  width: 44px;
  height: 24px;
  background: hsla(222, 47%, 30%, 0.5);
  border: 1px solid var(--border-glass);
  border-radius: 20px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}
.ppv-switch-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: var(--text-muted);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bg-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}
.ppv-switch-label.is-active .ppv-switch-track {
  background: linear-gradient(135deg, hsl(330, 80%, 60%), hsl(280, 80%, 60%));
  border-color: transparent;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1), 0 0 10px hsla(330, 80%, 60%, 0.4);
}
.ppv-switch-label.is-active .ppv-switch-knob {
  transform: translateX(20px);
  background: white;
  color: hsl(330, 80%, 50%);
}
.ppv-switch-text {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-muted);
  transition: color 0.3s;
}
.ppv-switch-label.is-active .ppv-switch-text {
  color: var(--text-main);
  text-shadow: 0 0 10px hsla(330, 80%, 75%, 0.5);
}

.price-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.currency-symbol {
  position: absolute;
  left: 12px;
  color: hsl(330, 80%, 75%);
  font-weight: 700;
  font-size: 0.95rem;
  z-index: 1;
}
.price-input {
  width: 110px;
  padding: 8px 12px 8px 26px;
  background: hsla(330, 80%, 15%, 0.3);
  border: 1px solid hsla(330, 80%, 50%, 0.4);
  border-radius: 8px;
  color: var(--text-main);
  font-weight: 600;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s;
  box-shadow: 0 2px 8px hsla(330, 80%, 50%, 0.1);
}
.price-input:focus {
  border-color: hsl(330, 80%, 60%);
  box-shadow: 0 0 0 2px hsla(330, 80%, 60%, 0.2), 0 2px 8px hsla(330, 80%, 50%, 0.1);
  background: hsla(330, 80%, 15%, 0.5);
}
.price-input::placeholder {
  color: hsla(330, 80%, 75%, 0.5);
}

/* Chrome, Safari, Edge, Opera */
.price-input::-webkit-outer-spin-button,
.price-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
/* Firefox */
.price-input[type=number] {
  -moz-appearance: textfield;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 8px 16px;
}
.actions button:disabled {
  background: hsla(222, 47%, 30%, 0.3);
  color: var(--text-muted);
  box-shadow: none;
  cursor: not-allowed;
  border: 1px solid transparent;
  opacity: 0.5;
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
