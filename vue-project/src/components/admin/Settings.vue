<template>
  <div class="space-y-6">
    <PageHeader
      title="Settings"
      description="Manage platform settings and configurations"
    />

    <!-- Навигация по настройкам -->
    <div class="flex space-x-4 border-b border-gray-700 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="px-4 py-2 -mb-px"
        :class="activeTab === tab.id
          ? 'text-purple-500 border-b-2 border-purple-500'
          : 'text-gray-400 hover:text-gray-300'"
      >
        {{ tab.name }}
      </button>
    </div>

    <!-- Содержимое настроек -->
    <div class="space-y-6">
      <!-- Системные настройки -->
      <SystemSettings v-if="activeTab === 'system'" />

      <!-- Настройки уведомлений -->
      <div v-if="activeTab === 'notifications'" class="space-y-4">
        <PageContent>
          <h3 class="text-lg font-medium text-white mb-4">Notification Settings</h3>
          <!-- Содержимое настроек уведомлений -->
        </PageContent>
      </div>

      <!-- Настройки безопасности -->
      <div v-if="activeTab === 'security'" class="space-y-4">
        <PageContent>
          <h3 class="text-lg font-medium text-white mb-4">Security Settings</h3>
          <!-- Содержимое настроек безопасности -->
        </PageContent>
      </div>

      <!-- Настройки API -->
      <div v-if="activeTab === 'api'" class="space-y-4">
        <PageContent>
          <h3 class="text-lg font-medium text-white mb-4">API Settings</h3>
          <!-- Содержимое настроек API -->
        </PageContent>
      </div>

      <!-- Бэкап и восстановление -->
      <div v-if="activeTab === 'backup'" class="space-y-4">
        <PageContent>
          <h3 class="text-lg font-medium text-white mb-4">Backup & Restore</h3>
          <!-- Содержимое настроек бэкапа -->
        </PageContent>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/admin/common/PageHeader.vue'
import PageContent from '@/components/admin/PageContent.vue'
import SystemSettings from '@/components/admin/settings/SystemSettings.vue'

const activeTab = ref('system')

const tabs = [
  { id: 'system', name: 'System' },
  { id: 'notifications', name: 'Notifications' },
  { id: 'security', name: 'Security' },
  { id: 'api', name: 'API' },
  { id: 'backup', name: 'Backup & Restore' }
]
</script>
