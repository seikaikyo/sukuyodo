<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'verified'): void
}>()

const pin = ref('')
const error = ref(false)
const appPin = import.meta.env.VITE_APP_PIN || ''

function verify() {
  if (pin.value === appPin) {
    localStorage.setItem('sukuyodo_pin', pin.value)
    emit('verified')
  } else {
    error.value = true
    setTimeout(() => { error.value = false }, 1500)
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') verify()
}
</script>

<template>
  <div class="pin-gate">
    <div class="pin-card" :class="{ shake: error }">
      <div class="pin-icon">&#x2601;</div>
      <h2 class="pin-title">宿曜道</h2>
      <p class="pin-hint">請輸入存取碼</p>
      <input
        v-model="pin"
        type="password"
        inputmode="numeric"
        maxlength="6"
        class="pin-input"
        :class="{ 'pin-error': error }"
        placeholder="----"
        autofocus
        @keydown="handleKeydown"
      />
      <button class="pin-btn" @click="verify">進入</button>
      <p v-if="error" class="error-msg">存取碼錯誤</p>
    </div>
  </div>
</template>

<style scoped>
.pin-gate {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--cosmos-void, #F8F6F0);
}

.pin-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4, 16px);
  padding: var(--space-8, 32px) var(--space-12, 48px);
  background: var(--bg-surface, #fff);
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-lg, 0 10px 15px rgba(0,0,0,0.1));
  border: 1px solid var(--border-subtle, rgba(0,0,0,0.06));
}

.pin-card.shake {
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}

.pin-icon {
  font-size: 40px;
  line-height: 1;
  color: var(--stellar-gold, #B8860B);
}

.pin-title {
  font-family: var(--font-display, serif);
  font-size: var(--font-xl, 24px);
  color: var(--text-primary, #2C2520);
  margin: 0;
}

.pin-hint {
  font-size: var(--font-sm, 14px);
  color: var(--text-muted, #7A7068);
  margin: 0;
}

.pin-input {
  width: 160px;
  padding: var(--space-3, 12px) var(--space-4, 16px);
  font-size: var(--font-lg, 18px);
  text-align: center;
  letter-spacing: 8px;
  border: 2px solid var(--border-default, rgba(0,0,0,0.1));
  border-radius: var(--radius-md, 8px);
  background: var(--parchment, #FAF8F5);
  color: var(--text-primary, #2C2520);
  outline: none;
  transition: border-color var(--transition-fast, 150ms);
}

.pin-input:focus {
  border-color: var(--stellar-gold, #B8860B);
}

.pin-input.pin-error {
  border-color: var(--warning, #C53030);
}

.pin-btn {
  width: 160px;
  padding: var(--space-3, 12px);
  font-size: var(--font-base, 16px);
  font-family: var(--font-body, sans-serif);
  color: var(--text-on-accent, #fff);
  background: var(--astral-deep, #3D5A80);
  border: none;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: background var(--transition-fast, 150ms);
}

.pin-btn:hover {
  background: var(--astral-medium, #5A7FA5);
}

.error-msg {
  font-size: var(--font-sm, 14px);
  color: var(--warning, #C53030);
  margin: 0;
}
</style>
