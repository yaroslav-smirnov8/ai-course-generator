// Импортируем стили
import './assets/main.css'

// 1. Core imports
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { initPreload } from './services/preload'
import { initImageOptimization } from './services/imageOptimizer'
import vLazyLoad from './directives/lazyLoad'
import OptimizedImage from './components/common/OptimizedImage.vue'

// Импорт наших собственных компонентов тостов
import SimpleToast from './components/SimpleToast.vue'
// Импортируем менеджер тостов
import { getToastManager } from './plugins/toastManager'

// 2. Views
import AboutView from './views/AboutView.vue'
import AdminView from './views/Admin.vue'
import Courses from './views/Courses.vue'
import FreeLessons from './views/FreeLessons.vue'
import Home from './views/Home.vue'
import Modes from './views/Modes.vue'
import Profile from './views/Profile.vue'
import NotFound from './views/NotFound.vue'

// 3. Admin Components
import AdminDashboard from './components/admin/Dashboard.vue'
import StatCard from './components/admin/cards/StatCard.vue'
import ActivityChart from './components/admin/charts/ActivityChart.vue'
import FeatureUsageChart from './components/admin/charts/FeatureUsageChart.vue'
import ActivityLog from './components/admin/ActivityLog.vue'
import AdminFilters from './components/admin/AdminFilters.vue'
import GenerationsPieChart from './components/admin/charts/GenerationsPieChart.vue'
import AdminPagination from './components/admin/common/AdminPagination.vue'
import DateRangePicker from './components/admin/common/DateRangePicker.vue'
import InfoTooltip from './components/admin/common/InfoTooltip.vue'

// 4. Base Components
import ErrorMessage from './components/ErrorMessage.vue'
import Exercises from './components/Exercises.vue'
import Games from './components/Games.vue'
import ImageGeneration from './components/ImageGeneration.vue'
import LessonPlan from './components/LessonPlan.vue'
import LoadingState from './components/LoadingState.vue'

// 5. Admin Cards
import AchievementCard from './components/admin/cards/AchievementCard.vue'
import TariffCard from './components/admin/cards/TariffCard.vue'

// 6. Admin Charts
import SparklineChart from './components/admin/charts/SparklineChart.vue'

// 7. Admin Navigation and Layout
import Breadcrumbs from './components/admin/Breadcrumbs.vue'
import NavItem from './components/admin/NavItem.vue'
import PageContent from './components/admin/PageContent.vue'
import PageHeader from './components/admin/PageHeader.vue'

// 8. Admin Modals
import AchievementModal from './components/admin/modals/AchievementModal.vue'
import TariffModal from './components/admin/modals/TariffModal.vue'
import UserModal from './components/admin/modals/UserModal.vue'

// 9. Admin Settings
import PromocodesManager from './components/admin/settings/PromocodesManager.vue'
import PromocodesStats from './components/admin/settings/PromocodesStats.vue'
import PromoUsageHistory from './components/admin/settings/PromoUsageHistory.vue'
import SystemSettings from './components/admin/settings/SystemSettings.vue'
import { TelegramService } from './services/telegram'

// Инициализация Telegram WebApp
try {
  TelegramService.initialize();
  
  // Добавляем небольшую задержку перед включением полноэкранного режима
  setTimeout(() => {
    TelegramService.enableFullscreen();
    console.log('Fullscreen mode requested');
  }, 500);
  
  console.log('Telegram WebApp initialized');
} catch (error) {
  console.error('Failed to initialize Telegram WebApp:', error);
}

// Инициализация предзагрузки изображений
initPreload()

// Инициализация оптимизации изображений
initImageOptimization()

// Создаем экземпляр приложения и pinia
const pinia = createPinia()
const app = createApp(App)

// Регистрация компонентов
// Views
app.component('AboutView', AboutView)
app.component('AdminView', AdminView)
app.component('Courses', Courses)
app.component('FreeLessons', FreeLessons)
app.component('Home', Home)
app.component('Modes', Modes)
app.component('Profile', Profile)
app.component('NotFound', NotFound)

// Admin Components
app.component('AdminDashboard', AdminDashboard)
app.component('StatCard', StatCard)
app.component('ActivityChart', ActivityChart)
app.component('FeatureUsageChart', FeatureUsageChart)
app.component('ActivityLog', ActivityLog)
app.component('AdminFilters', AdminFilters)
app.component('GenerationsPieChart', GenerationsPieChart)
app.component('AdminPagination', AdminPagination)
app.component('DateRangePicker', DateRangePicker)
app.component('InfoTooltip', InfoTooltip)

// Base Components
app.component('ErrorMessage', ErrorMessage)
app.component('Exercises', Exercises)
app.component('Games', Games)
app.component('ImageGeneration', ImageGeneration)
app.component('LessonPlan', LessonPlan)
app.component('LoadingState', LoadingState)

// Admin Cards and Charts
app.component('AchievementCard', AchievementCard)
app.component('TariffCard', TariffCard)
app.component('SparklineChart', SparklineChart)

// Admin Navigation and Layout
app.component('Breadcrumbs', Breadcrumbs)
app.component('NavItem', NavItem)
app.component('PageContent', PageContent)
app.component('PageHeader', PageHeader)

// Admin Modals
app.component('AchievementModal', AchievementModal)
app.component('TariffModal', TariffModal)
app.component('UserModal', UserModal)

// Admin Settings
app.component('PromocodesManager', PromocodesManager)
app.component('PromocodesStats', PromocodesStats)
app.component('PromoUsageHistory', PromoUsageHistory)
app.component('SystemSettings', SystemSettings)

// Регистрируем глобальный компонент
app.component('OptimizedImage', OptimizedImage)

// Подключаем плагины
app.use(pinia)
app.use(router)

// Регистрируем глобальный компонент SimpleToast
app.component('SimpleToast', SimpleToast)

// Настраиваем менеджер тостов для решения проблемы навигации
getToastManager().setupRouterGuards(router)

// Регистрируем директиву ленивой загрузки
app.directive('lazy', vLazyLoad)

// Монтируем приложение
app.mount('#app')
