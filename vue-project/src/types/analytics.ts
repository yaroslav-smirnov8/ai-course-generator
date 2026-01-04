// src/types/analytics.ts
export interface FeatureUsage {
  total_usage: number
  unique_users: number
}

export interface UserDistribution {
  by_role: Record<string, { count: number; percentage: number }>
  by_tariff: Record<string, { count: number; percentage: number }>
}

export interface Analytics {
  total_usage: number
  unique_users: number
  feature_distribution: Record<string, FeatureUsage>
  user_distribution: UserDistribution
  most_popular: Array<{ feature: string; percentage: number }>
  least_used: Array<{ feature: string; percentage: number }>
}
