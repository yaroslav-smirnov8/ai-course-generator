// src/components/admin/Tariffs.vue
<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-white">Tariff Management</h2>
      <button
        @click="openNewTariffModal"
        class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
      >
        Add Tariff
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="tariff in tariffs"
        :key="tariff.id"
        class="bg-gray-800 rounded-lg p-6"
      >
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-lg font-semibold text-white">{{ tariff.name }}</h3>
            <p class="text-gray-400 text-sm mt-1">{{ tariff.points_cost }} points</p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              :checked="tariff.is_active"
              @change="toggleTariff(tariff.id, !tariff.is_active)"
              class="sr-only peer"
            >
            <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4
                      peer-focus:ring-purple-800 rounded-full peer
                      peer-checked:after:translate-x-full
                      after:content-[''] after:absolute after:top-[2px] after:left-[2px]
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-all peer-checked:bg-purple-500">
            </div>
          </label>
        </div>

        <div class="space-y-2 mb-6">
          <div class="flex justify-between items-center">
            <span class="text-gray-400">Generation limit:</span>
            <span class="text-white">{{ tariff.generations_limit }}/day</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-400">Image limit:</span>
            <span class="text-white">{{ tariff.images_limit }}/day</span>
          </div>
        </div>

        <div class="border-t border-gray-700 pt-4">
          <h4 class="text-sm font-medium text-gray-400 mb-2">Features:</h4>
          <ul class="space-y-1">
            <li v-for="(feature, index) in tariff.features" :key="index" class="text-white flex items-center gap-2">
              <span class="text-green-400">✓</span>
              {{ feature }}
            </li>
          </ul>
        </div>

        <div class="mt-4">
          <button
            @click="editTariff(tariff)"
            class="w-full py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
          >
            Edit
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
