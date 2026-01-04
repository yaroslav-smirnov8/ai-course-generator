<template>
  <nav class="ds-nav-bottom">
    <div class="ds-nav-grid">
      <router-link 
        v-for="item in navItems" 
        :key="item.id" 
        :to="item.route" 
        class="ds-nav-link"
        active-class="ds-nav-link-active"
      >
        <span class="ds-nav-icon">{{ item.icon }}</span>
        <span class="ds-nav-text">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { initDesignSystem } from '@/plugins/designSystem';

const route = useRoute();

// Navigation items
const navItems = ref([
  { id: 'home', route: '/', label: 'Home', icon: '🏠' },
  { id: 'lessons', route: '/lessons', label: 'Lessons', icon: '📚' },
  { id: 'tools', route: '/tools', label: 'Tools', icon: '🛠️' },
  { id: 'profile', route: '/profile', label: 'Profile', icon: '👤' }
]);

onMounted(() => {
  initDesignSystem();
});
</script>

<style scoped>
.ds-nav-bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: var(--color-background-accent);
  border-top: 1px solid var(--color-primary-light);
  z-index: var(--z-index-navbar);
  box-shadow: 0 -4px 6px -1px var(--color-shadow-light);
  padding: var(--spacing-sm) 0;
}

.ds-nav-grid {
  display: flex;
  justify-content: space-around;
}

.ds-nav-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-sm);
  text-decoration: none;
  color: var(--color-text);
  font-size: var(--font-size-xs);
  transition: all var(--transition-speed) ease;
}

.ds-nav-icon {
  font-size: var(--font-size-xl);
  margin-bottom: var(--spacing-xs);
}

.ds-nav-link-active {
  color: var(--color-primary);
  transform: translateY(-2px);
}

.ds-nav-link-active .ds-nav-icon {
  filter: drop-shadow(0 0 5px var(--color-primary-shadow));
}
</style> 