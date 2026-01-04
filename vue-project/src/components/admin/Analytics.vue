<template>
  <div class="space-y-6">
    <PageHeader
      title="Аналитика"
      subtitle="Подробная аналитика использования платформы"
    >
      <template #actions>
        <div class="flex gap-4">
          <select
            v-model="timeRange"
            class="px-4 py-2 bg-gray-700 text-white rounded-lg"
            :disabled="isLoading"
          >
            <option value="day">Last 24 hours</option>
            <option value="week">Last 7 days</option>
            <option value="month">Last 30 days</option>
          </select>
          <Button @click="exportAnalytics" :disabled="isLoading || isExporting">
            <span v-if="isExporting" class="inline-flex items-center">
              <span class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></span>
              Exporting...
            </span>
            <span v-else>
              <DownloadIcon class="w-4 h-4 mr-2" />
              Export Report
            </span>
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Loading analytics data...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="loadAnalytics"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Try Again
      </button>
    </div>

    <div v-else>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard
        title="Total Users"
        :value="stats.totalUsers"
        :trend="stats.usersTrend"
        icon="Users"
      />
      <StatCard
        title="Active Users"
        :value="stats.activeUsers"
        :trend="stats.activeUsersTrend"
        icon="UserCheck"
      />
      <StatCard
        title="Total Generations"
        :value="stats.totalGenerations"
        :trend="stats.generationsTrend"
        icon="Zap"
      />
      <StatCard
        title="Success Rate"
        :value="`${stats.successRate}%`"
        :trend="stats.successRateTrend"
        icon="CheckCircle"
      />
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Activity Chart -->
      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Activity Over Time</h3>
        <ActivityChart
          title="Activity Over Time"
          :data="activityData"
          :lines="[
    { key: 'generations', name: 'Generations', color: '#8B5CF6' },
    { key: 'activeUsers', name: 'Active Users', color: '#10B981' }
  ]"
        />
      </PageContent>

      <!-- Usage Distribution -->
      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Usage Distribution</h3>
        <GenerationsPieChart :data="generationsData" />
      </PageContent>
    </div>

    <!-- Feature Usage Analytics -->
    <PageContent>
      <div class="space-y-4">
        <h3 class="text-lg font-medium text-white mb-4">Feature Usage</h3>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-900">
            <tr>
              <th class="p-4 text-left text-gray-400">Feature</th>
              <th class="p-4 text-left text-gray-400">Total Uses</th>
              <th class="p-4 text-left text-gray-400">Unique Users</th>
              <th class="p-4 text-left text-gray-400">Success Rate</th>
              <th class="p-4 text-left text-gray-400">Avg Time</th>
            </tr>
            </thead>
            <tbody>
            <tr
              v-for="feature in featureAnalytics?.mostPopular"
              :key="feature.feature"
              class="border-t border-gray-700"
            >
              <td class="p-4 text-white">{{ formatFeatureName(feature.feature) }}</td>
              <td class="p-4 text-gray-300">{{ feature.count }}</td>
              <td class="p-4 text-gray-300">{{ feature.uniqueUsers }}</td>
              <td class="p-4">
                  <span
                    class="px-2 py-1 rounded-full text-xs"
                    :class="getSuccessRateClass(feature.successRate)"
                  >
                    {{ feature.successRate.toFixed(1) }}%
                  </span>
              </td>
              <td class="p-4 text-gray-300">{{ formatTime(feature.averageTime) }}</td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>
    </PageContent>

    <!-- User Distribution -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Distribution by Role</h3>
        <div class="h-80">
          <PieChart width={400} height={300}>
            <Pie
              data={roleDistributionData.value}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
            >
              {roleDistributionData.value.map((entry, index) => (
              <Cell key={entry.name} fill={ROLE_COLORS[index % ROLE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </div>
      </PageContent>

      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Distribution by Tariff</h3>
        <div class="h-80">
          <PieChart width={400} height={300}>
            <Pie
              data={tariffDistributionData.value}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
            >
              {tariffDistributionData.value.map((entry, index) => (
              <Cell key={entry.name} fill={TARIFF_COLORS[index % TARIFF_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </div>
      </PageContent>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed, watch} from 'vue'
import { useMainStore } from '@/store'
import {
  Download as DownloadIcon,
  Users,
  UserCheck,
  Zap,
  CheckCircle
} from 'lucide-vue-next'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts'
import PageHeader from './common/PageHeader.vue'
import PageContent from './PageContent.vue'
import StatCard from './cards/StatCard.vue'
import ActivityChart from './charts/ActivityChart.vue'
import GenerationsPieChart from './charts/GenerationsPieChart.vue'
import { Button } from '@/components/ui/button'
import type { FeatureAnalytics } from '@/types'

// Constants
const ROLE_COLORS = ['#8B5CF6', '#10B981', '#F59E0B']
const TARIFF_COLORS = ['#3B82F6', '#6366F1', '#8B5CF6']

const store = useMainStore()

interface DataPoint {
  day: string;
  generations: number;
  activeUsers: number;
}

interface GenerationDataPoint {
  name: string;
  value: number;
}


// UI state
const isLoading = ref(false);
const isExporting = ref(false);
const error = ref<string | null>(null);

// Data state
const timeRange = ref('week')
const stats = ref({
  totalUsers: 0,
  usersTrend: 0,
  activeUsers: 0,
  activeUsersTrend: 0,
  totalGenerations: 0,
  generationsTrend: 0,
  successRate: 0,
  successRateTrend: 0
})
const featureAnalytics = ref<FeatureAnalytics | null>(null)
const activityData = ref<DataPoint[]>([]);
const generationsData = ref<GenerationDataPoint[]>([]);

// Computed
const roleDistributionData = computed(() => {
  if (!featureAnalytics.value?.userDistribution.byRole) return []

  return Object.entries(featureAnalytics.value.userDistribution.byRole).map(([role, count]) => ({
    name: role,
    value: count
  }))
})

const tariffDistributionData = computed(() => {
  if (!featureAnalytics.value?.userDistribution.byTariff) return []

  return Object.entries(featureAnalytics.value.userDistribution.byTariff).map(([tariff, count]) => ({
    name: tariff,
    value: count
  }))
})

// Methods
const loadAnalytics = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    // Get feature analytics
    const analyticsResponse = await store.getFeatureUsageAnalytics(timeRange.value);

    if (analyticsResponse) {
      featureAnalytics.value = analyticsResponse;
      console.log('Successfully loaded feature analytics');

      // Update stats
      stats.value = {
        totalUsers: analyticsResponse.uniqueUsers || 0,
        usersTrend: 5.2, // Hardcoded for now
        activeUsers: analyticsResponse.totalUsage || 0,
        activeUsersTrend: 3.1, // Hardcoded for now
        totalGenerations: analyticsResponse.totalUsage || 0,
        generationsTrend: 7.5, // Hardcoded for now
        successRate: 98.5, // Hardcoded for now
        successRateTrend: 0.5 // Hardcoded for now
      };

      // Update generations data
      if (analyticsResponse.featureDistribution) {
        const genData: GenerationDataPoint[] = Object.entries(analyticsResponse.featureDistribution)
          .map(([type, data]) => ({
            name: type,
            value: data.count
          }));
        generationsData.value = genData;
        console.log('Successfully loaded generations data:', genData.length);
      } else {
        console.warn('No feature distribution data in response');
        generationsData.value = [];
      }
    } else {
      console.error('No feature analytics data in response');
      featureAnalytics.value = null;
      generationsData.value = [];
    }

    // Load activity data
    try {
      const activity = await store.getActivityData(timeRange.value);

      if (Array.isArray(activity)) {
        activityData.value = activity;
        console.log('Successfully loaded activity data:', activity.length);
      } else {
        console.warn('Activity data is not an array:', activity);
        activityData.value = [];
      }
    } catch (err: any) {
      console.error('Error loading activity data:', err);
      activityData.value = [];
      // Don't set error here to allow partial data display
    }

  } catch (err: any) {
    console.error('Error loading analytics:', err);
    error.value = `Error loading analytics: ${err.message || 'Unknown error'}`;

    // Reset data
    featureAnalytics.value = null;
    generationsData.value = [];
    activityData.value = [];
  } finally {
    isLoading.value = false;
  }
};

const exportAnalytics = async () => {
  if (isExporting.value) return;

  isExporting.value = true;

  try {
    await store.exportData('analytics', 'csv');
    console.log('Successfully exported analytics data');
  } catch (err: any) {
    console.error('Error exporting analytics:', err);
    error.value = `Error exporting analytics: ${err.message || 'Unknown error'}`;
  } finally {
    isExporting.value = false;
  }
};

const formatFeatureName = (feature: string): string => {
  return feature
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const getSuccessRateClass = (rate: number): string => {
  if (rate >= 95) return 'bg-green-500/20 text-green-300'
  if (rate >= 90) return 'bg-yellow-500/20 text-yellow-300'
  return 'bg-red-500/20 text-red-300'
}

const formatTime = (seconds: number): string => {
  return `${seconds.toFixed(1)}s`
}

// Watch for time range changes
watch(timeRange, loadAnalytics)

// Initialize
onMounted(loadAnalytics)
</script>

<style scoped>
.recharts-wrapper {
  margin: 0 auto;
}
</style>
