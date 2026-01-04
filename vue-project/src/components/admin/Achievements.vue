<template>
  <div class="space-y-6">
    <PageHeader
      title="Achievements"
      description="Manage user achievement system"
    >
      <template #actions>
        <Button @click="openCreateModal" variant="default">
          <PlusIcon class="w-4 h-4 mr-2" />
          Add Achievement
        </Button>
      </template>
    </PageHeader>

    <!-- Таблица достижений -->
    <PageContent>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-900">
          <tr>
            <th class="p-4 text-left text-gray-400">Code</th>
            <th class="p-4 text-left text-gray-400">Name</th>
            <th class="p-4 text-left text-gray-400">Description</th>
            <th class="p-4 text-left text-gray-400">Conditions</th>
            <th class="p-4 text-left text-gray-400">Reward</th>
            <th class="p-4 text-left text-gray-400">Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr
            v-for="achievement in achievements"
            :key="achievement.code"
            class="border-t border-gray-700 hover:bg-gray-700/50"
          >
            <td class="p-4 font-mono">{{ achievement.code }}</td>
            <td class="p-4">
              <div class="flex items-center gap-2">
                <span class="text-2xl">{{ achievement.icon }}</span>
                {{ achievement.name }}
              </div>
            </td>
            <td class="p-4">{{ achievement.description }}</td>
            <td class="p-4">
              <div class="space-y-1">
                <div v-for="(value, key) in achievement.conditions"
                     :key="key"
                     class="text-sm text-gray-400"
                >
                  {{ formatCondition(key, value) }}
                </div>
              </div>
            </td>
            <td class="p-4">
              <span class="text-yellow-400">{{ achievement.points_reward }} points</span>
            </td>
            <td class="p-4">
              <div class="flex gap-2">
                <button
                  @click="editAchievement(achievement)"
                  class="text-blue-400 hover:text-blue-300"
                >
                  <PencilIcon class="w-5 h-5" />
                </button>
                <button
                  @click="deleteAchievement(achievement.code)"
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

      <div class="mt-4">
        <AdminPagination
          v-model:page="currentPage"
          :total="totalItems"
          :per-page="perPage"
        />
      </div>
    </PageContent>

    <!-- Модальное окно создания/редактирования -->
    <Dialog v-model:open="showModal">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{{ isEditing ? 'Edit Achievement' : 'New Achievement' }}</DialogTitle>
        </DialogHeader>

        <form @submit.prevent="saveAchievement" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm text-gray-400">Achievement Code</label>
              <input
                v-model="form.code"
                type="text"
                class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
                required
                pattern="[A-Z0-9_]+"
                placeholder="ACHIEVEMENT_CODE"
              />
              <p class="text-xs text-gray-500 mt-1">
                Uppercase letters, numbers and underscores only
              </p>
            </div>

            <div>
              <label class="text-sm text-gray-400">Icon</label>
              <input
                v-model="form.icon"
                type="text"
                class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
                maxlength="2"
                placeholder="🏆"
              />
            </div>
          </div>

          <div>
            <label class="text-sm text-gray-400">Name</label>
            <input
              v-model="form.name"
              type="text"
              class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <div>
            <label class="text-sm text-gray-400">Description</label>
            <textarea
              v-model="form.description"
              class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
              rows="3"
              required
            ></textarea>
          </div>

          <div>
            <label class="text-sm text-gray-400">Condition Type</label>
            <select
              v-model="form.conditionType"
              class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
              required
            >
              <option value="generation_count">Generation Count</option>
              <option value="consecutive_days">Consecutive Days</option>
              <option value="invites_count">Invites Count</option>
            </select>
          </div>

          <div>
            <label class="text-sm text-gray-400">Condition Value</label>
            <input
              v-model.number="form.conditionValue"
              type="number"
              min="1"
              class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <div>
            <label class="text-sm text-gray-400">Reward (points)</label>
            <input
              v-model.number="form.points_reward"
              type="number"
              min="0"
              class="mt-1 w-full rounded-md bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <DialogFooter>
            <Button variant="ghost" type="button" @click="showModal = false">
              Cancel
            </Button>
            <Button type="submit">
              {{ isEditing ? 'Save' : 'Create' }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMainStore } from '@/store'
import { Plus as PlusIcon, Pencil as PencilIcon, Trash as TrashIcon } from 'lucide-vue-next'

// Components
import PageHeader from './PageHeader.vue'
import PageContent from './PageContent.vue'
import AdminPagination from './common/AdminPagination.vue'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'

const store = useMainStore()

// Interfaces
interface Achievement {
  id?: number;
  code: string;
  name: string;
  description: string;
  icon?: string;
  points_reward: number;
  conditions: Record<string, any>;
}

interface AchievementForm {
  code: string;
  name: string;
  description: string;
  icon: string;
  points_reward: number;
  conditionType: string;
  conditionValue: number;
  conditions?: Record<string, any>;
}

// State
const achievements = ref<Achievement[]>([])
const currentPage = ref(1)
const perPage = ref(10)
const totalItems = ref(0)
const showModal = ref(false)
const isEditing = ref(false)
const form = ref<AchievementForm>({
  code: '',
  name: '',
  description: '',
  icon: '',
  points_reward: 0,
  conditionType: 'generation_count',
  conditionValue: 1
})

// Methods
const formatCondition = (key: string, value: any): string => {
  switch (key) {
    case 'generation_count':
      return `${value} generations`
    case 'consecutive_days':
      return `${value} consecutive days`
    case 'invites_count':
      return `${value} invites`
    default:
      return `${key}: ${value}`
  }
}

const loadAchievements = async () => {
  try {
    const response = await store.fetchAchievements({
      page: currentPage.value,
      perPage: perPage.value
    })
    achievements.value = response.items
    totalItems.value = response.total
  } catch (error) {
    console.error('Error loading achievements:', error)
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = {
    code: '',
    name: '',
    description: '',
    icon: '🏆',
    points_reward: 10,
    conditionType: 'generation_count',
    conditionValue: 1
  }
  showModal.value = true
}

const editAchievement = (achievement: Achievement) => {
  isEditing.value = true
  const [conditionType, conditionValue] = Object.entries(achievement.conditions)[0] || []
  form.value = {
    code: achievement.code,
    name: achievement.name,
    description: achievement.description,
    icon: achievement.icon || '',
    points_reward: achievement.points_reward,
    conditionType: conditionType || 'generation_count',
    conditionValue: conditionValue || 1
  }
  showModal.value = true
}

const saveAchievement = async () => {
  try {
    const achievementData = {
      code: form.value.code,
      name: form.value.name,
      description: form.value.description,
      icon: form.value.icon,
      points_reward: form.value.points_reward,
      conditions: {
        [form.value.conditionType]: form.value.conditionValue
      }
    }

    if (isEditing.value) {
      await store.updateAchievement(form.value.code, achievementData)
    } else {
      await store.createAchievement(achievementData)
    }
    showModal.value = false
    await loadAchievements()
  } catch (error) {
    console.error('Error saving achievement:', error)
  }
}

const deleteAchievement = async (code: string) => {
  try {
    // Confirm deletion with the user
    if (confirm('Are you sure you want to delete this achievement?')) {
      await store.deleteAchievement(code);
      await loadAchievements(); // Reload achievements after deletion
    }
  } catch (error) {
    console.error('Error deleting achievement:', error);
  }
}

// Initialization
onMounted(loadAchievements)
</script>
