<template>
  <div class="admin-card">
    <div class="admin-card-header">
      <h3 class="admin-card-title">Системные настройки</h3>
      <button
        @click="saveSettings"
        class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!isSettingsChanged || isSaving"
      >
        <span v-if="isSaving" class="inline-flex items-center">
          <span class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></span>
          Сохранение...
        </span>
        <span v-else>
          Сохранить изменения
        </span>
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="mt-6 text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Загрузка настроек...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="mt-6 bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="loadSettings"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Попробовать снова
      </button>
    </div>

    <!-- Success message -->
    <div v-if="successMessage" class="mt-6 bg-green-500/20 text-green-300 p-4 rounded-lg mb-4">
      <p>{{ successMessage }}</p>
    </div>

    <div v-if="!isLoading && !error" class="mt-6 space-y-6">
      <!-- Настройки тарифов -->
      <div>
        <h4 class="text-lg font-medium text-white mb-4">
          Настройки тарифов
          <InfoTooltip>
            Настройте лимиты генераций и стоимость для каждого тарифного плана.
            Изменения вступят в силу для всех новых активаций тарифов.
          </InfoTooltip>
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="tariff in tariffSettings" :key="tariff.type"
               class="p-4 bg-gray-700/50 rounded-lg">
            <h5 class="text-white font-medium mb-3">{{ tariff.name }}</h5>

            <!-- Лимиты генераций -->
            <div class="space-y-2">
              <div>
                <label class="block text-sm text-gray-400 mb-1">
                  Лимит генераций в день
                </label>
                <input
                  v-model.number="tariff.settings.generations_limit"
                  type="number"
                  min="0"
                  class="modal-input"
                >
              </div>

              <div>
                <label class="block text-sm text-gray-400 mb-1">
                  Лимит изображений в день
                </label>
                <input
                  v-model.number="tariff.settings.images_limit"
                  type="number"
                  min="0"
                  class="modal-input"
                >
              </div>

              <div>
                <label class="block text-sm text-gray-400 mb-1">
                  Стоимость (баллы)
                </label>
                <input
                  v-model.number="tariff.settings.price_points"
                  type="number"
                  min="0"
                  class="modal-input"
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Настройки реферальной системы -->
      <div class="pt-6 border-t border-gray-700">
        <h4 class="text-lg font-medium text-white mb-4">
          Реферальная система
          <InfoTooltip>
            Настройте размер скидок для приглашающих и приглашенных пользователей.
            Максимальная накопленная скидка ограничивает общий размер скидки для одного пользователя.
          </InfoTooltip>
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">
              Скидка для приглашенного пользователя (%)
            </label>
            <input
              v-model.number="referralSettings.new_user_discount"
              type="number"
              min="0"
              max="100"
              class="modal-input"
            >
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">
              Скидка для пригласившего (%)
            </label>
            <input
              v-model.number="referralSettings.referrer_discount"
              type="number"
              min="0"
              max="100"
              class="modal-input"
            >
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">
              Максимальная накопленная скидка (%)
            </label>
            <input
              v-model.number="referralSettings.max_discount"
              type="number"
              min="0"
              max="100"
              class="modal-input"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useMainStore } from '../../../store'
import InfoTooltip from '../common/InfoTooltip.vue'
import type { SystemSettings, TariffSetting, ReferralSettings } from '../../../types/settings';

const store = useMainStore();

// UI state
const isLoading = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// Настройки тарифов
const tariffSettings = ref<TariffSetting[]>([
  {
    type: 'tariff_2',
    name: 'Basic Tariff',
    settings: {
      generations_limit: 6,
      images_limit: 2,
      price_points: 400
    }
  },
  {
    type: 'tariff_4',
    name: 'Standard Tariff',
    settings: {
      generations_limit: 12,
      images_limit: 5,
      price_points: 650
    }
  },
  {
    type: 'tariff_6',
    name: 'Premium Tariff',
    settings: {
      generations_limit: 25,
      images_limit: 8,
      price_points: 900
    }
  }
]);

// Настройки реферальной системы
const referralSettings = ref<ReferralSettings>({
  new_user_discount: 1,
  referrer_discount: 2,
  max_discount: 20
});

const originalSettings = ref<SystemSettings | null>(null);

// Проверяем, были ли изменения в настройках
const isSettingsChanged = computed(() => {
  if (!originalSettings.value) return false;

  return JSON.stringify({
    tariffs: tariffSettings.value,
    referral: referralSettings.value
  }) !== JSON.stringify(originalSettings.value);
});

// Сохранение настроек
const saveSettings = async () => {
  if (isSaving.value) return;

  isSaving.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    const settings: SystemSettings = {
      tariffs: tariffSettings.value,
      referral: referralSettings.value
    };

    await store.updateSystemSettings(settings);
    originalSettings.value = JSON.parse(JSON.stringify(settings));

    // Показываем сообщение об успешном сохранении
    successMessage.value = 'Настройки успешно сохранены';

    // Скрываем сообщение через 3 секунды
    setTimeout(() => {
      successMessage.value = null;
    }, 3000);

  } catch (err: any) {
    console.error('Error saving settings:', err);
    error.value = `Ошибка при сохранении настроек: ${err.message || 'Неизвестная ошибка'}`;
  } finally {
    isSaving.value = false;
  }
};

// Загрузка текущих настроек
const loadSettings = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const settings = await store.fetchSystemSettings();

    if (settings && typeof settings === 'object') {
      // Обработка настроек тарифов
      if (settings.tariffs && Array.isArray(settings.tariffs)) {
        tariffSettings.value = settings.tariffs;
        console.log('Successfully loaded tariff settings:', settings.tariffs.length);
      } else {
        console.warn('No tariffs array in settings:', settings);
        // Оставляем дефолтные настройки
      }

      // Обработка настроек реферальной системы
      if (settings.referral && typeof settings.referral === 'object') {
        referralSettings.value = settings.referral;
        console.log('Successfully loaded referral settings');
      } else {
        console.warn('No referral object in settings:', settings);
        // Оставляем дефолтные настройки
      }

      // Сохраняем оригинальные настройки для сравнения
      originalSettings.value = JSON.parse(JSON.stringify(settings));
    } else {
      console.error('Unexpected settings response structure:', settings);
      error.value = 'Неожиданная структура ответа от API';
    }
  } catch (err: any) {
    console.error('Error loading settings:', err);
    error.value = `Ошибка при загрузке настроек: ${err.message || 'Неизвестная ошибка'}`;
  } finally {
    isLoading.value = false;
  }
};

// При монтировании компонента
onMounted(() => {
  loadSettings();
});
</script>
