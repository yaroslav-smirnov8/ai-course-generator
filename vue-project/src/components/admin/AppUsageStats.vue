<template>
  <div class="app-usage-stats">
    <div class="section-header">
      <h2>Статистика использования приложения</h2>
      <p>Подробная информация о том, как пользователи взаимодействуют с приложением</p>
    </div>

    <div class="filters">
      <div class="filter-group">
        <label>Period:</label>
        <select v-model="period" @change="loadStats">
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="year">Year</option>
          <option value="all">All Time</option>
        </select>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-rocket"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalLaunches }}</div>
          <div class="stat-label">Запусков приложения</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-eye"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalPageViews }}</div>
          <div class="stat-label">Просмотров страниц</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-mouse-pointer"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalActions }}</div>
          <div class="stat-label">Действий пользователей</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatTime(stats.averageSessionDuration) }}</div>
          <div class="stat-label">Средняя длительность сессии</div>
        </div>
      </div>
    </div>

    <div class="charts-container">
      <div class="chart-wrapper">
        <h3>Использование по страницам</h3>
        <div class="chart">
          <canvas ref="pageViewsChart"></canvas>
        </div>
      </div>

      <div class="chart-wrapper">
        <h3>Использование по платформам</h3>
        <div class="chart">
          <canvas ref="platformsChart"></canvas>
        </div>
      </div>
    </div>

    <div class="charts-container">
      <div class="chart-wrapper">
        <h3>Популярные действия пользователей</h3>
        <div class="chart">
          <canvas ref="actionsChart"></canvas>
        </div>
      </div>

      <div class="chart-wrapper">
        <h3>Конверсия действий</h3>
        <div class="chart">
          <canvas ref="conversionChart"></canvas>
        </div>
      </div>
    </div>

    <div class="table-container">
      <h3>Последние события</h3>
      <table class="events-table">
        <thead>
          <tr>
            <th>Время</th>
            <th>Пользователь</th>
            <th>Событие</th>
            <th>Страница</th>
            <th>Действие</th>
            <th>Платформа</th>
            <th>Детали</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(event, index) in events" :key="index">
            <td>{{ formatDate(event.timestamp) }}</td>
            <td>{{ event.user_id }}</td>
            <td>{{ formatEventType(event.event) }}</td>
            <td>{{ event.page || '-' }}</td>
            <td>{{ event.action || '-' }}</td>
            <td>{{ event.platform || '-' }}</td>
            <td>
              <button v-if="event.details" @click="showDetails(event)" class="details-btn">
                Подробнее
              </button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDetailsModal" class="details-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Детали события</h3>
          <button @click="showDetailsModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <pre>{{ JSON.stringify(selectedEventDetails, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import Chart from 'chart.js/auto'

const store = useMainStore()

// Состояние компонента
const period = ref('week')
const stats = ref({
  totalLaunches: 0,
  totalPageViews: 0,
  totalActions: 0,
  averageSessionDuration: 0,
  usageByPlatform: {},
  usageByPage: {},
  usageByAction: {}
})
const events = ref([])
const showDetailsModal = ref(false)
const selectedEventDetails = ref(null)

// Ссылки на элементы canvas для графиков
const pageViewsChart = ref(null)
const platformsChart = ref(null)
const actionsChart = ref(null)
const conversionChart = ref(null)

// Экземпляры графиков
let pageViewsChartInstance = null
let platformsChartInstance = null
let actionsChartInstance = null
let conversionChartInstance = null

// Загрузка статистики
const loadStats = async () => {
  try {
    // В реальном приложении здесь будет запрос к API с учетом выбранного периода
    // Для демонстрации используем данные из store
    await store.getAppUsageStats()
    stats.value = store.appUsageStats
    events.value = store.appUsageEvents.slice(-20).reverse() // Последние 20 событий в обратном порядке
    
    // Обновляем графики
    updateCharts()
  } catch (error) {
    console.error('Error loading app usage stats:', error)
  }
}

// Обновление графиков
const updateCharts = () => {
  updatePageViewsChart()
  updatePlatformsChart()
  updateActionsChart()
  updateConversionChart()
}

// Обновление графика просмотров страниц
const updatePageViewsChart = () => {
  if (pageViewsChartInstance) {
    pageViewsChartInstance.destroy()
  }
  
  const ctx = pageViewsChart.value.getContext('2d')
  const data = {
    labels: Object.keys(stats.value.usageByPage),
    datasets: [{
      label: 'Просмотры страниц',
      data: Object.values(stats.value.usageByPage),
      backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)'
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)'
      ],
      borderWidth: 1
    }]
  }
  
  pageViewsChartInstance = new Chart(ctx, {
    type: 'bar',
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Просмотры страниц'
        }
      }
    }
  })
}

// Обновление графика использования по платформам
const updatePlatformsChart = () => {
  if (platformsChartInstance) {
    platformsChartInstance.destroy()
  }
  
  const ctx = platformsChart.value.getContext('2d')
  const data = {
    labels: Object.keys(stats.value.usageByPlatform),
    datasets: [{
      label: 'Использование по платформам',
      data: Object.values(stats.value.usageByPlatform),
      backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)'
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)'
      ],
      borderWidth: 1
    }]
  }
  
  platformsChartInstance = new Chart(ctx, {
    type: 'pie',
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Использование по платформам'
        }
      }
    }
  })
}

// Обновление графика действий пользователей
const updateActionsChart = () => {
  if (actionsChartInstance) {
    actionsChartInstance.destroy()
  }
  
  const ctx = actionsChart.value.getContext('2d')
  const data = {
    labels: Object.keys(stats.value.usageByAction),
    datasets: [{
      label: 'Действия пользователей',
      data: Object.values(stats.value.usageByAction),
      backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)'
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)'
      ],
      borderWidth: 1
    }]
  }
  
  actionsChartInstance = new Chart(ctx, {
    type: 'bar',
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Действия пользователей'
        }
      }
    }
  })
}

// Обновление графика конверсии действий
const updateConversionChart = () => {
  if (conversionChartInstance) {
    conversionChartInstance.destroy()
  }
  
  // Для демонстрации создаем данные о конверсии
  // В реальном приложении эти данные должны приходить с сервера
  const conversionData = {
    labels: ['Launch', 'Course View', 'Lesson Opening', 'Task Completion', 'Purchase'],
    datasets: [{
      label: 'Action Conversion',
      data: [100, 80, 60, 40, 20],
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 1,
      fill: true
    }]
  }
  
  const ctx = conversionChart.value.getContext('2d')
  conversionChartInstance = new Chart(ctx, {
    type: 'line',
    data: conversionData,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Конверсия действий'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%'
            }
          }
        }
      }
    }
  })
}

// Форматирование времени
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

// Форматирование даты
const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US')
}

// Форматирование типа события
const formatEventType = (eventType) => {
  const eventTypes = {
    'app_launch': 'App Launch',
    'page_view': 'Page View',
    'user_action': 'User Action',
    'session_end': 'Session End'
  }
  return eventTypes[eventType] || eventType
}

// Показать детали события
const showDetails = (event) => {
  selectedEventDetails.value = event.details
  showDetailsModal.value = true
}

// Загружаем статистику при монтировании компонента
onMounted(() => {
  loadStats()
})

// Следим за изменением периода
watch(period, () => {
  loadStats()
})
</script>

<style scoped>
.app-usage-stats {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.section-header {
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 24px;
  margin-bottom: 5px;
}

.section-header p {
  color: #666;
  margin: 0;
}

.filters {
  display: flex;
  margin-bottom: 20px;
  background-color: #fff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.filter-group {
  margin-right: 20px;
  display: flex;
  align-items: center;
}

.filter-group label {
  margin-right: 10px;
  font-weight: 500;
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fff;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #f0f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: #3b82f6;
  font-size: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-wrapper {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chart-wrapper h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 18px;
}

.chart {
  height: 300px;
}

.table-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
}

.table-container h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 18px;
}

.events-table {
  width: 100%;
  border-collapse: collapse;
}

.events-table th,
.events-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.events-table th {
  background-color: #f9f9f9;
  font-weight: 500;
}

.events-table tr:last-child td {
  border-bottom: none;
}

.details-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.details-btn:hover {
  background-color: #2563eb;
}

.details-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: #fff;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 80vh;
  overflow: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.modal-body pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow: auto;
  font-family: monospace;
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .stats-cards {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .filters {
    flex-direction: column;
  }
  
  .filter-group {
    margin-right: 0;
    margin-bottom: 10px;
  }
}
</style> 