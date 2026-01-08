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

## Core Features

### Lesson Plan Generation Service

The project includes a comprehensive lesson plan generation service (`src/services/lessonPlanDetailService.ts`) that enables context-aware content creation aligned with selected topics and learning objectives. This service integrates tightly with the backend to provide dynamic, pedagogically sound lesson materials.

#### Primary Service Methods

- **detailLessonPlanScript** - Generates instructor scripts and narrative guidance for lesson delivery
- **detailLessonPlanHomework** - Creates structured homework assignments aligned with lesson objectives
- **detailLessonPlanExercises** - Produces supplementary practice exercises with varied difficulty levels
- **detailLessonPlanGame** - Develops interactive game-based learning activities for student engagement
- **detailLessonPlanPoint** - Expands individual lesson elements with detailed pedagogical content

### Intelligent Parameter Extraction and Validation

The service implements automatic parameter detection and validation through two core functions:

- **extractParamsFromPlan** - Analyzes lesson plan text using natural language processing to identify and extract contextual parameters (language, topic, target age group, pedagogical methodology, lesson format, and proficiency level)
- **mergeAndValidateParams** - Reconciles parameters from multiple sources (user input, extracted from plan, system defaults) with validation logic to ensure consistency

#### Supported Lesson Configuration Parameters

| Parameter | Default | Options |
|-----------|---------|---------|
| Language | English | Any language |
| Topic | User-specified | Extracted from plan or manual input |
| Age Group | Teenagers (13-18) | Elementary, Teenagers, Adults |
| Teaching Methodology | Communicative | Task-based, Grammar-translation, etc. |
| Lesson Type | Individual | Individual, Group |
| Delivery Format | Online | Online, Offline, Hybrid |
| Duration | 60 minutes | Configurable |
| Language Level | Intermediate | A1-C2 CEFR levels |

### Architecture and Processing Pipeline

The system implements a robust multi-stage processing pipeline:

1. **Topic Preservation** - Lesson focus is retained throughout the entire generation workflow via explicit API parameters
2. **Quota Management** - User generation limits are verified before API requests to prevent quota overages
3. **Structured Logging** - Comprehensive request/response logging at each processing stage for debugging and analytics
4. **Content Adaptation** - Generated content automatically adjusts to the specified lesson format (individual/group)
5. **Delivery Type Optimization** - Materials are customized for online or offline instructional delivery
6. **Intelligent Fallback** - If the detailed service experiences issues, the system automatically reverts to the baseline generation method

### Exception Handling and Resilience

The `LessonPlan.vue` component implements a built-in failover mechanism. Should the advanced detailing service encounter errors or timeouts, the system gracefully transitions to the previous generation approach, ensuring service continuity and user experience.
