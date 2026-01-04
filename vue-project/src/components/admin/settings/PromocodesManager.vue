<template>
  <div class="admin-card">
    <div class="admin-card-header">
      <h3 class="admin-card-title">
        Promocode Management
        <InfoTooltip position="top">
          Here you can create new promocodes and manage existing ones.
          Each promocode can be configured for a specific plan and have usage limits.
        </InfoTooltip>
      </h3>
      <button
        @click="showCreatePromo = true"
        class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
      >
        Create Promocode
      </button>
    </div>

    <!-- Форма создания/редактирования промокода -->
    <div v-if="showCreatePromo" class="mt-6 p-4 bg-gray-700/50 rounded-lg">
      <h4 class="text-lg font-medium text-white mb-4">
        {{ editingPromoId ? 'Editing Promocode' : 'Promocode Creation' }}
      </h4>
      <form @submit.prevent="savePromocode" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Name</label>
            <input
              v-model="newPromo.name"
              type="text"
              required
              class="modal-input"
              placeholder="For example: New Year Promotion"
            >
          </div>

          <!-- Promocode -->
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Promocode</label>
            <input
              v-model="newPromo.code"
              type="text"
              class="modal-input"
              placeholder="Leave empty for auto-generation"
            >
          </div>

          <!-- Promocode Type -->
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Promocode Type</label>
            <select
              v-model="newPromo.type"
              required
              class="modal-input"
              @change="onTypeChange"
            >
              <option value="points">Points</option>
              <option value="tariff">Plan</option>
              <option value="discount">Discount</option>
            </select>
          </div>

          <!-- Usage Type -->
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Usage Type</label>
            <select
              v-model="newPromo.usage_type"
              required
              class="modal-input"
            >
              <option value="unlimited">Unlimited</option>
              <option value="limited">Limited</option>
              <option value="single_user">For Specific User</option>
            </select>
          </div>

          <!-- Number of Points (if type = points) -->
          <div v-if="newPromo.type === 'points'">
            <label class="block text-sm font-medium text-gray-400 mb-1">Number of Points</label>
            <input
              v-model.number="newPromo.points_amount"
              type="number"
              min="1"
              required
              class="modal-input"
              placeholder="For example: 100"
            >
          </div>

          <!-- Plan (if type = tariff) -->
          <div v-if="newPromo.type === 'tariff'">
            <label class="block text-sm font-medium text-gray-400 mb-1">Plan</label>
            <select
              v-model="newPromo.tariff_type"
              required
              class="modal-input"
            >
              <option value="tariff_2">Standard</option>
              <option value="tariff_4">Premium</option>
              <option value="tariff_6">VIP</option>
            </select>
          </div>

          <!-- Plan Duration (if type = tariff) -->
          <div v-if="newPromo.type === 'tariff'">
            <label class="block text-sm font-medium text-gray-400 mb-1">Duration</label>
            <select
              v-model="newPromo.tariff_duration_months"
              required
              class="modal-input"
            >
              <option value="1">1 month</option>
              <option value="2">2 months</option>
              <option value="3">3 months</option>
              <option value="6">6 months</option>
              <option value="12">12 months</option>
            </select>
          </div>

          <!-- Discount Percentage (if type = discount) -->
          <div v-if="newPromo.type === 'discount'">
            <label class="block text-sm font-medium text-gray-400 mb-1">Discount Percentage</label>
            <input
              v-model.number="newPromo.discount_percent"
              type="number"
              min="1"
              max="100"
              required
              class="modal-input"
              placeholder="For example: 20"
            >
          </div>

          <!-- Number of Uses (if limited) -->
          <div v-if="newPromo.usage_type === 'limited'">
            <label class="block text-sm font-medium text-gray-400 mb-1">
              Number of Uses
            </label>
            <input
              v-model.number="newPromo.usage_limit"
              type="number"
              min="1"
              required
              class="modal-input"
              placeholder="For example: 100"
            >
          </div>

          <!-- User ID (if for specific user) -->
          <div v-if="newPromo.usage_type === 'single_user'">
            <label class="block text-sm font-medium text-gray-400 mb-1">
              User ID
            </label>
            <input
              v-model.number="newPromo.user_id"
              type="number"
              min="1"
              required
              class="modal-input"
              placeholder="For example: 123"
            >
          </div>

          <!-- End Date -->
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">
              Valid until (optional)
            </label>
            <input
              v-model="newPromo.valid_until"
              type="datetime-local"
              class="modal-input"
              :min="minDateTime"
            >
          </div>

          <!-- Description -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-400 mb-1">Description</label>
            <textarea
              v-model="newPromo.description"
              class="modal-input"
              rows="3"
              placeholder="Promocode description..."
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-4 mt-4">
          <button
            type="button"
            @click="cancelEdit"
            :disabled="isCreating"
            class="modal-btn-cancel disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="isCreating"
            class="modal-btn-submit disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isCreating" class="inline-flex items-center">
              <span class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></span>
              {{ editingPromoId ? 'Saving...' : 'Creating...' }}
            </span>
            <span v-else>
              {{ editingPromoId ? 'Save Changes' : 'Create Promocode' }}
            </span>
          </button>
        </div>
      </form>
    </div>

    <!-- Список промокодов -->
    <div class="mt-6">
      <!-- Loading state -->
      <div v-if="isLoading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
        <p class="mt-2 text-gray-400">Loading promocodes...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
        <p>{{ error }}</p>
        <button
          @click="loadPromocodes"
          class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
        >
          Try again
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="!promocodes.length" class="text-center py-8 bg-gray-800 rounded-lg">
        <p class="text-gray-400">No promocodes available</p>
      </div>

      <!-- Table -->
      <table v-else class="w-full">
        <thead class="bg-gray-900">
        <tr>
          <th class="p-4 text-left text-gray-400">Promocode</th>
          <th class="p-4 text-left text-gray-400">Name</th>
          <th class="p-4 text-left text-gray-400">Type</th>
          <th class="p-4 text-left text-gray-400">Value</th>
          <th class="p-4 text-left text-gray-400">Uses</th>
          <th class="p-4 text-left text-gray-400">Valid Until</th>
          <th class="p-4 text-left text-gray-400">Status</th>
          <th class="p-4 text-left text-gray-400">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr
          v-for="promo in promocodes"
          :key="promo.code"
          class="border-t border-gray-700"
        >
          <td class="p-4 font-mono">{{ promo.code }}</td>
          <td class="p-4">{{ promo.name }}</td>
          <td class="p-4">{{ formatPromoType(promo.type) }}</td>
          <td class="p-4">{{ formatPromoValue(promo) }}</td>
          <td class="p-4">
            {{ promo.usage_count }}/{{ promo.usage_limit || '∞' }}
          </td>
          <td class="p-4">{{ formatDate(promo.valid_until) }}</td>
          <td class="p-4">
             <span
               class="px-2 py-1 rounded-full text-xs"
               :class="getPromoStatusClass(promo)"
             >
               {{ getPromoStatus(promo) }}
             </span>
          </td>
          <td class="p-4">
            <div class="flex gap-2">
              <button
                @click="editPromo(promo)"
                class="text-blue-400 hover:text-blue-300 text-sm"
              >
                Edit
              </button>
              <button
                @click="deactivatePromo(promo.code)"
                class="text-red-400 hover:text-red-300 text-sm"
                v-if="isPromoActive(promo)"
                :disabled="isDeactivating === promo.code"
              >
                <span v-if="isDeactivating === promo.code" class="inline-block animate-pulse">
                  Deactivating...
                </span>
                <span v-else>
                  Deactivate
                </span>
              </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import { useMainStore } from '../../../store'
import InfoTooltip from '../common/InfoTooltip.vue'

interface Promocode {
  id: number
  code: string
  name: string
  description?: string
  type: 'points' | 'tariff' | 'discount'
  usage_type: 'unlimited' | 'limited' | 'single_user'
  points_amount?: number
  tariff_type?: string
  tariff_duration_months?: number
  discount_percent?: number
  usage_limit?: number
  usage_count: number
  user_id?: number
  valid_until?: string
  is_active: boolean
  is_valid: boolean
  remaining_uses?: number
  created_at: string
}

interface NewPromocode {
  name: string
  code?: string
  description?: string
  type: 'points' | 'tariff' | 'discount'
  usage_type: 'unlimited' | 'limited' | 'single_user'
  points_amount?: number
  tariff_type?: string
  tariff_duration_months?: number
  discount_percent?: number
  usage_limit?: number
  user_id?: number
  valid_until?: string
}

const store = useMainStore()

// UI state
const showCreatePromo = ref(false)
const isLoading = ref(false)
const isCreating = ref(false)
const isDeactivating = ref<string | null>(null)
const error = ref<string | null>(null)
const promocodes = ref<Promocode[]>([])
const editingPromoId = ref<number | null>(null)

// Новый промокод
const newPromo = ref<NewPromocode>({
  name: '',
  type: 'points',
  usage_type: 'limited',
  points_amount: 100,
  usage_limit: 1
})

// Минимальная дата для выбора (сегодня)
const minDateTime = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
})

// Форматирование типа промокода
const formatPromoType = (type: string) => {
  const types = {
    'points': 'Points',
    'tariff': 'Plan',
    'discount': 'Discount'
  }
  return types[type as keyof typeof types] || type
}

// Форматирование значения промокода
const formatPromoValue = (promo: Promocode) => {
  if (promo.type === 'points') {
    return `${promo.points_amount} points`
  } else if (promo.type === 'tariff') {
    const tariffs = {
      'tariff_2': 'Standard',
      'tariff_4': 'Premium',
      'tariff_6': 'VIP'
    }
    const tariffName = tariffs[promo.tariff_type as keyof typeof tariffs] || promo.tariff_type
    return `${tariffName} (${promo.tariff_duration_months} months)`
  } else if (promo.type === 'discount') {
    return `${promo.discount_percent}% discount`
  }
  return '-'
}

// Форматирование даты
const formatDate = (date?: string) => {
  if (!date) return 'No restrictions'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Обработка изменения типа промокода
const onTypeChange = () => {
  // Сбрасываем значения при смене типа
  if (newPromo.value.type === 'points') {
    newPromo.value.points_amount = 100
    newPromo.value.tariff_type = undefined
    newPromo.value.tariff_duration_months = undefined
    newPromo.value.discount_percent = undefined
  } else if (newPromo.value.type === 'tariff') {
    newPromo.value.points_amount = undefined
    newPromo.value.tariff_type = 'tariff_2'
    newPromo.value.tariff_duration_months = 1
    newPromo.value.discount_percent = undefined
  } else if (newPromo.value.type === 'discount') {
    newPromo.value.points_amount = undefined
    newPromo.value.tariff_type = undefined
    newPromo.value.tariff_duration_months = undefined
    newPromo.value.discount_percent = 10
  }
}

// Проверка активности промокода
const isPromoActive = (promo: Promocode) => {
  return promo.is_valid && promo.is_active
}

// Получение статуса промокода
const getPromoStatus = (promo: Promocode) => {
  if (!promo.is_active) return 'Deactivated'
  if (promo.valid_until && new Date(promo.valid_until) <= new Date()) return 'Expired'
  if (promo.usage_limit && promo.usage_count >= promo.usage_limit) return 'Used'
  return 'Active'
}

// Класс для статуса
const getPromoStatusClass = (promo: Promocode) => {
  const status = getPromoStatus(promo)
  const classes = {
    'Active': 'bg-green-500/20 text-green-300',
    'Expired': 'bg-red-500/20 text-red-300',
    'Used': 'bg-orange-500/20 text-orange-300',
    'Deactivated': 'bg-gray-500/20 text-gray-300'
  }
  return classes[status as keyof typeof classes]
}

// Создание/обновление промокода
const savePromocode = async () => {
  if (isCreating.value) return;

  isCreating.value = true;
  error.value = null;

  try {
    if (editingPromoId.value) {
      // Обновление существующего промокода
      const existingPromo = promocodes.value.find(p => p.id === editingPromoId.value);
      if (existingPromo) {
        await store.updatePromocode(existingPromo.code, newPromo.value);
      }
    } else {
      // Создание нового промокода
      await store.createPromocode(newPromo.value);
    }

    await loadPromocodes();
    cancelEdit();
  } catch (err: any) {
    console.error('Error saving promocode:', err);
    const action = editingPromoId.value ? 'updating' : 'creating';
    error.value = `Error ${action} promocode: ${err.message || 'Unknown error'}`;
  } finally {
    isCreating.value = false;
  }
}

// Отмена редактирования
const cancelEdit = () => {
  showCreatePromo.value = false;
  editingPromoId.value = null;
  resetForm();
}

// Сброс формы
const resetForm = () => {
  newPromo.value = {
    name: '',
    type: 'points',
    usage_type: 'limited',
    points_amount: 100,
    usage_limit: 1
  };
}

// Редактирование промокода
const editPromo = (promo: Promocode) => {
  console.log('Edit promo:', promo);

  // Заполняем форму данными промокода
  newPromo.value = {
    name: promo.name,
    code: promo.code,
    description: promo.description || '',
    type: promo.type,
    usage_type: promo.usage_type,
    points_amount: promo.points_amount || 100,
    tariff_type: promo.tariff_type || '',
    tariff_duration_months: promo.tariff_duration_months || 1,
    discount_percent: promo.discount_percent || 0,
    usage_limit: promo.usage_limit || 1,
    user_id: promo.user_id,
    valid_until: promo.valid_until || ''
  };

  // Устанавливаем режим редактирования
  editingPromoId.value = promo.id;
  showCreatePromo.value = true;
}

// Деактивация промокода
const deactivatePromo = async (code: string) => {
  if (isDeactivating.value) return;

  isDeactivating.value = code;
  error.value = null;

  try {
    await store.deactivatePromocode(code);
    await loadPromocodes();
  } catch (err: any) {
    console.error('Error deactivating promocode:', err);
    error.value = `Error deactivating promocode: ${err.message || 'Unknown error'}`;
  } finally {
    isDeactivating.value = null;
  }
}

// Загрузка промокодов
const loadPromocodes = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await store.fetchPromocodes();

    // Упрощенная обработка ответа
    if (Array.isArray(response)) {
      promocodes.value = response;
    } else if (response?.items && Array.isArray(response.items)) {
      promocodes.value = response.items;
    } else if (response?.data && Array.isArray(response.data)) {
      promocodes.value = response.data;
    } else {
      console.warn('Unexpected response structure:', response);
      promocodes.value = [];
    }

    console.log('Successfully loaded promocodes:', promocodes.value.length);
  } catch (err: any) {
    console.error('Error loading promocodes:', err);
    error.value = `Error loading promocodes: ${err.message || 'Unknown error'}`;
    promocodes.value = [];
  } finally {
    isLoading.value = false;
  }
}

// При монтировании компонента
onMounted(() => {
  loadPromocodes()
})
</script>
