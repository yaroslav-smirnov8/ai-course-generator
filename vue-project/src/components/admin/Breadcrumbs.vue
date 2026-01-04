<!-- src/components/admin/Breadcrumbs.vue -->
<template>
  <nav class="flex" aria-label="Breadcrumb">
    <ol class="inline-flex items-center space-x-1">
      <li v-for="(crumb, index) in breadcrumbs"
          :key="crumb.path"
          class="inline-flex items-center">
        <router-link
          v-if="index < breadcrumbs.length - 1"
          :to="crumb.path"
          class="text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
        >
          {{ crumb.name }}
        </router-link>
        <span
          v-else
          class="text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          {{ crumb.name }}
        </span>

        <ChevronRight
          v-if="index < breadcrumbs.length - 1"
          class="w-4 h-4 mx-2 text-gray-400"
        />
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'

interface Breadcrumb {
  name: string
  path: string
}

const route = useRoute()

const breadcrumbs = computed<Breadcrumb[]>(() => {
  const pathArray = route.path.split('/').filter(Boolean)
  const crumbs: Breadcrumb[] = []
  let path = ''

  // Add home
  crumbs.push({
    name: 'Admin',
    path: '/admin'
  })

  // Add remaining breadcrumbs
  pathArray.forEach((pathPart, index) => {
    if (index === 0 && pathPart === 'admin') return

    path += `/${pathPart}`
    const name = pathPart.charAt(0).toUpperCase() + pathPart.slice(1)

    crumbs.push({
      name,
      path
    })
  })

  return crumbs
})
</script>
