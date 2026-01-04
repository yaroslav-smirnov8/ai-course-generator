<!-- src/views/LessonPlanView.vue -->
<template>
  <div class="lesson-plan-view">
    <div class="header">
      <h1 class="text-2xl font-bold mb-4">Course Lesson Generator</h1>
      <p class="text-gray-400 mb-6">Create lessons for your course with detailed methodology and structure</p>
    </div>

    <!-- Tariff information and points balance panel -->
    <TariffInfoPanel :content-type="ContentType.LESSON_PLAN" />

    <!-- Points Purchase Modal -->
    <PointsPurchaseModal
      v-if="showPurchaseModal"
      @close="showPurchaseModal = false"
      @success="handlePurchaseSuccess"
    />

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Form section - 2/3 width on desktop -->
      <div class="md:col-span-2">
        <form @submit.prevent="generateLessonPlan" class="bg-gray-800 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">Lesson Configuration</h2>

          <!-- Language Selection -->
          <div class="form-group mb-4">
            <label for="language" class="block text-sm font-medium text-gray-300 mb-2">Language:</label>
            <select
              v-model="formData.language"
              id="language"
              required
              class="w-full bg-gray-700 text-white rounded-lg p-3 border border-gray-600"
            >
              <option value="english">English</option>
              <option value="spanish">Spanish</option>
              <option value="french">French</option>
              <option value="german">German</option>
              <option value="italian">Italian</option>
              <option value="chinese">Chinese</option>
              <option value="russian">Russian</option>
              <option value="arabic">Arabic</option>
            </select>
          </div>

          <!-- Level Selection -->
          <div class="form-group mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">Level:</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="level in ['beginner', 'intermediate', 'advanced']"
                :key="level"
                type="button"
                :class="[
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  formData.level === level
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                ]"
                @click="formData.level = level"
              >
                {{ level.charAt(0).toUpperCase() + level.slice(1) }}
              </button>
            </div>
          </div>

          <!-- Topic -->
          <div class="form-group mb-4">
            <label for="topic" class="block text-sm font-medium text-gray-300 mb-2">Lesson Topic:</label>
            <input
              v-model="formData.topic"
              id="topic"
              required
              class="w-full bg-gray-700 text-white rounded-lg p-3 border border-gray-600"
              placeholder="Enter lesson topic"
            >
          </div>

          <!-- Lesson Duration -->
          <div class="form-group mb-4">
            <label for="duration" class="block text-sm font-medium text-gray-300 mb-2">
              Duration (minutes): {{ formData.duration }}
            </label>
            <input
              v-model.number="formData.duration"
              id="duration"
              type="range"
              min="15"
              max="180"
              step="15"
              class="w-full"
            >
            <div class="flex justify-between text-sm text-gray-400">
              <span>15 min</span>
              <span>180 min</span>
            </div>
          </div>

          <!-- Methodologies -->
          <div class="form-group mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">Methodology:</label>

            <!-- Main Method Selection -->
            <div class="mb-2">
              <label class="block text-xs text-gray-400 mb-1">Main Method:</label>
              <select
                v-model="formData.methodologies.mainMethod"
                class="w-full bg-gray-700 text-white rounded-lg p-3 border border-gray-600"
              >
                <option value="communicative">Communicative Approach</option>
                <option value="taskBased">Task-Based Learning</option>
                <option value="directMethod">Direct Method</option>
                <option value="grammarTranslation">Grammar-Translation</option>
                <option value="tpr">Total Physical Response</option>
              </select>
            </div>

            <!-- Supporting Methods -->
            <div class="mb-2">
              <label class="block text-xs text-gray-400 mb-1">Supporting Methods:</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="method in supportMethods"
                  :key="method.value"
                  type="button"
                  :class="[
                    'px-3 py-1 rounded-full text-xs transition-colors',
                    isMethodSelected(method.value)
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  ]"
                  @click="toggleSupportMethod(method.value)"
                >
                  {{ method.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Learning Objectives -->
          <div class="form-group mb-4">
            <label for="objectives" class="block text-sm font-medium text-gray-300 mb-2">Learning Objectives:</label>
            <div class="space-y-2">
              <div
                v-for="(objective, index) in formData.objectives"
                :key="index"
                class="flex items-center gap-2"
              >
                <input
                  v-model="formData.objectives[index]"
                  class="flex-1 bg-gray-700 text-white rounded-lg p-3 border border-gray-600"
                  placeholder="Enter learning objective"
                >
                <button
                  type="button"
                  class="p-2 text-red-400 hover:text-red-300"
                  @click="removeObjective(index)"
                >
                  ✕
                </button>
              </div>
              <button
                type="button"
                class="mt-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 text-sm"
                @click="addObjective"
                :disabled="formData.objectives.length >= 5"
              >
                Add Objective
              </button>
            </div>
          </div>

          <!-- Materials -->
          <div class="form-group mb-4">
            <label for="materials" class="block text-sm font-medium text-gray-300 mb-2">Materials Needed:</label>
            <div class="space-y-2">
              <div
                v-for="(material, index) in formData.materials"
                :key="index"
                class="flex items-center gap-2"
              >
                <input
                  v-model="formData.materials[index]"
                  class="flex-1 bg-gray-700 text-white rounded-lg p-3 border border-gray-600"
                  placeholder="Enter required material"
                >
                <button
                  type="button"
                  class="p-2 text-red-400 hover:text-red-300"
                  @click="removeMaterial(index)"
                >
                  ✕
                </button>
              </div>
              <button
                type="button"
                class="mt-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 text-sm"
                @click="addMaterial"
                :disabled="formData.materials.length >= 10"
              >
                Add Material
              </button>
            </div>
          </div>

          <!-- Format Selection -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <!-- Assessment Type -->
            <div class="form-group">
              <label class="block text-sm font-medium text-gray-300 mb-2">Assessment:</label>
              <div class="flex flex-col gap-2">
                <button
                  v-for="assessment in ['formative', 'summative', 'none']"
                  :key="assessment"
                  type="button"
                  :class="[
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    formData.assessment === assessment
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  ]"
                  @click="formData.assessment = assessment as 'formative' | 'summative' | 'none'"
                >
                  {{ assessment.charAt(0).toUpperCase() + assessment.slice(1) }}
                </button>
              </div>
            </div>

            <!-- Lesson Format -->
            <div class="form-group">
              <label class="block text-sm font-medium text-gray-300 mb-2">Format:</label>
              <div class="flex flex-col gap-2">
                <button
                  v-for="format in ['online', 'offline', 'hybrid']"
                  :key="format"
                  type="button"
                  :class="[
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    formData.format === format
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  ]"
                  @click="formData.format = format as 'online' | 'offline' | 'hybrid'"
                >
                  {{ format.charAt(0).toUpperCase() + format.slice(1) }}
                </button>
              </div>
            </div>
          </div>

          <!-- Additional Options -->
          <div class="form-group mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">Additional Options:</label>
            <div class="flex items-center gap-2 mb-2">
              <input
                type="checkbox"
                id="culturalElements"
                v-model="formData.culturalElements"
                class="w-4 h-4 bg-gray-700 rounded border-gray-600"
              >
              <label for="culturalElements" class="text-sm text-gray-300">Include cultural elements</label>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="form-actions">
            <button
              type="submit"
              :disabled="isLoading || !canGenerate"
              class="w-full px-4 py-3 bg-purple-600 text-white rounded-lg font-medium"
              :class="{ 'opacity-50 cursor-not-allowed': !canGenerate || isLoading }"
            >
              {{ isLoading ? 'Generating...' : 'Generate Lesson Plan' }}
            </button>

            <!-- Low Balance Warning -->
            <div v-if="!canGenerate && !isLoading" class="mt-3 text-sm">
              <div v-if="insufficientBalance" class="text-red-400">
                <span>Insufficient balance.</span>
                <button
                  type="button"
                  class="text-purple-400 underline ml-2"
                  @click="showPurchaseModal = true"
                >
                  Buy Points
                </button>
              </div>
              <div v-else-if="dailyLimitReached" class="text-yellow-400">
                Daily generation limit reached.
              </div>
            </div>
          </div>
        </form>
      </div>

      <!-- Methodology Info Section - 1/3 width on desktop -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Methodology Guide</h2>

        <!-- Show details of the selected main methodology -->
        <div v-if="currentMethodologyInfo" class="mb-6">
          <h3 class="text-lg font-medium text-purple-400 mb-2">{{ currentMethodologyInfo.label }}</h3>
          <p class="text-gray-300 mb-3">{{ currentMethodologyInfo.description }}</p>

          <h4 class="text-md font-medium text-gray-200 mb-2">Key Features:</h4>
          <ul class="list-disc pl-5 text-gray-300 space-y-1">
            <li v-for="(feature, index) in currentMethodologyInfo.features" :key="index">
              {{ feature }}
            </li>
          </ul>
        </div>

        <!-- Generation Insights -->
        <div class="mt-4">
          <h3 class="text-lg font-medium mb-3">Generation Insights</h3>

          <div class="space-y-3">
            <div class="bg-gray-700 rounded-lg p-3">
              <h4 class="text-sm font-medium text-gray-300">Estimated Completion Time</h4>
              <p class="text-xl font-semibold text-purple-400">~1 minute</p>
            </div>

            <div class="bg-gray-700 rounded-lg p-3">
              <h4 class="text-sm font-medium text-gray-300">Points Cost</h4>
              <p class="text-xl font-semibold text-purple-400">{{ generationCost }} points</p>
            </div>

            <div class="bg-gray-700 rounded-lg p-3">
              <h4 class="text-sm font-medium text-gray-300">Lesson Complexity</h4>
              <div class="w-full bg-gray-600 rounded-full h-2.5 mt-2">
                <div
                  class="bg-purple-600 h-2.5 rounded-full"
                  :style="{ width: `${complexityPercentage}%` }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-gray-400 mt-1">
                <span>Basic</span>
                <span>Complex</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div class="bg-gray-800 rounded-lg p-8 max-w-md w-full text-center">
        <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <h3 class="text-xl font-medium text-white mb-2">Generating Lesson Plan</h3>
        <p class="text-gray-400">Creating a comprehensive lesson plan with your specified methodology...</p>
      </div>
    </div>

    <!-- Generated Content -->
    <div v-if="generatedContent" class="mt-8 bg-gray-800 rounded-lg p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">Generated Lesson Plan</h2>

        <div class="flex gap-2">
          <button
            @click="copyToClipboard"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2 text-sm"
          >
            <span>📋</span> Copy
          </button>
          <button
            @click="regenerate"
            class="px-4 py-2 bg-orange-600 text-white rounded-lg flex items-center gap-2 text-sm"
          >
            <span>🔄</span> Regenerate
          </button>
          <button
            @click="addToCourse"
            class="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2 text-sm"
          >
            <span>➕</span> Add to Course
          </button>
        </div>
      </div>

      <div class="transaction-info bg-purple-500/10 p-4 rounded-lg mb-4">
        <div class="text-purple-300 font-medium">
          <span>Points Spent: {{ generationCost }}</span>
          <span class="mx-2">•</span>
          <span>New Balance: {{ userPoints }}</span>
        </div>
      </div>

      <div class="bg-pink-900/60 rounded-lg p-4 max-h-[60vh] overflow-y-auto">
        <MarkdownRenderer :content="generatedContent" theme="dark" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMainStore } from '../store'
import { ContentType, ActionType } from '../core/constants'
import TariffInfoPanel from '../components/common/TariffInfoPanel.vue'
import PointsPurchaseModal from '../components/common/PointsPurchaseModal.vue'
import MarkdownRenderer from '../components/common/MarkdownRenderer.vue'

interface LessonPlanFormData {
  language: string;
  level: string;
  topic: string;
  duration: number;
  methodologies: {
    mainMethod: string;
    supportMethods: string[];
  };
  objectives: string[];
  materials: string[];
  assessment: 'formative' | 'summative' | 'none';
  format: 'online' | 'offline' | 'hybrid';
  culturalElements: boolean;
}

interface MethodologyInfo {
  value: string;
  label: string;
  description: string;
  features: string[];
}

const store = useMainStore()

// Form data
const formData = ref<LessonPlanFormData>({
  language: 'english',
  level: 'intermediate',
  topic: '',
  duration: 60,
  methodologies: {
    mainMethod: 'communicative',
    supportMethods: []
  },
  objectives: [''],
  materials: [''],
  assessment: 'formative',
  format: 'online',
  culturalElements: false
})

// UI states
const generatedContent = ref<string | null>(null)
const isLoading = computed(() => store.loading)
const error = computed(() => store.error)
const showPurchaseModal = ref(false)
const lastGenerationCost = ref(0)

// Computed properties for points and limits
const userPoints = computed(() => store.user?.points || 0)
const generationCost = computed(() => store.getGenerationCost(ContentType.LESSON_PLAN))
const dailyLimitRemaining = computed(() => store.remainingGenerations(ContentType.LESSON_PLAN))
const dailyLimitReached = computed(() => dailyLimitRemaining.value <= 0)
const insufficientBalance = computed(() => userPoints.value < generationCost.value)

// Проверка возможности генерации
const canGenerate = computed(() => {
  if (isLoading.value) return false
  return !insufficientBalance.value && !dailyLimitReached.value
})

// Complexity calculation based on form inputs
const complexityPercentage = computed(() => {
  let score = 0;

  // Add points for different factors
  score += formData.value.objectives.filter(o => o.trim()).length * 10; // More objectives = more complex
  score += formData.value.materials.filter(m => m.trim()).length * 5; // More materials = more complex
  score += formData.value.methodologies.supportMethods.length * 15; // More methods = more complex
  score += formData.value.culturalElements ? 10 : 0; // Cultural elements add complexity
  score += formData.value.assessment !== 'none' ? 10 : 0; // Assessment adds complexity
  score += formData.value.duration > 90 ? 15 : 0; // Longer lessons are more complex

  // Cap at 100%
  return Math.min(score, 100);
})

// Methodology information
const methodologies = ref<MethodologyInfo[]>([
  {
    value: 'communicative',
    label: 'Communicative Approach',
    description: 'Emphasizes interaction as both the means and the ultimate goal of language learning.',
    features: [
      'Focus on communication over grammar perfection',
      'Use of authentic materials',
      'Group activities and role-playing',
      'Fluency over accuracy in early stages'
    ]
  },
  {
    value: 'taskBased',
    label: 'Task-Based Learning',
    description: 'Organizes learning around tasks that students need to complete to achieve specific outcomes.',
    features: [
      'Real-world tasks as central unit',
      'Three-phase structure (pre-task, task cycle, language focus)',
      'Meaning-focused activities',
      'Assessment based on task completion'
    ]
  },
  {
    value: 'directMethod',
    label: 'Direct Method',
    description: 'Avoids using students\' native language and uses only the target language.',
    features: [
      'No translation allowed',
      'Grammar taught inductively',
      'Emphasis on speaking and listening',
      'Visual aids for vocabulary teaching'
    ]
  },
  {
    value: 'grammarTranslation',
    label: 'Grammar-Translation',
    description: 'Focuses on grammar rules and vocabulary memorization through translation.',
    features: [
      'Systematic analysis of grammar rules',
      'Vocabulary lists and memorization',
      'Translation exercises',
      'Reading and writing emphasis'
    ]
  },
  {
    value: 'tpr',
    label: 'Total Physical Response',
    description: 'Coordinates language with physical movement to help students learn through actions.',
    features: [
      'Commands and physical responses',
      'Listening comprehension before speaking',
      'Use of imperatives',
      'Reduced student anxiety through movement'
    ]
  }
])

// Support methods list
const supportMethods = ref<{value: string, label: string}[]>([
  { value: 'audioLingual', label: 'Audio-Lingual' },
  { value: 'silent', label: 'Silent Way' },
  { value: 'suggestopedia', label: 'Suggestopedia' },
  { value: 'lexical', label: 'Lexical Approach' },
  { value: 'clil', label: 'CLIL' },
  { value: 'flipped', label: 'Flipped Classroom' }
])

// Get current methodology info
const currentMethodologyInfo = computed(() => {
  return methodologies.value.find(m => m.value === formData.value.methodologies.mainMethod);
})

// Methods for form manipulation
const addObjective = () => {
  if (formData.value.objectives.length < 5) {
    formData.value.objectives.push('');
  }
}

const removeObjective = (index: number) => {
  if (formData.value.objectives.length > 1) {
    formData.value.objectives.splice(index, 1);
  }
}

const addMaterial = () => {
  if (formData.value.materials.length < 10) {
    formData.value.materials.push('');
  }
}

const removeMaterial = (index: number) => {
  if (formData.value.materials.length > 1) {
    formData.value.materials.splice(index, 1);
  }
}

const isMethodSelected = (method: string) => {
  return formData.value.methodologies.supportMethods.includes(method);
}

const toggleSupportMethod = (method: string) => {
  const methods = formData.value.methodologies.supportMethods;
  const index = methods.indexOf(method);

  if (index === -1) {
    if (methods.length < 3) { // Limit to 3 supporting methods
      methods.push(method);
    }
  } else {
    methods.splice(index, 1);
  }
}

// Generation methods
const generateLessonPlan = async () => {
  try {
    if (!canGenerate.value) {
      if (insufficientBalance.value) {
        store.setError(`Insufficient balance. You need ${generationCost.value} points.`)
        return
      }
      if (dailyLimitReached.value) {
        store.setError(`Daily limit reached. Try again tomorrow or upgrade your plan.`)
        return
      }
      return
    }

    // Filter out empty objectives and materials
    formData.value.objectives = formData.value.objectives.filter(o => o.trim());
    formData.value.materials = formData.value.materials.filter(m => m.trim());

    // Ensure at least one objective and material
    if (formData.value.objectives.length === 0) formData.value.objectives.push('');
    if (formData.value.materials.length === 0) formData.value.materials.push('');

    generatedContent.value = null
    store.clearError()
    lastGenerationCost.value = generationCost.value

    // Prepare data for generation
    const requestData = {
      user_id: store.user?.id,
      type: ContentType.LESSON_PLAN,
      prompt: JSON.stringify(formData.value),
      action_data: {
        content_type: ContentType.LESSON_PLAN,
        language: formData.value.language,
        level: formData.value.level,
        topic: formData.value.topic
      }
    }

    // Generate lesson plan
    const result = await store.generateLessonPlan(formData.value)
    console.log('Generation result:', result)

    // Deduct points
    await store.deductPoints(generationCost.value, 'generation')

    // Check achievements
    await store.checkAchievements(
      ActionType.GENERATION,
      requestData.action_data
    )

    generatedContent.value = result

  } catch (error: any) {
    console.error('Error in component:', error)
    store.setError(error.message || 'An error occurred during generation')

    if (error.message?.includes('balance') || error.message?.includes('insufficient')) {
      showPurchaseModal.value = true
    }
  }
}

const regenerate = () => {
  if (insufficientBalance.value) {
    store.setError(`Insufficient balance for regeneration. You need ${generationCost.value} points.`)
    return
  }
  generateLessonPlan()
}

const copyToClipboard = async () => {
  if (generatedContent.value) {
    try {
      await navigator.clipboard.writeText(generatedContent.value)
      store.setMessage('Copied to clipboard!')
    } catch (err) {
      console.error('Failed to copy text:', err)
      store.setError('Failed to copy to clipboard')
    }
  }
}

const addToCourse = () => {
  if (!generatedContent.value) return;

  // Send to parent component or course store
  store.setMessage('Lesson added to course!')

  // In a real implementation, you would likely emit an event to the parent
  // or call a method on a course store to add this lesson
}

const handlePurchaseSuccess = (data: { points: number, price: number }) => {
  showPurchaseModal.value = false
  store.setMessage(`Successfully purchased ${data.points} points!`)
}

// Initialize component
onMounted(() => {
  // Add any initialization logic here
  // For example, you might want to check for an existing lesson to edit
})
</script>

<style scoped>
/* Base container styling */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

/* Dark UI styling */
.form-group {
  margin-bottom: 1.5rem;
}
</style>
