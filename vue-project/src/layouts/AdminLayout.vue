<!-- src/layouts/AdminLayout.vue -->
<template>
  <div class="flex h-screen bg-gray-100 dark:bg-gray-900">
    <!-- Sidebar -->
    <aside
      :class="`
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        fixed md:relative
        w-64 h-screen
        transition-transform duration-300 ease-in-out
        bg-white dark:bg-gray-800
        border-r border-gray-200 dark:border-gray-700
        z-50 md:translate-x-0
      `"
    >
      <!-- Sidebar Header -->
      <div class="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
        <span class="text-lg font-semibold text-gray-800 dark:text-white">
          Admin Panel
        </span>
        <button
          @click="toggleSidebar"
          class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <Menu class="w-6 h-6 text-gray-600 dark:text-gray-300" />
        </button>
      </div>

      <!-- Navigation -->
      <nav class="p-4 space-y-2">
        <nav-item v-for="item in navigationItems"
                  :key="item.path"
                  :icon="item.icon"
                  :to="item.path"
                  :label="item.label"
        />
      </nav>

      <!-- Bottom Section -->
      <div class="absolute bottom-0 w-full p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          @click="handleLogout"
          class="flex items-center w-full px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
        >
          <LogOut class="w-5 h-5 mr-3" />
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Header -->
      <header class="h-16 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div class="flex items-center justify-between h-full px-4">
          <button
            @click="toggleSidebar"
            class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Menu class="w-6 h-6 text-gray-600 dark:text-gray-300" />
          </button>
          <div class="ml-auto flex items-center space-x-4">
            <!-- Add header items like notifications, user profile, etc. -->
            <button
              @click="toggleTheme"
              class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Sun v-if="isDark" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
              <Moon v-else class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </button>
            <div v-if="currentUser" class="text-gray-600 dark:text-gray-300">
              {{ currentUser.name }}
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
        <slot></slot>
      </main>
    </div>

    <!-- Mobile Overlay -->
    <div
      v-if="isSidebarOpen && isMobile"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
      @click="closeSidebar"
    />
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, onUnmounted, computed} from 'vue'
import { useRouter } from 'vue-router'
import { useMainStore } from '@/store'
import {
  Menu,
  Home,
  Users,
  Settings,
  BarChart2,
  Box,
  Shield,
  CreditCard,
  LogOut,
  Sun,
  Moon
} from 'lucide-vue-next'
import NavItem from '@/components/admin/NavItem.vue'

const router = useRouter()
const store = useMainStore()

const isSidebarOpen = ref(true)
const isMobile = ref(false)
const isDark = ref(false)

const navigationItems = [
  { path: '/admin', label: 'Dashboard', icon: Home },
  { path: '/admin/users', label: 'Users', icon: Users },
  { path: '/admin/content', label: 'Content', icon: Box },
  { path: '/admin/subscriptions', label: 'Subscriptions', icon: CreditCard },
  { path: '/admin/analytics', label: 'Analytics', icon: BarChart2 },
  { path: '/admin/roles', label: 'Roles', icon: Shield },
  { path: '/admin/settings', label: 'Settings', icon: Settings }
]

const currentUser = computed(() => store.user)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (window.innerWidth < 768) {
    isSidebarOpen.value = false
  }
}

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const closeSidebar = () => {
  if (isMobile.value) {
    isSidebarOpen.value = false
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark')
}

const handleLogout = async () => {
  await store.logout()
  router.push('/login')
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Check system dark mode preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.router-link-active {
  @apply bg-purple-50 text-purple-600 dark:bg-gray-700 dark:text-purple-400;
}

/* Smooth transitions */
.transition-transform {
  transition-property: transform;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 300ms;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: theme('colors.gray.100');
  @apply dark:bg-gray-800;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}
</style>
