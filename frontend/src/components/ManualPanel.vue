<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import { manual } from '../content/manual.js'

const rendered = computed(() => marked.parse(manual))
</script>

<template>
  <section class="card">
    <div class="card-body">
      <div class="markdown-content" v-html="rendered" />
    </div>
  </section>
</template>
