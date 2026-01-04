<!-- src/views/Modes.vue -->
<template>
  <div ref="modesViewRef" class="modes-view" data-view="modes">
    <header class="p-6 text-center">
      <h1 class="text-2xl font-bold text-white mb-2">Plans and Points</h1>
      <p class="text-gray-300 text-sm">
        Purchase plans to save points or buy points separately
      </p>
    </header>

    <!-- Balance -->
    <div class="points-display p-4 mx-4 rounded-xl mb-6 bg-gradient-to-r from-purple-800/50 to-purple-500/30">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-lg text-white">Your Balance</h2>
          <div class="text-3xl font-bold text-purple-400 mt-1">
            {{ user?.points || 0 }} ⭐
          </div>
        </div>
        <button
          @click="isPointsModalOpen = true"
          class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          Buy Points
        </button>
      </div>
    </div>

    <!-- Current tariff information -->
    <div v-if="currentTariffInfo" class="mx-4 p-4 mb-6 bg-green-500/20 rounded-xl">
      <h3 class="text-white font-medium">Current Plan: <span class="text-green-400 font-bold">{{ currentTariffInfo.name }}</span></h3>
      <p v-if="tariffExpiry" class="text-sm text-gray-300 mt-1">
        Valid until: {{ formatDate(tariffExpiry) }}
      </p>
      <div v-if="daysUntilExpiry > 0" class="mt-2 bg-blue-500/20 p-2 rounded">
        <p class="text-sm">
          {{ daysUntilExpiry }} {{ getDaysWord(daysUntilExpiry) }} left
        </p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs flex border-b border-gray-700 px-4 mb-6">
      <button
        @click="activeTab = 'tariffs'"
        class="py-3 px-4 text-sm font-medium"
        :class="activeTab === 'tariffs' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'"
      >
        Plans
      </button>
      <button
        @click="activeTab = 'points'"
        class="py-3 px-4 text-sm font-medium"
        :class="activeTab === 'points' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'"
      >
        Points
      </button>
    </div>

    <!-- Tariffs -->
    <div v-if="activeTab === 'tariffs'" class="tariffs-grid px-4 grid gap-4">
      <div
        v-for="tariff in availableTariffs"
        :key="tariff.type"
        class="tariff-card p-6 rounded-xl relative overflow-hidden border-2"
        :class="[
          isCurrentTariff(tariff.type) ? 'bg-green-500/20 border-green-500' : 'bg-gray-800/50 border-gray-700',
          isLowerTier(tariff.type) ? 'opacity-60' : ''
        ]"
      >
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-xl font-bold text-white">{{ tariff.name }}</h3>
            <p class="text-gray-400 text-sm mt-1">{{ getDailyValue(tariff.limits.generations) }} generations per day</p>
          </div>
          <div
            v-if="isCurrentTariff(tariff.type)"
            class="bg-green-500 text-white text-xs px-2 py-1 rounded">
            Active
          </div>
        </div>

        <div class="bg-purple-500/20 p-3 rounded-lg mb-4">
          <p class="text-purple-300 text-sm">Total for 30 days: <span class="font-bold">{{ tariff.limits.generations * 30 }} generations</span></p>
        </div>

        <ul class="space-y-2 mb-6">
          <li class="flex items-center text-gray-300">
            <span class="mr-2 text-green-500">✓</span>
            {{ tariff.limits.generations }} generations per day
          </li>
          <li class="flex items-center text-gray-300">
            <span class="mr-2 text-green-500">✓</span>
            {{ tariff.limits.images }} images per day
          </li>
          <li v-for="(value, key) in getTariffFeatures(tariff)" :key="key" class="flex items-center text-gray-300">
            <span class="mr-2 text-green-500">✓</span>
            {{ formatFeatureName(key) }}
          </li>
        </ul>

        <div class="flex gap-2 mt-4">
          <button
            @click="purchaseTariff(tariff.type)"
            class="w-full py-3 rounded-lg font-medium text-sm"
            :class="[
    isLowerTier(tariff.type) ?
      'bg-gray-600 text-gray-400' :
      'bg-blue-600 text-white hover:bg-blue-700'
  ]"
            :disabled="isButtonDisabled(tariff.type)"
          >
            {{ getPurchaseButtonText(tariff.type) }}
          </button>
        </div>
      </div>
    </div>

    <!-- Points packages -->
    <div v-if="activeTab === 'points'" class="points-packages px-4 grid gap-4">
      <div
        v-for="pkg in pointsPackages"
        :key="pkg.id"
        class="package-card p-6 rounded-xl bg-gray-800/50 border-2 border-gray-700"
        :class="{ 'border-yellow-500': pkg.isPopular }"
      >
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-xl font-bold text-white">{{ pkg.points }} points</h3>
            <div class="flex items-center mt-1">
              <span class="text-gray-400 text-sm">Price:</span>
              <span class="ml-1 font-medium text-white">{{ pkg.price }} ₽</span>
            </div>
          </div>
          <div
            v-if="pkg.isPopular"
            class="bg-yellow-500 text-gray-900 text-xs px-2 py-1 rounded">
            Popular
          </div>
        </div>

        <div class="mb-4 p-3 rounded" :class="calculateValue(pkg) > 0 ? 'bg-red-500/20' : 'bg-green-500/20'">
          <p class="text-white text-sm">
            <span :class="calculateValue(pkg) > 0 ? 'text-red-400' : 'text-green-400'">
              {{ calculateValue(pkg) > 0
              ? `${calculateValue(pkg)}% more expensive than plan`
              : 'Great deal!' }}
            </span>
            <br>{{ calculateValue(pkg) > 0
            ? 'Recommended to buy points only if plan has expired'
            : 'Good price for individual points' }}
          </p>
        </div>

        <button
          @click="buyPoints(pkg.points, pkg.price)"
          class="w-full py-3 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 text-white"
          :disabled="isPurchasing"
        >
          Buy for {{ pkg.price }} ₽
        </button>
      </div>
    </div>

    <!-- Modal window for buying points -->
    <div v-if="isPointsModalOpen" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full m-4">
        <h3 class="text-xl font-bold text-white mb-4">Buy Points</h3>

        <div class="space-y-4">
          <div
            v-for="pkg in pointsPackages"
            :key="pkg.id"
            class="p-4 border rounded-lg border-gray-700 flex justify-between items-center"
            :class="{ 'border-yellow-500 bg-yellow-500/10': pkg.isPopular }"
          >
            <div>
              <p class="font-medium text-white">{{ pkg.points }} points</p>
              <p class="text-gray-400 text-sm">{{ pkg.price }} ₽</p>
            </div>
            <button
              @click="buyPoints(pkg.points, pkg.price); isPointsModalOpen = false"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
              :disabled="isPurchasing"
            >
              Buy
            </button>
          </div>
        </div>

        <div class="flex justify-end mt-6">
          <button
            @click="isPointsModalOpen = false"
            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="isPurchasing" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-gray-800 p-6 rounded-xl">
        <div class="w-12 h-12 border-4 border-t-transparent border-purple-500 rounded-full animate-spin mx-auto"></div>
        <p class="mt-4 text-white">Please wait...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Добавляем типизацию для window.cleanupDOM
declare global {
  interface Window {
    cleanupDOM?: () => void;
  }
}

import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useMainStore } from '@/store'
import { useRoute } from 'vue-router'
import { TariffType } from '@/core/constants'
import type { TariffInfo, UserTariffHistory } from '@/types'
import { tariffService } from '@/services/tariffService'

// Define interface for points package
interface PointsPackage {
  id: number;
  points: number;
  price: number;
  isPopular: boolean;
}

const store = useMainStore()
const route = useRoute()
const activeTab = ref('tariffs')
const isPointsModalOpen = ref(false)
const isPurchasing = ref(false)

// Predefined tariffs in case loading from server fails
const defaultTariffs: TariffInfo[] = [
  {
    type: TariffType.BASIC,
    name: 'Basic',
    pricePoints: 400,
    limits: {
      generations: 6,
      images: 2
    },
    features: ['save_templates'], // Changed from object to string array
    validUntil: null
  },
  {
    type: TariffType.STANDARD,
    name: 'Standard',
    pricePoints: 650,
    limits: {
      generations: 12,
      images: 5
    },
    features: ['priority_queue', 'save_templates'], // Changed from object to string array
    validUntil: null
  },
  {
    type: TariffType.PREMIUM,
    name: 'Premium',
    pricePoints: 900,
    limits: {
      generations: 25,
      images: 8
    },
    features: ['priority_queue', 'save_templates', 'advanced_generation', 'custom_requests', 'course_generation'], // Changed from object to string array
    validUntil: null
  }
];

const availableTariffs = ref<TariffInfo[]>(defaultTariffs)

// User info
const user = computed(() => store.user)

// Tariff info
const currentTariffInfo = computed(() => store.currentTariffInfo)
const tariffExpiry = computed(() => store.tariffValidUntil)
const daysUntilExpiry = computed(() => store.daysLeftUntilTariffExpiry)
const isTariffActive = computed(() => store.isTariffActive)

// Check current tariff
const isCurrentTariff = (tariffType: TariffType): boolean => {
  if (!user.value || !user.value.tariff) return false;
  return user.value.tariff === tariffType;
}

// Check for tariff lower than current
const isLowerTier = (tariffType: TariffType): boolean => {
  // If user doesn't have a tariff, nothing is considered lower tier
  if (!user.value?.tariff) return false;

  const tierValues = {
    [TariffType.BASIC]: 1,
    [TariffType.STANDARD]: 2,
    [TariffType.PREMIUM]: 3
  };

  // Get numeric values for comparison
  const currentTierValue = tierValues[user.value.tariff as TariffType] || 0;
  const targetTierValue = tierValues[tariffType] || 0;

  // Return true if the target tier is lower than current tier
  return targetTierValue < currentTierValue;
}

// Get text for purchase button
const getPurchaseButtonText = (tariffType: TariffType): string => {
  if (isCurrentTariff(tariffType)) {
    return 'Current Plan';
  } else if (isLowerTier(tariffType)) {
    return 'Unavailable';
  } else {
    return `${getTariffPrice(tariffType)} ₽ / 30 days`;
  }
}

// Get tariff price in rubles
const getTariffPrice = (tariffType: TariffType): number => {
  // Return prices in rubles according to constants
  switch (tariffType) {
    case TariffType.BASIC:
      return 400;
    case TariffType.STANDARD:
      return 650;
    case TariffType.PREMIUM:
      return 900;
    default:
      return 0;
  }
}

// Get number of generations per day
const getDailyValue = (value: number): string => {
  return value.toString()
}

// Get tariff features
const getTariffFeatures = (tariff: TariffInfo): Record<string, boolean> => {
  // Convert string array to object with boolean values
  const featuresObj: Record<string, boolean> = {};
  (tariff.features || []).forEach(feature => {
    featuresObj[feature] = true;
  });
  return featuresObj;
}

// Format feature name
const formatFeatureName = (feature: string): string => {
  const names: Record<string, string> = {
    'priority_queue': 'Priority Queue',
    'save_templates': 'Save Templates',
    'advanced_generation': 'Advanced Generation',
    'api_access': 'API Access',
    'export_to_pdf': 'Export to PDF',
    'team_access': 'Team Access',
    'custom_requests': 'Custom Requests',
    'course_generation': 'Course Generation'
  }

  return names[feature] || feature
}

// Declension of the word "day"
const getDaysWord = (days: number): string => {
  const lastDigit = days % 10
  const lastTwoDigits = days % 100

  if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
    return 'days'
  }

  if (lastDigit === 1) {
    return 'day'
  }

  if (lastDigit >= 2 && lastDigit <= 4) {
    return 'days'
  }

  return 'days'
}

// Date formatting
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Unlimited'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })
}

// Points packages
const pointsPackages = ref<PointsPackage[]>([
  {
    id: 1,
    points: 45,
    price: 120,
    isPopular: false
  },
  {
    id: 2,
    points: 100,
    price: 250,
    isPopular: true
  }
])

// Calculate value of tariffs compared to buying points
const calculateValue = (pkg: PointsPackage): number => {
  // Tariff data (even if not loaded from server)
  const tariffs = [
    { name: 'Basic', price: 400, dailyPoints: 6, totalPoints: 180 },
    { name: 'Standard', price: 650, dailyPoints: 12, totalPoints: 360 },
    { name: 'Maximum', price: 900, dailyPoints: 25, totalPoints: 750 }
  ]

  // Take basic tariff for comparison (best value per point)
  const basicTariff = tariffs.reduce((best, current) => {
    const currentCostPerPoint = current.price / current.totalPoints;
    const bestCostPerPoint = best.price / best.totalPoints;
    return currentCostPerPoint < bestCostPerPoint ? current : best;
  }, tariffs[0]);

  // Calculate price per point in package
  const pricePerPoint = pkg.price / pkg.points;

  // Calculate price per point in basic tariff
  const tariffPricePerPoint = basicTariff.price / basicTariff.totalPoints;

  // Calculate percentage of overpayment when buying points separately
  // Formula: (price_per_point_in_package / price_per_point_in_tariff - 1) * 100%
  const overchargePercent = Math.round((pricePerPoint / tariffPricePerPoint - 1) * 100);

  return overchargePercent;
}

// Purchase tariff
const purchaseTariff = async (tariffType: TariffType) => {
  // Prevent multiple purchases of the same tariff
  if (isLowerTier(tariffType) || isCurrentTariff(tariffType) || isPurchasing.value) return;

  isPurchasing.value = true;

  try {
    const success = await store.updateUserTariff(tariffType);

    if (success) {
      // Force reload both user data and tariff data with a clean slate
      localStorage.removeItem('user_stats');  // Clear any local storage cache

      // Update all relevant data
      await Promise.all([
        store.fetchCurrentUser(),
        store.fetchUserTariff(),
        store.getUserStatistics(),  // Force refresh of usage statistics
        loadTariffs()
      ]);

      // Wait a moment for changes to propagate
      setTimeout(() => {
        store.setMessage(`Plan successfully activated. Limits reset.`);
      }, 500);
    }
  } catch (error: any) {
    console.error('Error purchasing tariff:', error);
    // Error handling logic...
  } finally {
    isPurchasing.value = false;
  }
}

const userHasPurchasedTariff = computed(() => {
  return (tariffType: TariffType) => {
    // If we have tariff history, check it
    if (store.tariffHistory && store.tariffHistory.length > 0) {
      return store.tariffHistory.some((history: UserTariffHistory) =>
        history.tariff_type === tariffType
      );
    }

    // Otherwise just check current tariff
    return store.user?.tariff === tariffType;
  }
});

const isButtonDisabled = (tariffType: TariffType): boolean => {
  // Disable if it's current tariff, lower tier, or during purchase
  return isCurrentTariff(tariffType) ||
    isLowerTier(tariffType) ||
    isPurchasing.value;
}

// Extend tariff
const extendTariff = async () => {
  if (isPurchasing.value || !currentTariffInfo.value) return
  isPurchasing.value = true

  try {
    const success = await store.extendCurrentTariff(1) // Extension for 1 month

    if (success) {
      // Update data after extension
      await loadTariffs()
    }
  } catch (error) {
    console.error('Error extending tariff:', error)
    store.setError('Error extending plan')
  } finally {
    isPurchasing.value = false
  }
}

// Buy points
const buyPoints = async (points: number, price: number) => {
  if (isPurchasing.value) return
  isPurchasing.value = true

  try {
    // For demo purposes, just add points without real payment
    await store.addPoints(points, 'purchase')

    // Update user data
    await store.fetchCurrentUser()
    store.setMessage(`Successfully purchased ${points} points`)
  } catch (error) {
    console.error('Error purchasing points:', error)
    store.setError('Error purchasing points')
  } finally {
    isPurchasing.value = false
  }
}

// Loading tariffs
const loadTariffs = async () => {
  try {
    // Load available tariffs
    const loadedTariffs = await tariffService.getAvailableTariffs();
    if (loadedTariffs && loadedTariffs.length > 0) {
      availableTariffs.value = loadedTariffs as TariffInfo[];
    } else {
      // If loading failed, use default tariffs
      availableTariffs.value = defaultTariffs;
    }

    // Load information about user's current tariff
    await store.fetchUserTariff();
  } catch (error) {
    console.error('Error loading tariffs:', error);
    // In case of error, use default tariffs
    availableTariffs.value = defaultTariffs;
    store.setError('Failed to load current plans');
  }
}

// Add ref for root element
const modesViewRef = ref<HTMLElement | null>(null);

onMounted(() => {
  console.log('Modes: component is mounting');

  // Load tariffs on mount
  loadTariffs();

  // Check tab parameter in URL and set active tab
  if (route.query.tab) {
    const tabParam = route.query.tab.toString();
    if (tabParam === 'tariffs' || tabParam === 'points') {
      activeTab.value = tabParam;
      console.log(`Modes: active tab set from URL: ${tabParam}`);
    }
  }

  // Delay for safe component mounting
  setTimeout(() => {
    // Force make component visible
    if (modesViewRef.value) {
      modesViewRef.value.style.display = 'block';
      modesViewRef.value.style.visibility = 'visible';
      modesViewRef.value.style.opacity = '1';
      modesViewRef.value.style.zIndex = '30';
      console.log('Modes: component visibility forcibly set');
    }

    // Check if there was a transition from LessonPlan
    const lastRoute = localStorage.getItem('lastLessonPlanRoute');
    const lessonPlanUnmounted = localStorage.getItem('lessonPlanUnmounted');

    if (lastRoute && lastRoute.includes('lesson-plan') || lessonPlanUnmounted) {
      console.log('Modes: detected transition from LessonPlan, performing additional cleanup');

      // Safely remove all elements related to LessonPlan
      safelyRemoveElements();

      // Clear transition flags
      localStorage.removeItem('lastLessonPlanRoute');
      localStorage.removeItem('lessonPlanUnmounted');
    }

    // Add event handler for lessonplan-unmounted
    document.addEventListener('lessonplan-unmounted', handleLessonPlanUnmounted);

    // Add event handler for games-unmounted
    document.addEventListener('games-unmounted', handleGamesUnmounted);
  }, 100); // Small delay for DOM stabilization
});

// Extract element removal logic to a separate function for reuse
const safelyRemoveElements = () => {
  // Hide all elements related to LessonPlan
  const selectors = [
    '.lesson-plan-container',
    '[data-component="lesson-plan"]',
    '.planet-background',
    '.simple-toast-container',
    '.form-group',
    '.title-form-group',
    '.generation-form',
    '.result-container',
    '.plan-content'
  ];

  selectors.forEach(selector => {
    try {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        console.log(`Modes: found ${elements.length} elements by selector ${selector}`);
        elements.forEach(el => {
          try {
            if (el instanceof HTMLElement) {
              // Completely hide element
              el.style.display = 'none';
              el.style.visibility = 'hidden';
              el.style.opacity = '0';
              el.style.pointerEvents = 'none';
              el.style.position = 'absolute';
              el.style.left = '-9999px';
              el.style.top = '-9999px';
              el.style.width = '0';
              el.style.height = '0';
              el.style.overflow = 'hidden';
              console.log(`Modes: hidden element ${selector}`);
            }
          } catch (e) {
            console.error(`Modes: error hiding element ${selector}:`, e);
          }
        });
      }
    } catch (err) {
      console.error(`Modes: error searching for elements by selector ${selector}:`, err);
    }
  });

  // Call global DOM cleanup function
  if (typeof window.cleanupDOM === 'function') {
    try {
      window.cleanupDOM();
      console.log('Modes: global DOM cleanup function called');
    } catch (e) {
      console.error('Modes: error calling global DOM cleanup function:', e);
    }
  }
};

// Event handler for lessonplan-unmounted
const handleLessonPlanUnmounted = () => {
  console.log('Modes: received lessonplan-unmounted event');

  // Use setTimeout for safe execution after DOM update
  setTimeout(() => {
    // Safely remove elements
    safelyRemoveElements();
  }, 50);
};

// Event handler for games-unmounted
const handleGamesUnmounted = () => {
  console.log('Modes: received games-unmounted event');

  // Use setTimeout for safe execution after DOM update
  setTimeout(() => {
    // Safely remove elements
    safelyRemoveElements();
  }, 50);
};

onBeforeUnmount(() => {
  console.log('Modes: component is unmounting');

  // Remove event handlers
  document.removeEventListener('lessonplan-unmounted', handleLessonPlanUnmounted);
  document.removeEventListener('games-unmounted', handleGamesUnmounted);
});
</script>

<style scoped>
.modes-view {
  min-height: 100vh;
  width: 100%;
  display: block;
  visibility: visible;
  opacity: 1;
  z-index: 30;
  position: relative;
}

.tariffs-grid, .points-packages {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

@media (max-width: 640px) {
  .tariffs-grid, .points-packages {
    grid-template-columns: 1fr;
  }
}
</style>
