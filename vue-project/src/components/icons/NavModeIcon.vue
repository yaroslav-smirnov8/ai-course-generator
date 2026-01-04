<!-- src/components/icons/NavModeIcon.vue -->
<template>
  <svg
    width="35"
    height="35"
    viewBox="0 0 35 35"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="[$attrs.class, { 'active': active }]"
  >
    <!-- Галочки -->
    <path
      d="M2.91675 8.02083L4.68759 10.2083L10.9376 4.375"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M2.91675 18.2291L4.68759 20.4166L10.9376 14.5833"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M2.91675 28.4376L4.68759 30.6251L10.9376 24.7917"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <!-- Горизонтальные линии -->
    <path
      d="M17.5 7.29175H32.0833"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
    />
    <path
      d="M17.5 17.5H32.0833"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
    />
    <path
      d="M17.5 27.7083H32.0833"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  active?: boolean
}

defineProps<Props>()
</script>

<style scoped>
svg {
  transition: all 0.2s ease;
  color: #1C274C; /* Базовый цвет */
}

svg:hover {
  transform: scale(1.05);
}

.active {
  color: #9333EA; /* Цвет для активного состояния */
  filter: drop-shadow(0 0 4px rgba(147, 51, 234, 0.5));
}
</style>
