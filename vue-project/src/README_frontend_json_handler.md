# Frontend for Enhanced JSON Handler

## Overview

This implementation adds support for an enhanced JSON handler in the frontend part of the application. The new functionality allows:

1. Display information about data recovery from incomplete or corrupted API responses
2. Visualize course structure with data completeness indication
3. Check and validate course structure
4. Provide a user-friendly interface when working with partially recovered data

## Components

### 1. JsonRecoveryStatus.vue

Component for displaying JSON data recovery status with the ability to show details and actions.

**Properties:**
- `status`: 'success' | 'partial' | 'failure' | 'none'
- `details`: Object with information about recovered and missing fields
- `dismissible`: Flag indicating whether the notification can be closed
- `actions`: Array of actions (buttons) for interaction

### 2. ApiErrorHandler.vue

Wrapper component for handling API errors and displaying data recovery information.

**Properties:**
- `apiError`: String with error description
- `errorDetails`: Detailed error information
- `errorActions`: Actions for error handling
- `watchRecovery`: Flag for tracking recovery status from store

### 3. CourseStructureViewer.vue

Component for visualizing course structure with data completeness status display.

**Properties:**
- `course`: Object with course data
- `recoveryStatus`: Data recovery status

**Events:**
- `regenerate`: Request to regenerate course
- `close`: Request to close structure view

## Utilities

### courseValidation.ts

Set of functions for checking and validating course and lesson structure.

**Main functions:**
- `validateCourseStructure`: Checks completeness and correctness of course structure
- `validateLesson`: Checks completeness and correctness of lesson
- `getCourseRecoveryInfo`: Analyzes course recovery state

## Store Integration

### store/course.ts

Store extension for working with JSON recovery metadata.

**Added properties:**
- `recoveryStatus`: Data recovery status
- `recoveryDetails`: Detailed recovery information

**Added methods:**
- `resetRecoveryInfo`: Reset recovery information

## API Integration

### services/courseGenerator.ts

Service update for handling recovery metadata in API responses.

**Changes:**
- Added `ApiResponse<T>` interface for typing responses with metadata
- Updated `generateCourseStructure` method to extract recovery metadata
- Added handling of various metadata formats

## Usage

1. Wrapping components to display errors and recovery status:
```vue
<ApiErrorHandler>
  <YourComponent />
</ApiErrorHandler>
```

2. Displaying recovery status in interface:
```vue
<JsonRecoveryStatus 
  :status="store.recoveryStatus"
  :details="store.recoveryDetails"
/>
```

3. Checking course data completeness:
```ts
import { validateCourseStructure } from '@/utils/courseValidation';

const validation = validateCourseStructure(course);
console.log(`Data completeness: ${validation.score}%`);
```

## Data Flow Example

1. User requests course generation
2. Backend uses enhanced JSON handler and returns data with recovery metadata
3. Frontend processes metadata and displays corresponding information
4. User sees recovery status and can decide on regeneration if needed

## Visual Feedback

- **Green indicator**: data fully recovered
- **Yellow indicator**: data partially recovered
- **Red indicator**: data heavily corrupted, recovery failed

For each lesson, a data completeness indicator is also displayed, allowing quick identification of problem areas in the course structure.
