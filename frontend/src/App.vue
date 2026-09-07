<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from './stores/auth.js'
import LoginView from './views/LoginView.vue'
import TargetPanel from './components/TargetPanel.vue'
import QueryPanel from './components/QueryPanel.vue'
import PortScanPanel from './components/PortScanPanel.vue'
import MibsPanel from './components/MibsPanel.vue'
import MibBrowserPanel from './components/MibBrowserPanel.vue'
import AuditLogPanel from './components/AuditLogPanel.vue'
import ManualPanel from './components/ManualPanel.vue'
import HelpPanel from './components/HelpPanel.vue'

const auth = useAuthStore()

const navItems = computed(() => [
  { key: 'query', label: 'SNMP Query' },
  { key: 'portscan', label: 'Port-Scan' },
  { key: 'mibs', label: 'MIBs' },
  { key: 'mibbrowser', label: 'MIB-Browser' },
  ...(auth.isAdmin ? [{ key: 'audit', label: 'Audit-Log' }] : []),
  { key: 'manual', label: 'Handbuch' },
])

const active = ref('query')
const helpOpen = ref(false)

const sectionTitles = {
  query: 'SNMP Query',
  portscan: 'Port-Scan',
  mibs: 'MIBs',
  mibbrowser: 'MIB-Browser',
  audit: 'Audit-Log',
  manual: 'Handbuch',
}

function openManual() {
  helpOpen.value = false
  active.value = 'manual'
}
</script>

<template>
  <LoginView v-if="!auth.isLoggedIn" />

  <div v-else class="min-h-screen flex">
    <aside class="w-72 flex-shrink-0 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col h-screen sticky top-0">
      <div class="px-4 py-4 border-b border-slate-100 dark:border-slate-700 flex items-start justify-between">
        <div>
          <h1 class="text-base font-bold text-ks-700 dark:text-ks-300">snmpweb</h1>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Angemeldet als {{ auth.username }} ({{ auth.role }})
          </p>
        </div>
        <button
          class="w-6 h-6 rounded-full bg-ks-50 dark:bg-ks-900 text-ks-700 dark:text-ks-200 text-xs font-bold flex items-center justify-center flex-shrink-0 hover:bg-ks-100 dark:hover:bg-ks-800"
          title="Hilfe zu diesem Bereich"
          @click="helpOpen = true"
        >
          ?
        </button>
      </div>

      <div class="px-4 py-4 border-b border-slate-100 dark:border-slate-700 overflow-y-auto">
        <TargetPanel />
      </div>

      <nav class="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
        <button
          v-for="item in navItems"
          :key="item.key"
          class="nav-link"
          :class="{ 'nav-link-active': active === item.key }"
          @click="active = item.key"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="p-3 border-t border-slate-100 dark:border-slate-700">
        <button class="btn-secondary w-full justify-center" @click="auth.logout()">Abmelden</button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto p-6">
      <QueryPanel v-if="active === 'query'" />
      <PortScanPanel v-else-if="active === 'portscan'" />
      <MibsPanel v-else-if="active === 'mibs'" />
      <MibBrowserPanel v-else-if="active === 'mibbrowser'" />
      <AuditLogPanel v-else-if="active === 'audit' && auth.isAdmin" />
      <ManualPanel v-else-if="active === 'manual'" />
    </main>

    <HelpPanel
      :open="helpOpen"
      :section="active"
      :section-title="sectionTitles[active]"
      @close="helpOpen = false"
      @open-manual="openManual"
    />
  </div>
</template>
