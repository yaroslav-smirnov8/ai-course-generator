<template>
  <div class="exercise-like-container profile-view" ref="profileViewRef" data-view="profile">
    <div class="content">
      <h2>User Profile</h2>

      <!-- Состояние загрузки -->
      <div v-if="isLoading" class="loading">
        <div class="loader"></div>
        <p>Loading profile data...</p>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="loadUserProfile" class="error-close">✕</button>
        <button @click="loadUserProfile" class="action-button mt-4">
          <span class="icon">🔄</span>
          Try Again
        </button>
      </div>

      <div v-if="!isLoading && !error" class="profile-content">
        <!-- Основная информация -->
        <div class="form-group">
          <div class="user-info-container">
            <div v-if="userData.photo_url" class="user-avatar">
              <img :src="userData.photo_url" alt="Аватар пользователя" />
            </div>
            <div v-else class="user-avatar user-initials">
              {{ userInitials }}
            </div>
            <div class="user-details">
              <h3>{{ userData.name || 'User' }}</h3>
              <p>{{ userData.email || userData.username || 'No data' }}</p>
            </div>
          </div>
        </div>

        <!-- Статистика -->
        <div class="form-group">
          <label>Your Statistics</label>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ userData.points || 0 }}</div>
              <div class="stat-label">Points</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userData.invites || 0 }}</div>
              <div class="stat-label">Invites</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userData.streak || 0 }}</div>
              <div class="stat-label">Days Streak</div>
            </div>
          </div>
        </div>

        <!-- Информация о тарифе -->
        <div class="form-group">
          <label>Your Plan</label>
          <div class="tariff-info">
            <div class="tariff-row">
              <span class="tariff-label">Current Plan:</span>
              <span class="tariff-value">{{ tariffName }}</span>
            </div>
            <div class="tariff-row">
              <span class="tariff-label">Valid Until:</span>
              <span class="tariff-value" :class="{'expiring-soon': isExpiringSoon}">
                {{ formattedExpiryDate }}
              </span>
            </div>
            <div class="tariff-row">
              <span class="tariff-label">Generations Today:</span>
              <span class="tariff-value" v-if="typeof remainingGenerations === 'string' && remainingGenerations === '∞'">
                {{ remainingGenerations }}
              </span>
              <span class="tariff-value" v-else>
                {{ remainingGenerations }}/{{ generationsLimit }}
              </span>
            </div>
            <div class="tariff-row">
              <span class="tariff-label">Images Today:</span>
              <span class="tariff-value" v-if="typeof remainingImages === 'string' && remainingImages === '∞'">
                {{ remainingImages }}
              </span>
              <span class="tariff-value" v-else>
                {{ remainingImages }}/{{ imagesLimit }}
              </span>
            </div>
          </div>

          <!-- Кнопка обновления тарифа -->
          <div class="form-actions">
            <button @click="goToTariffs" class="submit-btn">
              Upgrade Plan
            </button>
          </div>
        </div>

        <!-- Достижения -->
        <div class="form-group">
          <label>Achievements</label>
          <div v-if="achievements.length === 0" class="empty-achievements">
            You don't have any achievements yet
          </div>
          <div v-else class="achievements-grid">
            <div
              v-for="achievement in achievements"
              :key="achievement.id"
              class="achievement-item"
              :class="{'achievement-unlocked': achievement.unlocked}"
            >
              <div class="achievement-icon">{{ achievement.icon }}</div>
              <div class="achievement-details">
                <h4>{{ achievement.name }}</h4>
                <p>{{ achievement.description }}</p>
                <div
                  v-if="achievement.progress !== undefined"
                  class="achievement-progress"
                >
                  <div
                    class="achievement-progress-bar"
                    :style="{ width: `${achievement.progress}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Промокоды -->
        <div class="form-group">
          <label>Promo Codes</label>
          <div class="promocode-container">
            <div class="promocode-actions">
              <button
                @click="showPromoCodeModal = true"
                class="action-button"
              >
                <span class="icon">🏷️</span>
                Activate Promo Code
              </button>
              <button
                @click="showPromoCodeHistory = !showPromoCodeHistory"
                class="action-button secondary"
              >
                <span class="icon">📋</span>
                {{ showPromoCodeHistory ? 'Hide History' : 'History' }}
              </button>
            </div>
            <p class="promocode-info">
              Use promo codes to get points, activate plans or get discounts
            </p>

            <!-- История промокодов -->
            <div v-if="showPromoCodeHistory" class="mt-4">
              <PromoCodeHistory />
            </div>
          </div>
        </div>

        <!-- Реферальная система -->
        <div class="form-group">
          <label>Invite Friends</label>
          <div class="referral-container">
            <div class="referral-input-group">
              <input
                type="text"
                :value="referralLink"
                readonly
                class="form-input"
              >
              <button
                @click="copyReferralLink"
                class="action-button"
              >
                <span class="icon">📋</span>
                Copy
              </button>
            </div>
            <div class="referral-stats">
              <div class="referral-stat">
                <span class="stat-value">{{ userData.invites || 0 }}</span>
                <span class="stat-label">Invited</span>
              </div>
              <div class="referral-stat">
                <span class="stat-value">{{ userData.referralEarnings || 0 }}</span>
                <span class="stat-label">Points Earned</span>
              </div>
            </div>
            <p class="referral-info">
              Get 100 points for each invited friend
            </p>
          </div>
        </div>
      </div>

      <!-- Пространство для нижней навигации -->
      <div class="bottom-nav-spacer"></div>
    </div>

    <!-- Модальное окно промокода -->
    <PromoCodeInput
      :show="showPromoCodeModal"
      @close="showPromoCodeModal = false"
      @success="handlePromoCodeSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useMainStore } from "@/store";
import { apiClient } from "@/api/client";
import { useRouter } from "vue-router";
import { ContentType, TariffType, UNLIMITED_ROLES } from "@/core/constants";
import PromoCodeInput from "@/components/common/PromoCodeInput.vue";
import PromoCodeHistory from "@/components/common/PromoCodeHistory.vue";
import { toastService } from "@/services/toastService";

const store = useMainStore();
const router = useRouter();
const isLoading = ref(true);
const error = ref<string | null>(null);

// Добавляем ref для корневого элемента
const profileViewRef = ref<HTMLElement | null>(null);

// Данные пользователя
const userData = ref<any>({
  name: '',
  email: '',
  username: '',
  points: 0,
  invites: 0,
  streak: 0,
  photo_url: '',
  referralEarnings: 0
});

// Достижения пользователя
const achievements = ref<any[]>([]);

// Реферальная ссылка
const referralLink = ref('');

// Состояние промокодов
const showPromoCodeModal = ref(false);
const showPromoCodeHistory = ref(false);

// Инициалы пользователя
const userInitials = computed(() => {
  const name = userData.value.name || '';
  const names = name.split(' ');
  return names.map((n: string) => n[0] || '').join('');
});

// Информация о тарифе
const tariffName = computed(() => {
  if (!store.user?.tariff) return 'Basic';

  switch (store.user.tariff) {
    case TariffType.BASIC:
      return 'Basic';
    case TariffType.STANDARD:
      return 'Standard';
    case TariffType.PREMIUM:
      return 'Premium';
    default:
      return store.user.tariff;
  }
});

// Форматированная дата окончания тарифа
const formattedExpiryDate = computed(() => {
  if (!store.user?.tariff_valid_until) return 'Unlimited';

  const expiryDate = new Date(store.user.tariff_valid_until);
  return expiryDate.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });
});

// Проверка, истекает ли тариф скоро (в течение 3 дней)
const isExpiringSoon = computed(() => {
  if (!store.user?.tariff_valid_until) return false;

  const expiryDate = new Date(store.user.tariff_valid_until);
  const now = new Date();
  const diffTime = expiryDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return diffDays <= 3 && diffDays >= 0;
});

// Лимиты генераций
const generationsLimit = computed(() => {
  // Если пользователь имеет безлимитную роль
  if (store.user?.role && UNLIMITED_ROLES.includes(store.user.role)) {
    return "∞"; // Возвращаем символ бесконечности
  }

  // Если у пользователя есть тариф, используем жестко заданные значения из бэкенда
  if (store.user?.tariff) {
    switch (store.user.tariff) {
      case TariffType.PREMIUM:
        return 25; // Лимит для Премиум тарифа из бэкенда
      case TariffType.STANDARD:
        return 12; // Лимит для Стандартного тарифа из бэкенда
      case TariffType.BASIC:
        return 6;  // Лимит для Базового тарифа из бэкенда
      default:
        // Если тариф не распознан, используем значение из tariffInfo
        return store.tariffInfo?.limits?.generations || 0;
    }
  }

  // Если нет тарифа, возвращаем 0
  return 0;
});

const imagesLimit = computed(() => {
  // Если пользователь имеет безлимитную роль
  if (store.user?.role && UNLIMITED_ROLES.includes(store.user.role)) {
    return "∞"; // Возвращаем символ бесконечности
  }

  // Если у пользователя есть тариф, используем жестко заданные значения из бэкенда
  if (store.user?.tariff) {
    switch (store.user.tariff) {
      case TariffType.PREMIUM:
        return 8;  // Лимит для Премиум тарифа из бэкенда
      case TariffType.STANDARD:
        return 5;  // Лимит для Стандартного тарифа из бэкенда
      case TariffType.BASIC:
        return 2;  // Лимит для Базового тарифа из бэкенда
      default:
        // Если тариф не распознан, используем значение из tariffInfo
        return store.tariffInfo?.limits?.images || 0;
    }
  }

  // Если нет тарифа, возвращаем 0
  return 0;
});

// Оставшиеся генерации
const remainingGenerations = computed(() => {
  // Проверяем, является ли пользователь администратором или другой ролью с безлимитным доступом
  if (store.user?.role && UNLIMITED_ROLES.includes(store.user.role)) {
    return "∞"; // Возвращаем символ бесконечности для безлимитных пользователей
  }

  // Если у пользователя нет тарифа, возвращаем 0
  if (!store.user?.tariff) {
    return 0;
  }

  // Получаем значение из хранилища
  const remaining = store.remainingGenerations(ContentType.LESSON_PLAN);

  // Если у пользователя есть тариф, но счетчики не инициализированы или равны нулю
  if (generationsLimit.value > 0) {
    // Если нет статистики использования или счетчик равен 0, и при этом оставшиеся генерации равны 0
    if (remaining === 0 && (!store.userStats || store.userStats.dailyGenerations === 0)) {
      // Проверяем, какой тариф у пользователя и возвращаем соответствующий лимит
      switch (store.user.tariff) {
        case TariffType.PREMIUM:
          return 25; // Лимит для Премиум тарифа из бэкенда
        case TariffType.STANDARD:
          return 12; // Лимит для Стандартного тарифа из бэкенда
        case TariffType.BASIC:
          return 6;  // Лимит для Базового тарифа из бэкенда
        default:
          return generationsLimit.value; // Используем значение из tariffInfo, если тариф не распознан
      }
    }
  }

  // Если у пользователя есть тариф и лимит, но счетчик показывает 0, принудительно обновляем статистику
  if (remaining === 0 && generationsLimit.value > 0 && store.userStats && store.userStats.dailyGenerations > 0) {
    console.log('[Profile] Detected inconsistency in generation counts, refreshing stats...');
    // Запускаем обновление статистики, но не ждем его завершения, чтобы не блокировать UI
    store.updateUsageStats().catch(err => console.error('Error refreshing stats:', err));
  }

  return remaining;
});

const remainingImages = computed(() => {
  // Проверяем, является ли пользователь администратором или другой ролью с безлимитным доступом
  if (store.user?.role && UNLIMITED_ROLES.includes(store.user.role)) {
    return "∞"; // Возвращаем символ бесконечности для безлимитных пользователей
  }

  // Если у пользователя нет тарифа, возвращаем 0
  if (!store.user?.tariff) {
    return 0;
  }

  // Получаем значение из хранилища
  const remaining = store.remainingGenerations(ContentType.IMAGE);

  // Если у пользователя есть тариф, но счетчики не инициализированы или равны нулю
  if (imagesLimit.value > 0) {
    // Если нет статистики использования или счетчик равен 0, и при этом оставшиеся генерации равны 0
    if (remaining === 0 && (!store.userStats || store.userStats.dailyImages === 0)) {
      // Проверяем, какой тариф у пользователя и возвращаем соответствующий лимит
      switch (store.user.tariff) {
        case TariffType.PREMIUM:
          return 8;  // Лимит для Премиум тарифа из бэкенда
        case TariffType.STANDARD:
          return 5;  // Лимит для Стандартного тарифа из бэкенда
        case TariffType.BASIC:
          return 2;  // Лимит для Базового тарифа из бэкенда
        default:
          return imagesLimit.value; // Используем значение из tariffInfo, если тариф не распознан
      }
    }
  }

  // Если у пользователя есть тариф и лимит, но счетчик показывает 0, принудительно обновляем статистику
  if (remaining === 0 && imagesLimit.value > 0 && store.userStats && store.userStats.dailyImages > 0) {
    console.log('[Profile] Detected inconsistency in image counts, refreshing stats...');
    // Запускаем обновление статистики, но не ждем его завершения, чтобы не блокировать UI
    store.updateUsageStats().catch(err => console.error('Error refreshing stats:', err));
  }

  return remaining;
});

// Переход на страницу тарифов
const goToTariffs = () => {
  router.push({ path: '/modes', query: { tab: 'tariffs' } });
};

// Загрузка данных профиля
const loadUserProfile = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    // Получаем данные пользователя из хранилища или загружаем, если их нет
    if (!store.user) {
      await store.initializeApp();
    }

    // Всегда обновляем информацию о тарифе при загрузке профиля
    // для получения актуальных данных
    console.log('Обновляем информацию о тарифе...');
    try {
      const tariffInfo = await store.fetchUserTariff();

      // Проверяем, что информация о тарифе загружена корректно
      if (!tariffInfo && store.user?.tariff) {
        console.warn('Не удалось загрузить информацию о тарифе, хотя тариф у пользователя есть. Повторяем попытку...');
        // Делаем еще одну попытку с задержкой
        await new Promise(resolve => setTimeout(resolve, 1000));
        await store.fetchUserTariff();
      }

      // Проверяем результат повторной попытки - убираем строгую проверку
      if (store.tariffInfo) {
        console.log('Информация о тарифе успешно загружена:', store.tariffInfo);
      } else {
        console.log('Информация о тарифе не загружена, но это может быть нормально для базового тарифа');
      }
    } catch (tariffError) {
      console.error('Error loading tariff information:', tariffError);
      error.value = 'Error loading tariff information. Please try refreshing the page.';
    }

    // Всегда обновляем статистику использования при загрузке профиля
    console.log('Обновляем статистику использования...');
    try {
      // Принудительно обновляем статистику с сервера
      await store.updateUsageStats();

      // Проверяем, что счетчики обновились корректно
      if (store.userStats) {
        console.log('Статистика использования обновлена:', {
          dailyGenerations: store.userStats.dailyGenerations,
          dailyImages: store.userStats.dailyImages
        });

        // Если счетчики не соответствуют ожидаемым значениям, пробуем еще раз
        if (store.user?.tariff === TariffType.PREMIUM &&
            store.userStats.dailyGenerations === 0 &&
            store.tariffInfo?.limits?.generations === 25) {
          console.log('Обнаружено несоответствие счетчиков, пробуем обновить еще раз...');
          await new Promise(resolve => setTimeout(resolve, 500)); // Небольшая задержка
          await store.updateUsageStats();
        }
      }
    } catch (statsError) {
      console.error('Ошибка при обновлении статистики:', statsError);
    }

    // Логируем текущие лимиты для отладки
    console.log('Текущие лимиты:', {
      tariffInfo: store.tariffInfo,
      userStats: store.userStats,
      generationsLimit: store.tariffInfo?.limits?.generations,
      imagesLimit: store.tariffInfo?.limits?.images,
      dailyGenerations: store.userStats?.dailyGenerations,
      dailyImages: store.userStats?.dailyImages
    });

    if (store.user) {
      userData.value = {
        name: store.user.first_name + (store.user.last_name ? ` ${store.user.last_name}` : ''),
        email: store.user.email || '',
        username: store.user.username || '',
        points: store.user.points || 0,
        invites: 0, // Это поле может отсутствовать в модели пользователя
        streak: 0, // Это поле может отсутствовать в модели пользователя
        photo_url: '' // Будет заполнено ниже, если доступно
      };

      // Получаем фото из Telegram WebApp, если доступно
      try {
        const telegramUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
        if (telegramUser && telegramUser.photo_url) {
          userData.value.photo_url = telegramUser.photo_url;
        }
      } catch (photoError) {
        console.error('Ошибка при получении фото из Telegram:', photoError);
      }

      console.log('Профиль пользователя загружен:', {
        user: store.user,
        tariffInfo: store.tariffInfo,
        userStats: store.userStats
      });

      // Загружаем статистику пользователя
      try {
        const stats = await apiClient.getUserStats();
        if (stats) {
          userData.value.points = stats.points || userData.value.points;
          userData.value.streak = stats.streak || userData.value.streak;
          userData.value.invites = stats.invites || userData.value.invites;
        }
      } catch (statsError) {
        // Проверяем, является ли ошибка 404 (API не реализован)
        const isNotFoundError = statsError?.response?.status === 404;
        if (!isNotFoundError) {
          console.error('Ошибка при загрузке статистики:', statsError);
        } else {
          console.log('API статистики не реализован, используем значения по умолчанию');
        }
      }

      // Загружаем достижения пользователя
      try {
        const achievementsData = await apiClient.get('/api/v1/users/achievements');
        if (achievementsData) {
          // Преобразуем данные API в формат для отображения
          achievements.value = [];
          
          // Добавляем недавно разблокированные достижения
          if (achievementsData.recent_unlocks && Array.isArray(achievementsData.recent_unlocks)) {
            achievementsData.recent_unlocks.forEach(unlock => {
              if (unlock.achievement) {
                achievements.value.push({
                  id: unlock.achievement.id,
                  icon: unlock.achievement.icon || '🏆',
                  name: unlock.achievement.name,
                  description: unlock.achievement.description,
                  unlocked: true,
                  progress: 100
                });
              }
            });
          }
          
          // Добавляем следующие доступные достижения
          if (achievementsData.next_achievements && Array.isArray(achievementsData.next_achievements)) {
            achievementsData.next_achievements.forEach(next => {
              achievements.value.push({
                id: next.id,
                icon: next.icon || '🎯',
                name: next.name,
                description: next.description,
                unlocked: false,
                progress: 0
              });
            });
          }
        }
      } catch (achievementsError) {
        console.error('Ошибка при загрузке достижений:', achievementsError);
        // Показываем пустой массив при ошибке
        achievements.value = [];
      }

      // Получаем реферальную ссылку
      try {
        const referralData = await apiClient.getReferralLink();
        if (referralData && referralData.link) {
          referralLink.value = referralData.link;
        }
      } catch (referralError) {
        console.error('Ошибка при загрузке реферальной ссылки:', referralError);
        // При ошибке показываем пустую строку
        referralLink.value = '';
      }

      // Получаем статистику рефералов
      try {
        const referralStats = await apiClient.getReferralStats();
        if (referralStats) {
          userData.value.invites = referralStats.total_invites || 0;
          userData.value.referralEarnings = referralStats.earned_points || 0;
        }
      } catch (statsError) {
        const isNotFoundError = statsError?.response?.status === 404;
        if (!isNotFoundError) {
          console.error('Ошибка при загрузке статистики рефералов:', statsError);
        } else {
          console.log('API статистики рефералов не реализован');
        }
      }
    } else {
      throw new Error('Не удалось получить данные пользователя');
    }
  } catch (e) {
    console.error('Error loading profile:', e);
    error.value = e instanceof Error ? e.message : 'An error occurred while loading the profile';
  } finally {
    isLoading.value = false;
  }
};

// Копирование реферальной ссылки
const copyReferralLink = async () => {
  try {
    await navigator.clipboard.writeText(referralLink.value);
    // Показываем уведомление в Telegram
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showPopup({
        title: 'Success',
        message: 'Referral link copied to clipboard',
        buttons: [{ type: 'ok' }]
      });
    }
  } catch (err) {
    console.error('Ошибка при копировании:', err);
    // Показываем ошибку в Telegram
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showPopup({
        title: 'Error',
        message: 'Failed to copy link',
        buttons: [{ type: 'ok' }]
      });
    }
  }
};

// Обработчик успешного применения промокода
const handlePromoCodeSuccess = async (result: any) => {
  console.log('Промокод успешно применен:', result);

  // Обновляем данные пользователя
  try {
    await store.initializeApp(); // Перезагружаем данные пользователя

    // Обновляем локальные данные
    if (store.user) {
      userData.value.points = store.user.points || 0;
    }

    // Show detailed notification about what user received
    let message = 'Promo code successfully applied!';
    if (result.points_added && result.points_added > 0) {
      message += ` Received ${result.points_added} points.`;
    }
    if (result.tariff_activated) {
      message += ` Activated plan ${result.tariff_activated}.`;
    }
    if (result.discount_applied && result.discount_applied > 0) {
      message += ` Received ${result.discount_applied}% discount.`;
    }

    toastService.success(message);

    // Show promo code history after successful application
    showPromoCodeHistory.value = true;

  } catch (error) {
    console.error('Ошибка при обновлении данных пользователя:', error);
  }
};

// Добавляем обработку для исправления отображения после плана урока
onMounted(() => {
  console.log('Profile view mounted');

  // Проверяем, откуда мы пришли (из localStorage)
  const lastRoute = localStorage.getItem('lastRoute');
  let fromLessonPlan = false;

  if (lastRoute) {
    try {
      const parsed = JSON.parse(lastRoute);
      if (parsed.path && parsed.path.includes('/lesson-plan')) {
        fromLessonPlan = true;
        console.log('Profile: детектирован переход с плана урока');
      }
    } catch (e) {
      console.error('Ошибка при чтении lastRoute:', e);
    }
  }

  // Если пришли с плана урока, принудительно делаем компонент видимым
  if (fromLessonPlan && profileViewRef.value) {
    // Делаем компонент видимым с задержкой (чтобы дать время другим процессам завершиться)
    setTimeout(() => {
      if (profileViewRef.value) {
        const el = profileViewRef.value;
        el.style.display = 'block';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
        el.style.zIndex = '10'; // Используем z-index контента

        // Проверяем, что основной контейнер виден
        const mainContent = document.querySelector('.main-content-container');
        if (mainContent) {
          (mainContent as HTMLElement).style.display = 'block';
          (mainContent as HTMLElement).style.visibility = 'visible';
          (mainContent as HTMLElement).style.opacity = '1';
        }

        console.log('Profile: принудительное восстановление видимости');
      }
    }, 100);

    // Дополнительно очищаем любые оставшиеся элементы плана урока
    setTimeout(() => {
      const lessonPlanElements = document.querySelectorAll('.lesson-plan-container');
      lessonPlanElements.forEach(el => {
        try {
          el.remove();
          console.log('Profile: удален оставшийся элемент плана урока');
        } catch (e) {
          console.error('Ошибка при удалении элемента плана урока:', e);
        }
      });
    }, 200);
  }

  // Загружаем данные профиля
  loadUserProfile();
});
</script>

<style>
/* Контейнер в стиле компонента упражнений */
.exercise-like-container {
  width: 100%;
  min-height: 100vh;
  padding: 50px 0 0;
  box-sizing: border-box;
  background-color: rgba(28, 5, 34, 0.3);
  backdrop-filter: blur(3px);
  overflow-x: hidden;
}

/* Стили для profile-view */
.profile-view {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50;

  /* Видимость */
  display: block;
  visibility: visible;
  opacity: 1;

  /* Скроллинг */
  overflow-y: auto;

  /* Предотвращение воздействия на другие элементы DOM */
  isolation: isolate;

  /* Не задаем фоновое изображение */
  background-color: transparent;
}

/* Блок с основным содержимым */
.content {
  max-width: 480px;
  margin: 0 auto;
  padding: 1rem;
  background-color: rgba(42, 8, 46, 0.25);
  backdrop-filter: blur(5px);
  border-radius: 16px;
}

/* Специальный элемент для создания отступа под навигацией */
.bottom-nav-spacer {
  width: 100%;
  height: 80px;
  display: block;
}

/* Заголовок */
.content h2 {
  color: white;
  font-size: 1.8rem;
  margin-bottom: 1rem;
  text-align: center;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

/* Стили для полей ввода и кнопок с нужным розовым цветом */
.form-input {
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  background-color: rgba(255, 204, 243, 0.7) !important;
  color: #333;
  outline: none;
}

/* Кнопка отправки */
.submit-btn {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 24px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  background-color: rgba(255, 204, 243, 0.7) !important;
  color: #333;
  transition: all 0.2s;
}

.submit-btn:hover {
  background-color: #ff67e7 !important;
  color: white;
  box-shadow: 0 0 15px rgba(255, 103, 231, 0.6);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Действия с результатом */
.result-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

/* Кнопки действий */
.action-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: rgba(255, 204, 243, 0.7) !important;
  color: #333;
  transition: all 0.2s;
}

.action-button:hover {
  background-color: #ff67e7 !important;
  color: white;
}

/* Стили для групп формы с нужным фиолетовым цветом */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background-color: rgba(42, 8, 46, 0.25) !important;
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

.form-group label {
  color: white;
  font-weight: 500;
}

/* Контейнер для отправки формы */
.form-actions {
  background-color: rgba(42, 8, 46, 0.25) !important;
  border-radius: 16px;
  padding: 1rem;
  margin-top: 1rem;
}

/* Индикатор загрузки */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.loader {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #ff67e7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading p {
  color: white;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Стили для ошибки */
.error {
  background-color: rgba(220, 53, 69, 0.2);
  border-left: 4px solid #dc3545;
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 0 10px 10px 0;
  position: relative;
  color: white;
}

.error-close {
  position: absolute;
  top: 5px;
  right: 5px;
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
}

/* Стили для информации о пользователе */
.user-info-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  background-color: rgba(255, 204, 243, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-initials {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
}

.user-details {
  flex: 1;
}

.user-details h3 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.user-details p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Стили для статистики */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.stat-item {
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 16px;
  padding: 0.75rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 0.8rem;
  color: #333;
  opacity: 0.8;
}

/* Стили для информации о тарифе */
.tariff-info {
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.tariff-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.tariff-row:last-child {
  margin-bottom: 0;
}

.tariff-label {
  color: #333;
  opacity: 0.8;
}

.tariff-value {
  font-weight: bold;
  color: #333;
}

.expiring-soon {
  color: #ff9800 !important;
}

/* Стили для достижений */
.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.achievement-item {
  background-color: rgba(255, 204, 243, 0.4);
  border-radius: 16px;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.achievement-unlocked {
  background-color: rgba(255, 204, 243, 0.7);
}

.achievement-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.achievement-details h4 {
  color: #333;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.achievement-details p {
  color: #333;
  opacity: 0.8;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.achievement-progress {
  width: 100%;
  height: 4px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.achievement-progress-bar {
  height: 100%;
  background-color: #ff67e7;
  border-radius: 2px;
}

.empty-achievements {
  text-align: center;
  padding: 1rem;
  color: rgba(255, 255, 255, 0.7);
}

/* Стили для промокодов */
.promocode-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.promocode-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.promocode-info {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin: 0;
}

.action-button.secondary {
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-button.secondary:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* Стили для реферальной системы */
.referral-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.referral-input-group {
  display: flex;
  gap: 0.5rem;
}

.referral-stats {
  display: flex;
  gap: 1rem;
  margin: 0.75rem 0;
}

.referral-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  flex: 1;
}

.referral-stat .stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.referral-stat .stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0.25rem;
}

.referral-info {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Фиксы для мобильных устройств */
@media (max-width: 768px) {
  .achievements-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
