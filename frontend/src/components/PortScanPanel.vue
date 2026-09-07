<script setup>
import { computed, ref } from 'vue'
import { useTargetStore } from '../stores/target.js'
import { useHistoryStore } from '../stores/history.js'
import client, { apiErrorMessage } from '../api/client.js'

const target = useTargetStore()
const history = useHistoryStore()
const ports = ref('22,23,80,161,162,443,502,8080')
const scanType = ref('tcp')
const serviceDetection = ref(false)
const osDetection = ref(false)
const timing = ref('T4')

const rows = ref([])
const osGuesses = ref([])
const status = ref('')
const error = ref(false)
const loading = ref(false)

const needsRawSockets = computed(() => scanType.value !== 'tcp' || osDetection.value)

async function scan() {
  const host = target.host.trim()
  if (!host) {
    status.value = 'Bitte einen Host angeben.'
    error.value = true
    return
  }
  loading.value = true
  error.value = false
  status.value = 'Scan läuft…'
  try {
    const res = await client.post('/portscan', {
      host,
      ports: ports.value.trim(),
      scan_type: scanType.value,
      service_detection: serviceDetection.value,
      os_detection: osDetection.value,
      timing: timing.value,
    })
    rows.value = res.data.ports
    osGuesses.value = res.data.os_guesses
    status.value = `${res.data.ports.length} Port(s) gefunden.`
    history.recordHost(host)
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="card">
    <div class="card-header">Port-Scan</div>
    <div class="card-body flex flex-col gap-4">
      <div>
        <label class="label" for="ports">Ports</label>
        <input id="ports" v-model="ports" class="input" />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <label class="label" for="scan-type">Scan-Typ</label>
          <select id="scan-type" v-model="scanType" class="input">
            <option value="tcp">TCP-Connect</option>
            <option value="udp">UDP</option>
            <option value="tcp+udp">TCP + UDP</option>
          </select>
        </div>
        <div>
          <label class="label" for="timing">Timing</label>
          <select id="timing" v-model="timing" class="input">
            <option value="T2">T2 (polite)</option>
            <option value="T3">T3 (normal)</option>
            <option value="T4">T4 (aggressiv)</option>
            <option value="T5">T5 (insane)</option>
          </select>
        </div>
        <label class="flex items-end gap-1.5 text-sm text-slate-600 dark:text-slate-300 pb-2">
          <input v-model="serviceDetection" type="checkbox" />
          Service-Version (-sV)
        </label>
        <label class="flex items-end gap-1.5 text-sm text-slate-600 dark:text-slate-300 pb-2">
          <input v-model="osDetection" type="checkbox" />
          OS-Erkennung (-O)
        </label>
      </div>

      <p v-if="needsRawSockets" class="text-xs text-slate-400 dark:text-slate-500">
        UDP- und OS-Scans brauchen Raw Sockets (NET_RAW/NET_ADMIN) im Container — standardmäßig
        aus (siehe <code>cap_add</code> in <code>docker-compose.yml</code>), sonst liefert nmap hier einen Fehler.
      </p>

      <div>
        <button class="btn-primary" :disabled="loading" @click="scan">Scan</button>
      </div>

      <p v-if="status" class="text-sm" :class="error ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'">
        {{ status }}
      </p>

      <div v-if="osGuesses.length" class="text-sm">
        <p class="label mb-1">OS-Vermutung</p>
        <p v-for="guess in osGuesses" :key="guess.name" class="text-slate-600 dark:text-slate-300">
          {{ guess.name }} ({{ guess.accuracy }}% sicher)
        </p>
      </div>

      <div v-if="rows.length" class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Port</th>
              <th>Protokoll</th>
              <th>Status</th>
              <th>Service</th>
              <th>Produkt/Version</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="`${row.port}-${row.protocol}`">
              <td>{{ row.port }}</td>
              <td>{{ row.protocol }}</td>
              <td>{{ row.state }}</td>
              <td>{{ row.service }}</td>
              <td>{{ [row.product, row.version].filter(Boolean).join(' ') || '–' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
