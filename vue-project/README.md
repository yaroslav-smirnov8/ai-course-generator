# vue-project

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## Новые функциональные возможности

### Сервис детализации плана урока

В проект добавлен новый сервис для детализации плана урока, который обеспечивает более точную генерацию контента, соответствующего выбранной теме. Сервис находится в файле `src/services/lessonPlanDetailService.ts`.

Основные функции сервиса:

- **detailLessonPlanScript** - создание скрипта учителя на основе плана урока
- **detailLessonPlanHomework** - создание домашнего задания для плана урока
- **detailLessonPlanExercises** - создание дополнительных упражнений для плана урока
- **detailLessonPlanGame** - создание игровой активности для плана урока
- **detailLessonPlanPoint** - детализация конкретного пункта плана урока

### Система автоматического определения параметров урока

В сервис добавлена система для интеллектуального анализа текста плана урока и извлечения из него ключевых параметров:

- **extractParamsFromPlan** - функция извлечения параметров урока из текста плана (язык, тема, возраст, методология, формат, тип и т.д.)
- **mergeAndValidateParams** - функция объединения и проверки параметров из формы, плана и дефолтных значений

Поддерживаемые параметры:
- Язык урока (дефолт: English)
- Тема урока
- Возрастная группа (дефолт: teens)
- Методология
- Тип занятия: индивидуальный/групповой (дефолт: individual)
- Формат проведения: онлайн/оффлайн (дефолт: online)
- Продолжительность (дефолт: 60 минут)
- Уровень владения языком (дефолт: intermediate)

Ключевые улучшения:

1. Передача темы урока (lesson_focus) из исходного плана в API для генерации тематически согласованного контента
2. Явная проверка пользовательских лимитов генерации перед отправкой запроса
3. Детальное логирование всех стадий запроса и ответа для упрощения отладки
4. Обеспечение сохранения темы при генерации контента через явные указания в параметре action
5. Более надежная обработка ошибок и нестандартных форматов ответов
6. **НОВОЕ:** Автоматическая адаптация контента под формат занятия (индивидуальный/групповой)
7. **НОВОЕ:** Автоматическая адаптация контента под тип проведения (онлайн/оффлайн)
8. **НОВОЕ:** Интеллектуальное определение параметров из текста плана с поддержкой разных языков

В компоненте `LessonPlan.vue` добавлен механизм отказоустойчивости - при проблемах с новым сервисом система автоматически переключается на предыдущий метод генерации.
