<script setup>
import { ref, watch } from 'vue'
import { marked } from 'marked'
import { getHelp } from '../content/helpTexts.js'

const props = defineProps({
  open: Boolean,
  section: { type: String, default: '' },
  sectionTitle: { type: String, default: '' },
})
defineEmits(['close', 'open-manual'])

const rendered = ref('')

watch(
  () => props.section,
  (section) => {
    rendered.value = marked.parse(getHelp(section))
  },
  { immediate: true }
)
</script>

<template>
  <Teleport to="body">
    <Transition name="help-slide">
      <div v-if="open" class="fixed inset-0 z-[65] flex">
        <div class="fixed inset-0 bg-slate-900/40" @click="$emit('close')" />

        <div class="relative ml-auto w-full max-w-sm bg-white dark:bg-slate-800 shadow-2xl flex flex-col h-full">
          <div class="flex items-center justify-between px-4 py-3.5 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-full bg-ks-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">?</span>
              <div>
                <div class="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wider">Hilfe</div>
                <div class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ sectionTitle }}</div>
              </div>
            </div>
            <button
              class="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-700"
              title="Hilfe schließen"
              @click="$emit('close')"
            >
              ✕
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-4">
            <div class="markdown-content" v-html="rendered" />
          </div>

          <div class="px-4 py-2.5 border-t border-slate-100 dark:border-slate-700 flex items-center justify-end">
            <button class="text-xs text-ks-600 dark:text-ks-300 hover:underline" @click="$emit('open-manual')">
              Vollständiges Handbuch →
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.help-slide-enter-from { transform: translateX(100%); opacity: 0; }
.help-slide-enter-active { transition: transform 0.2s ease-out, opacity 0.15s ease-out; }
.help-slide-leave-to { transform: translateX(100%); opacity: 0; }
.help-slide-leave-active { transition: transform 0.15s ease-in, opacity 0.1s ease-in; }
</style>
