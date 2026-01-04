<!-- src/components/NavigationBar.vue -->
<script setup lang="ts">
import { useRoute } from 'vue-router'
import Shuttle from '../assets/images/nav/button-courses.svg'
import Planet from '../assets/images/nav/button-main.svg'
import List from '../assets/images/nav/button-mode.svg'
import Profile from '../assets/images/nav/button-profile.svg'

const route = useRoute()

const navigationItems = [
  {
    name: 'Home',
    route: '/',
    icon: Planet
  },
  {
    name: 'Plans',
    route: '/modes',
    icon: List
  },
  {
    name: 'Courses',
    route: '/courses',
    icon: Shuttle
  },
  {
    name: 'Profile',
    route: '/profile',
    icon: Profile
  }
]
</script>



<template>
  <nav class="fixed bottom-0 left-0 right-0 z-50">
    <div class="bg-[#FFCCF3]">
      <div class="grid grid-cols-4 h-20">
        <router-link
          v-for="item in navigationItems"
          :key="item.route"
          :to="item.route"
          class="flex flex-col items-center justify-center py-2"
          :class="[
            route.path === item.route
              ? 'text-purple-600'
              : 'text-zinc-700'
          ]"
        >
          <component
            :is="item.icon"
            class="w-6 h-6 mb-1"
            :class="{
              'opacity-100': route.path === item.route,
              'opacity-70': route.path !== item.route
            }"
          />
          <span class="text-xs font-normal">{{ item.name }}</span>
        </router-link>
      </div>
    </div>
  </nav>
</template>

<style scoped>
nav {
  box-shadow: 0 -4px 6px -1px rgba(255, 225, 255, 0.15);
}

.router-link-active {
  position: relative;
}

.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  background-color: #ffc0cb;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(147, 51, 234, 0.5);
}
</style>
