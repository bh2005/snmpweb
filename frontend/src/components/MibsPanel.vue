<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import client, { apiErrorMessage } from '../api/client.js'

const auth = useAuthStore()
const mibs = ref([])
const status = ref('')
const error = ref(false)
const fileInput = ref(null)
const uploading = ref(false)

async function loadMibs() {
  try {
    const res = await client.get('/mibs')
    mibs.value = res.data
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  }
}

async function upload() {
  const file = fileInput.value?.files?.[0]
  if (!file) {
    status.value = 'Bitte eine MIB-Datei auswählen.'
    error.value = true
    return
  }
  uploading.value = true
  error.value = false
  status.value = 'MIB wird hochgeladen und kompiliert…'
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await client.post('/mibs', formData)
    status.value = `MIB ${res.data.name} kompiliert.`
    fileInput.value.value = ''
    await loadMibs()
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  } finally {
    uploading.value = false
  }
}

async function remove(name) {
  status.value = `Lösche MIB ${name}…`
  error.value = false
  try {
    await client.delete(`/mibs/${encodeURIComponent(name)}`)
    status.value = `MIB ${name} gelöscht.`
    await loadMibs()
  } catch (e) {
    error.value = true
    status.value = apiErrorMessage(e)
  }
}

onMounted(loadMibs)
</script>

<template>
  <section class="card">
    <div class="card-header">MIBs</div>
    <div class="card-body flex flex-col gap-4">
      <div v-if="auth.isAdmin" class="flex flex-wrap items-end gap-3">
        <div class="flex-1 min-w-[220px]">
          <label class="label" for="mib-file">MIB-Datei (.mib)</label>
          <input id="mib-file" ref="fileInput" type="file" accept=".mib,.txt,.my" class="input" />
        </div>
        <button class="btn-primary" :disabled="uploading" @click="upload">Hochladen &amp; kompilieren</button>
      </div>

      <p v-if="status" class="text-sm" :class="error ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'">
        {{ status }}
      </p>

      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Kompiliert</th>
              <th v-if="auth.isAdmin">Aktion</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mib in mibs" :key="mib.name">
              <td>{{ mib.name }}</td>
              <td>{{ mib.compiled ? 'ja' : 'nein' }}</td>
              <td v-if="auth.isAdmin">
                <button class="btn-danger" @click="remove(mib.name)">Löschen</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
