<script setup>
import { computed, inject, ref } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  filter: { type: String, default: '' },
})

const selectNode = inject('selectMibNode')
const expanded = ref(false)

function matches(node, query) {
  if (node.name.toLowerCase().includes(query) || (node.oid || '').includes(query)) return true
  return (node.children || []).some((child) => matches(child, query))
}

const visible = computed(() => {
  const query = props.filter.trim().toLowerCase()
  return !query || matches(props.node, query)
})

const hasChildren = computed(() => props.node.children && props.node.children.length > 0)
const forceOpen = computed(() => !!props.filter.trim() && visible.value && hasChildren.value)
const isOpen = computed(() => forceOpen.value || expanded.value)

function onLabelClick() {
  selectNode(props.node)
  if (hasChildren.value) expanded.value = !expanded.value
}
</script>

<template>
  <li v-if="visible">
    <div
      class="flex items-baseline gap-1.5 py-0.5 px-1 rounded cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700/60"
    >
      <span
        class="inline-block w-4 select-none text-slate-400 dark:text-slate-500"
        @click="hasChildren && (expanded = !expanded)"
      >
        {{ hasChildren ? (isOpen ? '▾' : '▸') : '' }}
      </span>
      <span
        class="break-all"
        :class="node.kind === 'module' ? 'font-semibold text-ks-700 dark:text-ks-300' : node.kind === 'leaf' ? 'text-green-600 dark:text-green-400' : ''"
        @click="onLabelClick"
      >
        {{ node.kind === 'module' ? node.name : `${node.name} (${node.oid})` }}
      </span>
    </div>
    <ul v-if="hasChildren && isOpen" class="list-none pl-4">
      <MibTreeNode v-for="child in node.children" :key="child.oid || child.name" :node="child" :filter="filter" />
    </ul>
  </li>
</template>
