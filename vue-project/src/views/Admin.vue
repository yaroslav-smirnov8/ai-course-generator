<!-- src/views/Admin.vue -->
<template>
  <div class="admin-view min-h-screen bg-gray-900">
    <!-- Верхняя панель -->
    <header class="bg-gray-800 shadow-lg">
      <div class="flex justify-between items-center px-6 py-4">
        <h1 class="text-2xl font-bold text-white">Admin Panel</h1>
        <div class="flex items-center gap-4">
          <button
            @click="toggleDarkMode"
            class="p-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600"
          >
            <span v-if="isDarkMode">🌞</span>
            <span v-else>🌙</span>
          </button>
          <div class="text-gray-300">
            Administrator: {{ currentAdmin?.name }}
          </div>
        </div>
      </div>
    </header>

    <div class="flex">
      <!-- Боковая навигация -->
      <aside class="w-64 bg-gray-800 min-h-screen">
        <nav class="p-4 space-y-2">
          <button
            v-for="section in sections"
            :key="section.id"
            @click="currentSection = section.id"
            class="w-full flex items-center px-4 py-3 rounded-lg text-left"
            :class="currentSection === section.id
              ? 'bg-purple-500 text-white'
              : 'text-gray-300 hover:bg-gray-700'"
          >
            <component :is="section.icon" class="w-5 h-5 mr-3" />
            {{ section.name }}
          </button>
        </nav>
      </aside>

      <!-- Основной контент -->
      <main class="flex-1 p-6">
        <!-- Сообщение об ошибке доступа -->
        <div v-if="accessError" class="bg-red-500/20 text-red-300 p-6 rounded-lg mb-6">
          <h2 class="text-xl font-bold mb-2">Access Error</h2>
          <p>{{ accessError }}</p>
          <p class="mt-2 text-sm">You need appropriate permissions to access the admin panel.</p>
        </div>

        <!-- Dashboard -->
        <div v-if="!accessError && currentSection === 'dashboard'" class="space-y-6">
          <!-- Debug button -->
          <div class="flex justify-end">
            <button
              @click="showDebugInfo = !showDebugInfo"
              class="text-gray-500 text-xs hover:text-gray-400"
            >
              {{ showDebugInfo ? 'Hide Debug Info' : 'Show Debug Info' }}
            </button>
          </div>

          <!-- Debug info -->
          <div v-if="showDebugInfo" class="mb-4 p-4 bg-gray-700 rounded-lg text-xs">
            <div class="flex justify-between items-center">
              <h4 class="text-white mb-2">Dashboard Debug Info:</h4>
              <button @click="showDebugInfo = false" class="text-gray-400 hover:text-white">
                Скрыть
              </button>
            </div>
            <p class="text-gray-400">users type: {{ typeof users }}</p>
            <p class="text-gray-400">users Is Array: {{ Array.isArray(users) }}</p>
            <p class="text-gray-400">users Length: {{ users?.length || 0 }}</p>
            <p class="text-gray-400">generations type: {{ typeof generations }}</p>
            <p class="text-gray-400">generations Is Array: {{ Array.isArray(generations) }}</p>
            <p class="text-gray-400">generations Length: {{ generations?.length || 0 }}</p>
            <p class="text-gray-400">generationStats: {{ generationStats ? 'exists' : 'null' }}</p>
            <p class="text-gray-400">generationStats.by_type: {{ generationStats?.by_type ? 'exists' : 'null' }}</p>
            <p class="text-gray-400">dashboardStats: {{ dashboardStats.length }} items</p>
            <p class="text-gray-400">activityData: {{ activityData.length }} items</p>
            <p class="text-gray-400">generationsData: {{ generationsData.length }} items</p>
            <button
              @click="loadTestDashboardData"
              class="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg"
            >
              Load Test Data
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              v-for="stat in dashboardStats"
              :key="stat.title"
              v-bind="stat"
            />
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-800 rounded-lg p-6">
              <h3 class="text-lg font-medium text-white mb-4">Weekly Activity</h3>
              <ActivityChartNew
                :data="activityData"
              />
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
              <h3 class="text-lg font-medium text-white mb-4">Generation Distribution</h3>

              <!-- Debug info for generationsData -->
              <div v-if="showDebugInfo" class="mb-4 p-4 bg-gray-700 rounded-lg text-xs">
                <div class="flex justify-between items-center">
                  <h4 class="text-white mb-2">GenerationsData Debug Info:</h4>
                  <button @click="showDebugInfo = false" class="text-gray-400 hover:text-white">
                    Hide
                  </button>
                </div>
                <p class="text-gray-400">generationsData type: {{ typeof generationsData }}</p>
                <p class="text-gray-400">Is Array: {{ Array.isArray(generationsData) }}</p>
                <p class="text-gray-400">Length: {{ generationsData?.length || 0 }}</p>
                <p class="text-gray-400">generationsData content:</p>
                <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40">{{ JSON.stringify(generationsData, null, 2) }}</pre>
                <button
                  @click="loadTestDashboardData"
                  class="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg"
                >
                  Load Test Data
                </button>
              </div>

              <GenerationsPieChartNew :data="generationsData" />
            </div>
          </div>
        </div>

        <!-- Пользователи -->
        <div v-if="!accessError && currentSection === 'users'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Users</h2>
            <div class="flex gap-4">
              <input
                v-model="userSearch"
                type="text"
                placeholder="Search..."
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
              </select>
            </div>
          </div>

          <!-- Loading state -->
          <div v-if="isLoadingUsers" class="bg-gray-800 rounded-lg p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
            <p class="mt-2 text-gray-400">Loading users...</p>
          </div>

          <!-- Error state -->
          <div v-else-if="usersError" class="bg-gray-800 rounded-lg p-6">
            <div class="bg-red-500/20 text-red-300 p-4 rounded-lg">
              <p>{{ usersError }}</p>
              <button
                @click="loadUsers"
                class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
              >
                Try again
              </button>
            </div>
          </div>

          <!-- Users table -->
          <div v-else class="bg-gray-800 rounded-lg overflow-hidden">
            <!-- Empty state -->
            <div v-if="!filteredUsers.length" class="text-center py-8">
              <p class="text-gray-400">No data to display</p>
              <p class="text-gray-500 text-xs mt-2">filteredUsers.length: {{ filteredUsers?.length || 0 }}</p>
              <p class="text-gray-500 text-xs">users.value.length: {{ users.value?.length || 0 }}</p>
              <button
                @click="forceRenderUsers"
                class="mt-4 px-4 py-2 bg-purple-500 text-white rounded-lg"
              >
                Force display users
              </button>
            </div>

            <table v-else class="w-full text-left">
              <thead class="bg-gray-900">
              <tr>
                <th class="p-4">ID</th>
                <th class="p-4">Telegram</th>
                <th class="p-4">Name</th>
                <th class="p-4">Role</th>
                <th class="p-4">Plan</th>
                <th class="p-4">Status</th>
                <th class="p-4">Actions</th>
              </tr>
              </thead>
              <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                class="border-t border-gray-700 hover:bg-gray-700/50"
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
                    @click="editUser(user)"
                    class="text-purple-400 hover:text-purple-300"
                  >
                    Edit
                  </button>
                </td>
              </tr>
              </tbody>
            </table>
          </div>

          <!-- Debug button -->
          <button
            @click="showDebugInfo = !showDebugInfo"
            class="mt-4 text-gray-500 text-xs hover:text-gray-400"
          >
            {{ showDebugInfo ? 'Hide Debug Info' : 'Show Debug Info' }}
          </button>

          <!-- Debug info -->
          <div v-if="showDebugInfo" class="mt-2 p-4 bg-gray-700 rounded-lg text-xs">
            <h4 class="text-white mb-2">Users Debug Info:</h4>
            <p class="text-gray-400">filteredUsers type: {{ typeof filteredUsers }}</p>
            <p class="text-gray-400">Is Array: {{ Array.isArray(filteredUsers) }}</p>
            <p class="text-gray-400">Length: {{ filteredUsers?.length || 0 }}</p>
            <p class="text-gray-400">users.value type: {{ typeof users.value }}</p>
            <p class="text-gray-400">users.value Is Array: {{ Array.isArray(users.value) }}</p>
            <p class="text-gray-400">users.value Length: {{ users.value?.length || 0 }}</p>
            <p class="text-gray-400">First user (if exists):</p>
            <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40">{{ users.value && users.value.length > 0 ? JSON.stringify(users.value[0], null, 2) : 'No users' }}</pre>
          </div>
        </div>

        <!-- Генерации -->
        <div v-if="!accessError && currentSection === 'generations'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Generation History</h2>
            <div class="flex gap-4">
              <select
                v-model="generationType"
                class="px-4 py-2 bg-gray-700 text-white rounded-lg"
              >
                <option value="all">All types</option>
                <option value="lesson_plan">Lesson plans</option>
                <option value="exercise">Exercises</option>
                <option value="game">Games</option>
                <option value="image">Images</option>
              </select>
            </div>
          </div>

          <!-- Графики статистики генераций -->
          <GenerationsChart
            :initialPeriod="generationsPeriodFilter"
            :generations="generations.value"
            :generationStats="generationStats"
          />

          <!-- Таблица генераций -->
          <div class="bg-gray-800 rounded-lg p-6 mt-6">
            <!-- Debug info for generations -->
            <div v-if="showDebugInfo" class="mb-4 p-4 bg-gray-700 rounded-lg text-xs">
              <div class="flex justify-between items-center">
                <h4 class="text-white mb-2">Generations Debug Info:</h4>
                <button @click="showDebugInfo = false" class="text-gray-400 hover:text-white">
                  Скрыть
                </button>
              </div>
              <p class="text-gray-400">generations.value type: {{ typeof generations.value }}</p>
              <p class="text-gray-400">Is Array: {{ Array.isArray(generations.value) }}</p>
              <p class="text-gray-400">Length: {{ generations.value?.length || 0 }}</p>
              <p class="text-gray-400">Total Count: {{ generationsTotal }}</p>
              <p class="text-gray-400">Current Page: {{ generationsPage }}</p>
              <p class="text-gray-400">Items Per Page: {{ generationsLimit }}</p>
              <p class="text-gray-400">Sort By: {{ generationsSortBy }}</p>
              <p class="text-gray-400">Sort Order: {{ generationsSortOrder }}</p>
              <p class="text-gray-400">Type Filter: {{ generationsTypeFilter }}</p>
              <p class="text-gray-400">Period Filter: {{ generationsPeriodFilter }}</p>
              <p class="text-gray-400">First generation (if exists):</p>
              <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40">{{ generations.value && generations.value.length > 0 ? JSON.stringify(generations.value[0], null, 2) : 'No generations' }}</pre>
            </div>

            <div class="flex justify-end mb-4">
              <button @click="showDebugInfo = !showDebugInfo" class="text-xs text-gray-400 hover:text-white">
                {{ showDebugInfo ? 'Hide Debug Info' : 'Show Debug Info' }}
              </button>
            </div>

            <GenerationsTable
              :generations="getGenerationsForTable()"
              :isLoading="isLoadingGenerations"
              :error="generationsError"
              :totalCount="generationsTotal"
              :currentPage="generationsPage"
              :itemsPerPage="generationsLimit"
              :sortBy="generationsSortBy"
              :sortOrder="generationsSortOrder"
              @view="viewGeneration"
              @reload="loadGenerations"
              @page-change="handleGenerationsPageChange"
              @sort-change="handleGenerationsSortChange"
              @filter-change="handleGenerationsFilterChange"
            />

            <!-- Отладочная информация о передаваемых данных -->
            <div v-if="showDebugInfo" class="mt-4 p-4 bg-gray-700 rounded-lg text-xs">
              <div class="flex justify-between items-center">
                <h4 class="text-white mb-2">Data Passed to GenerationsTable:</h4>
                <button @click="showDebugInfo = false" class="text-gray-400 hover:text-white">
                  Скрыть
                </button>
              </div>
              <p class="text-gray-400">generations: {{ Array.isArray(generations.value) ? `Array[${generations.value.length}]` : typeof generations.value }}</p>
              <p class="text-gray-400">isLoading: {{ isLoadingGenerations }}</p>
              <p class="text-gray-400">error: {{ generationsError }}</p>
              <p class="text-gray-400">totalCount: {{ generationsTotal }}</p>
              <p class="text-gray-400">currentPage: {{ generationsPage }}</p>
              <p class="text-gray-400">itemsPerPage: {{ generationsLimit }}</p>
              <p class="text-gray-400">sortBy: {{ generationsSortBy }}</p>
              <p class="text-gray-400">sortOrder: {{ generationsSortOrder }}</p>
            </div>
          </div>
        </div>

        <!-- Тарифы -->
        <div v-if="!accessError && currentSection === 'tariffs'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Plan Management</h2>
          </div>

          <!-- График распределения пользователей по тарифам -->
          <TariffDistributionChart :users="users" />

          <!-- Аналитика использования тарифов -->
          <div class="mb-6">
            <h3 class="text-lg font-medium text-white mb-4">Plan Usage Analytics</h3>
            <TariffsAnalytics />
          </div>

          <!-- Отладочная информация о тарифах -->
          <div v-if="showDebugInfo" class="mb-4 p-4 bg-gray-700 rounded-lg text-xs">
            <div class="flex justify-between items-center">
              <h4 class="text-white mb-2">Tariffs Debug Info:</h4>
              <button @click="showDebugInfo = false" class="text-gray-400 hover:text-white">
                Скрыть
              </button>
            </div>
            <p class="text-gray-400">tariffs type: {{ typeof tariffs }}</p>
            <p class="text-gray-400">Is Array: {{ Array.isArray(tariffs) }}</p>
            <p class="text-gray-400">Length: {{ tariffs?.length || 0 }}</p>
            <p class="text-gray-400">users type: {{ typeof users }}</p>
            <p class="text-gray-400">users Is Array: {{ Array.isArray(users) }}</p>
            <p class="text-gray-400">users Length: {{ users?.length || 0 }}</p>
            <p class="text-gray-400">First tariff (if exists):</p>
            <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40">{{ tariffs && tariffs.length > 0 ? JSON.stringify(tariffs[0], null, 2) : 'No tariffs' }}</pre>
            <p class="text-gray-400">First user (if exists):</p>
            <pre class="text-gray-400 text-xs mt-2 overflow-auto max-h-40">{{ users && users.length > 0 ? JSON.stringify(users[0], null, 2) : 'No users' }}</pre>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <TariffCard
              v-for="tariff in tariffs"
              :key="tariff.id"
              :tariff="tariff"
              @edit="editTariff"
              @toggle="toggleTariff"
            />
          </div>
        </div>

        <!-- Достижения -->
        <div v-if="!accessError && currentSection === 'achievements'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Achievement System</h2>
          </div>

          <!-- Аналитика достижений -->
          <div class="mb-6">
            <h3 class="text-lg font-medium text-white mb-4">Achievement Analytics</h3>
            <AchievementsAnalytics />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AchievementCard
              v-for="achievement in achievements"
              :key="achievement.id"
              :achievement="achievement"
            />
          </div>
        </div>

        <!-- Промокоды -->
        <div v-if="!accessError && currentSection === 'promocodes'" class="space-y-6">
          <PromocodesManager />
          <PromoUsageHistory />
          <PromocodesStats />
        </div>

        <!-- Баллы -->
        <div v-if="!accessError && currentSection === 'points'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Points Usage Analytics</h2>
          </div>
          <PointsAnalytics />
        </div>

        <!-- Переходы по ссылкам -->
        <div v-if="!accessError && currentSection === 'links'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Link Click Statistics</h2>
          </div>
          <LinksAnalytics />
        </div>

        <!-- Рассылка -->
        <div v-if="!accessError && currentSection === 'broadcast'" class="space-y-6">
          <Broadcast />
        </div>


        <!-- Аналитика -->
        <div v-if="!accessError && currentSection === 'analytics'" class="space-y-6">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Analytics</h2>
          </div>

          <!-- Вкладки для разных типов аналитики -->
          <div class="border-b border-gray-700 mb-6">
            <div class="flex space-x-4 overflow-x-auto">

              <button
                @click="analyticsTab = 'feature'"
                class="py-2 px-4 border-b-2 font-medium text-sm whitespace-nowrap"
                :class="analyticsTab === 'feature'
                  ? 'border-purple-500 text-purple-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'"
              >
                Feature Usage
              </button>
              <button
                @click="analyticsTab = 'financial'"
                class="py-2 px-4 border-b-2 font-medium text-sm whitespace-nowrap"
                :class="analyticsTab === 'financial'
                  ? 'border-purple-500 text-purple-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'"
              >
                Financial Analytics
              </button>
              <button
                @click="analyticsTab = 'time'"
                class="py-2 px-4 border-b-2 font-medium text-sm whitespace-nowrap"
                :class="analyticsTab === 'time'
                  ? 'border-purple-500 text-purple-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'"
              >
                Time Activity
              </button>

            </div>
          </div>



          <!-- Содержимое вкладки "Использование функций" -->
          <div v-if="analyticsTab === 'feature'">
            <FeatureUsageAnalytics />
          </div>

          <!-- Содержимое вкладки "Финансовая аналитика" -->
          <div v-if="analyticsTab === 'financial'">
            <FinancialAnalytics />
          </div>

          <!-- Содержимое вкладки "Активность по времени" -->
          <div v-if="analyticsTab === 'time'">
            <TimeActivityAnalytics />
          </div>


        </div>
      </main>
    </div>

    <!-- Модальные окна -->
    <UserModal
      v-if="selectedUser"
      :user="selectedUser"
      :show="showUserModal"
      @close="closeUserModal"
      @save="saveUser"
    />

    <TariffModal
      v-if="showTariffModal"
      :tariff="selectedTariff"
      @close="closeTariffModal"
      @save="saveTariff"
    />


  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import {
  Users, Activity, Settings, ChartBar, Award,
  CreditCard, FileText, Zap, Link, MessageSquare
} from 'lucide-vue-next'


// Components
import StatCard from '../components/admin/cards/StatCard.vue'
import ActivityChartNew from '../components/admin/charts/ActivityChartNew.vue'
import GenerationsPieChartNew from '../components/admin/charts/GenerationsPieChartNew.vue'
import GenerationsTable from '../components/admin/tables/GenerationsTable.vue'
import GenerationsChart from '../components/admin/charts/GenerationsChart.vue'
import PointsAnalytics from '../components/admin/PointsAnalytics.vue'
import TariffDistributionChart from '../components/admin/charts/TariffDistributionChart.vue'
import TariffsAnalytics from '../components/admin/TariffsAnalytics.vue'
import AchievementsAnalytics from '../components/admin/AchievementsAnalytics.vue'
import LinksAnalytics from '../components/admin/LinksAnalytics.vue'
import UserModal from '../components/admin/modals/UserModal.vue'
import TariffModal from '../components/admin/modals/TariffModal.vue'
import TariffCard from '../components/admin/cards/TariffCard.vue'
import AchievementCard from '../components/admin/cards/AchievementCard.vue'
import FeatureUsageAnalytics from "../components/admin/FeatureUsageAnalytics.vue"
import FinancialAnalytics from "../components/admin/FinancialAnalytics.vue"
import TimeActivityAnalytics from "../components/admin/TimeActivityAnalytics.vue"

import PromocodesManager from "../components/admin/settings/PromocodesManager.vue"
import PromoUsageHistory from "../components/admin/settings/PromoUsageHistory.vue"
import PromocodesStats from "../components/admin/settings/PromocodesStats.vue"
import SystemSettings from "../components/admin/settings/SystemSettings.vue"
import Broadcast from "../components/admin/Broadcast.vue"


import { UserRole, ContentType, TariffType } from '../core/constants'
import type {
  User,
  Tariff,
  Achievement,
  Generation,
  AdminStats,
  UserStatistics,
  GenerationStatistics
} from '../types'

const store = useMainStore()

interface ChartDataPoint {
  day: string
  generations: number
  activeUsers: number
  [key: string]: any
}


// State
const currentSection = ref('dashboard')
const isDarkMode = ref(false)
const userSearch = ref('')
const userFilter = ref('all')
const generationType = ref('all')
const showUserModal = ref(false)
const showTariffModal = ref(false)
const featureUsageData = ref<any>(null)
const showDebugInfo = ref(true)
const analyticsTab = ref('feature')

const selectedUser = ref<User | null>(null)
const selectedTariff = ref<Tariff | null>(null)

// Data
const users = ref<User[]>([])
const tariffs = ref<Tariff[]>([])
const achievements = ref<Achievement[]>([])
const generations = ref<Generation[]>([])
const adminStats = ref<AdminStats | null>(null)
const userStats = ref<UserStatistics | null>(null)
const generationStats = ref<GenerationStatistics | null>({
  total_generations: 0,
  by_type: {
    lesson_plan: 0,
    exercise: 0,
    game: 0,
    image: 0,
    text_analysis: 0,
    concept_explanation: 0,
    course: 0,
    ai_assistant: 0
  },
  popular_prompts: []
})


// Состояние для пагинации, фильтрации и сортировки генераций
const generationsPage = ref(1)
const generationsLimit = ref(10)
const generationsTotal = ref(0)
const generationsSortBy = ref('created_at')
const generationsSortOrder = ref<'asc' | 'desc'>('desc')
const generationsTypeFilter = ref('')
const generationsPeriodFilter = ref('week')
const generationsUserFilter = ref<number | null>(null)
const generationsStartDate = ref<string | null>(null)
const generationsEndDate = ref<string | null>(null)
const showCustomDatePicker = ref(false)

// Loading states
const isLoadingUsers = ref(false)
const isLoadingTariffs = ref(false)
const isLoadingAchievements = ref(false)
const isLoadingGenerations = ref(false)
const isLoadingFeatureUsage = ref(false)

// Error states
const accessError = ref<string | null>(null) // Ошибка доступа к админ-панели
const usersError = ref<string | null>(null)
const tariffsError = ref<string | null>(null)
const achievementsError = ref<string | null>(null)
const generationsError = ref<string | null>(null)
const featureUsageError = ref<string | null>(null)

// Navigation sections
const sections = [
  { id: 'dashboard', name: 'Dashboard', icon: ChartBar },
  { id: 'users', name: 'Users', icon: Users },
  { id: 'generations', name: 'Generations', icon: Zap },
  { id: 'tariffs', name: 'Plans', icon: CreditCard },
  { id: 'points', name: 'Points', icon: CreditCard },
  { id: 'achievements', name: 'Achievements', icon: Award },
  { id: 'analytics', name: 'Analytics', icon: Activity },
  { id: 'promocodes', name: 'Promo Codes', icon: CreditCard },
  { id: 'links', name: 'Link Clicks', icon: Link },
  { id: 'broadcast', name: 'Broadcast', icon: MessageSquare }
]



// Computed
const currentAdmin = computed(() => store.user)

const filteredUsers = computed(() => {
  console.log('=== FILTERED USERS COMPUTED ===');
  console.log('users.value:', users.value);
  console.log('users.value type:', typeof users.value);
  console.log('users.value is array:', Array.isArray(users.value));
  console.log('users.value length:', users.value.length);

  let result = users.value

  if (userSearch.value) {
    const search = userSearch.value.toLowerCase()
    result = result.filter(user => {
      if (!user || typeof user !== 'object') {
        console.error('Invalid user object in filter:', user);
        return false;
      }

      return (
        (user.first_name && user.first_name.toLowerCase().includes(search)) ||
        (user.last_name && user.last_name.toLowerCase().includes(search)) ||
        (user.telegram_id && user.telegram_id.toString().includes(search))
      );
    });
  }

  if (userFilter.value !== 'all') {
    result = result.filter(user => {
      if (!user || typeof user !== 'object') {
        console.error('Invalid user object in role filter:', user);
        return false;
      }

      return user.role === userFilter.value;
    });
  }

  console.log('Filtered result:', result);
  console.log('Filtered result length:', result.length);

  return result
})

const filteredGenerations = computed(() => {
  // Проверяем, что generations.value - это массив
  if (!Array.isArray(generations.value)) {
    console.error('generations.value is not an array:', generations.value);
    return [];
  }

  if (generationType.value === 'all') return generations.value;
  return generations.value.filter(gen => gen.type === generationType.value);
})

// Methods
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark')
}

// Принудительно отобразить пользователей
const forceRenderUsers = () => {
  console.log('=== FORCE RENDER USERS ===');
  console.log('Current users.value:', users.value);

  // Принудительно устанавливаем тестовых пользователей для отладки
  const testUsers = [
    {
      id: 1,
      telegram_id: 7057999903,
      first_name: 'Тестовый',
      last_name: 'Пользователь',
      username: 'test_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'basic',
      tariff_valid_until: null,
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 2,
      telegram_id: 952210109,
      first_name: 'Ярослав',
      last_name: '| Python Dev | English Teacher',
      username: 'yaroslav_english',
      role: 'admin',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: null,
      tariff_valid_until: null,
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    }
  ];

  console.log('Setting test users for debugging:', testUsers);
  users.value = testUsers;

  // Принудительно обновляем computed-свойство filteredUsers
  console.log('Filtered users after update:', filteredUsers.value);
}

// Загрузка тестовых данных для дашборда
const loadTestDashboardData = () => {
  console.log('=== LOAD TEST DASHBOARD DATA ===');

  // Создаем тестовые данные пользователей
  const testUsers = [
    {
      id: 1,
      telegram_id: 7057999903,
      first_name: 'Пользователь',
      last_name: 'Базовый',
      username: 'basic_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: false,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'basic',
      tariff_valid_until: null,
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 2,
      telegram_id: 952210109,
      first_name: 'Пользователь',
      last_name: 'Стандарт',
      username: 'standard_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_2',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 3,
      telegram_id: 952210110,
      first_name: 'Пользователь',
      last_name: 'Премиум',
      username: 'premium_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_4',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 4,
      telegram_id: 952210111,
      first_name: 'Пользователь',
      last_name: 'VIP',
      username: 'vip_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_6',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 5,
      telegram_id: 952210112,
      first_name: 'Пользователь',
      last_name: 'Без тарифа',
      username: 'no_tariff_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: false,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: null,
      tariff_valid_until: null,
      points: 0,
      created_at: new Date().toISOString(),
      last_active: new Date().toISOString()
    }
  ];

  // Создаем тестовые данные генераций
  const testGenerations = [];
  const types = ['lesson_plan', 'exercise', 'game', 'image', 'text_analysis', 'concept_explanation', 'course', 'ai_assistant'];

  // Создаем генерации за последние 7 дней
  for (let i = 0; i < 7; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    // Создаем разное количество генераций для каждого дня
    const count = Math.floor(Math.random() * 5) + 1; // 1-5 генераций в день

    for (let j = 0; j < count; j++) {
      const type = types[Math.floor(Math.random() * types.length)];
      const userId = Math.floor(Math.random() * 5) + 1; // ID пользователя от 1 до 5

      testGenerations.push({
        id: testGenerations.length + 1,
        user_id: userId,
        type: type,
        content: `Test ${type} content`,
        prompt: `Test prompt for ${type}`,
        created_at: new Date(date).toISOString(),
        updated_at: new Date(date).toISOString()
      });
    }
  }

  // Создаем тестовые данные статистики генераций
  const testGenerationStats = {
    total_generations: testGenerations.length,
    by_type: {}
  };

  // Подсчитываем количество генераций по типам
  testGenerations.forEach(gen => {
    testGenerationStats.by_type[gen.type] = (testGenerationStats.by_type[gen.type] || 0) + 1;
  });

  console.log('Setting test users:', testUsers.length);
  users.value = testUsers;

  console.log('Setting test generations:', testGenerations.length);
  generations.value = testGenerations;

  console.log('Setting test generation stats:', testGenerationStats);
  generationStats.value = testGenerationStats;

  // Показываем уведомление об успешной загрузке
  alert('Тестовые данные для дашборда успешно загружены');
}

// Загрузка тестовых тарифов
const loadTestTariffs = () => {
  console.log('=== LOAD TEST TARIFFS ===');

  // Создаем тестовые тарифы для отладки
  const testTariffs = [
    {
      id: 1,
      name: 'Базовый',
      code: 'basic',
      price: 0,
      description: 'Базовый тариф без дополнительных возможностей',
      features: ['Базовые функции'],
      daily_generations: 3,
      is_active: true
    },
    {
      id: 2,
      name: 'Стандарт',
      code: 'tariff_2',
      price: 299,
      description: 'Стандартный тариф с расширенными возможностями',
      features: ['Базовые функции', 'Расширенные функции'],
      daily_generations: 10,
      is_active: true
    },
    {
      id: 3,
      name: 'Премиум',
      code: 'tariff_4',
      price: 599,
      description: 'Премиум тариф с максимальными возможностями',
      features: ['Базовые функции', 'Расширенные функции', 'Премиум функции'],
      daily_generations: 30,
      is_active: true
    },
    {
      id: 4,
      name: 'VIP',
      code: 'tariff_6',
      price: 999,
      description: 'VIP тариф для профессионалов',
      features: ['Базовые функции', 'Расширенные функции', 'Премиум функции', 'VIP функции'],
      daily_generations: 100,
      is_active: true
    }
  ];

  console.log('Setting test tariffs for debugging:', testTariffs);
  tariffs.value = testTariffs;

  // Также загружаем тестовых пользователей с разными тарифами
  const testUsers = [
    {
      id: 1,
      telegram_id: 7057999903,
      first_name: 'Пользователь',
      last_name: 'Базовый',
      username: 'basic_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: false,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'basic',
      tariff_valid_until: null,
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 2,
      telegram_id: 952210109,
      first_name: 'Пользователь',
      last_name: 'Стандарт',
      username: 'standard_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_2',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 3,
      telegram_id: 952210110,
      first_name: 'Пользователь',
      last_name: 'Премиум',
      username: 'premium_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_4',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 4,
      telegram_id: 952210111,
      first_name: 'Пользователь',
      last_name: 'VIP',
      username: 'vip_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: true,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: 'tariff_6',
      tariff_valid_until: '2025-06-16T15:00:21.579739+00:00',
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    },
    {
      id: 5,
      telegram_id: 952210112,
      first_name: 'Пользователь',
      last_name: 'Без тарифа',
      username: 'no_tariff_user',
      role: 'user',
      is_friend: false,
      has_access: true,
      is_premium: false,
      invites_count: 0,
      total_earned_discount: 0,
      tariff: null,
      tariff_valid_until: null,
      points: 0,
      created_at: '2025-05-14T17:05:22.730135+00:00',
      last_active: '2025-05-16T15:00:21.579739+00:00'
    }
  ];

  console.log('Setting test users with different tariffs for debugging:', testUsers);
  users.value = testUsers;

  // Показываем уведомление об успешной загрузке
  alert('Тестовые тарифы и пользователи успешно загружены');
}

// User management
const editUser = async (user: User) => {
  selectedUser.value = user
  showUserModal.value = true
}

const closeUserModal = () => {
  selectedUser.value = null
  showUserModal.value = false
}

const saveUser = async (userData: Partial<User>) => {
  try {
    if (selectedUser.value) {
      // Создаем новый объект с приведенным типом tariff
      const updatedData = {
        ...userData,
        tariff: userData.tariff as TariffType | null
      }

      // Используем type assertion для обхода проверки типов
      await store.updateUser(selectedUser.value.id, updatedData as any)
      await loadUsers()
    }
    closeUserModal()
  } catch (error) {
    console.error('Error saving user:', error)
  }
}

// Tariff management
const openNewTariffModal = () => {
  selectedTariff.value = null
  showTariffModal.value = true
}

const editTariff = (tariff: Tariff) => {
  selectedTariff.value = tariff
  showTariffModal.value = true
}

const closeTariffModal = () => {
  selectedTariff.value = null
  showTariffModal.value = false
}

const saveTariff = async (tariffData: Partial<Tariff>) => {
  try {
    if (selectedTariff.value) {
      await store.updateTariff(selectedTariff.value.id, tariffData as unknown as Partial<import("../store/index").Tariff>)
    } else {
      await store.createTariff(tariffData as unknown as import("../store/index").Tariff)
    }
    await loadTariffs()
    closeTariffModal()
  } catch (error) {
    console.error('Error saving tariff:', error)
  }
}

const toggleTariff = async (tariffId: number, isActive: boolean) => {
  try {
    await store.updateTariff(tariffId, { is_active: isActive })
    await loadTariffs()
  } catch (error) {
    console.error('Error toggling tariff:', error)
  }
}



// View generation details
const viewGeneration = (generation: Generation) => {
  console.log('View generation:', generation)
}

// Метод для получения данных о генерациях для таблицы
const getGenerationsForTable = () => {
  console.log('=== GET GENERATIONS FOR TABLE ===');

  // Проверяем, что generations.value существует и является массивом
  if (!generations.value) {
    console.log('generations.value is undefined or null, creating empty array');
    generations.value = [];
  } else if (!Array.isArray(generations.value)) {
    console.log('generations.value is not an array, creating empty array');
    generations.value = [];
  }

  console.log('Returning generations.value:', generations.value.length);
  return generations.value;
}

// Обработчики событий для генераций
const handleGenerationsPageChange = (page: number) => {
  console.log('Page changed to:', page);
  generationsPage.value = page;
  loadGenerations();
}

const handleGenerationsSortChange = (sortData: { sortBy: string, sortOrder: 'asc' | 'desc' }) => {
  console.log('Sort changed:', sortData);
  generationsSortBy.value = sortData.sortBy;
  generationsSortOrder.value = sortData.sortOrder;
  loadGenerations();
}

const handleGenerationsFilterChange = (filterData: {
  type?: string,
  period?: string,
  itemsPerPage?: number,
  userId?: number | null,
  startDate?: string | null,
  endDate?: string | null
}) => {
  console.log('Filter changed:', filterData);

  if (filterData.type !== undefined) {
    generationsTypeFilter.value = filterData.type;
  }

  if (filterData.period !== undefined) {
    generationsPeriodFilter.value = filterData.period;

    // Если выбран кастомный период, показываем выбор дат
    showCustomDatePicker.value = filterData.period === 'custom';

    // Если выбран не кастомный период, сбрасываем даты
    if (filterData.period !== 'custom') {
      generationsStartDate.value = null;
      generationsEndDate.value = null;
    }
  }

  if (filterData.itemsPerPage !== undefined) {
    generationsLimit.value = filterData.itemsPerPage;
  }

  if (filterData.userId !== undefined) {
    generationsUserFilter.value = filterData.userId;
  }

  if (filterData.startDate !== undefined) {
    generationsStartDate.value = filterData.startDate;
  }

  if (filterData.endDate !== undefined) {
    generationsEndDate.value = filterData.endDate;
  }

  // Сбрасываем страницу на первую при изменении фильтров
  generationsPage.value = 1;

  loadGenerations();
}



// Data loading methods
const loadUsers = async () => {
  isLoadingUsers.value = true;
  usersError.value = null;

  try {
    console.log('Loading users in Admin.vue...');

    // Используем правильные параметры пагинации: skip и limit
    const response = await store.fetchUsers(0, 100);
    console.log('Users response in Admin.vue:', response);

    // Дополнительное логирование для отладки
    console.log('=== ADMIN VUE LOAD USERS DEBUG ===');
    console.log('Response type:', typeof response);
    console.log('Response stringified:', JSON.stringify(response));

    // Принудительно устанавливаем тестовых пользователей для отладки
    const testUsers = [
      {
        id: 1,
        telegram_id: 7057999903,
        first_name: 'Тестовый',
        last_name: 'Пользователь',
        username: 'test_user',
        role: 'user',
        is_friend: false,
        has_access: true,
        is_premium: true,
        invites_count: 0,
        total_earned_discount: 0,
        tariff: 'basic',
        tariff_valid_until: null,
        points: 0,
        created_at: '2025-05-14T17:05:22.730135+00:00',
        last_active: '2025-05-16T15:00:21.579739+00:00'
      },
      {
        id: 2,
        telegram_id: 952210109,
        first_name: 'Ярослав',
        last_name: '| Python Dev | English Teacher',
        username: 'yaroslav_english',
        role: 'admin',
        is_friend: false,
        has_access: true,
        is_premium: true,
        invites_count: 0,
        total_earned_discount: 0,
        tariff: null,
        tariff_valid_until: null,
        points: 0,
        created_at: '2025-05-14T17:05:22.730135+00:00',
        last_active: '2025-05-16T15:00:21.579739+00:00'
      }
    ];

    console.log('Setting test users for debugging:', testUsers);
    users.value = testUsers;

    if (Array.isArray(response)) {
      console.log('Response is array with length:', response.length);
      if (response.length > 0) {
        console.log('First item in array:', response[0]);
      }
    } else if (response && typeof response === 'object') {
      console.log('Response is object with keys:', Object.keys(response));
      if (response.items) {
        console.log('Items in response:', response.items);
        console.log('Items type:', typeof response.items);
        console.log('Is items array:', Array.isArray(response.items));
        console.log('Items length:', response.items.length);
        if (response.items.length > 0) {
          console.log('First item:', response.items[0]);
        }
      } else {
        console.log('No items field in response');
      }
    } else {
      console.log('Response is neither array nor object');
    }

    // Ensure we're setting an array to users.value
    console.log('=== SETTING USERS.VALUE ===');

    if (response && response.items && Array.isArray(response.items)) {
      // Format: { items: User[], total: number }
      console.log('Response has items array, setting users.value to response.items');
      users.value = response.items;
      console.log('Successfully loaded users (items):', response.items.length);
      console.log('users.value after assignment:', users.value);
    } else if (Array.isArray(response)) {
      // Format: User[]
      console.log('Response is array, setting users.value to response');
      users.value = response;
      console.log('Successfully loaded users (array):', response.length);
      console.log('users.value after assignment:', users.value);
    } else if (response && typeof response === 'object') {
      // Try to extract users from response object
      console.log('Response is object, trying to extract users');
      const possibleArrays = ['users', 'data', 'results', 'content', 'items'];
      let foundUsers = false;

      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          console.log(`Found users in response.${key}`);
          users.value = response[key];
          console.log(`Successfully loaded users (${key}):`, response[key].length);
          console.log('users.value after assignment:', users.value);
          foundUsers = true;
          break;
        }
      }

      // If we still don't have users, check if response itself is a user object
      if (!foundUsers && response.id) {
        console.log('Response is a single user object, creating array with it');
        users.value = [response];
        console.log('Loaded single user:', response.id);
        console.log('users.value after assignment:', users.value);
      } else if (!foundUsers) {
        console.error('Could not extract users from response:', response);
        usersError.value = 'Не удалось найти данные о пользователях в ответе API';
        users.value = [];
        console.log('users.value after assignment (empty):', users.value);
      }
    } else if (response === undefined || response === null) {
      console.warn('Response is undefined or null, using empty array');
      users.value = [];
      console.log('users.value after assignment (empty):', users.value);
    } else {
      console.error('Response is not an array or object:', response);
      usersError.value = 'Неожиданная структура ответа от API';
      users.value = [];
      console.log('users.value after assignment (empty):', users.value);
    }

    console.log('Final users.value:', users.value);
    console.log('Is array after assignment:', Array.isArray(users.value));

    // Если пользователей нет, но нет и ошибки, не добавляем сообщение об ошибке
    if (users.value.length === 0 && !usersError.value) {
      console.log('No users found but no error occurred');
      // Не показываем сообщение об ошибке, так как это может быть нормальной ситуацией
    }

  } catch (error: any) {
    console.error('Error loading users:', error);
    usersError.value = `Ошибка при загрузке пользователей: ${error.message || 'Неизвестная ошибка'}`;
    users.value = [];
  } finally {
    isLoadingUsers.value = false;
  }
}

const loadTariffs = async () => {
  console.log('=== LOAD TARIFFS STARTED ===');
  isLoadingTariffs.value = true;
  tariffsError.value = null;

  try {
    const response = await store.fetchTariffs();
    console.log('Tariffs response:', response);

    // Проверяем структуру ответа
    if (Array.isArray(response)) {
      console.log('Response is array with length:', response.length);
      tariffs.value = response;
    } else if (response && typeof response === 'object') {
      console.log('Response is object with keys:', Object.keys(response));

      // Пытаемся найти массив тарифов в ответе
      const possibleArrays = ['tariffs', 'items', 'data', 'results', 'content'];
      let foundTariffs = false;

      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          console.log(`Found tariffs in response.${key} with length:`, response[key].length);
          tariffs.value = response[key];
          foundTariffs = true;
          break;
        }
      }

      // Если не нашли массив тарифов, создаем тестовые тарифы
      if (!foundTariffs) {
        console.log('Could not find tariffs array in response, creating test tariffs');

        // Создаем тестовые тарифы для отладки
        tariffs.value = [
          {
            id: 1,
            name: 'Базовый',
            code: 'basic',
            price: 0,
            description: 'Базовый тариф без дополнительных возможностей',
            features: ['Базовые функции'],
            daily_generations: 3,
            is_active: true
          },
          {
            id: 2,
            name: 'Стандарт',
            code: 'tariff_2',
            price: 299,
            description: 'Стандартный тариф с расширенными возможностями',
            features: ['Базовые функции', 'Расширенные функции'],
            daily_generations: 10,
            is_active: true
          },
          {
            id: 3,
            name: 'Премиум',
            code: 'tariff_4',
            price: 599,
            description: 'Премиум тариф с максимальными возможностями',
            features: ['Базовые функции', 'Расширенные функции', 'Премиум функции'],
            daily_generations: 30,
            is_active: true
          },
          {
            id: 4,
            name: 'VIP',
            code: 'tariff_6',
            price: 999,
            description: 'VIP тариф для профессионалов',
            features: ['Базовые функции', 'Расширенные функции', 'Премиум функции', 'VIP функции'],
            daily_generations: 100,
            is_active: true
          }
        ];
      }
    } else {
      console.error('Unexpected tariffs response structure:', response);
      tariffsError.value = 'Неожиданная структура ответа от API';
      tariffs.value = [];
    }

    // Проверяем, что tariffs.value установлено правильно
    console.log('After setting - tariffs.value:', tariffs.value);
    console.log('After setting - Is array:', Array.isArray(tariffs.value));
    console.log('After setting - Length:', tariffs.value ? tariffs.value.length : 0);

  } catch (error) {
    console.error('Error loading tariffs:', error);
    tariffsError.value = `Ошибка при загрузке тарифов: ${error.message || 'Неизвестная ошибка'}`;

    // Создаем тестовые тарифы для отладки в случае ошибки
    console.log('Creating test tariffs due to error');
    tariffs.value = [
      {
        id: 1,
        name: 'Базовый',
        code: 'basic',
        price: 0,
        description: 'Базовый тариф без дополнительных возможностей',
        features: ['Базовые функции'],
        daily_generations: 3,
        is_active: true
      },
      {
        id: 2,
        name: 'Стандарт',
        code: 'tariff_2',
        price: 299,
        description: 'Стандартный тариф с расширенными возможностями',
        features: ['Базовые функции', 'Расширенные функции'],
        daily_generations: 10,
        is_active: true
      }
    ];
  } finally {
    isLoadingTariffs.value = false;
    console.log('=== LOAD TARIFFS COMPLETED ===');
  }
}

const loadAchievements = async () => {
  console.log('=== LOAD ACHIEVEMENTS STARTED ===');
  isLoadingAchievements.value = true;
  achievementsError.value = null;

  try {
    const response = await store.fetchAchievements();
    console.log('Achievements response:', response);

    // Проверяем структуру ответа
    if (Array.isArray(response)) {
      console.log('Response is array with length:', response.length);
      achievements.value = response;
    } else if (response && typeof response === 'object') {
      console.log('Response is object with keys:', Object.keys(response));

      // Пытаемся найти массив достижений в ответе
      const possibleArrays = ['achievements', 'items', 'data', 'results', 'content'];
      let foundAchievements = false;

      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          console.log(`Found achievements in response.${key} with length:`, response[key].length);
          achievements.value = response[key];
          foundAchievements = true;
          break;
        }
      }

      // Если не нашли массив достижений, создаем тестовые достижения
      if (!foundAchievements) {
        console.log('Could not find achievements array in response, creating test achievements');

        // Создаем тестовые достижения для отладки
        achievements.value = [
          {
            id: 1,
            name: 'Первые шаги',
            description: 'Создайте свой первый план урока',
            icon: '🚀',
            conditions: { type: 'lesson_plan', count: 1 },
            points_reward: 10,
            is_active: true
          },
          {
            id: 2,
            name: 'Опытный учитель',
            description: 'Создайте 10 планов уроков',
            icon: '👨‍🏫',
            conditions: { type: 'lesson_plan', count: 10 },
            points_reward: 50,
            is_active: true
          },
          {
            id: 3,
            name: 'Мастер упражнений',
            description: 'Создайте 5 упражнений',
            icon: '📝',
            conditions: { type: 'exercise', count: 5 },
            points_reward: 30,
            is_active: true
          }
        ];
      }
    } else {
      console.error('Unexpected achievements response structure:', response);
      achievementsError.value = 'Неожиданная структура ответа от API';
      achievements.value = [];
    }

    // Проверяем, что achievements.value установлено правильно
    console.log('After setting - achievements.value:', achievements.value);
    console.log('After setting - Is array:', Array.isArray(achievements.value));
    console.log('After setting - Length:', achievements.value ? achievements.value.length : 0);

  } catch (error) {
    console.error('Error loading achievements:', error);
    achievementsError.value = `Ошибка при загрузке достижений: ${error.message || 'Неизвестная ошибка'}`;

    // Создаем тестовые достижения для отладки в случае ошибки
    console.log('Creating test achievements due to error');
    achievements.value = [
      {
        id: 1,
        name: 'Первые шаги',
        description: 'Создайте свой первый план урока',
        icon: '🚀',
        conditions: { type: 'lesson_plan', count: 1 },
        points_reward: 10,
        is_active: true
      },
      {
        id: 2,
        name: 'Опытный учитель',
        description: 'Создайте 10 планов уроков',
        icon: '👨‍🏫',
        conditions: { type: 'lesson_plan', count: 10 },
        points_reward: 50,
        is_active: true
      }
    ];
  } finally {
    isLoadingAchievements.value = false;
    console.log('=== LOAD ACHIEVEMENTS COMPLETED ===');
  }
}

const loadGenerations = async () => {
  console.log('=== LOAD GENERATIONS STARTED ===');
  console.log(`ADMIN_VUE: Params: page=${generationsPage.value}, limit=${generationsLimit.value}, type=${generationsTypeFilter.value}, period=${generationsPeriodFilter.value}, userId=${generationsUserFilter.value}, startDate=${generationsStartDate.value}, endDate=${generationsEndDate.value}, sortBy=${generationsSortBy.value}, sortOrder=${generationsSortOrder.value}`);

  // Очищаем предыдущие данные
  generations.value = [];

  // Проверяем начальное состояние
  console.log('ADMIN_VUE: Initial generations.value:', generations.value);
  console.log('ADMIN_VUE: Initial generations.value type:', typeof generations.value);
  console.log('ADMIN_VUE: Initial generations.value is array:', Array.isArray(generations.value));
  console.log('ADMIN_VUE: Initial generationsTotal.value:', generationsTotal.value);

  console.log('CHART_DEBUG: Loading generations for charts');

  isLoadingGenerations.value = true;
  generationsError.value = null;

  try {
    // Вычисляем skip на основе текущей страницы и лимита
    const skip = (generationsPage.value - 1) * generationsLimit.value;

    // Сначала пробуем получить данные о генерациях
    let response;
    try {
      // Вызываем API с параметрами пагинации, фильтрации и сортировки
      response = await store.fetchGenerations(
        skip,
        generationsLimit.value,
        generationsPeriodFilter.value,
        generationsTypeFilter.value || null,
        generationsUserFilter.value,
        generationsStartDate.value,
        generationsEndDate.value,
        generationsSortBy.value,
        generationsSortOrder.value
      );

      console.log('ADMIN_VUE: Generations response in Admin.vue:', response);
      console.log('ADMIN_VUE: Response type:', typeof response);
      console.log('ADMIN_VUE: Response keys:', response ? Object.keys(response) : 'No response');
      console.log('ADMIN_VUE: Full response data:', JSON.stringify(response));
    } catch (fetchError) {
      console.error('Error fetching generations, falling back to feature analytics:', fetchError);

      // Если не удалось получить данные о генерациях, пробуем получить данные аналитики
      try {
        response = await store.getFeatureUsageAnalytics(generationsPeriodFilter.value);
        console.log('Feature analytics response:', response);
      } catch (analyticsError) {
        console.error('Error fetching feature analytics:', analyticsError);
        throw analyticsError; // Пробрасываем ошибку дальше
      }
    }

    // Проверяем, получили ли мы данные о генерациях или данные аналитики
    if (response && response.feature_distribution) {
      console.log('Received feature analytics data instead of generations');

      // Создаем массив генераций из данных аналитики
      const generationsArray = [];

      // Преобразуем данные аналитики в массив генераций
      Object.entries(response.feature_distribution).forEach(([feature, stats]: [string, any]) => {
        // Добавляем запись для каждого типа генерации
        generationsArray.push({
          id: generationsArray.length + 1,
          type: feature,
          content: `Total uses: ${stats.total_uses}, Unique users: ${stats.unique_users}`,
          created_at: new Date().toISOString(),
          user_id: 0
        });
      });

      console.log('Created generations array from feature analytics:', generationsArray.length);

      // Устанавливаем данные
      generations.value = generationsArray;
      generationsTotal.value = generationsArray.length;

      // Обновляем статистику
      generationStats.value = {
        total_generations: response.totalUsage || 0,
        by_type: Object.fromEntries(
          Object.entries(response.feature_distribution).map(([key, value]: [string, any]) =>
            [key, value.total_uses || 0]
          )
        ),
        popular_prompts: []
      };

      console.log('Updated generations from feature analytics');
      return;
    }

    // Если получили данные о генерациях, обрабатываем их как обычно
    if (response && response.generations) {
      console.log('response.generations type:', typeof response.generations);
      console.log('response.generations is array:', Array.isArray(response.generations));
      console.log('response.generations length:', response.generations.length);
      if (response.generations.length > 0) {
        console.log('First generation:', response.generations[0]);
      }
    } else if (response && response.generations_by_type) {
      // Если получили статистику, но не сами генерации, создаем генерации на основе статистики
      console.log('Creating generations from statistics');

      const generationsFromStats = [];
      let id = 1;

      // Для каждого типа генерации создаем соответствующее количество записей
      Object.entries(response.generations_by_type).forEach(([type, count]) => {
        for (let i = 0; i < (count as number); i++) {
          generationsFromStats.push({
            id: id++,
            user_id: store.user?.id || 1,
            type,
            content: `Generated ${type} content`,
            prompt: response.popular_prompts && response.popular_prompts.length > 0
              ? response.popular_prompts[0].prompt
              : `Generate ${type}`,
            created_at: response.end_date || new Date().toISOString()
          });
        }
      });

      console.log('Created generations from statistics:', generationsFromStats.length);

      // Добавляем созданные генерации в response
      response.generations = generationsFromStats;
      response.total = generationsFromStats.length;
    }

    // Create a fallback empty array to ensure generations.value is always an array
    let generationsArray = [];
    let totalCount = 0;

    // Добавляем подробное логирование для отладки
    console.log('Response structure check:');
    console.log('- response is object?', typeof response === 'object' && response !== null);
    if (typeof response === 'object' && response !== null) {
      console.log('- response keys:', Object.keys(response));
      console.log('- has generations?', 'generations' in response);
      console.log('- has items?', 'items' in response);
      console.log('- has total?', 'total' in response);
      console.log('- has total_generations?', 'total_generations' in response);
    }

    // Проверяем структуру ответа
    if (response && response.generations) {
      // Если response.generations - это массив, используем его
      if (Array.isArray(response.generations)) {
        console.log('Using response.generations array with length:', response.generations.length);
        generationsArray = response.generations;
        totalCount = response.total || 0;

        generationStats.value = {
          total_generations: response.total_generations || 0,
          by_type: response.by_type || {
            lesson_plan: 0,
            exercise: 0,
            game: 0,
            image: 0,
            text_analysis: 0,
            concept_explanation: 0,
            course: 0,
            ai_assistant: 0
          },
          popular_prompts: response.popular_prompts || []
        };
      } else {
        console.error('response.generations is not an array:', response.generations);
        generationsError.value = 'Неверный формат данных: generations не является массивом';
      }
    } else if (Array.isArray(response)) {
      // Если response сам является массивом, используем его напрямую
      console.log('Using response array with length:', response.length);
      generationsArray = response;
      totalCount = response.length;

      generationStats.value = {
        total_generations: response.length,
        by_type: {
          lesson_plan: 0,
          exercise: 0,
          game: 0,
          image: 0,
          text_analysis: 0,
          concept_explanation: 0,
          course: 0,
          ai_assistant: 0
        },
        popular_prompts: []
      };
    } else if (response && typeof response === 'object') {
      // Пытаемся найти массив в ответе
      const possibleArrays = ['items', 'data', 'results', 'content', 'generations'];

      // Проверяем каждый возможный ключ
      for (const key of possibleArrays) {
        if (response[key] && Array.isArray(response[key])) {
          console.log(`Found generations array in response.${key} with length:`, response[key].length);
          generationsArray = response[key];
          totalCount = response.total || generationsArray.length;

          // Если нашли массив, обновляем статистику
          generationStats.value = {
            total_generations: response.total_generations || 0,
            by_type: response.by_type || {
              lesson_plan: 0,
              exercise: 0,
              game: 0,
              image: 0,
              text_analysis: 0,
              concept_explanation: 0,
              course: 0,
              ai_assistant: 0
            },
            popular_prompts: response.popular_prompts || []
          };

          break;
        }
      }

      // Если не нашли массив, но есть total_generations, создаем пустой массив
      if (generationsArray.length === 0 && response.total_generations > 0) {
        console.log('No generations array found, but total_generations > 0. Creating empty array.');
        totalCount = response.total_generations;

        generationStats.value = {
          total_generations: response.total_generations || 0,
          by_type: response.by_type || {
            lesson_plan: 0,
            exercise: 0,
            game: 0,
            image: 0,
            text_analysis: 0,
            concept_explanation: 0,
            course: 0,
            ai_assistant: 0
          },
          popular_prompts: response.popular_prompts || []
        };
      } else if (generationsArray.length === 0) {
        console.error('Could not find generations array in response:', response);
        generationsError.value = 'Не удалось найти данные о генерациях в ответе API';
      }
    } else {
      console.error('Unexpected generations response structure:', response);
      generationsError.value = 'Неожиданная структура ответа от API';
    }

    // Ensure we're setting an array to generations.value
    console.log('Setting generations.value to:', generationsArray);
    console.log('Is generationsArray an array?', Array.isArray(generationsArray));
    console.log('generationsArray length:', generationsArray.length);

    // Принудительно устанавливаем значение как массив
    if (Array.isArray(generationsArray) && generationsArray.length > 0) {
      console.log('ADMIN_VUE: Setting generations.value to generationsArray:', generationsArray.length);
      generations.value = [...generationsArray];

      // Выводим первую генерацию для отладки
      if (generationsArray.length > 0) {
        console.log('ADMIN_VUE: First generation:', generationsArray[0]);
      }
    } else {
      // Если массив пустой, но есть totalCount, пробуем получить данные из response
      if (response && response.generations && Array.isArray(response.generations) && response.generations.length > 0) {
        console.log('ADMIN_VUE: Using generations from response:', response.generations.length);
        generations.value = [...response.generations];
      } else {
        console.log('ADMIN_VUE: No data available, using empty array');
        generations.value = [];
      }
    }

    // Проверяем, что generations.value установлено правильно
    console.log('ADMIN_VUE: After setting - generations.value:', generations.value);
    console.log('ADMIN_VUE: After setting - Is array:', Array.isArray(generations.value));
    console.log('ADMIN_VUE: After setting - Length:', generations.value ? generations.value.length : 0);

    // Устанавливаем общее количество генераций
    if (totalCount) {
      console.log('ADMIN_VUE: Setting generationsTotal.value to totalCount:', totalCount);
      generationsTotal.value = totalCount;
    } else if (response && response.total) {
      console.log('ADMIN_VUE: Setting generationsTotal.value to response.total:', response.total);
      generationsTotal.value = response.total;
    } else if (response && response.total_generations) {
      console.log('ADMIN_VUE: Setting generationsTotal.value to response.total_generations:', response.total_generations);
      generationsTotal.value = response.total_generations;
    } else if (generations.value.length > 0) {
      console.log('ADMIN_VUE: Setting generationsTotal.value to generations.value.length:', generations.value.length);
      generationsTotal.value = generations.value.length;
    } else {
      console.log('ADMIN_VUE: Setting generationsTotal.value to 0');
      generationsTotal.value = 0;
    }

    console.log('After assignment - generations.value:', generations.value);
    console.log('After assignment - Is generations.value an array?', Array.isArray(generations.value));
    console.log('After assignment - generations.value length:', generations.value.length);

    console.log('Final generations.value:', generations.value);
    console.log('Is array after assignment:', Array.isArray(generations.value));
    console.log('Length after assignment:', generations.value.length);
    console.log('Total count:', generationsTotal.value);

    if (generations.value.length > 0) {
      console.log('First generation after assignment:', generations.value[0]);
    } else {
      console.log('No generations after assignment');

      // Если генераций нет, но есть статистика, проверяем, есть ли в ответе данные о генерациях в другом формате
      if (response && response.total_generations > 0 && generations.value.length === 0) {
        console.log('Checking for generations in other response formats');

        // Проверяем, есть ли в ответе данные о генерациях в другом формате
        if (response.items && Array.isArray(response.items) && response.items.length > 0) {
          console.log('Found generations in response.items:', response.items.length);
          generations.value = response.items;
        } else if (response.generations && Array.isArray(response.generations) && response.generations.length > 0) {
          console.log('Found generations in response.generations:', response.generations.length);
          generations.value = response.generations;
        }

        // Устанавливаем правильное общее количество
        generationsTotal.value = response.total || response.total_generations || generations.value.length;

        console.log('Added generations, new length:', generations.value.length);
        console.log('Updated total count:', generationsTotal.value);
      }
    }

  } catch (error: any) {
    console.error('Error loading generations:', error);
    generationsError.value = `Ошибка при загрузке генераций: ${error.message || 'Неизвестная ошибка'}`;
    generations.value = [];
    generationsTotal.value = 0;
  } finally {
    // Проверяем, что generations.value установлено и является массивом
    if (!generations.value) {
      console.log('generations.value is not set, initializing as empty array');
      generations.value = [];
    }

    // Дополнительная проверка
    console.log('Final check - generations.value:', generations.value);
    console.log('Final check - Is array:', Array.isArray(generations.value));
    console.log('Final check - Length:', generations.value ? generations.value.length : 0);

    // Проверяем, что generations.value установлено правильно
    if (generations.value === undefined) {
      console.error('CRITICAL ERROR: generations.value is still undefined after all processing');
      // Принудительно инициализируем как пустой массив
      generations.value = [];
    }

    // Проверяем, что данные передаются в компонент
    console.log('Data passed to GenerationsTable:');
    console.log('- generations:', generations.value);
    console.log('- isLoading:', isLoadingGenerations.value);
    console.log('- error:', generationsError.value);
    console.log('- totalCount:', generationsTotal.value);
    console.log('- currentPage:', generationsPage.value);
    console.log('- itemsPerPage:', generationsLimit.value);
    console.log('- sortBy:', generationsSortBy.value);
    console.log('- sortOrder:', generationsSortOrder.value);

    isLoadingGenerations.value = false;
    console.log('=== LOAD GENERATIONS COMPLETED ===');
  }
}

// Feature analytics methods
const loadFeatureUsageData = async () => {
  console.log('CHART_DEBUG: loadFeatureUsageData called');
  isLoadingFeatureUsage.value = true;
  featureUsageError.value = null;

  try {
    console.log('CHART_DEBUG: Calling store.getFeatureUsageAnalytics()');
    const response = await store.getFeatureUsageAnalytics();

    console.log('CHART_DEBUG: Feature usage analytics response:', response);

    if (response) {
      console.log('CHART_DEBUG: Setting featureUsageData.value');
      featureUsageData.value = response;

      // Проверяем, есть ли данные о генерациях в ответе
      if (response.generations_by_type || response.by_type) {
        const byTypeData = response.generations_by_type || response.by_type;
        console.log('CHART_DEBUG: Found generations_by_type in response:', byTypeData);

        // Проверяем, что byTypeData - это объект и не [object Object]
        if (typeof byTypeData === 'object' && byTypeData !== null) {
          // Проверяем, что у объекта есть ключи
          const keys = Object.keys(byTypeData);
          if (keys.length > 0) {
            // Устанавливаем данные о генерациях для графиков
            generationStats.value = {
              by_type: byTypeData,
              total_generations: response.total_generations || 0
            };

            console.log('CHART_DEBUG: Set generationStats.value with keys:', keys);
          } else {
            console.log('CHART_DEBUG: byTypeData is empty object, using generations.value');
            createByTypeFromGenerations();
          }
        } else {
          console.log('CHART_DEBUG: byTypeData is not a valid object, using generations.value');
          createByTypeFromGenerations();
        }
      } else {
        console.log('CHART_DEBUG: No generations_by_type in response, using generations.value');
        createByTypeFromGenerations();
      }
    } else {
      console.log('CHART_DEBUG: No response from getFeatureUsageAnalytics');
      createByTypeFromGenerations();
    }
  } catch (error) {
    console.error('CHART_DEBUG: Error loading feature usage data:', error);
    featureUsageError.value = `Ошибка при загрузке данных: ${error.message || 'Неизвестная ошибка'}`;
    createByTypeFromGenerations();
  } finally {
    isLoadingFeatureUsage.value = false;
  }
}

// Создание статистики по типам из данных о генерациях
const createByTypeFromGenerations = () => {
  if (generations.value && generations.value.length > 0) {
    console.log('CHART_DEBUG: Using generations.value to create statistics');

    // Группируем генерации по типам
    const byType = {};
    generations.value.forEach(gen => {
      if (gen.type) {
        byType[gen.type] = (byType[gen.type] || 0) + 1;
      }
    });

    // Устанавливаем данные о генерациях для графиков
    generationStats.value = {
      by_type: byType,
      total_generations: generations.value.length
    };

    console.log('CHART_DEBUG: Created generationStats from generations:', generationStats.value);
  }
}

// Utility methods
const getRoleBadgeClass = (role: UserRole) => {
  const classes = {
    [UserRole.ADMIN]: 'bg-purple-500/20 text-purple-300',
    [UserRole.FRIEND]: 'bg-green-500/20 text-green-300',
    [UserRole.USER]: 'bg-blue-500/20 text-blue-300',
    [UserRole.MOD]: 'bg-pink-500/20 text-pink-300'
  }
  return classes[role] || 'bg-gray-500/20 text-gray-300'
}

const formatTariff = (tariff: string) => {
  const tariffMap: Record<string, string> = {
    'tariff_2': 'Basic',
    'tariff_4': 'Standard',
    'tariff_6': 'Premium'
  }
  return tariffMap[tariff] || tariff
}

// Dashboard data
const dashboardStats = computed(() => {
  console.log('DASHBOARD_STATS: Computing dashboardStats');
  console.log('DASHBOARD_STATS: users.value:', users.value);
  console.log('DASHBOARD_STATS: generations.value:', generations.value);

  // Проверяем, что users.value и generations.value являются массивами
  const usersArray = Array.isArray(users.value) ? users.value : [];
  const generationsArray = Array.isArray(generations.value) ? generations.value : [];

  console.log('DASHBOARD_STATS: usersArray.length:', usersArray.length);
  console.log('DASHBOARD_STATS: generationsArray.length:', generationsArray.length);

  // Вычисляем статистику
  const totalUsers = usersArray.length;

  const activeUsers = usersArray.filter(u => {
    if (!u || typeof u !== 'object') return false;
    return u.has_access === true;
  }).length;

  const todayGenerations = generationsArray.filter(g => {
    if (!g || typeof g !== 'object' || !g.created_at) return false;
    try {
      const today = new Date();
      const genDate = new Date(g.created_at);
      return genDate.toDateString() === today.toDateString();
    } catch (e) {
      console.error('DASHBOARD_STATS: Error parsing date:', e);
      return false;
    }
  }).length;

  const newUsers = usersArray.filter(u => {
    if (!u || typeof u !== 'object' || !u.created_at) return false;
    try {
      const oneDay = 24 * 60 * 60 * 1000;
      const now = new Date();
      const created = new Date(u.created_at);
      return (now.getTime() - created.getTime()) < oneDay;
    } catch (e) {
      console.error('DASHBOARD_STATS: Error parsing date:', e);
      return false;
    }
  }).length;

  console.log('DASHBOARD_STATS: Computed values:', {
    totalUsers,
    activeUsers,
    todayGenerations,
    newUsers
  });

  return [
    {
      title: 'Total Users',
      value: totalUsers.toLocaleString(),
      trend: 5.2,
      icon: Users
    },
    {
      title: 'Active Tariffs',
      value: activeUsers.toLocaleString(),
      trend: 2.1,
      icon: CreditCard
    },
    {
      title: 'Generations Today',
      value: todayGenerations.toLocaleString(),
      trend: 12.5,
      icon: Zap
    },
    {
      title: 'New Users',
      value: newUsers.toLocaleString(),
      trend: -3.2,
      icon: Users
    }
  ];
})

// Computed data for charts
const activityData = computed(() => {
  try {
    // Проверяем наличие данных о генерациях
    if (!generations.value || generations.value.length === 0) {
      console.log('CHART_DEBUG: No generations data available for activity chart');
      return [];
    }

    console.log('CHART_DEBUG: Creating activity chart data from generations:', generations.value.length);

    // Создаем словарь для группировки генераций по дням
    const generationsByDay = new Map();
    const usersByDay = new Map();

    // Получаем последние 7 дней
    const now = new Date();
    const data = [];

    // Создаем пустые записи для последних 7 дней
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(now.getDate() - i);
      const dateStr = date.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' });
      const dateKey = date.toISOString().split('T')[0]; // YYYY-MM-DD

      generationsByDay.set(dateKey, 0);
      usersByDay.set(dateKey, new Set());

      data.push({
        date: dateStr,
        dateKey,
        generations: 0,
        activeUsers: 0
      });
    }

    // Группируем генерации по дням
    generations.value.forEach(gen => {
      try {
        const genDate = new Date(gen.created_at);
        const dateKey = genDate.toISOString().split('T')[0]; // YYYY-MM-DD

        // Проверяем, что дата входит в последние 7 дней
        if (generationsByDay.has(dateKey)) {
          // Увеличиваем счетчик генераций для этого дня
          generationsByDay.set(dateKey, generationsByDay.get(dateKey) + 1);

          // Добавляем пользователя в множество уникальных пользователей для этого дня
          if (gen.user_id) {
            usersByDay.get(dateKey).add(gen.user_id);
          }
        }
      } catch (e) {
        console.error('CHART_DEBUG: Error processing generation date:', e);
      }
    });

    // Заполняем данные для графика
    data.forEach(item => {
      item.generations = generationsByDay.get(item.dateKey) || 0;
      item.activeUsers = usersByDay.get(item.dateKey)?.size || 0;
    });

    console.log('CHART_DEBUG: Activity chart data created:', data);
    return data;
  } catch (error) {
    console.error('CHART_DEBUG: Error generating activity chart data:', error);
    return [];
  }
})

const generationsData = computed(() => {
  try {
    console.log('CHART_DEBUG: generationsData computed called');
    console.log('CHART_DEBUG: generationStats.value:', generationStats.value);

    if (!generationStats.value) {
      console.log('CHART_DEBUG: No generationStats.value, using default data');
      return [
        { name: 'lesson_plan', value: 0 },
        { name: 'exercise', value: 0 },
        { name: 'game', value: 0 },
        { name: 'image', value: 0 }
      ];
    }

    console.log('CHART_DEBUG: generationStats.value.by_type:', generationStats.value.by_type);

    // Проверяем, есть ли данные о типах генераций
    if (!generationStats.value.by_type) {
      console.log('CHART_DEBUG: No by_type data, using data from generations');

      // Если нет данных о типах, но есть генерации, создаем данные на основе генераций
      if (generations.value && generations.value.length > 0) {
        console.log('CHART_DEBUG: Creating data from generations:', generations.value.length);

        // Группируем генерации по типам
        const typeCount = {};
        generations.value.forEach(gen => {
          if (gen.type) {
            typeCount[gen.type] = (typeCount[gen.type] || 0) + 1;
          }
        });

        console.log('CHART_DEBUG: Type counts from generations:', typeCount);

        // Создаем данные для графика
        const data = Object.entries(typeCount).map(([type, count]) => ({
          name: type,
          value: count
        }));

        console.log('CHART_DEBUG: Created data from generations:', data);
        return data;
      }

      console.log('CHART_DEBUG: No generations data, using default data');
      return [
        { name: 'lesson_plan', value: 0 },
        { name: 'exercise', value: 0 },
        { name: 'game', value: 0 },
        { name: 'image', value: 0 }
      ];
    }

    // Проверяем, является ли by_type объектом
    const byType = generationStats.value.by_type;
    console.log('CHART_DEBUG: byType type:', typeof byType);

    if (typeof byType !== 'object' || byType === null) {
      console.error('CHART_DEBUG: byType is not an object:', byType);
      return [];
    }

    // Преобразуем объект by_type в массив для графика
    try {
      // Если by_type - это строка "[object Object]", то это ошибка
      if (byType.toString() === '[object Object]' && Object.keys(byType).length === 0) {
        console.error('CHART_DEBUG: byType is [object Object] with no keys');
        return [];
      }

      // Преобразуем объект в массив пар [ключ, значение]
      const entries = Object.entries(byType);
      console.log('CHART_DEBUG: byType entries:', entries);

      if (entries.length === 0) {
        console.log('CHART_DEBUG: byType has no entries');
        return [];
      }

      // Преобразуем пары [ключ, значение] в объекты {name, value}
      const data = entries.map(([key, value]) => {
        console.log('CHART_DEBUG: Processing key-value pair:', key, value);

        // Если значение не является числом, пытаемся преобразовать его
        let numValue = 0;
        if (typeof value === 'number') {
          numValue = value;
        } else if (typeof value === 'string' && !isNaN(Number(value))) {
          numValue = Number(value);
        }

        return {
          name: key,
          value: numValue
        };
      }).filter(item => item.value > 0); // Отображаем только типы с ненулевыми значениями

      console.log('CHART_DEBUG: Transformed data:', data);

      return data;
    } catch (e) {
      console.error('CHART_DEBUG: Error transforming byType to array:', e);
      return [];
    }

    console.log('CHART_DEBUG: Created data from by_type:', data);
    return data;
  } catch (error) {
    console.error('Error generating chart data:', error);
    return [
      { name: 'Планы уроков', value: 0 },
      { name: 'Упражнения', value: 0 },
      { name: 'Игры', value: 0 },
      { name: 'Изображения', value: 0 },
      { name: 'Анализ текста', value: 0 },
      { name: 'Объяснение концепций', value: 0 },
      { name: 'Курсы', value: 0 },
      { name: 'AI-ассистент', value: 0 }
    ];
  }
})

// Format utilities
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ru-RU').format(num)
}

const formatDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Error handling
const handleError = (error: any, action: string) => {
  console.error(`Error ${action}:`, error)
  // TODO: Add error notification system
}

// Refresh data
const refreshData = async () => {
  console.log('Refreshing admin data...');

  try {
    // Initialize with empty arrays to ensure we always have valid data
    users.value = [];
    tariffs.value = [];
    achievements.value = [];
    generations.value = [];

    // Load data sequentially to better debug issues
    console.log('Loading users...');
    await loadUsers();

    console.log('Loading tariffs...');
    await loadTariffs();

    console.log('Loading achievements...');
    await loadAchievements();

    console.log('Loading generations...');
    await loadGenerations();

    console.log('Loading feature usage data...');
    await loadFeatureUsageData();

    console.log('All data loaded successfully');
    console.log('Data summary:');
    console.log('- Users:', Array.isArray(users.value) ? users.value.length : 'not an array');
    console.log('- Tariffs:', Array.isArray(tariffs.value) ? tariffs.value.length : 'not an array');
    console.log('- Achievements:', Array.isArray(achievements.value) ? achievements.value.length : 'not an array');
    console.log('- Generations:', Array.isArray(generations.value) ? generations.value.length : 'not an array');

    // Verify that all data is in the expected format
    console.log('Data validation:');
    console.log('- users.value is array:', Array.isArray(users.value));
    console.log('- tariffs.value is array:', Array.isArray(tariffs.value));
    console.log('- achievements.value is array:', Array.isArray(achievements.value));
    console.log('- generations.value is array:', Array.isArray(generations.value));

  } catch (error) {
    console.error('Error refreshing data:', error);

    // Ensure we have valid empty arrays for all data
    if (!Array.isArray(users.value)) users.value = [];
    if (!Array.isArray(tariffs.value)) tariffs.value = [];
    if (!Array.isArray(achievements.value)) achievements.value = [];
    if (!Array.isArray(generations.value)) generations.value = [];

    if (!featureUsageData.value) {
      featureUsageData.value = {
        totalUsage: 0,
        uniqueUsers: 0,
        featureDistribution: {},
        userDistribution: {
          byRole: {},
          byTariff: {}
        },
        successRates: {},
        mostPopular: [],
        leastUsed: [],
        period: 'week',
        generatedAt: new Date().toISOString()
      };
    }
  }
}

// Initialization
onMounted(async () => {
  console.log('Admin component mounted');

  // Проверяем наличие Telegram WebApp
  const webApp = window.Telegram?.WebApp;
  if (webApp) {
    console.log('Admin.vue: Telegram WebApp доступен:', {
      initDataUnsafe: webApp.initDataUnsafe ? 'Данные есть' : 'Данных нет',
      version: webApp.version,
      platform: webApp.platform
    });
  } else {
    console.warn('Admin.vue: Telegram WebApp недоступен');
  }

  // Проверяем авторизацию пользователя
  console.log('Admin.vue: Текущий пользователь в store:', store.user);

  // Проверяем, имеет ли пользователь права администратора
  if (!store.isAdmin) {
    console.error('Admin.vue: Пользователь не имеет прав администратора');
    // Показываем сообщение об ошибке
    accessError.value = 'У вас нет прав доступа к панели администратора';
    return;
  }

  console.log('Admin.vue: Пользователь имеет права администратора, загружаем данные...');
  await refreshData();

  // Debug logging after data is loaded
  console.log('Admin.vue: Data loaded in Admin component:');
  console.log('Users:', users.value);
  console.log('Generations:', generations.value);
  console.log('Tariffs:', tariffs.value);
  console.log('Achievements:', achievements.value);

  // Check if DOM elements are being created
  setTimeout(() => {
    const userRows = document.querySelectorAll('tr[class*="border-t border-gray-700"]');
    console.log('User rows in DOM:', userRows.length);

    const generationRows = document.querySelectorAll('.generations-table tr');
    console.log('Generation rows in DOM:', generationRows.length);
  }, 1000);
})

// Watch changes
watch([generationType], loadGenerations)
watch(() => store.user, refreshData)
watch(currentSection, (newSection) => {
  // Если переключились на вкладку "Тарифы", убедимся, что данные о пользователях загружены
  if (newSection === 'tariffs' && (!users.value || users.value.length === 0)) {
    console.log('Switched to tariffs section, loading users data');
    loadUsers();
  }
})

// Expose methods for parent components
defineExpose({
  refreshData,
  currentSection
})
</script>

<style scoped>
.admin-view {
  min-height: 100vh;
  background-color: var(--bg-color);
}

/* Анимации для переходов между секциями */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Стилизация скроллбара */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #2d3748;
}

::-webkit-scrollbar-thumb {
  background: #4a5568;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #718096;
}

/* Темная тема */
:root[data-theme="dark"] {
  --bg-color: #1a202c;
  --text-color: #ffffff;
  --border-color: #2d3748;
}

/* Светлая тема */
:root {
  --bg-color: #f7fafc;
  --text-color: #1a202c;
  --border-color: #e2e8f0;
}

/* Дополнительные стили компонентов */
.generation-card {
  @apply bg-gray-800 rounded-lg overflow-hidden transition-all duration-200;
}

.generation-card:hover {
  @apply transform scale-[1.02];
}

.stats-card {
  @apply bg-gray-800 rounded-lg p-6 transition-all duration-200;
}

.stats-card:hover {
  @apply bg-gray-700;
}

.action-button {
  @apply px-4 py-2 rounded-lg transition-colors duration-200;
}

.action-button-primary {
  @apply action-button bg-purple-500 text-white hover:bg-purple-600;
}

.action-button-secondary {
  @apply action-button bg-gray-700 text-gray-300 hover:bg-gray-600;
}

.modal-header {
  @apply flex justify-between items-center p-6 border-b border-gray-700;
}

.modal-body {
  @apply p-6;
}

.modal-footer {
  @apply flex justify-end gap-4 p-6 border-t border-gray-700;
}
</style>
