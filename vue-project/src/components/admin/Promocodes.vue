<template>
  <div class="space-y-6">
    <PageHeader
      title="Promocodes"
      description="Manage promotional codes, track usage and analytics"
    />

    <!-- Основные компоненты -->
    <PromocodesManager />
    <PromoUsageHistory />
    <PromocodesStats />
  </div>
</template>

<script setup lang="ts">
import PageHeader from './common/PageHeader.vue'
import PromocodesManager from './settings/PromocodesManager.vue'
import PromoUsageHistory from './settings/PromoUsageHistory.vue'
import PromocodesStats from './settings/PromocodesStats.vue'
</script>
