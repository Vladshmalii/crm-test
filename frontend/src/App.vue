<template>
  <router-view></router-view>
</template>

<style>
:root {
  --bg-color: #0f172a;
  --panel-bg: rgba(30, 41, 59, 0.7);
  --panel-border: rgba(255, 255, 255, 0.1);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --accent-color: #3b82f6;
  --accent-hover: #2563eb;
  --danger-color: #ef4444;
  --danger-hover: #dc2626;
  --ppv-color: #ec4899;
  --message-bg: rgba(51, 65, 85, 0.8);
  --chatter-msg-bg: rgba(59, 130, 246, 0.85);
  
  --font-main: 'Inter', system-ui, -apple-system, sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-main);
  background-color: var(--bg-color);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  /* subtle animated background gradient */
  background: radial-gradient(circle at top right, #1e1b4b, #0f172a 50%, #020617);
  background-attachment: fixed;
}

/* Glassmorphism utilities */
.glass {
  background: var(--panel-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--panel-border);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
