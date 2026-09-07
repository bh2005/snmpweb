<script setup>
import { provide, ref } from 'vue'
import { useTargetStore } from '../stores/target.js'
import client, { apiErrorMessage } from '../api/client.js'
import MibTreeNode from './MibTreeNode.vue'
import QueryPanel from './QueryPanel.vue'

const target = useTargetStore()
const modules = ref(null)
const selected = ref(null)
const status = ref('')
const error = ref(false)
const loading = ref(false)
const filterQuery = ref('')

function selectMibNode(node) {
  if (node.kind !== 'module') {
    target.oid = node.oid
  }
  selected.value = node
}
provide('selectMibNode', selectMibNode)

async function loadTree() {
  loading.value = true
  error.value = false
  status.value = 'Baum wird geladen…'
  try {
    const res = await client.get('/mibs/tree')
    modules.value = res.data
    status.value = `${res.data.length} MIB-Modul(e) geladen.`
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
    <div class="card-header">MIB-Browser</div>
    <div class="card-body flex flex-col gap-4">
      <div>
        <button class="btn-secondary" :disabled="loading" @click="loadTree">Baum laden</button>
      </div>

      <p v-if="status" class="text-sm" :class="error ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'">
        {{ status }}
      </p>

      <div v-if="modules">
        <input v-model="filterQuery" class="input" placeholder="Baum durchsuchen (Name oder OID)…" />
      </div>

      <div class="flex flex-col md:flex-row gap-4 items-start">
        <div class="flex-1 min-w-0 max-h-[420px] overflow-y-auto text-sm">
          <p v-if="!modules" class="text-slate-400 dark:text-slate-500 text-sm">Noch nicht geladen.</p>
          <ul v-else class="list-none">
            <MibTreeNode v-for="mod in modules" :key="mod.name" :node="mod" :filter="filterQuery" />
          </ul>
        </div>

        <div class="flex-1 min-w-0 self-stretch rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4 text-sm">
          <template v-if="selected">
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Name:</strong> {{ selected.name }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">OID:</strong> {{ selected.oid || '–' }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Modul:</strong> {{ selected.module || '–' }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Art:</strong> {{ selected.kind }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Syntax:</strong> {{ selected.syntax || '–' }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Zugriff:</strong> {{ selected.access || '–' }}</p>
            <p><strong class="text-slate-500 dark:text-slate-400 font-semibold">Status:</strong> {{ selected.status || '–' }}</p>
            <p v-if="selected.description" class="text-slate-500 dark:text-slate-400 mt-2">{{ selected.description }}</p>
          </template>
          <p v-else class="text-slate-400 dark:text-slate-500">Objekt im Baum anklicken, um Details zu sehen.</p>
        </div>
      </div>
    </div>
  </section>

  <QueryPanel class="mt-6" />
</template>
