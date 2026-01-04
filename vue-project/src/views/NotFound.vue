<template>
  <div class="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-center px-4">
    <!-- 404 Header -->
    <h1 class="text-6xl font-bold text-white mb-4">404</h1>
    <h2 class="text-2xl text-gray-400 mb-8">Page not found</h2>

    <!-- Message -->
    <p class="text-gray-300 mb-8 max-w-md">
      Unfortunately, the requested page does not exist or has been moved
    </p>

    <!-- Navigation buttons -->
    <div class="flex flex-col sm:flex-row gap-4">
      <router-link
        to="/"
        class="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
      >
        Return to home
      </router-link>

      <button
        @click="$router.go(-1)"
        class="px-6 py-3 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
      >
        Back
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
// Component implemented using Composition API
// All styles use Tailwind CSS
</script>
