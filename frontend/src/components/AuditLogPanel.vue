<script setup>
import { onMounted, ref } from 'vue'
import client, { apiErrorMessage } from '../api/client.js'

const entries = ref([])
const status = ref('')
const error = ref(false)
const loading = ref(false)

async function refresh() {
  loading.value = true
  error.value = false
  try {
    const res = await client.get('/audit', { params: { limit: 200 } })
    entries.value = res.data
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="card">
    <div class="card-header">Audit-Log</div>
    <div class="card-body flex flex-col gap-4">
      <div>
        <button class="btn-secondary" :disabled="loading" @click="refresh">Aktualisieren</button>
      </div>

      <p v-if="status" class="text-sm text-red-600 dark:text-red-400">{{ status }}</p>

      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Zeit</th>
              <th>User</th>
              <th>Aktion</th>
              <th>Host</th>
              <th>Ziel</th>
              <th>OK</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in entries" :key="`${entry.ts}-${entry.username}-${entry.action}`">
              <td>{{ entry.ts }}</td>
              <td>{{ entry.username }}</td>
              <td>{{ entry.action }}</td>
              <td>{{ entry.host }}</td>
              <td>{{ entry.target }}</td>
              <td>{{ entry.success ? 'ja' : 'nein' }}</td>
              <td>{{ entry.detail }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
