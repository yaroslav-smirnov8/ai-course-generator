// src/components/admin/Users.vue
<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-white">Users</h2>
      <div class="flex gap-4">
        <input
          v-model="userSearch"
          type="text"
          placeholder="Search users..."
          class="px-4 py-2 bg-gray-700 text-white rounded-lg"
        />
        <select
          v-model="userFilter"
          class="px-4 py-2 bg-gray-700 text-white rounded-lg"
        >
          <option value="all">All roles</option>
          <option value="user">Users</option>
          <option value="admin">Administrators</option>
          <option value="friend">Friends</option>
          <option value="mod">Moderators</option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Loading users...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="fetchUsers"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Try again
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!filteredUsers.length" class="text-center py-8 bg-gray-800 rounded-lg">
      <p class="text-gray-400">No data to display</p>
    </div>

    <!-- Users table -->
    <div v-else class="bg-gray-800 rounded-lg overflow-hidden">
      <table class="w-full text-left">
        <thead class="bg-gray-900">
        <tr>
          <th class="p-4">ID</th>
          <th class="p-4">Telegram</th>
          <th class="p-4">Name</th>
          <th class="p-4">Role</th>
          <th class="p-4">Tariff</th>
          <th class="p-4">Status</th>
          <th class="p-4">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr
          v-for="user in paginatedUsers"
          :key="user.id"
          class="border-t border-gray-700 hover:bg-gray-700/50 cursor-pointer"
          @click="openUserModal(user)"
        >
          <td class="p-4">{{ user.id }}</td>
          <td class="p-4">{{ user.telegram_id }}</td>
          <td class="p-4">{{ user.first_name }} {{ user.last_name || '' }}</td>
          <td class="p-4">
              <span
                class="px-2 py-1 rounded-full text-xs"
                :class="getRoleBadgeClass(user.role)"
              >
                {{ user.role }}
              </span>
          </td>
          <td class="p-4">
              <span
                v-if="user.tariff"
                class="px-2 py-1 rounded-full text-xs bg-blue-500/20 text-blue-300"
              >
                {{ formatTariff(user.tariff) }}
              </span>
            <span v-else class="text-gray-500">-</span>
          </td>
          <td class="p-4">
              <span
                class="px-2 py-1 rounded-full text-xs"
                :class="user.has_access ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'"
              >
                {{ user.has_access ? 'Active' : 'Inactive' }}
              </span>
          </td>
          <td class="p-4">
            <button
              @click.stop="openUserModal(user)"
              class="text-purple-400 hover:text-purple-300 px-3 py-1 rounded-lg border border-purple-400 hover:bg-purple-400/10"
            >
              Manage
            </button>
          </td>
        </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="mt-4">
        <AdminPagination
          v-model:page="currentPage"
          v-model:perPage="pageSize"
          :total="filteredUsers.length"
        />
      </div>
    </div>

    <!-- Debug info (hidden by default) -->
    <div v-if="showDebug" class="mt-4 p-4 bg-gray-700 rounded-lg text-xs">
      <h4 class="text-white mb-2">Debug Info:</h4>
      <p class="text-gray-400">Raw API response: {{ rawApiResponse }}</p>
      <p class="text-gray-400">Users count: {{ users.length }}</p>
      <p class="text-gray-400">Filtered users count: {{ filteredUsers.length }}</p>
      <button @click="showDebug = false" class="text-purple-400 text-xs mt-2">Hide Debug</button>
    </div>
    <button
      v-else
      @click="showDebug = true"
      class="mt-4 text-gray-500 text-xs hover:text-gray-400"
    >
      Show Debug Info
    </button>

    <!-- Модальное окно пользователя -->
    <UserModal
      :show="showUserModal"
      :user="selectedUser"
      @close="closeUserModal"
      @save="handleUserSave"
      @userUpdated="handleUserUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import AdminPagination from './common/AdminPagination.vue'
import UserModal from './modals/UserModal.vue'

// Interface for User based on the actual API response
interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  role: string;
  is_friend: boolean;
  has_access: boolean;
  is_premium: boolean;
  platform?: string | null;
  webapp_version?: string | null;
  theme_params?: any | null;
  invite_code?: string | null;
  invited_by_code?: string | null;
  invites_count: number;
  total_earned_discount: number;
  tariff?: string | null;
  tariff_valid_until?: string | null;
  points: number;
  created_at: string;
  last_active: string;
  unsubscribed_at?: string | null;
}

const store = useMainStore()

// State
const userSearch = ref('')
const userFilter = ref('all')
const users = ref<User[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const showDebug = ref(false)
const rawApiResponse = ref<any>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// Модальное окно пользователя
const showUserModal = ref(false)
const selectedUser = ref<User | null>(null)

// Computed
const filteredUsers = computed(() => {
  let result = users.value || []

  if (userSearch.value) {
    const search = userSearch.value.toLowerCase()
    result = result.filter(user =>
      (user.first_name?.toLowerCase() || '').includes(search) ||
      (user.last_name?.toLowerCase() || '').includes(search) ||
      (user.username?.toLowerCase() || '').includes(search) ||
      (user.telegram_id?.toString() || '').includes(search)
    )
  }

  if (userFilter.value !== 'all') {
    result = result.filter(user => user.role === userFilter.value)
  }

  return result
})

// Pagination computed properties
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredUsers.value.length / pageSize.value))
})

const paginatedUsers = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  return filteredUsers.value.slice(startIndex, startIndex + pageSize.value)
})

// Removed displayedPages computed property as we're now using AdminPagination component

// Methods
const getRoleBadgeClass = (role: string) => {
  const classes = {
    admin: 'bg-purple-500/20 text-purple-300',
    friend: 'bg-green-500/20 text-green-300',
    user: 'bg-blue-500/20 text-blue-300',
    mod: 'bg-yellow-500/20 text-yellow-300'
  }
  return classes[role as keyof typeof classes] || 'bg-gray-500/20 text-gray-300'
}

const formatTariff = (tariff: string) => {
  const tariffMap: Record<string, string> = {
    'tariff_2': 'Basic',
    'tariff_4': 'Standard',
    'tariff_6': 'Premium'
  }
  return tariffMap[tariff] || tariff
}

// Методы для модального окна
const openUserModal = (user: User) => {
  selectedUser.value = user
  showUserModal.value = true
}

const closeUserModal = () => {
  showUserModal.value = false
  selectedUser.value = null
}

const handleUserSave = async (userData: Partial<User>) => {
  try {
    if (selectedUser.value?.id) {
      await store.updateUser(selectedUser.value.id, userData)
      console.log('User updated successfully:', userData)

      // Обновляем пользователя в локальном списке
      const userIndex = users.value.findIndex(u => u.id === selectedUser.value!.id)
      if (userIndex !== -1) {
        users.value[userIndex] = { ...users.value[userIndex], ...userData }
      }
    }

    closeUserModal()
  } catch (error) {
    console.error('Error saving user:', error)
  }
}

const handleUserUpdated = () => {
  // Перезагружаем список пользователей
  fetchUsers()
}

// Fetch users directly from API
const fetchUsers = async (skipParam = 0, limitParam = 100) => {
  isLoading.value = true
  error.value = null

  // Reset to first page when fetching new data
  if (skipParam === 0) {
    currentPage.value = 1
  }

  try {
    // Use store method to fetch users with correct pagination parameters
    const response = await store.fetchUsers(skipParam, limitParam)

    // Save raw response for debugging
    rawApiResponse.value = response

    // Handle different response formats
    if (response && response.items && Array.isArray(response.items)) {
      // Format: { items: User[], total: number }
      users.value = response.items
      // Update total count if available
      if (typeof response.total === 'number') {
        totalCount.value = response.total
      }
      console.log('Successfully loaded users (items):', response.items.length, 'total:', totalCount.value)
    } else if (Array.isArray(response)) {
      // Format: User[]
      users.value = response
      totalCount.value = response.length
      console.log('Successfully loaded users (array):', response.length)
    } else if (response && typeof response === 'object') {
      // Try to extract users from response object
      const possibleArrays = ['users', 'data', 'results', 'content']
      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          users.value = response[key]
          console.log(`Successfully loaded users (${key}):`, response[key].length)

          // Try to find total count in response
          const possibleTotalFields = ['total', 'total_count', 'count', 'totalCount']
          for (const field of possibleTotalFields) {
            if (typeof response[field] === 'number') {
              totalCount.value = response[field]
              break
            }
          }

          break
        }
      }

      // If we still don't have users, check if response itself is a user object
      if (!users.value.length && response.id) {
        users.value = [response]
        totalCount.value = 1
        console.log('Loaded single user:', response.id)
      }
    }

    // If we still don't have users, log error
    if (!users.value.length) {
      console.error('Could not extract users from response:', response)
      error.value = 'Failed to load users. You may not have permission to view the user list or the list is empty.'
    }
  } catch (err: any) {
    console.error('Error fetching users:', err)
    error.value = `Error loading users: ${err.message || 'Unknown error'}`
    users.value = []
    totalCount.value = 0
  } finally {
    isLoading.value = false
  }
}

// Watchers for pagination
watch(pageSize, () => {
  // Reset to first page when changing page size
  currentPage.value = 1
  // Load data with new page size
  loadPage()
})

watch(currentPage, () => {
  // Load data when page changes
  loadPage()
})

watch([userSearch, userFilter], () => {
  // Reset to first page when filtering
  currentPage.value = 1
})

// Server-side pagination function
const loadPage = async () => {
  const skip = (currentPage.value - 1) * pageSize.value
  await fetchUsers(skip, pageSize.value)
}

// Lifecycle hooks
onMounted(async () => {
  console.log('Users component mounted')

  // Проверяем наличие Telegram WebApp
  const webApp = window.Telegram?.WebApp
  if (webApp) {
    console.log('Telegram WebApp доступен:', {
      initDataUnsafe: webApp.initDataUnsafe,
      version: webApp.version,
      platform: webApp.platform,
      colorScheme: webApp.colorScheme
    })
  } else {
    console.warn('Telegram WebApp недоступен')
  }

  // Проверяем авторизацию пользователя
  console.log('Текущий пользователь в store:', store.user)

  // Initial data load
  await loadPage()

  // Логируем результаты после загрузки
  console.log('Результаты загрузки пользователей:', {
    users: users.value,
    filteredUsers: filteredUsers.value,
    currentPage: currentPage.value,
    pageSize: pageSize.value,
    totalPages: totalPages.value,
    error: error.value,
    isLoading: isLoading.value,
    rawApiResponse: rawApiResponse.value
  })
})
</script>
