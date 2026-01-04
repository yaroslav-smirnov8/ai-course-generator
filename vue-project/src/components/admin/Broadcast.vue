<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-white">Message Broadcast</h2>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
      >
        Create Broadcast
      </button>
    </div>

    <!-- Статистика -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-gray-800 p-4 rounded-lg">
        <h3 class="text-sm text-gray-400 mb-1">Total Messages</h3>
        <p class="text-2xl font-bold text-white">{{ statistics.total_messages || 0 }}</p>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <h3 class="text-sm text-gray-400 mb-1">Sent</h3>
        <p class="text-2xl font-bold text-green-400">{{ statistics.sent_messages || 0 }}</p>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <h3 class="text-sm text-gray-400 mb-1">Pending</h3>
        <p class="text-2xl font-bold text-yellow-400">{{ statistics.pending_messages || 0 }}</p>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <h3 class="text-sm text-gray-400 mb-1">Success Rate</h3>
        <p class="text-2xl font-bold text-blue-400">{{ statistics.success_rate || 0 }}%</p>
      </div>
    </div>

    <!-- История рассылок -->
    <div class="bg-gray-800 rounded-lg overflow-hidden">
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-lg font-semibold text-white">Broadcast History</h3>
      </div>
      
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
        <p class="text-gray-400 mt-2">Loading...</p>
      </div>

      <div v-else-if="history.length === 0" class="p-8 text-center text-gray-400">
        No broadcasts yet
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-900">
            <tr>
              <th class="p-4">ID</th>
              <th class="p-4">Type</th>
              <th class="p-4">Message</th>
              <th class="p-4">Status</th>
              <th class="p-4">Recipients</th>
              <th class="p-4">Date</th>
              <th class="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in history"
              :key="item.id"
              class="border-t border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-4">{{ item.id }}</td>
              <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="item.is_personal ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'"
                >
                  {{ item.is_personal ? 'Personal' : 'Broadcast' }}
                </span>
              </td>
              <td class="p-4 max-w-xs">
                <div class="truncate" :title="item.message_text">
                  {{ item.message_text || 'No text' }}
                </div>
              </td>
              <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="item.is_sent ? 'bg-green-500/20 text-green-300' : 'bg-yellow-500/20 text-yellow-300'"
                >
                  {{ item.is_sent ? 'Sent' : 'Pending' }}
                </span>
              </td>
              <td class="p-4">
                <div v-if="item.is_sent" class="text-sm">
                  <div class="text-green-400">✓ {{ item.success_count || 0 }}</div>
                  <div v-if="item.error_count > 0" class="text-red-400">✗ {{ item.error_count }}</div>
                </div>
                <div v-else class="text-gray-400">-</div>
              </td>
              <td class="p-4 text-sm text-gray-400">
                {{ formatDate(item.created_at) }}
              </td>
              <td class="p-4">
                <button
                  v-if="!item.is_sent"
                  @click="sendBroadcast(item)"
                  class="text-green-400 hover:text-green-300 px-3 py-1 rounded-lg border border-green-400 hover:bg-green-400/10 mr-2"
                >
                  Send
                </button>
                <button
                  @click="viewDetails(item)"
                  class="text-purple-400 hover:text-purple-300 px-3 py-1 rounded-lg border border-purple-400 hover:bg-purple-400/10"
                >
                  Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модальное окно создания рассылки -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-800 rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center p-6 border-b border-gray-700">
          <h3 class="text-xl font-semibold text-white">Create Broadcast</h3>
          <button @click="showCreateModal = false" class="text-gray-400 hover:text-white">
            <XIcon class="w-6 h-6" />
          </button>
        </div>

        <div class="p-6">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">
              Message Text
            </label>
            <textarea
              v-model="newBroadcast.message"
              rows="4"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:border-purple-500"
              placeholder="Enter message text..."
            ></textarea>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">
              Photo URL (optional)
            </label>
            <input
              v-model="newBroadcast.photo_url"
              type="url"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:border-purple-500"
              placeholder="https://example.com/image.jpg"
            />
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">
              Photo Caption (optional)
            </label>
            <input
              v-model="newBroadcast.photo_caption"
              type="text"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:border-purple-500"
              placeholder="Image caption"
            />
          </div>

          <div class="mb-6">
            <label class="flex items-center">
              <input
                v-model="newBroadcast.scheduled"
                type="checkbox"
                class="mr-2"
              />
              <span class="text-gray-300">Schedule sending</span>
            </label>
            
            <div v-if="newBroadcast.scheduled" class="mt-2">
              <input
                v-model="newBroadcast.scheduled_time"
                type="datetime-local"
                class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:border-purple-500"
              />
            </div>
          </div>

          <div class="flex justify-end gap-4">
            <button
              @click="showCreateModal = false"
              class="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              @click="createBroadcast"
              :disabled="!newBroadcast.message.trim()"
              class="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { X as XIcon } from 'lucide-vue-next'
import { useMainStore } from '@/store'

const store = useMainStore()

// State
const loading = ref(false)
const showCreateModal = ref(false)
const statistics = ref({
  total_messages: 0,
  sent_messages: 0,
  pending_messages: 0,
  success_rate: 0
})
const history = ref([])

const newBroadcast = ref({
  message: '',
  photo_url: '',
  photo_caption: '',
  scheduled: false,
  scheduled_time: ''
})

// Methods
const loadStatistics = async () => {
  try {
    const response = await store.api.get('/broadcast/statistics')
    statistics.value = response.data
  } catch (error) {
    console.error('Error loading statistics:', error)
  }
}

const loadHistory = async () => {
  loading.value = true
  try {
    const response = await store.api.get('/broadcast/history')
    history.value = response.data
  } catch (error) {
    console.error('Error loading history:', error)
  } finally {
    loading.value = false
  }
}

const createBroadcast = async () => {
  try {
    const payload = {
      message: newBroadcast.value.message,
      photo_url: newBroadcast.value.photo_url || null,
      photo_caption: newBroadcast.value.photo_caption || null,
      scheduled_time: newBroadcast.value.scheduled ? newBroadcast.value.scheduled_time : null
    }

    const response = await store.api.post('/broadcast/broadcast', payload)
    
    if (response.data.bot_url) {
      // Открываем бот в новой вкладке
      window.open(response.data.bot_url, '_blank')
    }

    showCreateModal.value = false
    newBroadcast.value = {
      message: '',
      photo_url: '',
      photo_caption: '',
      scheduled: false,
      scheduled_time: ''
    }

    // Обновляем данные
    await loadHistory()
    await loadStatistics()

  } catch (error) {
    console.error('Error creating broadcast:', error)
    alert('Ошибка создания рассылки')
  }
}

const sendBroadcast = async (item: any) => {
  try {
    const botUrl = `https://t.me/neuro_teacher_bot?start=send_broadcast_${item.id}`
    window.open(botUrl, '_blank')
  } catch (error) {
    console.error('Error sending broadcast:', error)
  }
}

const viewDetails = (item: any) => {
  // Показать детали рассылки
  alert(`Детали рассылки ID: ${item.id}\n\nТекст: ${item.message_text}\nСтатус: ${item.is_sent ? 'Отправлено' : 'В ожидании'}`)
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadStatistics()
  loadHistory()
})
</script>
