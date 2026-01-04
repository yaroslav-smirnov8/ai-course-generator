// Тестовый скрипт для ручного тестирования сервиса детализации плана урока
// Этот скрипт можно запустить через Node.js с помощью команды:
// node -r ts-node/register test/test-lesson-plan-detail.ts

import { lessonPlanDetailService } from '../src/services/lessonPlanDetailService';

// Пример формы плана урока
const sampleFormData = {
  language: 'English',
  topic: 'Introduction to Art History',
  age: '12-15',
  methodology: 'interactive',
  individual_group: 'group',
  online_offline: 'online',
  duration: 60,
  level: 'intermediate'
};

// Пример плана урока
const sampleLessonPlan = `
# Lesson Plan: Introduction to Art History

**Language**: English
**Age Group**: 12-15
**Methodology**: Interactive
**Duration**: 60 minutes
**Type**: Lecture with discussion
**Format**: Online
**Focus**: General understanding of art history
**Complexity Level**: Medium

## Lesson Objectives:
- Introduce students to key periods and styles in art history
- Develop visual analysis skills
- Encourage appreciation of different artistic traditions
- Promote discussion about the role of art in society

## Materials Needed:
- Digital presentation with high-quality art images
- Virtual whiteboard for collaborative activities
- Digital handouts with timeline and key terms
- Access to online museum collections for virtual exploration

## Lesson Structure:

1. Introduction (5 min)
   - Brief overview of what art history is and why it matters
   - Quick icebreaker: Students share their favorite artwork or artist

2. Art History Timeline Overview (10 min)
   - Presentation of major art periods from prehistoric to contemporary
   - Introduction to key terminology for discussing art

3. Group Work: Art Period Exploration (15 min)
   - Divide class into small groups, each assigned a different art period
   - Groups research their period and prepare to present one significant artwork

4. Group Presentations (15 min)
   - Each group briefly presents their findings
   - Discussion of differences and similarities between periods

5. Visual Analysis Exercise (10 min)
   - Guided practice analyzing one artwork together as a class
   - Discussion of elements like composition, color, technique, and meaning

6. Conclusion and Homework Assignment (5 min)
   - Review of key concepts
   - Introduction to homework assignment: Find an artwork that interests you and write a short analysis

## Assessment:
- Participation in group work and discussions
- Quality of group presentation
- Completion of visual analysis exercise
- Homework assignment

## Differentiation:
- For higher-level students: More complex analytical questions
- For students needing support: Simplified analysis framework with guided questions
- Extension: Research on specific artists of interest
`;

// Тестирование скрипта учителя
async function testTeacherScript() {
  console.log('\n=== Тестирование генерации скрипта учителя ===\n');
  
  try {
    const result = await lessonPlanDetailService.detailLessonPlanScript(
      sampleLessonPlan, 
      sampleFormData
    );
    
    console.log('=== Результат генерации скрипта учителя ===');
    console.log(result.substring(0, 500) + '...');
    console.log('\n=== Первые 500 символов результата ===');
    
    // Проверяем, что в результате есть упоминание искусства и истории
    const containsArt = result.toLowerCase().includes('art');
    const containsHistory = result.toLowerCase().includes('history');
    
    console.log('\n=== Проверка тематики ===');
    console.log(`Содержит упоминание "art": ${containsArt}`);
    console.log(`Содержит упоминание "history": ${containsHistory}`);
    
    return true;
  } catch (error) {
    console.error('Ошибка при тестировании скрипта учителя:', error);
    return false;
  }
}

// Тестирование домашнего задания
async function testHomework() {
  console.log('\n=== Тестирование генерации домашнего задания ===\n');
  
  try {
    const result = await lessonPlanDetailService.detailLessonPlanHomework(
      sampleLessonPlan, 
      sampleFormData
    );
    
    console.log('=== Результат генерации домашнего задания ===');
    console.log(result.substring(0, 500) + '...');
    console.log('\n=== Первые 500 символов результата ===');
    
    // Проверяем, что в результате есть упоминание искусства и истории
    const containsArt = result.toLowerCase().includes('art');
    const containsHistory = result.toLowerCase().includes('history');
    
    console.log('\n=== Проверка тематики ===');
    console.log(`Содержит упоминание "art": ${containsArt}`);
    console.log(`Содержит упоминание "history": ${containsHistory}`);
    
    return true;
  } catch (error) {
    console.error('Ошибка при тестировании домашнего задания:', error);
    return false;
  }
}

// Основная функция тестирования
async function runTests() {
  console.log('Запуск тестирования сервиса детализации плана урока...');
  
  let passedTests = 0;
  const totalTests = 2;
  
  if (await testTeacherScript()) {
    passedTests++;
  }
  
  if (await testHomework()) {
    passedTests++;
  }
  
  console.log(`\n=== Результаты тестирования ===`);
  console.log(`Пройдено тестов: ${passedTests}/${totalTests}`);
  
  if (passedTests === totalTests) {
    console.log('✅ Все тесты пройдены успешно!');
  } else {
    console.log('❌ Есть проблемы в тестах. Проверьте логи выше.');
  }
}

// Запускаем тестирование
runTests().catch(console.error);

/*
Инструкция по использованию:

1. Установите ts-node, если он еще не установлен:
   npm install -g ts-node

2. Запустите скрипт:
   node -r ts-node/register test/test-lesson-plan-detail.ts

3. Проверьте результаты тестов и логи.

Примечание: Этот тест предназначен для ручной проверки 
и требует настроенного окружения с доступом к API.
*/ 