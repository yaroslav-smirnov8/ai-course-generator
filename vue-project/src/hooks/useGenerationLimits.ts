// src/hooks/useGenerationLimits.ts
import { computed } from 'vue'
import { useMainStore } from '@/store'
import { ContentType, UserRole, TariffType, UNLIMITED_ROLES } from '@/core/constants'
import type { User, DailyLimits, TariffInfo } from '@/types'

interface GenerationLimits {
  total: number
  remaining: number
  isUnlimited: boolean
}

export function useGenerationLimits(contentType: ContentType) {
  const store = useMainStore()

  const hasUnlimitedAccess = computed(() => {
    const user = store.user as User | null
    return user ? (UNLIMITED_ROLES as readonly UserRole[]).includes(user.role) : false
  })

  const currentTariff = computed(() => {
    const user = store.user as User | null
    return user?.tariff || null
  })

  const tariffInfo = computed(() => {
    return store.tariffInfo as TariffInfo | null
  })

  const canGenerate = computed(() => {
    if (!store.user) return false

    // Users with unlimited access can always generate
    if (hasUnlimitedAccess.value) return true

    // Users without a tariff cannot generate
    if (!currentTariff.value || !tariffInfo.value) return false

    // Check remaining generations based on content type
    return contentType === ContentType.IMAGE
      ? store.remainingGenerations(ContentType.IMAGE) > 0
      : store.remainingGenerations(ContentType.LESSON_PLAN) > 0
  })

  const generationLimits = computed((): GenerationLimits => {
    if (hasUnlimitedAccess.value) {
      return {
        total: Infinity,
        remaining: Infinity,
        isUnlimited: true
      }
    }

    if (!currentTariff.value || !tariffInfo.value) {
      return {
        total: 0,
        remaining: 0,
        isUnlimited: false
      }
    }

    const remaining = contentType === ContentType.IMAGE
      ? store.remainingGenerations(ContentType.IMAGE)
      : store.remainingGenerations(ContentType.LESSON_PLAN)

    const total = contentType === ContentType.IMAGE
      ? tariffInfo.value.limits.images
      : tariffInfo.value.limits.generations

    return {
      total,
      remaining,
      isUnlimited: false
    }
  })

  const checkAndTrackGeneration = async () => {
    if (!canGenerate.value) {
      throw new Error('Generation limit reached')
    }

    try {
      await store.checkAndTrackGeneration(contentType)
    } catch (error) {
      console.error('Error tracking generation:', error)
      throw error
    }
  }

  return {
    canGenerate,
    generationLimits,
    checkAndTrackGeneration,
    hasUnlimitedAccess
  }
}
