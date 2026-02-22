<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import PinGate from './components/PinGate.vue'

const appPin = import.meta.env.VITE_APP_PIN || ''
const needPin = appPin !== ''
const verified = ref(!needPin || localStorage.getItem('sukuyodo_pin') === appPin)

function onVerified() {
  verified.value = true
}
</script>

<template>
  <div class="app">
    <PinGate v-if="!verified" @verified="onVerified" />
    <template v-else>
      <div class="stardust"></div>
      <RouterView />
    </template>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>
