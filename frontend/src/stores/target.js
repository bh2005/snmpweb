import { defineStore } from 'pinia'

export const useTargetStore = defineStore('target', {
  state: () => ({
    host: '',
    port: 161,
    version: 'v2c',
    community: 'public',
    username: '',
    authProtocol: 'none',
    authPassword: '',
    privProtocol: 'none',
    privPassword: '',
    oid: '1.3.6.1.2.1.1',
  }),

  getters: {
    asRequestTarget: (state) => {
      const target = {
        host: state.host,
        port: Number(state.port) || 161,
        version: state.version,
      }
      if (state.version === 'v3') {
        target.username = state.username
        target.auth_protocol = state.authProtocol
        target.auth_password = state.authPassword
        target.priv_protocol = state.privProtocol
        target.priv_password = state.privPassword
      } else {
        target.community = state.community
      }
      return target
    },
  },
})
