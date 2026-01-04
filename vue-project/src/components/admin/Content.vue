# src/components/admin/Content.vue
<template>
  <div class="space-y-6">
    <PageHeader
      title="Content Management"
      description="Manage and monitor content generation across the platform"
    >
      <template #actions>
        <Button @click="exportData" variant="default">
          <DownloadIcon class="w-4 h-4 mr-2" />
          Export Data
        </Button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <AdminFilters
      @filter="handleFilter"
      @export="handleExport"
      :showAdditionalFilters="true"
      :additionalFilters="filterOptions"
    />

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
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
      <StatCard
        title="Active Users"
        :value="stats.activeUsers"
        :trend="stats.usersTrend"
        icon="Users"
      />
    </div>

    <!-- Content Table -->
    <PageContent>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-900">
          <tr>
            <th class="p-4 text-left text-gray-400">ID</th>
            <th class="p-4 text-left text-gray-400">Type</th>
            <th class="p-4 text-left text-gray-400">User ID</th>
            <th class="p-4 text-left text-gray-400">Created</th>
            <th class="p-4 text-left text-gray-400">Status</th>
            <th class="p-4 text-left text-gray-400">Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr
            v-for="item in content"
            :key="item.id"
            class="border-t border-gray-700 hover:bg-gray-700/50"
          >
            <td class="p-4">{{ item.id }}</td>
            <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="getTypeClass(item.type)"
                >
                  {{ formatType(item.type) }}
                </span>
            </td>
            <td class="p-4">
              <div class="flex items-center gap-2">
                {{ item.user_id }}
                <button
                  @click="viewUser(item.user_id)"
                  class="text-blue-400 hover:text-blue-300"
                >
                  <EyeIcon class="w-4 h-4" />
                </button>
              </div>
            </td>
            <td class="p-4 text-gray-400">
              {{ formatDate(item.created_at) }}
            </td>
            <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="getStatusClass(item.status)"
                >
                  {{ item.status }}
                </span>
            </td>
            <td class="p-4">
              <div class="flex gap-2">
                <button
                  @click="viewContent(item)"
                  class="text-blue-400 hover:text-blue-300"
                >
                  <EyeIcon class="w-5 h-5" />
                </button>
                <button
                  @click="deleteContent(item.id)"
                  class="text-red-400 hover:text-red-300"
                >
                  <TrashIcon class="w-5 h-5" />
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="mt-4">
        <AdminPagination
          v-model:page="currentPage"
          :total="totalItems"
          :per-page="perPage"
          @update:perPage="handlePerPageChange"
        />
      </div>
    </PageContent>

    <!-- Content View Modal -->
    <Dialog v-model:open="showContentModal">
      <DialogContent class="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Content Details</DialogTitle>
        </DialogHeader>

        <div class="space-y-4" v-if="selectedContent">
          <div class="flex justify-between text-sm text-gray-400 mb-2">
            <span>Type: {{ formatType(selectedContent.type) }}</span>
            <span>Created: {{ formatDate(selectedContent.created_at) }}</span>
          </div>

          <div class="bg-gray-900 rounded-lg p-4 overflow-auto max-h-96">
            <pre class="text-gray-300 whitespace-pre-wrap">{{ selectedContent.content }}</pre>
          </div>

          <div class="mt-4 bg-gray-900 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-400 mb-2">Prompt</h4>
            <p class="text-gray-300">{{ selectedContent.prompt }}</p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" @click="showContentModal = false">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import { formatDate } from '@/utils/date'
import {
  Download as DownloadIcon,
  Eye as EyeIcon,
  Trash as TrashIcon
} from 'lucide-vue-next'

// Components
import PageHeader from './common/PageHeader.vue'
import PageContent from './PageContent.vue'
import AdminFilters from './common/AdminFilters.vue'
import AdminPagination from './common/AdminPagination.vue'
import StatCard from './cards/StatCard.vue'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'

// Store
const store = useMainStore()

import type { Generation } from '@/types'
import {ContentType} from "@/types/enums";

// Types
type ContentItem = Generation;

interface ContentStats {
  totalGenerations: number;
  generationsTrend: number;
  successRate: number;
  successRateTrend: number;
  activeUsers: number;
  usersTrend: number;
}

interface GenerationStats {
  generations: Generation[];
  total: number;
  total_generations: number;
  by_type: {
    lesson_plans: number;
    exercises: number;
    games: number;
    images: number;
  };
  popular_prompts: Array<{
    prompt: string;
    count: number;
  }>;
}

// State
const content = ref<Generation[]>([]);
const currentPage = ref(1);
const perPage = ref(10);
const totalItems = ref(0);
const showContentModal = ref(false);
const selectedContent = ref<ContentItem | null>(null);
const stats = ref<ContentStats>({
  totalGenerations: 0,
  generationsTrend: 0,
  successRate: 0,
  successRateTrend: 0,
  activeUsers: 0,
  usersTrend: 0
});

// Filter options
const filterOptions = [
  { value: 'lesson_plan', label: 'Lesson Plans' },
  { value: 'exercise', label: 'Exercises' },
  { value: 'game', label: 'Games' },
  { value: 'image', label: 'Images' },
  { value: 'text_analysis', label: 'Text Analysis' },
  { value: 'concept_explanation', label: 'Concept Explanation' },
  { value: 'course', label: 'Courses' },
  { value: 'free_query', label: 'AI Assistant' }
];

// Methods
const loadContent = async () => {
  try {
    const response = await store.getGenerationStatistics({
      page: currentPage.value,
      perPage: perPage.value
    });

    // Явно приведем тип массива к Generation[]
    content.value = response.generations as Generation[];
    totalItems.value = response.total;

    stats.value = {
      totalGenerations: response.total_generations,
      generationsTrend: 5.2,
      successRate: 98.5,
      successRateTrend: 0.5,
      activeUsers: 150,
      usersTrend: 12.3
    };
  } catch (error) {
    console.error('Error loading content:', error);
  }
};

const formatType = (type: ContentType): string => {
  const types = {
    [ContentType.LESSON_PLAN]: 'Lesson Plan',
    [ContentType.EXERCISE]: 'Exercise',
    [ContentType.GAME]: 'Game',
    [ContentType.IMAGE]: 'Image',
    [ContentType.TRANSCRIPT]: 'Transcript',
    [ContentType.TEXT_ANALYSIS]: 'Text Analysis',
    [ContentType.CONCEPT_EXPLANATION]: 'Concept Explanation',
    [ContentType.COURSE]: 'Course',
    [ContentType.FREE_QUERY]: 'AI Assistant'
  };
  return types[type] || type;
};

const getTypeClass = (type: ContentType): string => {
  const classes = {
    [ContentType.LESSON_PLAN]: 'bg-blue-500/20 text-blue-300',
    [ContentType.EXERCISE]: 'bg-green-500/20 text-green-300',
    [ContentType.GAME]: 'bg-yellow-500/20 text-yellow-300',
    [ContentType.IMAGE]: 'bg-purple-500/20 text-purple-300',
    [ContentType.TRANSCRIPT]: 'bg-pink-500/20 text-pink-300',
    [ContentType.TEXT_ANALYSIS]: 'bg-indigo-500/20 text-indigo-300',
    [ContentType.CONCEPT_EXPLANATION]: 'bg-orange-500/20 text-orange-300',
    [ContentType.COURSE]: 'bg-teal-500/20 text-teal-300',
    [ContentType.FREE_QUERY]: 'bg-cyan-500/20 text-cyan-300'
  };
  return classes[type] || 'bg-gray-500/20 text-gray-300';
};

const getStatusClass = (status: 'success' | 'error'): string => {
  const classes = {
    'success': 'bg-green-500/20 text-green-300',
    'error': 'bg-red-500/20 text-red-300'
  };
  return classes[status];
};

const viewContent = (contentItem: ContentItem) => {
  selectedContent.value = contentItem;
  showContentModal.value = true;
};

const viewUser = async (userId: number) => {
  if (userId) {
    try {
      await store.openUserModal(userId);
    } catch (error) {
      console.error('Error opening user modal:', error);
    }
  }
};

const deleteContent = async (contentId: number) => {
  if (confirm('Are you sure you want to delete this content?')) {
    try {
      await store.deleteContent(contentId);
      await loadContent();
    } catch (error) {
      console.error('Error deleting content:', error);
    }
  }
};

const handleFilter = (filters: any) => {
  // Apply filters and reload content
  loadContent();
};

const handleExport = async () => {
  try {
    await store.exportGenerationsData();
  } catch (error) {
    console.error('Error exporting data:', error);
  }
};

const handlePerPageChange = (newPerPage: number) => {
  perPage.value = newPerPage;
  currentPage.value = 1; // Reset to first page when changing items per page
  loadContent();
};

const exportData = () => handleExport();

// Watch for changes
watch([currentPage], () => {
  loadContent();
});

// Initialize
onMounted(() => {
  loadContent();
});
</script>

<style scoped>
.content-modal {
  max-width: 800px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
