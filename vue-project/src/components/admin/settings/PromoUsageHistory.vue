<template>
  <div class="admin-card">
    <div class="admin-card-header">
      <h3 class="modal-title">Promocode Usage History</h3>

      <!-- Фильтры -->
      <div class="flex gap-2">
        <input
          v-model="filters.promocode"
          type="text"
          placeholder="Search by promocode"
          class="bg-gray-700 text-white rounded-lg px-4 py-2"
        >
        <select
          v-model="filters.tariff"
          class="bg-gray-700 text-white rounded-lg px-4 py-2"
        >
          <option value="">All Tariffs</option>
          <option value="tariff_2">Basic</option>
          <option value="tariff_4">Standard</option>
          <option value="tariff_6">Premium</option>
        </select>
        <div class="flex gap-2">
          <input
            v-model="filters.dateFrom"
            type="date"
            class="bg-gray-700 text-white rounded-lg px-4 py-2"
          >
          <input
            v-model="filters.dateTo"
            type="date"
            class="bg-gray-700 text-white rounded-lg px-4 py-2"
          >
        </div>
      </div>
    </div>

    <!-- История -->
    <div class="mt-6 overflow-x-auto">
      <!-- Loading state -->
      <div v-if="isLoading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
        <p class="mt-2 text-gray-400">Loading history...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
        <p>{{ error }}</p>
        <button
          @click="loadHistory"
          class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
        >
          Try again
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="!filteredHistory.length" class="text-center py-8 bg-gray-800 rounded-lg">
        <p class="text-gray-400">No data to display</p>
      </div>

      <!-- Table -->
      <table v-else class="w-full min-w-[800px]">
        <thead class="bg-gray-900">
        <tr>
          <th class="p-4 text-left text-gray-400">Activation Date</th>
          <th class="p-4 text-left text-gray-400">Promocode</th>
          <th class="p-4 text-left text-gray-400">User</th>
          <th class="p-4 text-left text-gray-400">Plan</th>
          <th class="p-4 text-left text-gray-400">Duration</th>
          <th class="p-4 text-left text-gray-400">Status</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="item in filteredHistory"
            :key="item.id"
            class="border-t border-gray-700">
          <td class="p-4">{{ formatDate(item.activated_at) }}</td>
          <td class="p-4 font-mono">{{ item.promocode }}</td>
          <td class="p-4">
            <div class="flex items-center gap-2">
              <span>{{ getUserName(item.user) }}</span>
              <button
                @click="viewUser(item.user)"
                class="text-blue-400 hover:text-blue-300"
                :disabled="isViewingUser"
              >
                <EyeIcon class="w-4 h-4" />
              </button>
            </div>
          </td>
          <td class="p-4">{{ formatTariff(item.tariff_type) }}</td>
          <td class="p-4">{{ item.duration_months }} months</td>
          <td class="p-4">
             <span
               :class="getStatusClass(item.status)"
               class="px-2 py-1 rounded-full text-xs"
             >
               {{ formatStatus(item.status) }}
             </span>
          </td>
        </tr>
        </tbody>
      </table>

      <!-- Пагинация -->
      <div v-if="filteredHistory.length > 0" class="mt-4">
        <AdminPagination
          v-model:page="currentPage"
          :total="totalItems"
          :per-page="perPage"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, watch} from 'vue'
import { Eye as EyeIcon } from 'lucide-vue-next'
import { useMainStore } from '../../../store'
import AdminPagination from '@/components/admin/common/AdminPagination.vue'

// Интерфейсы
interface UserInfo {
  id: number;
  name: string;
}

interface PromoHistoryItem {
  id: number;
  activated_at: string;
  promocode: string;
  user: UserInfo;
  tariff_type: string;
  duration_months: number;
  status: string;
}

interface Filters {
  promocode: string;
  tariff: string;
  dateFrom: string;
  dateTo: string;
}

const store = useMainStore()

// Состояние
const currentPage = ref(1)
const perPage = ref(10)
const totalItems = ref(0)
const history = ref<PromoHistoryItem[]>([])
const isLoading = ref(false)
const isViewingUser = ref(false)
const error = ref<string | null>(null)

// Фильтры
const filters = ref<Filters>({
  promocode: '',
  tariff: '',
  dateFrom: '',
  dateTo: ''
})

// Форматирование
const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

const formatTariff = (tariffType: string) => {
  const tariffs = {
    'tariff_2': 'Basic',
    'tariff_4': 'Standard',
    'tariff_6': 'Premium'
  }
  return tariffs[tariffType as keyof typeof tariffs] || tariffType
}

const formatStatus = (status: string) => {
  const statuses = {
    'active': 'Active',
    'expired': 'Expired',
    'cancelled': 'Cancelled'
  }
  return statuses[status as keyof typeof statuses] || status
}

const getStatusClass = (status: string) => {
  const classes = {
    'active': 'bg-green-500/20 text-green-300',
    'expired': 'bg-red-500/20 text-red-300',
    'cancelled': 'bg-orange-500/20 text-orange-300'
  }
  return classes[status as keyof typeof classes] || ''
}

// Фильтрация
const filteredHistory = computed((): PromoHistoryItem[] => {
  let result = history.value

  if (filters.value.promocode) {
    result = result.filter(item =>
      item.promocode.toLowerCase().includes(filters.value.promocode.toLowerCase())
    )
  }

  if (filters.value.tariff) {
    result = result.filter(item => item.tariff_type === filters.value.tariff)
  }

  if (filters.value.dateFrom || filters.value.dateTo) {
    result = result.filter(item => {
      const date = new Date(item.activated_at)
      const fromDate = filters.value.dateFrom ? new Date(filters.value.dateFrom) : null
      const toDate = filters.value.dateTo ? new Date(filters.value.dateTo) : null

      if (fromDate && toDate) {
        return date >= fromDate && date <= toDate
      } else if (fromDate) {
        return date >= fromDate
      } else if (toDate) {
        return date <= toDate
      }
      return true
    })
  }

  return result
})

// Получение имени пользователя
const getUserName = (user: UserInfo): string => {
  if (!user) return 'Unknown user';

  if (typeof user === 'object') {
    if (user.name) return user.name;

    // Если имя не найдено, попробуем другие возможные поля
    const possibleNameFields = ['full_name', 'username', 'first_name', 'email'];
    for (const field of possibleNameFields) {
      if (user[field as keyof typeof user]) {
        return user[field as keyof typeof user] as string;
      }
    }

    // Если ничего не найдено, вернем ID
    return `User #${user.id}`;
  }

  return String(user);
};

// Действия
const viewUser = async (user: UserInfo) => {
  if (isViewingUser.value) return;

  isViewingUser.value = true;

  try {
    await store.openUserModal(user.id);
  } catch (err: any) {
    console.error('Error opening user modal:', err);
    error.value = `Error opening user information: ${err.message || 'Unknown error'}`;
  } finally {
    isViewingUser.value = false;
  }
};

// Загрузка данных
const loadHistory = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await store.getPromocodesHistory({
      page: currentPage.value,
      per_page: perPage.value,
      ...filters.value
    });

    if (response && response.data && Array.isArray(response.data)) {
      history.value = response.data;
      totalItems.value = response.total || response.data.length;
      console.log('Successfully loaded promocodes history:', response.data.length);
    } else if (Array.isArray(response)) {
      // Если ответ сам является массивом
      history.value = response;
      totalItems.value = response.length;
      console.log('Successfully loaded promocodes history (array):', response.length);
    } else if (response && typeof response === 'object') {
      // Попробуем найти массив в ответе
      const possibleArrays = ['items', 'data', 'results', 'content', 'history'];
      let foundHistory = false;

      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          history.value = response[key];
          totalItems.value = response.total || response[key].length;
          console.log(`Successfully loaded promocodes history from ${key}:`, response[key].length);
          foundHistory = true;
          break;
        }
      }

      if (!foundHistory) {
        console.error('Could not extract history from response:', response);
        error.value = 'Could not find promocode history data in API response';
        history.value = [];
        totalItems.value = 0;
      }
    } else {
      console.error('Unexpected promocodes history response structure:', response);
      error.value = 'Unexpected API response structure';
      history.value = [];
      totalItems.value = 0;
    }
  } catch (err: any) {
    console.error('Error loading promocodes history:', err);
    error.value = `Error loading promocodes history: ${err.message || 'Unknown error'}`;
    history.value = [];
    totalItems.value = 0;
  } finally {
    isLoading.value = false;
  }
}

// Отслеживание изменений
watch([currentPage, perPage, filters], () => {
  loadHistory()
})

onMounted(() => {
  loadHistory()
})
</script>
