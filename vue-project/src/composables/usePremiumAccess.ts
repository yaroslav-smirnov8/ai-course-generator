import { computed } from 'vue'
import { useMainStore } from '@/store'
import { TariffType, UserRole } from '@/core/constants'

export function usePremiumAccess() {
  const store = useMainStore()

  // Проверяем, является ли пользователь админом или имеет безлимитную роль
  const isUnlimitedUser = computed(() => {
    const userRole = store.user?.role
    return userRole === UserRole.ADMIN ||
           userRole === UserRole.FRIEND ||
           userRole === UserRole.MOD
  })

  // Проверяем, есть ли у пользователя Premium тариф
  const hasPremiumTariff = computed(() => {
    const userTariff = store.user?.tariff
    return userTariff === 'tariff_6' // TariffType.PREMIUM
  })

  // Проверяем доступ к премиум функциям
  const hasPremiumAccess = computed(() => {
    return isUnlimitedUser.value || hasPremiumTariff.value
  })

  // Получаем текущий тариф пользователя
  const currentTariff = computed(() => store.user?.tariff)

  // Получаем роль пользователя
  const userRole = computed(() => store.user?.role)

  // Проверяем, загружены ли данные пользователя
  const isUserLoaded = computed(() => !!store.user)

  return {
    isUnlimitedUser,
    hasPremiumTariff,
    hasPremiumAccess,
    currentTariff,
    userRole,
    isUserLoaded
  }
}
