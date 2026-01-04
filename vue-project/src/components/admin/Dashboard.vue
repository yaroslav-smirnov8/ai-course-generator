//components/admin/Dashboard.vue
<template>
  <div class="space-y-6">
    <!-- Общая статистика -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard
        title="Total Users"
        :value="stats.totalUsers"
        :trend="stats.usersTrend"
        icon="Users"
      />
      <StatCard
        title="Active Tariffs"
        :value="stats.activeTariffs"
        :trend="stats.tariffsTrend"
        icon="CreditCard"
      />
      <StatCard
        title="Daily Generations"
        :value="stats.dailyGenerations"
        :trend="stats.generationsTrend"
        icon="Zap"
      />
      <StatCard
        title="Feature Usage"
        :value="stats.featureUsage"
        :trend="stats.usageTrend"
        icon="Activity"
      />
    </div>

    <!-- Графики -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Активность пользователей -->
      <ActivityChart
        title="User Activity"
        :data="activityData"
        :lines="activityChartLines"
      />

      <!-- Использование функций -->
      <Card>
        <CardHeader>
          <CardTitle>Feature Usage</CardTitle>
          <CardDescription>Most used features</CardDescription>
        </CardHeader>
        <CardContent>
          <FeatureUsageChart :data="featureData" />
        </CardContent>
      </Card>
    </div>

    <!-- Недавняя активность -->
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div v-for="activity in recentActivity" :key="activity.id"
               class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-800">
            <div class="flex items-center gap-4">
              <div class="p-2 rounded-full" :class="getActivityColor(activity.type)">
                <component :is="getActivityIcon(activity.type)" class="w-4 h-4" />
              </div>
              <div>
                <p class="text-sm text-gray-300">{{ activity.description }}</p>
                <p class="text-xs text-gray-500">{{ formatDate(activity.timestamp) }}</p>
              </div>
            </div>
            <button class="text-purple-400 hover:text-purple-300">
              Details
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import StatCard from './cards/StatCard.vue'
import ActivityChart from './charts/ActivityChart.vue'
import FeatureUsageChart from './charts/FeatureUsageChart.vue'
import { Users, Activity, AlertTriangle, CreditCard, Zap } from 'lucide-vue-next'
import { apiClient } from '../../api'
import { useMainStore } from '../../store'

const store = useMainStore()

interface DashboardStats {
  totalUsers: number
  usersTrend: number
  activeTariffs: number
  tariffsTrend: number
  dailyGenerations: number
  generationsTrend: number
  featureUsage: number
  usageTrend: number
}

interface ActivityItem {
  id: number
  type: string
  description: string
  timestamp: string
}

const stats = ref<DashboardStats>({
  totalUsers: 0,
  usersTrend: 0,
  activeTariffs: 0,
  tariffsTrend: 0,
  dailyGenerations: 0,
  generationsTrend: 0,
  featureUsage: 0,
  usageTrend: 0
})

const activityData = ref<any[]>([])
const featureData = ref<any[]>([])
const recentActivity = ref<ActivityItem[]>([])

const activityChartLines = [
  { key: 'activeUsers', name: 'Active Users', color: '#8B5CF6' },
  { key: 'generations', name: 'Generations', color: '#34D399' }
]

onMounted(async () => {
  await fetchDashboardData()
})

const fetchDashboardData = async () => {
  try {
    // Используем store вместо прямого запроса к API
    const data = await store.getDashboardData();

    console.log('Dashboard data from store:', data);

    // Check if data has the expected structure
    if (data && data.stats) {
      stats.value = data.stats;
      activityData.value = data.activity || [];
      featureData.value = data.features || [];
      recentActivity.value = data.recent || [];
    } else {
      console.error('Dashboard data has unexpected structure:', data);
      // Provide fallback data
      stats.value = {
        totalUsers: 0,
        usersTrend: 0,
        activeTariffs: 0,
        tariffsTrend: 0,
        dailyGenerations: 0,
        generationsTrend: 0,
        featureUsage: 0,
        usageTrend: 0
      };
      activityData.value = [];
      featureData.value = [];
      recentActivity.value = [];
    }
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    // Provide fallback data on error
    stats.value = {
      totalUsers: 0,
      usersTrend: 0,
      activeTariffs: 0,
      tariffsTrend: 0,
      dailyGenerations: 0,
      generationsTrend: 0,
      featureUsage: 0,
      usageTrend: 0
    };
    activityData.value = [];
    featureData.value = [];
    recentActivity.value = [];
  }
}

const formatDate = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const getActivityColor = (type: string) => {
  const colors = {
    generation: 'bg-purple-500/20 text-purple-400',
    user: 'bg-blue-500/20 text-blue-400',
    tariff: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400'
  }
  return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-400'
}

const getActivityIcon = (type: string) => {
  const icons = {
    generation: Zap,
    user: Users,
    tariff: CreditCard,
    error: AlertTriangle
  }
  return icons[type as keyof typeof icons] || Activity
}
</script>
