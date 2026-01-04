import { computed } from 'vue';
import { useMainStore } from '@/store';

// Расширение типа для store
interface ExtendedStore {
  logout?: () => void;
  [key: string]: any;
}

export function useAuth() {
  const store = useMainStore() as ExtendedStore;

  const isAuthenticated = computed(() => {
    // Примечание: Здесь должна быть реальная проверка аутентификации
    // В зависимости от вашей логики аутентификации
    return store.isAuthenticated || false;
  });

  const currentUser = computed(() => {
    return store.user;
  });

  const logout = () => {
    // Логика выхода
    // Если в вашем store нет метода logout, это заглушка
    // Можно адаптировать под ваш реальный метод аутентификации
    try {
      if (typeof store.logout === 'function') {
        store.logout();
      } else {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Ошибка при выходе из системы:', error);
    }
  };

  return {
    isAuthenticated,
    currentUser,
    logout
  };
} 