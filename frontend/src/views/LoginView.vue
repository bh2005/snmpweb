<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { apiErrorMessage } from '../api/client.js'

const auth = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
  } catch (e) {
    error.value = apiErrorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-6">
    <div class="card w-full max-w-sm p-8">
      <h1 class="text-lg font-bold text-ks-700 dark:text-ks-300">snmpweb</h1>
      <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">
        SNMP GET / WALK Tester &amp; Port-Check
      </p>

      <form class="flex flex-col gap-3" @submit.prevent="onSubmit">
        <div>
          <label class="label" for="login-username">Benutzername</label>
          <input id="login-username" v-model="username" class="input" autocomplete="username" required />
        </div>
        <div>
          <label class="label" for="login-password">Passwort</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            class="input"
            autocomplete="current-password"
            required
          />
        </div>

        <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>

        <button type="submit" class="btn-primary justify-center mt-2" :disabled="loading">
          {{ loading ? 'Anmelden…' : 'Anmelden' }}
        </button>
      </form>
    </div>
  </div>
</template>
