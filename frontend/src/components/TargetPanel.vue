<script setup>
import { useTargetStore } from '../stores/target.js'
import { useHistoryStore } from '../stores/history.js'

const target = useTargetStore()
const history = useHistoryStore()
</script>

<template>
  <div class="flex flex-col gap-3">
    <p class="text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">Ziel</p>

    <div>
      <label class="label" for="host">Host</label>
      <input id="host" v-model="target.host" list="host-history" class="input" placeholder="10.123.40.xx" />
      <datalist id="host-history">
        <option v-for="h in history.hosts" :key="h" :value="h" />
      </datalist>
    </div>

    <div class="flex gap-2">
      <div class="flex-1">
        <label class="label" for="port">Port</label>
        <input id="port" v-model.number="target.port" type="number" class="input" />
      </div>
      <div class="flex-1">
        <label class="label" for="version">Version</label>
        <select id="version" v-model="target.version" class="input">
          <option value="v2c">v2c</option>
          <option value="v1">v1</option>
          <option value="v3">v3</option>
        </select>
      </div>
    </div>

    <div v-if="target.version !== 'v3'">
      <label class="label" for="community">Community</label>
      <input id="community" v-model="target.community" class="input" />
    </div>

    <template v-else>
      <div>
        <label class="label" for="v3-username">Username</label>
        <input id="v3-username" v-model="target.username" class="input" />
      </div>
      <div>
        <label class="label" for="v3-auth-protocol">Auth-Protokoll</label>
        <select id="v3-auth-protocol" v-model="target.authProtocol" class="input">
          <option value="none">none</option>
          <option value="SHA">SHA</option>
          <option value="SHA256">SHA256</option>
          <option value="MD5">MD5</option>
        </select>
      </div>
      <div>
        <label class="label" for="v3-auth-password">Auth-Passwort</label>
        <input id="v3-auth-password" v-model="target.authPassword" type="password" class="input" />
      </div>
      <div>
        <label class="label" for="v3-priv-protocol">Priv-Protokoll</label>
        <select id="v3-priv-protocol" v-model="target.privProtocol" class="input">
          <option value="none">none</option>
          <option value="AES128">AES128</option>
          <option value="AES256">AES256</option>
          <option value="DES">DES</option>
        </select>
      </div>
      <div>
        <label class="label" for="v3-priv-password">Priv-Passwort</label>
        <input id="v3-priv-password" v-model="target.privPassword" type="password" class="input" />
      </div>
    </template>
  </div>
</template>
