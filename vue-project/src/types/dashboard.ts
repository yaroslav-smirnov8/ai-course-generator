//types/dashboard.ts
export interface DashboardStats {
  totalUsers: number
  usersTrend: number
  activeTariffs: number
  tariffsTrend: number
  dailyGenerations: number
  generationsTrend: number
  featureUsage: number
  usageTrend: number
}

export interface DataPoint {
  date: string
  activeUsers: number
  generations: number
}

export interface ChartLine {
  key: string
  name: string
  color: string
}

export interface FeatureData {
  name: string
  value: number
}

export interface ActivityItem {
  id: number
  type: string
  description: string
  timestamp: string
}
