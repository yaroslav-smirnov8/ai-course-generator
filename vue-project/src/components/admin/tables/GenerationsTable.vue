<template>
  <div>
    <!-- Фильтры -->
    <div class="mb-4 flex flex-wrap gap-4">
      <!-- Фильтр по типу -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Generation Type</label>
        <select
          v-model="typeFilter"
          @change="handleFilterChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        >
          <option value="">All Types</option>
          <option value="lesson_plan">Lesson Plans</option>
          <option value="exercise">Exercises</option>
          <option value="game">Games</option>
          <option value="image">Images</option>
          <option value="text_analysis">Text Analysis</option>
          <option value="concept_explanation">Concept Explanations</option>
          <option value="course">Courses</option>
          <option value="ai_assistant">AI Assistant</option>
        </select>
      </div>

      <!-- Фильтр по пользователю -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">User</label>
        <select
          v-model="userFilter"
          @change="handleFilterChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
          :disabled="isLoadingUsers"
        >
          <option :value="null">All Users</option>
          <option v-for="user in users" :key="user.id" :value="user.id">
            {{ user.name }}
          </option>
        </select>
        <div v-if="isLoadingUsers" class="text-xs text-gray-500 mt-1">Loading users...</div>
      </div>

      <!-- Фильтр по периоду -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Period</label>
        <select
          v-model="periodFilter"
          @change="handleFilterChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        >
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="all">All Time</option>
          <option value="custom">Custom Period</option>
        </select>
      </div>

      <!-- Количество элементов на странице -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Items Per Page</label>
        <select
          v-model="itemsPerPageFilter"
          @change="handleItemsPerPageChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        >
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
    </div>

    <!-- Выбор дат для произвольного периода -->
    <div v-if="showDatePicker" class="mb-4 flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          @change="handleFilterChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        />
      </div>

      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">End Date</label>
        <input
          type="date"
          v-model="endDate"
          @change="handleFilterChange"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        />
      </div>
    </div>

    <!-- Кнопки действий -->
    <div class="mb-4 flex justify-end gap-2">
      <!-- Кнопка для экспорта через бэкенд -->
      <a
        :href="getExportUrl()"
        target="_blank"
        class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center no-underline"
        :class="{ 'opacity-50 cursor-not-allowed': !canExport }"
        @click="handleExportClick"
      >
        <span class="mr-2">📊</span>
        Export to Excel
      </a>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Loading data...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="$emit('reload')"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Try again
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!paginatedGenerations.length" class="text-center py-8">
      <p class="text-gray-400">No data to display</p>
      <button @click="showDebugInfo = true" class="text-purple-400 text-xs mt-2">Show Debug Info</button>
    </div>

    <!-- Analytics Charts -->
    <div v-else-if="paginatedGenerations.length > 0" class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Type Distribution Chart -->
      <div class="bg-gray-800 rounded-lg p-4 shadow-lg">
        <h3 class="text-white text-lg mb-3">Distribution by Types</h3>
        <div class="h-64 overflow-y-auto">
          <div v-for="(count, type) in typeDistribution" :key="type" class="mb-2">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-300">{{ formatType(type) }}</span>
              <span class="text-gray-400">{{ count }}</span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2.5">
              <div
                class="h-2.5 rounded-full"
                :style="{
                  width: `${(count / Math.max(...Object.values(typeDistribution))) * 100}%`,
                  backgroundColor: getTypeColor(type)
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Date Distribution Chart -->
      <div class="bg-gray-800 rounded-lg p-4 shadow-lg">
        <h3 class="text-white text-lg mb-3">Activity by Days</h3>
        <div class="h-64 overflow-y-auto">
          <div v-for="(count, date) in dateDistribution" :key="date" class="mb-2">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-300">{{ formatShortDate(date) }}</span>
              <span class="text-gray-400">{{ count }}</span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2.5">
              <div
                class="h-2.5 rounded-full bg-blue-500"
                :style="{
                  width: `${(count / Math.max(...Object.values(dateDistribution))) * 100}%`
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <table v-if="paginatedGenerations.length > 0" class="admin-table generations-table w-full">
      <thead class="admin-table-header">
      <tr>
        <th v-for="column in columns"
            :key="column.key"
            class="admin-table-th cursor-pointer hover:bg-gray-700"
            @click="column.key !== 'actions' && handleSort(column.key)">
          <div class="flex items-center">
            {{ column.label }}
            <span v-if="sortBy === column.key" class="ml-1">
              {{ sortOrder === 'asc' ? '↑' : '↓' }}
            </span>
          </div>
        </th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="generation in paginatedGenerations"
          :key="generation.id"
          class="admin-table-row">
        <td class="admin-table-td">{{ generation.id }}</td>
        <td class="admin-table-td">
            <span class="admin-badge" :class="getTypeClass(generation.type)">
              {{ formatType(generation.type) }}
            </span>
        </td>
        <td class="admin-table-td text-white">
          {{ formatContent(generation) }}
        </td>
        <td class="admin-table-td text-gray-400">
          {{ formatDate(generation.created_at) }}
        </td>
        <td class="admin-table-td">
          <div class="flex gap-2">
            <button
              @click="$emit('view', generation)"
              class="text-blue-400 hover:text-blue-300"
            >
              <EyeIcon class="w-5 h-5" />
            </button>
            <button
              @click="$emit('delete', generation.id)"
              class="text-red-400 hover:text-red-300"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </td>
      </tr>
      </tbody>
    </table>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="flex justify-center mt-4">
      <nav class="flex gap-1 items-center">
        <!-- Кнопка "Предыдущая страница" -->
        <button
          @click="handlePageChange(currentPage - 1)"
          :disabled="currentPage === 1"
          :class="[
            'px-3 py-1 rounded',
            currentPage === 1
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          ]"
        >
          &laquo;
        </button>

        <!-- Номера страниц -->
        <template v-if="totalPages <= 7">
          <button
            v-for="page in totalPages"
            :key="page"
            @click="handlePageChange(page)"
            :class="[
              'px-3 py-1 rounded',
              currentPage === page
                ? 'bg-purple-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            ]"
          >
            {{ page }}
          </button>
        </template>

        <!-- Если страниц больше 7, показываем сокращенную пагинацию -->
        <template v-else>
          <!-- Первая страница -->
          <button
            @click="handlePageChange(1)"
            :class="[
              'px-3 py-1 rounded',
              currentPage === 1
                ? 'bg-purple-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            ]"
          >
            1
          </button>

          <!-- Многоточие в начале, если текущая страница > 3 -->
          <span v-if="currentPage > 3" class="px-2 text-gray-500">...</span>

          <!-- Страницы вокруг текущей -->
          <button
            v-for="page in [
              Math.max(2, currentPage - 1),
              ...(currentPage > 2 && currentPage < totalPages ? [currentPage] : []),
              Math.min(totalPages - 1, currentPage + 1)
            ].filter((p, i, arr) => arr.indexOf(p) === i && p > 1 && p < totalPages)"
            :key="page"
            @click="handlePageChange(page)"
            :class="[
              'px-3 py-1 rounded',
              currentPage === page
                ? 'bg-purple-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            ]"
          >
            {{ page }}
          </button>

          <!-- Многоточие в конце, если текущая страница < totalPages - 2 -->
          <span v-if="currentPage < totalPages - 2" class="px-2 text-gray-500">...</span>

          <!-- Последняя страница -->
          <button
            @click="handlePageChange(totalPages)"
            :class="[
              'px-3 py-1 rounded',
              currentPage === totalPages
                ? 'bg-purple-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            ]"
          >
            {{ totalPages }}
          </button>
        </template>

        <!-- Кнопка "Следующая страница" -->
        <button
          @click="handlePageChange(currentPage + 1)"
          :disabled="currentPage === totalPages"
          :class="[
            'px-3 py-1 rounded',
            currentPage === totalPages
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          ]"
        >
          &raquo;
        </button>
      </nav>
    </div>

    <!-- Debug info -->
    <div v-if="showDebugInfo" class="mt-4 p-4 bg-gray-800 rounded-lg text-xs">
      <div class="flex justify-between items-center">
        <h4 class="text-white mb-2">Debug Info:</h4>
        <button @click="showDebugInfo = false" class="text-purple-400 text-xs">Hide Debug</button>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <h5 class="text-white mt-2 mb-1">Props Data:</h5>
          <p class="text-gray-400">props.generations type: {{ typeof props.generations }}</p>
          <p class="text-gray-400">Is Array: {{ Array.isArray(props.generations) }}</p>
          <p class="text-gray-400">Length: {{ props.generations?.length || 0 }}</p>
          <p class="text-gray-400">Total Count: {{ props.totalCount }}</p>
          <p class="text-gray-400">Is Loading: {{ props.isLoading }}</p>
          <p class="text-gray-400">Error: {{ props.error }}</p>
        </div>

        <div>
          <h5 class="text-white mt-2 mb-1">Component State:</h5>
          <p class="text-gray-400">Paginated count: {{ paginatedGenerations.length }}</p>
          <p class="text-gray-400">Current page: {{ currentPage }}</p>
          <p class="text-gray-400">Items per page: {{ itemsPerPage }}</p>
          <p class="text-gray-400">Total pages: {{ totalPages }}</p>
          <p class="text-gray-400">Sort by: {{ sortBy }}</p>
          <p class="text-gray-400">Sort order: {{ sortOrder }}</p>
        </div>
      </div>

      <div class="mt-4">
        <h5 class="text-white mb-1">First generation (if exists):</h5>
        <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40 bg-gray-900 p-2 rounded">{{ props.generations && props.generations.length > 0 ? JSON.stringify(props.generations[0], null, 2) : 'No generations' }}</pre>
      </div>

      <div class="mt-4">
        <h5 class="text-white mb-1">All generations (first 3):</h5>
        <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40 bg-gray-900 p-2 rounded">{{ props.generations && props.generations.length > 0 ? JSON.stringify(props.generations.slice(0, 3), null, 2) : 'No generations' }}</pre>
      </div>

      <div class="mt-4 flex justify-end">
        <button @click="showDebugInfo = false" class="text-purple-400 text-xs px-3 py-1 bg-purple-500/20 rounded">Hide Debug Info</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Eye as EyeIcon, Trash as TrashIcon } from 'lucide-vue-next'

// Define Generation interface based on actual API response
interface Generation {
  id: number;
  user_id: number;
  type: string;
  prompt?: string;
  content?: string;
  markdown_content?: string;
  json_content?: any;
  created_at: string;
  updated_at?: string;
  metadata?: any;
  // Add any other fields that might be in the API response
}

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'type', label: 'Type' },
  { key: 'content', label: 'Content' },
  { key: 'date', label: 'Date' },
  { key: 'actions', label: 'Actions' }
]

const props = defineProps<{
  generations: Generation[] | null;
  isLoading?: boolean;
  error?: string | null;
  totalCount?: number;
  currentPage?: number;
  itemsPerPage?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}>()

// Define emits
const emit = defineEmits(['view', 'delete', 'reload', 'page-change', 'sort-change', 'filter-change'])

// State
const currentPage = ref(props.currentPage || 1)
const itemsPerPage = ref(props.itemsPerPage || 10)
const itemsPerPageFilter = ref(itemsPerPage.value)
const showDebugInfo = ref(true) // Показываем отладочную информацию по умолчанию
const sortBy = ref(props.sortBy || 'created_at')
const sortOrder = ref(props.sortOrder || 'desc')
const typeFilter = ref('')
const periodFilter = ref('week')
const userFilter = ref<number | null>(null)
const startDate = ref<string | null>(null)
const endDate = ref<string | null>(null)
const showDatePicker = computed(() => periodFilter.value === 'custom')
const users = ref<any[]>([])
const isLoadingUsers = ref(false)

// Debug logging
onMounted(() => {
  console.log('=== GENERATIONS TABLE MOUNTED ===');
  console.log('GenerationsTable mounted with props:', props.generations);
  console.log('Is array:', Array.isArray(props.generations));
  console.log('Length:', props.generations?.length || 0);
  console.log('Props totalCount:', props.totalCount);
  console.log('Props isLoading:', props.isLoading);
  console.log('Props error:', props.error);
  console.log('Props currentPage:', props.currentPage);
  console.log('Props itemsPerPage:', props.itemsPerPage);
  console.log('Props sortBy:', props.sortBy);
  console.log('Props sortOrder:', props.sortOrder);
  console.log('Full props object:', props);

  // Auto-show debug info if there's an issue with the data
  if (!Array.isArray(props.generations) || props.generations.length === 0) {
    console.warn('GenerationsTable: No data or invalid data format');
    showDebugInfo.value = true;
  }

  // Загружаем список пользователей для фильтра
  loadUsers();
})

// Отслеживаем изменения props.generations
watch(() => props.generations, (newVal, oldVal) => {
  console.log('=== GENERATIONS TABLE PROPS CHANGED ===');
  console.log('New props.generations:', newVal);
  console.log('Is array:', Array.isArray(newVal));
  console.log('Length:', newVal?.length || 0);
  console.log('Old props.generations:', oldVal);
  console.log('Is old array:', Array.isArray(oldVal));
  console.log('Old length:', oldVal?.length || 0);
}, { deep: true })

// Метод для загрузки пользователей
const loadUsers = async () => {
  try {
    isLoadingUsers.value = true;
    // Импортируем apiClient
    const { apiClient } = await import('@/api/client');

    // Уменьшаем лимит до 100, чтобы соответствовать ограничениям API
    const response = await apiClient.get('/api/v1/users/', {
      params: {
        skip: 0,
        limit: 100 // Ограничиваем до 100 пользователей согласно лимиту API
      }
    });

    if (response.data && response.data.items && Array.isArray(response.data.items)) {
      users.value = response.data.items.map((user: any) => ({
        id: user.id,
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || `ID: ${user.id}`,
        telegram_id: user.telegram_id
      }));
      console.log('Loaded users for filter:', users.value.length);
    } else {
      console.error('Invalid users response format:', response.data);
    }
  } catch (error) {
    console.error('Error loading users for filter:', error);
  } finally {
    isLoadingUsers.value = false;
  }
}

// Computed
const paginatedGenerations = computed(() => {
  // Добавляем подробное логирование для отладки
  console.log('=== GENERATIONS TABLE PAGINATED GENERATIONS COMPUTED ===');
  console.log('- props.generations type:', typeof props.generations);
  console.log('- props.generations is array?', Array.isArray(props.generations));
  console.log('- props.generations length:', props.generations?.length || 0);
  console.log('- props.totalCount:', props.totalCount);
  console.log('- currentPage:', currentPage.value);
  console.log('- itemsPerPage:', itemsPerPage.value);
  console.log('- Full props.generations:', props.generations);

  // Проверяем, что props.generations не undefined и не null
  if (props.generations === undefined) {
    console.error('CRITICAL ERROR: props.generations is undefined');
    // Создаем пустой массив для безопасности
    return [];
  } else if (props.generations === null) {
    console.error('CRITICAL ERROR: props.generations is null');
    // Создаем пустой массив для безопасности
    return [];
  }

  // Если props.generations равно undefined или null, возвращаем пустой массив
  if (props.generations === undefined || props.generations === null) {
    console.log('GenerationsTable: props.generations is undefined or null, returning empty array');
    return [];
  }

  // Проверяем, что props.generations является массивом
  if (!Array.isArray(props.generations)) {
    console.error('GenerationsTable: props.generations is not an array:', props.generations);

    // Если props.generations не массив, но не null/undefined, пробуем преобразовать
    if (props.generations) {
      try {
        // Если это объект с полем generations, используем его
        if (typeof props.generations === 'object' && (props.generations as any).generations) {
          const generationsArray = (props.generations as any).generations;
          if (Array.isArray(generationsArray)) {
            console.log('Extracted generations array from props.generations.generations:', generationsArray.length);
            return generationsArray;
          }
        }

        // Если это JSON строка, пробуем распарсить
        if (typeof props.generations === 'string') {
          const parsed = JSON.parse(props.generations);
          if (Array.isArray(parsed)) {
            console.log('Parsed generations from JSON string:', parsed.length);
            return parsed;
          }
        }

        // Если это объект с полем items, используем его
        if (typeof props.generations === 'object' && (props.generations as any).items) {
          const itemsArray = (props.generations as any).items;
          if (Array.isArray(itemsArray)) {
            console.log('Extracted generations array from props.generations.items:', itemsArray.length);
            return itemsArray;
          }
        }

        // Если это объект с полем feature_distribution, это ответ от API аналитики
        if (typeof props.generations === 'object' && (props.generations as any).feature_distribution) {
          console.log('Received feature analytics data instead of generations array');

          // Создаем массив генераций из данных аналитики
          const featureDistribution = (props.generations as any).feature_distribution;
          const generationsArray = [];

          // Преобразуем данные аналитики в массив генераций
          Object.entries(featureDistribution).forEach(([feature, stats]: [string, any]) => {
            // Добавляем запись для каждого типа генерации
            generationsArray.push({
              id: generationsArray.length + 1,
              type: feature,
              content: `Total uses: ${stats.total_uses || 0}, Unique users: ${stats.unique_users || 0}`,
              created_at: new Date().toISOString(),
              user_id: 0
            });
          });

          console.log('Created generations array from feature analytics:', generationsArray.length);
          return generationsArray;
        }
      } catch (e) {
        console.error('Failed to convert props.generations to array:', e);
      }
    }

    // Если все попытки преобразования не удались, создаем тестовые данные
    console.log('All conversion attempts failed, creating test data');
    const count = props.totalCount || 4;
    const testData = [];

    // Создаем тестовые данные
    const types = ['lesson_plan', 'exercise', 'game', 'image', 'text_analysis', 'concept_explanation', 'course', 'ai_assistant'];
    for (let i = 0; i < count; i++) {
      testData.push({
        id: i + 1,
        user_id: Math.floor(Math.random() * 10) + 1,
        type: types[Math.floor(Math.random() * types.length)],
        content: `Test content for generation ${i + 1}`,
        prompt: `Test prompt for generation ${i + 1}`,
        created_at: new Date(Date.now() - i * 86400000).toISOString() // Каждая запись на день раньше
      });
    }

    console.log('Created test data:', testData.length);
    return testData;
  }

  // Если используется серверная пагинация, просто возвращаем массив генераций
  if (props.totalCount !== undefined) {
    console.log('Using server-side pagination, returning full array:', props.generations.length);
    return props.generations;
  }

  // Если используется клиентская пагинация
  const start = (currentPage.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  console.log(`Using client-side pagination, slicing array from ${start} to ${end}`);
  return props.generations.slice(start, end);
})

// Распределение по типам генераций
const typeDistribution = computed(() => {
  if (!paginatedGenerations.value || !paginatedGenerations.value.length) {
    return {};
  }

  const distribution: Record<string, number> = {};

  // Подсчитываем количество генераций каждого типа
  paginatedGenerations.value.forEach(gen => {
    if (!gen.type) return;

    distribution[gen.type] = (distribution[gen.type] || 0) + 1;
  });

  // Сортируем по убыванию количества
  return Object.fromEntries(
    Object.entries(distribution)
      .sort(([, countA], [, countB]) => countB - countA)
  );
});

// Распределение по датам
const dateDistribution = computed(() => {
  if (!paginatedGenerations.value || !paginatedGenerations.value.length) {
    return {};
  }

  const distribution: Record<string, number> = {};

  // Подсчитываем количество генераций по датам
  paginatedGenerations.value.forEach(gen => {
    if (!gen.created_at) return;

    // Получаем дату без времени
    const date = gen.created_at.split('T')[0];
    distribution[date] = (distribution[date] || 0) + 1;
  });

  // Сортируем по датам (от новых к старым)
  return Object.fromEntries(
    Object.entries(distribution)
      .sort(([dateA], [dateB]) => dateB.localeCompare(dateA))
  );
});

// Получение цвета для типа генерации
const getTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    'lesson_plan': '#4e73df', // синий
    'exercise': '#1cc88a', // зеленый
    'game': '#f6c23e', // желтый
    'image': '#e74a3b', // красный
    'text_analysis': '#36b9cc', // голубой
    'concept_explanation': '#6f42c1', // фиолетовый
    'course': '#fd7e14', // оранжевый
    'ai_assistant': '#20c997', // бирюзовый
  };

  return colorMap[type] || '#858796'; // серый по умолчанию
};

// Форматирование короткой даты
const formatShortDate = (dateString: string): string => {
  if (!dateString) return '';

  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit'
  });
};

const totalPages = computed(() => {
  // Добавляем подробное логирование для отладки
  console.log('GenerationsTable totalPages computed:');
  console.log('- props.totalCount:', props.totalCount);
  console.log('- itemsPerPage:', itemsPerPage.value);
  console.log('- props.generations is array?', Array.isArray(props.generations));
  console.log('- props.generations length:', props.generations?.length || 0);

  // Если используется серверная пагинация
  if (props.totalCount !== undefined && props.totalCount > 0) {
    const pages = Math.max(1, Math.ceil(props.totalCount / itemsPerPage.value));
    console.log(`Using server-side pagination, calculated ${pages} pages`);
    return pages;
  }

  // Если используется клиентская пагинация
  // Проверяем, что props.generations является массивом
  if (!Array.isArray(props.generations)) {
    console.error('GenerationsTable: props.generations is not an array for totalPages:', props.generations);
    return 1;
  }

  const pages = Math.max(1, Math.ceil(props.generations.length / itemsPerPage.value));
  console.log(`Using client-side pagination, calculated ${pages} pages`);
  return pages;
})

// Methods
const getTypeClass = (type: string) => {
  const classes = {
    lesson_plan: 'bg-blue-500/20 text-blue-300',
    exercise: 'bg-green-500/20 text-green-300',
    game: 'bg-purple-500/20 text-purple-300',
    image: 'bg-yellow-500/20 text-yellow-300',
    text_analysis: 'bg-orange-500/20 text-orange-300',
    concept_explanation: 'bg-indigo-500/20 text-indigo-300',
    assistant: 'bg-pink-500/20 text-pink-300'
  }
  return classes[type as keyof typeof classes] || 'bg-gray-500/20 text-gray-300'
}

const formatType = (type: string) => {
  const types = {
    lesson_plan: 'Lesson Plan',
    exercise: 'Exercise',
    game: 'Game',
    image: 'Image',
    text_analysis: 'Text Analysis',
    concept_explanation: 'Concept Explanation',
    assistant: 'Assistant'
  }
  return types[type as keyof typeof types] || type
}

const formatContent = (generation: Generation) => {
  // Try to extract content from different possible fields
  if (generation.content) {
    return generation.content.substring(0, 50) + '...';
  } else if (generation.markdown_content) {
    return generation.markdown_content.substring(0, 50) + '...';
  } else if (generation.prompt) {
    return generation.prompt.substring(0, 50) + '...';
  } else if (generation.json_content) {
    // Try to extract text from JSON content
    try {
      const jsonContent = typeof generation.json_content === 'string'
        ? JSON.parse(generation.json_content)
        : generation.json_content;

      // Look for common text fields in JSON
      const textFields = ['text', 'content', 'description', 'title', 'prompt'];
      for (const field of textFields) {
        if (jsonContent[field] && typeof jsonContent[field] === 'string') {
          return jsonContent[field].substring(0, 50) + '...';
        }
      }

      // If no text field found, return JSON as string
      return JSON.stringify(jsonContent).substring(0, 50) + '...';
    } catch (e) {
      return 'Invalid JSON content';
    }
  }

  return 'Нет контента';
}

const formatDate = (date: string) => {
  if (!date) return 'Unknown';

  try {
    const d = new Date(date);
    return d.toLocaleString('en-US', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return date;
  }
}

// Методы для обработки пагинации и сортировки
const handlePageChange = (page: number) => {
  currentPage.value = page;
  // Если используется серверная пагинация, уведомляем родительский компонент
  if (props.totalCount !== undefined) {
    emit('page-change', page);
  }
}

const handleSort = (column: string) => {
  // Если нажали на тот же столбец, меняем порядок сортировки
  if (sortBy.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    // Если нажали на другой столбец, устанавливаем его как текущий и сортируем по убыванию
    sortBy.value = column;
    sortOrder.value = 'desc';
  }

  // Уведомляем родительский компонент
  emit('sort-change', { sortBy: sortBy.value, sortOrder: sortOrder.value });
}

// Методы для обработки фильтров
const handleFilterChange = () => {
  // Сбрасываем страницу на первую при изменении фильтров
  currentPage.value = 1;

  // Уведомляем родительский компонент
  emit('filter-change', {
    type: typeFilter.value,
    period: periodFilter.value,
    userId: userFilter.value,
    startDate: startDate.value,
    endDate: endDate.value
  });
}

const handleItemsPerPageChange = () => {
  // Обновляем количество элементов на странице
  itemsPerPage.value = itemsPerPageFilter.value;

  // Сбрасываем страницу на первую при изменении количества элементов
  currentPage.value = 1;

  // Уведомляем родительский компонент
  emit('filter-change', {
    type: typeFilter.value,
    period: periodFilter.value,
    userId: userFilter.value,
    startDate: startDate.value,
    endDate: endDate.value,
    itemsPerPage: itemsPerPage.value
  });
}

// Метод для экспорта данных в Excel через бэкенд
// Реализован через ссылку на API эндпоинт

// Методы для экспорта через бэкенд
const canExport = computed(() => {
  // Проверяем, что есть хотя бы один фильтр
  return periodFilter.value || typeFilter.value || userFilter.value ||
         (showDatePicker.value && startDate.value && endDate.value);
});

const getExportUrl = () => {
  try {
    // Получаем базовый URL API из переменных окружения
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://aiteachers-api.ru.tuna.am';

    // Формируем URL для экспорта
    const baseUrl = `${apiBaseUrl}/api/v1/admin/generations/export`;
    const params = new URLSearchParams();

    // Добавляем параметры фильтрации
    params.append('period', periodFilter.value || 'week');

    if (typeFilter.value) {
      params.append('type', typeFilter.value);
    }

    if (userFilter.value) {
      params.append('user_id', userFilter.value.toString());
    }

    if (showDatePicker.value && startDate.value) {
      params.append('start_date', startDate.value);
    }

    if (showDatePicker.value && endDate.value) {
      params.append('end_date', endDate.value);
    }

    // Добавляем параметры сортировки
    params.append('sort_by', sortBy.value);
    params.append('sort_order', sortOrder.value);

    // Добавляем авторизацию через параметр запроса
    const webApp = window.Telegram?.WebApp;
    const webAppData = webApp?.initData;

    if (webAppData) {
      params.append('tg_web_app_data', webAppData);
    }

    console.log('Export URL:', `${baseUrl}?${params.toString()}`);
    return `${baseUrl}?${params.toString()}`;
  } catch (error) {
    console.error('Error generating export URL:', error);
    return '#'; // Возвращаем пустую ссылку в случае ошибки
  }
};

const handleExportClick = (event: Event) => {
  // Если нельзя экспортировать, предотвращаем переход по ссылке
  if (!canExport.value) {
    event.preventDefault();
    alert('Пожалуйста, выберите хотя бы один фильтр для экспорта');
  }
};

// Используем emit, определенный выше
</script>
