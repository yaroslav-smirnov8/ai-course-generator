<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-800 rounded-lg w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Заголовок -->
      <div class="flex justify-between items-center p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
        <h3 class="text-xl font-semibold text-white">
          {{ user ? `User: ${user.first_name} ${user.last_name || ''}` : 'New User' }}
        </h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white">
          <XIcon class="w-6 h-6" />
        </button>
      </div>

      <!-- Вкладки -->
      <div class="border-b border-gray-700">
        <nav class="flex space-x-8 px-6">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap"
            :class="activeTab === tab.id
              ? 'border-purple-500 text-purple-500'
              : 'border-transparent text-gray-400 hover:text-gray-300'"
          >
            {{ tab.name }}
          </button>
        </nav>
      </div>

      <!-- Содержимое вкладок -->
      <div class="p-6">
        <!-- Вкладка: Основная информация -->
        <div v-if="activeTab === 'info'" class="space-y-6">
          <!-- Основная информация пользователя -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <h4 class="text-lg font-semibold text-white">Basic Information</h4>

              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-400">ID:</span>
                  <span class="text-white">{{ user?.id }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Telegram ID:</span>
                  <span class="text-white">{{ user?.telegram_id }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Username:</span>
                  <span class="text-white">@{{ user?.username || 'Not specified' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Name:</span>
                  <span class="text-white">{{ user?.first_name }} {{ user?.last_name || '' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Role:</span>
                  <span class="text-white">{{ user?.role || 'Not specified' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Access:</span>
                  <span class="text-white">{{ user?.has_access ? 'Active' : 'Blocked' }}</span>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <h4 class="text-lg font-semibold text-white">Statistics</h4>

              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-400">Points:</span>
                  <span class="text-white font-semibold">{{ user?.points || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Invitations:</span>
                  <span class="text-white">{{ user?.invites_count || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Plan:</span>
                  <span class="text-white">{{ user?.tariff ? formatTariff(user.tariff) : 'Free' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Invite Code:</span>
                  <span class="text-white font-mono">{{ user?.invite_code || 'Not created' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Даты -->
          <div class="border-t border-gray-700 pt-6">
            <h4 class="text-lg font-semibold text-white mb-4">Timestamps</h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span class="text-gray-400 block">Created:</span>
                <span class="text-white">{{ formatDate(user?.created_at) }}</span>
              </div>
              <div>
                <span class="text-gray-400 block">Last Active:</span>
                <span class="text-white">{{ formatDate(user?.last_active) }}</span>
              </div>
              <div v-if="user?.unsubscribed_at">
                <span class="text-gray-400 block">Unsubscribed:</span>
                <span class="text-red-300">{{ formatDate(user?.unsubscribed_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Текущий тариф -->
          <div class="border-t border-gray-700 pt-6">
            <h4 class="text-lg font-semibold text-white mb-4">Current Plan</h4>
            <div class="bg-gray-700 rounded-lg p-4">
              <div class="flex justify-between items-center">
                <div>
                  <span class="text-gray-400">Plan:</span>
                  <span class="text-white ml-2">
                    {{ user?.tariff ? formatTariff(user.tariff) : 'Free' }}
                  </span>
                </div>
                <div v-if="user?.tariff_valid_until">
                  <span class="text-gray-400">Valid Until:</span>
                  <span class="text-white ml-2">{{ formatDate(user.tariff_valid_until) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Вкладка: Управление -->
        <div v-if="activeTab === 'manage'" class="space-y-6">
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- Изменение тарифа -->
            <div class="bg-gray-700 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-white mb-4">Plan Management</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-1">Plan</label>
                  <select
                    v-model="formData.tariff"
                    class="w-full bg-gray-600 text-white rounded-lg px-4 py-2 border border-gray-500 focus:border-purple-500"
                  >
                    <option value="">Free</option>
                    <option value="tariff_2">Standard</option>
                    <option value="tariff_4">Premium</option>
                    <option value="tariff_6">VIP</option>
                  </select>
                </div>
                <div v-if="formData.tariff">
                  <label class="block text-sm font-medium text-gray-400 mb-1">Valid Until</label>
                  <input
                    v-model="formData.tariff_valid_until"
                    type="datetime-local"
                    class="w-full bg-gray-600 text-white rounded-lg px-4 py-2 border border-gray-500 focus:border-purple-500"
                  >
                </div>
              </div>
            </div>

            <!-- Управление баллами -->
            <div class="bg-gray-700 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-white mb-4">Points Management</h4>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-1">Current Points</label>
                  <input
                    :value="user?.points || 0"
                    type="number"
                    disabled
                    class="w-full bg-gray-600 text-gray-300 rounded-lg px-4 py-2 border border-gray-500"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-400 mb-1">Change By</label>
                  <input
                    v-model.number="pointsChange"
                    type="number"
                    placeholder="±100"
                    class="w-full bg-gray-600 text-white rounded-lg px-4 py-2 border border-gray-500 focus:border-purple-500"
                  >
                </div>
                <div class="flex items-end">
                  <button
                    type="button"
                    @click="updatePoints"
                    :disabled="!pointsChange"
                    class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Apply
                  </button>
                </div>
              </div>
              <p class="text-xs text-gray-400 mt-2">
                Enter a positive number to add points or negative to deduct
              </p>
            </div>

            <!-- Управление доступом -->
            <div class="bg-gray-700 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-white mb-4">Access Management</h4>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-white">Active Access</span>
                    <p class="text-sm text-gray-400">Allow user to use the application</p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      v-model="formData.has_access"
                      type="checkbox"
                      class="sr-only peer"
                    >
                    <div class="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-500"></div>
                  </label>
                </div>

                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-white">Role</span>
                    <p class="text-sm text-gray-400">Change user role</p>
                  </div>
                  <select
                    v-model="formData.role"
                    class="bg-gray-600 text-white rounded-lg px-4 py-2 border border-gray-500 focus:border-purple-500"
                  >
                    <option value="user">User</option>
                    <option value="admin">Administrator</option>
                    <option value="friend">Friend</option>
                    <option value="mod">Moderator</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Кнопки действий -->
            <div class="flex justify-between items-center pt-4 border-t border-gray-600">
              <div class="space-x-4">
                <button
                  type="button"
                  @click="banUser"
                  :disabled="!user?.has_access"
                  class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Block
                </button>
                <button
                  type="button"
                  @click="unbanUser"
                  :disabled="user?.has_access"
                  class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Unblock
                </button>
              </div>
              <button
                type="submit"
                class="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>

        <!-- Вкладка: История платежей -->
        <div v-if="activeTab === 'payments'" class="space-y-6">
          <div class="bg-gray-700 rounded-lg p-4">
            <h4 class="text-lg font-semibold text-white mb-4">Payment History</h4>

            <!-- Загрузка -->
            <div v-if="paymentsLoading" class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-purple-500"></div>
              <p class="mt-2 text-gray-400">Loading payments...</p>
            </div>

            <!-- Список платежей -->
            <div v-else-if="payments.length" class="space-y-3">
              <div
                v-for="payment in payments"
                :key="payment.id"
                class="bg-gray-600 rounded-lg p-4 flex justify-between items-center"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-white font-medium">{{ payment.amount }}₽</span>
                    <span
                      class="px-2 py-1 rounded-full text-xs"
                      :class="getPaymentStatusClass(payment.status)"
                    >
                      {{ formatPaymentStatus(payment.status) }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-400">{{ payment.description || payment.type }}</p>
                  <p class="text-xs text-gray-500">{{ formatDate(payment.created_at) }}</p>
                </div>
                <div class="text-right">
                  <p class="text-sm text-gray-400">{{ formatPaymentType(payment.type) }}</p>
                  <p v-if="payment.external_id" class="text-xs text-gray-500 font-mono">
                    ID: {{ payment.external_id }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Пустое состояние -->
            <div v-else class="text-center py-8">
              <p class="text-gray-400">No payments found</p>
            </div>
          </div>
        </div>

        <!-- Вкладка: Сообщения -->
        <div v-if="activeTab === 'messages'" class="space-y-6">
          <div class="bg-gray-700 rounded-lg p-4">
            <h4 class="text-lg font-semibold text-white mb-4">Send Message</h4>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-400 mb-1">Message</label>
                <textarea
                  v-model="messageText"
                  rows="4"
                  class="w-full bg-gray-600 text-white rounded-lg px-4 py-2 border border-gray-500 focus:border-purple-500"
                  placeholder="Enter message for user..."
                ></textarea>
              </div>
              <div class="flex justify-end">
                <button
                  type="button"
                  @click="sendMessageThroughBot"
                  :disabled="!messageText.trim()"
                  class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send via Telegram bot
                </button>
              </div>
            </div>

            <div class="mt-6 p-4 bg-blue-500/20 rounded-lg">
              <p class="text-blue-300 text-sm">
                <strong>How it works:</strong> When you click the button, a Telegram bot will open where you can send a personal message to this user.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопки закрытия -->
      <div class="flex justify-end gap-4 p-6 border-t border-gray-700 bg-gray-800 sticky bottom-0">
        <button
          type="button"
          @click="$emit('close')"
          class="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X as XIcon } from 'lucide-vue-next'
import type { User } from '../../../types'
import { useMainStore } from '@/store'

interface Props {
  show: boolean
  user: User | null
}

interface Payment {
  id: number
  amount: number
  status: string
  type: string
  description?: string
  external_id?: string
  created_at: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', userData: Partial<User>): void
  (e: 'userUpdated'): void
}>()

const store = useMainStore()

// Состояние вкладок
const activeTab = ref('info')
const tabs = [
  { id: 'info', name: 'Information' },
  { id: 'manage', name: 'Management' },
  { id: 'payments', name: 'Payments' },
  { id: 'messages', name: 'Messages' }
]

// Данные формы
const formData = ref<any>({
  username: '',
  first_name: '',
  last_name: '',
  tariff: null,
  has_access: true,
  role: 'user'
})

// Управление баллами
const pointsChange = ref<number | null>(null)

// История платежей
const payments = ref<Payment[]>([])
const paymentsLoading = ref(false)

// Сообщения
const messageText = ref('')

// Форматирование даты
const formatDate = (date?: string | Date) => {
  if (!date) return 'Not specified'
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Форматирование тарифа
const formatTariff = (tariff: string) => {
  const tariffMap: Record<string, string> = {
    'tariff_2': 'Standard',
    'tariff_4': 'Premium',
    'tariff_6': 'VIP'
  }
  return tariffMap[tariff] || tariff
}

// Форматирование статуса платежа
const formatPaymentStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': 'Completed',
    'pending': 'Pending',
    'failed': 'Failed',
    'cancelled': 'Cancelled'
  }
  return statusMap[status] || status
}

// Форматирование типа платежа
const formatPaymentType = (type: string) => {
  const typeMap: Record<string, string> = {
    'tariff': 'Тариф',
    'points': 'Баллы'
  }
  return typeMap[type] || type
}

// Классы для статуса платежа
const getPaymentStatusClass = (status: string) => {
  const classes = {
    'completed': 'bg-green-500/20 text-green-300',
    'pending': 'bg-yellow-500/20 text-yellow-300',
    'failed': 'bg-red-500/20 text-red-300',
    'cancelled': 'bg-gray-500/20 text-gray-300'
  }
  return classes[status as keyof typeof classes] || 'bg-gray-500/20 text-gray-300'
}

// Загрузка платежей пользователя
const loadUserPayments = async () => {
  if (!props.user?.id) return

  paymentsLoading.value = true
  try {
    const response = await store.getUserPayments(props.user.id)
    payments.value = response || []
  } catch (error) {
    console.error('Error loading user payments:', error)
    // Заглушка для демонстрации при ошибке
    payments.value = [
      {
        id: 1,
        amount: 299,
        status: 'completed',
        type: 'tariff',
        description: 'Standard tariff',
        external_id: 'pay_123456',
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        amount: 100,
        status: 'completed',
        type: 'points',
        description: '100 баллов',
        external_id: 'pay_789012',
        created_at: new Date(Date.now() - 86400000).toISOString()
      }
    ]
  } finally {
    paymentsLoading.value = false
  }
}

// Обновление баллов
const updatePoints = async () => {
  if (!props.user?.id || !pointsChange.value) return

  try {
    await store.updateUserPoints(props.user.id, pointsChange.value)
    console.log(`Updated points for user ${props.user.id}: ${pointsChange.value}`)
    pointsChange.value = null
    emit('userUpdated')
  } catch (error) {
    console.error('Error updating points:', error)
  }
}

// Блокировка пользователя
const banUser = async () => {
  if (!props.user?.id) return

  try {
    formData.value.has_access = false
    await handleSubmit()
  } catch (error) {
    console.error('Error banning user:', error)
  }
}

// Разблокировка пользователя
const unbanUser = async () => {
  if (!props.user?.id) return

  try {
    formData.value.has_access = true
    await handleSubmit()
  } catch (error) {
    console.error('Error unbanning user:', error)
  }
}

// Отправка сообщения через бот
const sendMessageThroughBot = async () => {
  if (!props.user?.id || !messageText.value.trim()) return

  try {
    const response = await store.api.post(`/broadcast/send-to-user/${props.user.id}`, {
      message: messageText.value
    })

    if (response.data.bot_url) {
      // Открываем бот в новой вкладке
      window.open(response.data.bot_url, '_blank')
      messageText.value = ''

      // Показываем уведомление
      alert('Перейдите в открывшуюся вкладку с ботом для отправки сообщения')
    }
  } catch (error) {
    console.error('Error preparing message:', error)
    alert('Ошибка подготовки сообщения')
  }
}

// Старая функция для совместимости
const sendMessage = sendMessageThroughBot

// Обработка отправки формы
const handleSubmit = async () => {
  try {
    emit('save', formData.value)
    emit('userUpdated')
  } catch (error) {
    console.error('Error updating user:', error)
  }
}

// При изменении пользователя обновляем форму
watch(() => props.user, (newUser) => {
  if (newUser) {
    formData.value = { ...newUser }
    // Загружаем платежи при открытии модального окна
    if (props.show) {
      loadUserPayments()
    }
  } else {
    formData.value = {
      telegram_id: 0,
      username: '',
      first_name: '',
      last_name: '',
      role: 'user',
      has_access: true,
      tariff: null
    }
  }
}, { immediate: true })

// Загружаем платежи при переключении на вкладку платежей
watch(activeTab, (newTab) => {
  if (newTab === 'payments' && props.user?.id) {
    loadUserPayments()
  }
})
</script>
