import { defineStore } from 'pinia'

const MAX_ENTRIES = 10
const HOSTS_KEY = 'snmpweb_recent_hosts'
const OIDS_KEY = 'snmpweb_recent_oids'

function loadList(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const useHistoryStore = defineStore('history', {
  state: () => ({
    hosts: loadList(HOSTS_KEY),
    oids: loadList(OIDS_KEY),
  }),

  actions: {
    recordHost(host) {
      this.hosts = this._pushRecent(this.hosts, host, HOSTS_KEY)
    },

    recordOid(oid) {
      this.oids = this._pushRecent(this.oids, oid, OIDS_KEY)
    },

    _pushRecent(list, value, storageKey) {
      const trimmed = (value || '').trim()
      if (!trimmed) return list
      const next = [trimmed, ...list.filter((v) => v !== trimmed)].slice(0, MAX_ENTRIES)
      localStorage.setItem(storageKey, JSON.stringify(next))
      return next
    },
  },
})
