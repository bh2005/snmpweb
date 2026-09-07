<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { useTargetStore } from '../stores/target.js'
import { useHistoryStore } from '../stores/history.js'
import client, { apiErrorMessage } from '../api/client.js'

const target = useTargetStore()
const history = useHistoryStore()
const rows = ref([])
const lastKind = ref('')
const status = ref('')
const error = ref(false)
const loading = ref(false)
const viewMode = ref('flat')

const polling = ref(false)
const pollIntervalSec = ref(5)
let pollTimer = null

async function run(kind) {
  const oid = target.oid.trim()
  if (!oid) {
    status.value = 'Bitte eine OID angeben.'
    error.value = true
    return
  }
  loading.value = true
  error.value = false
  status.value = kind === 'get' ? 'GET läuft…' : 'WALK läuft…'
  try {
    const payload =
      kind === 'get'
        ? { ...target.asRequestTarget, oids: [oid] }
        : { ...target.asRequestTarget, oid }
    const res = await client.post(`/snmp/${kind}`, payload)
    rows.value = res.data
    lastKind.value = kind
    status.value = `${res.data.length} Ergebnis(se).`
    history.recordHost(target.host)
    history.recordOid(oid)
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  } finally {
    loading.value = false
  }
}

function togglePolling() {
  if (polling.value) {
    clearInterval(pollTimer)
    pollTimer = null
    polling.value = false
    return
  }
  polling.value = true
  run('get')
  pollTimer = setInterval(() => run('get'), pollIntervalSec.value * 1000)
}

onUnmounted(() => clearInterval(pollTimer))

function csvEscape(value) {
  const str = String(value ?? '')
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str
}

function exportCsv() {
  const header = ['oid', 'name', 'type', 'value']
  const lines = [header.join(',')]
  for (const row of rows.value) {
    lines.push(header.map((key) => csvEscape(row[key])).join(','))
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  a.href = url
  a.download = `snmpweb-${lastKind.value || 'query'}-${target.host || 'target'}-${stamp}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function naturalCompare(a, b) {
  const pa = a.split('.').map(Number)
  const pb = b.split('.').map(Number)
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const diff = (pa[i] ?? -1) - (pb[i] ?? -1)
    if (diff !== 0) return diff
  }
  return 0
}

// Erkennt SNMP-Tabellenspalten am aufgeloesten Namen (z.B. "IF-MIB::ifDescr.1")
// und pivotiert sie zu einer Index-x-Spalte-Ansicht, statt der flachen Liste.
const pivot = computed(() => {
  if (lastKind.value !== 'walk' || !rows.value.length) return null
  const parsed = rows.value.map((r) => {
    const m = r.name.match(/^(.+?)\.(\d+(?:\.\d+)*)$/)
    return m ? { column: m[1], index: m[2], value: r.value } : null
  })
  if (parsed.some((p) => !p)) return null

  const columns = [...new Set(parsed.map((p) => p.column))]
  if (columns.length < 2) return null

  const indices = [...new Set(parsed.map((p) => p.index))].sort(naturalCompare)
  const cell = new Map()
  for (const p of parsed) cell.set(`${p.index}|${p.column}`, p.value)
  return { columns, indices, cell }
})
</script>

<template>
  <section class="card">
    <div class="card-header">SNMP Query</div>
    <div class="card-body flex flex-col gap-4">
      <div>
        <label class="label" for="oid">OID</label>
        <input id="oid" v-model="target.oid" list="oid-history" class="input" />
        <datalist id="oid-history">
          <option v-for="o in history.oids" :key="o" :value="o" />
        </datalist>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <button class="btn-primary" :disabled="loading || polling" @click="run('get')">GET</button>
        <button class="btn-secondary" :disabled="loading || polling" @click="run('walk')">WALK</button>

        <label class="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-300 ml-2">
          <input type="checkbox" :checked="polling" @change="togglePolling" />
          Live
        </label>
        <select v-model.number="pollIntervalSec" class="input w-auto" :disabled="polling">
          <option :value="2">2s</option>
          <option :value="5">5s</option>
          <option :value="10">10s</option>
          <option :value="30">30s</option>
        </select>
      </div>

      <p v-if="status" class="text-sm" :class="error ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'">
        {{ status }}
      </p>

      <div v-if="rows.length" class="flex flex-col gap-3">
        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" @click="exportCsv">CSV exportieren</button>
          <button v-if="pivot" class="btn-secondary" @click="viewMode = viewMode === 'flat' ? 'table' : 'flat'">
            {{ viewMode === 'flat' ? 'Tabellenansicht' : 'Flache Liste' }}
          </button>
        </div>

        <div v-if="viewMode === 'table' && pivot" class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>Index</th>
                <th v-for="col in pivot.columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="idx in pivot.indices" :key="idx">
                <td>{{ idx }}</td>
                <td v-for="col in pivot.columns" :key="col">{{ pivot.cell.get(`${idx}|${col}`) ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>OID</th>
                <th>Name</th>
                <th>Typ</th>
                <th>Wert</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.oid">
                <td>{{ row.oid }}</td>
                <td>{{ row.name }}</td>
                <td>{{ row.type }}</td>
                <td>{{ row.value }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>
