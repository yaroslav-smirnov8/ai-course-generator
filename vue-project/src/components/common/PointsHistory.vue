<template>
  <div class="bg-gray-800 rounded-lg p-6">
    <h2 class="text-xl font-bold text-white mb-4">Points History</h2>

    <!-- Filter Tabs -->
    <div class="flex space-x-2 mb-6 overflow-x-auto">
      <button
        v-for="type in ['all', 'generation', 'purchase', 'reward', 'refund', 'achievement']"
        :key="type"
        class="px-3 py-2 rounded-lg text-sm whitespace-nowrap"
        :class="filter === type
          ? 'bg-purple-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        @click="handleFilterChange(type)"
      >
        {{ type.charAt(0).toUpperCase() + type.slice(1) }}
      </button>
    </div>

    <!-- Transactions List -->
    <div v-if="transactions.length === 0 && !loading" class="text-center py-8 text-gray-400">
      No transactions found
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="transaction in transactions"
        :key="transaction.id"
        class="bg-gray-700 rounded-lg p-4"
      >
        <div class="flex justify-between items-start mb-2">
          <div>
            <TransactionBadge :type="transaction.type" />
            <p class="text-gray-300 mt-1">{{ transaction.description }}</p>
          </div>
          <div
            class="text-xl font-bold"
            :class="transaction.amount > 0 ? 'text-green-400' : 'text-red-400'"
          >
            {{ transaction.amount > 0 ? '+' : '' }}{{ transaction.amount }}
          </div>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-400">{{ formatDate(transaction.created_at) }}</span>
          <span class="text-gray-400">Balance: {{ transaction.balance_after }}</span>
        </div>
      </div>

      <!-- Load More Button -->
      <button
        v-if="hasMore"
        class="w-full py-3 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors mt-4"
        @click="loadMore"
        :disabled="loading"
      >
        {{ loading ? 'Loading...' : 'Load More' }}
      </button>
    </div>

    <!-- Loading Indicator -->
    <div v-if="loading && page === 1" class="flex justify-center py-8">
      <div class="w-8 h-8 border-2 border-gray-300 border-t-purple-600 rounded-full animate-spin"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useMainStore } from '@/store';

// Helper component
const TransactionBadge = {
  props: {
    type: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const colors = {
      'generation': 'bg-red-500',
      'purchase': 'bg-green-500',
      'reward': 'bg-purple-500',
      'refund': 'bg-blue-500',
      'invite_bonus': 'bg-yellow-500',
      'achievement': 'bg-pink-500',
      'admin_correction': 'bg-gray-500'
    };

    const badgeClass = computed(() => {
      return `${colors[props.type] || 'bg-gray-500'} text-white text-xs px-2 py-1 rounded-full`;
    });

    return { badgeClass };
  },
  template: `
    <span :class="badgeClass">
      {{ type }}
    </span>
  `
};

// Format date helper function
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Main component setup
const store = useMainStore();
const transactions = ref([]);
const loading = ref(true);
const page = ref(1);
const hasMore = ref(true);
const filter = ref('all');

// Watch for changes in page or filter
watch([page, filter], () => {
  loadTransactions();
});

// Load transactions from API
const loadTransactions = async () => {
  try {
    loading.value = true;
    const response = await store.getPointsTransactions(
      page.value,
      10,
      filter.value !== 'all' ? filter.value : null
    );

    if (response.items.length === 0) {
      hasMore.value = false;
    } else {
      transactions.value = page.value === 1
        ? response.items
        : [...transactions.value, ...response.items];
    }
  } catch (error) {
    console.error('Error loading transactions:', error);
  } finally {
    loading.value = false;
  }
};

// Load more transactions
const loadMore = () => {
  if (!loading.value && hasMore.value) {
    page.value++;
  }
};

// Handle filter change
const handleFilterChange = (newFilter) => {
  filter.value = newFilter;
  page.value = 1;
  hasMore.value = true;
};

// Initial load on component mount
onMounted(() => {
  loadTransactions();
});
</script>
