<script setup>
import { ref, onMounted } from 'vue'

let ws
let messages = ref([])
let input = ref('')

onMounted(() => {
  ws = new WebSocket('ws://localhost:8000/ws')

  ws.onmessage = (event) => {
    messages.value.push(event.data)
  }

})

function sendMessage() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(input.value)
    input.value = ''
  }
}

</script>

<template>
  <div>
    <input v-model="input" placeholder="Type a message" />
    <button @click="sendMessage">Send</button>
    <h3>Received messages</h3>
    <ul>
      <li v-for="(msg, i) in messages" :key="i">{{ msg }}</li>
    </ul>
    <PvButton @click="sendMessage">Test</PvButton>
  </div>
</template>
