# app/services/content/processor.py
from typing import Dict, Any
import re
import json
from ...utils.formatters import format_markdown, clean_text
import logging

class ContentProcessor:
    @staticmethod
    def _extract_and_format_json(content: str, content_type: str = "general") -> str:
        """
        Извлекает JSON из контента и преобразует его в читаемый Markdown формат
        """
        try:
            # Попытка найти JSON в контенте
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                if content_type == "lesson_plan":
                    return ContentProcessor._format_lesson_plan_from_json(data)
                elif content_type == "exercise":
                    return ContentProcessor._format_exercises_from_json(data)
                elif content_type == "game":
                    return ContentProcessor._format_game_from_json(data)
                else:
                    return ContentProcessor._format_generic_json(data)
            
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Если JSON не найден или не удалось обработать, возвращаем исходный контент
        return content
    
    @staticmethod
    def _format_lesson_plan_from_json(data: dict) -> str:
        """Форматирует план урока из JSON в Markdown"""
        if not isinstance(data, dict):
            return str(data)
        
        # Ищем информацию об уроке в различных возможных ключах
        lesson_title = data.get('Название урока', data.get('title', data.get('lesson_title', 'Lesson Plan')))
        objectives = data.get('Цели урока', data.get('objectives', data.get('lesson_objectives', [])))
        grammar = data.get('Грамматика', data.get('grammar', data.get('grammar_focus', [])))
        vocabulary = data.get('Лексика', data.get('vocabulary', data.get('vocabulary_focus', [])))
        
        # Создаем детальный план урока
        markdown = f"# {lesson_title}\n\n"
        
        if objectives:
            markdown += "## Цели урока\n"
            for obj in objectives:
                markdown += f"- {obj}\n"
            markdown += "\n"
        
        # Добавляем стандартную структуру урока
        markdown += "## Структура урока (60 минут)\n\n"
        
        markdown += "### 1. Введение и разминка (10 минут)\n"
        markdown += "- Приветствие и проверка домашнего задания\n"
        markdown += "- Краткое повторение материала предыдущего урока\n"
        markdown += "- Введение в тему урока\n\n"
        
        markdown += "### 2. Презентация нового материала (15 минут)\n"
        if grammar:
            markdown += "**Грамматический фокус:**\n"
            for gram in grammar:
                markdown += f"- {gram}\n"
            markdown += "\n"
        
        if vocabulary:
            markdown += "**Лексический фокус:**\n"
            for vocab in vocabulary:
                markdown += f"- {vocab}\n"
            markdown += "\n"
        
        markdown += "### 3. Управляемая практика (15 минут)\n"
        markdown += "- Упражнения на закрепление новой грамматики\n"
        markdown += "- Отработка новой лексики в контексте\n"
        markdown += "- Парная/групповая работа\n\n"
        
        markdown += "### 4. Свободная практика (15 минут)\n"
        markdown += "- Коммуникативные упражнения\n"
        markdown += "- Ролевые игры или дискуссии\n"
        markdown += "- Практическое применение изученного материала\n\n"
        
        markdown += "### 5. Заключение и домашнее задание (5 минут)\n"
        markdown += "- Подведение итогов урока\n"
        markdown += "- Разъяснение домашнего задания\n"
        markdown += "- Ответы на вопросы\n\n"
        
        markdown += "## Материалы\n"
        markdown += "- Учебник\n"
        markdown += "- Раздаточный материал\n"
        markdown += "- Аудио/видео материалы\n"
        markdown += "- Доска/презентация\n\n"
        
        markdown += "## Оценивание\n"
        markdown += "- Наблюдение за участием в классе\n"
        markdown += "- Проверка выполнения упражнений\n"
        markdown += "- Анализ использования новой лексики и грамматики\n"
        
        return markdown
    
    @staticmethod
    def _format_exercises_from_json(data: dict) -> str:
        """Форматирует упражнения из JSON в Markdown"""
        if not isinstance(data, dict):
            return str(data)
        
        markdown = ""
        
        # Если есть уроки, извлекаем упражнения из них
        lessons = data.get('Уроки', data.get('lessons', []))
        if lessons and isinstance(lessons, list):
            for i, lesson in enumerate(lessons, 1):
                if isinstance(lesson, dict):
                    lesson_title = lesson.get('Название урока', lesson.get('title', f'Lesson {i}'))
                    objectives = lesson.get('Цели урока', lesson.get('objectives', []))
                    grammar = lesson.get('Грамматика', lesson.get('grammar', []))
                    vocabulary = lesson.get('Лексика', lesson.get('vocabulary', []))
                    
                    markdown += f"# Упражнения для урока: {lesson_title}\n\n"
                    
                    # Упражнение на лексику
                    if vocabulary:
                        markdown += "## Упражнение 1: Vocabulary Practice\n\n"
                        markdown += "**Цель:** Отработка новой лексики\n\n"
                        markdown += "**Инструкции:** Соедините слова с их определениями:\n\n"
                        
                        for j, word in enumerate(vocabulary[:5], 1):
                            markdown += f"{j}. {word}\n"
                        markdown += "\n"
                        
                        markdown += "**Ответы:**\n"
                        for j, word in enumerate(vocabulary[:5], 1):
                            markdown += f"{j}. {word} - [определение]\n"
                        markdown += "\n"
                    
                    # Упражнение на грамматику
                    if grammar:
                        markdown += "## Упражнение 2: Grammar Practice\n\n"
                        markdown += "**Цель:** Отработка грамматических структур\n\n"
                        markdown += f"**Грамматический фокус:** {', '.join(grammar)}\n\n"
                        markdown += "**Инструкции:** Завершите предложения, используя правильную грамматическую форму:\n\n"
                        
                        for j in range(1, 6):
                            markdown += f"{j}. ___________________ (example sentence)\n"
                        markdown += "\n"
                        
                        markdown += "**Ответы:**\n"
                        for j in range(1, 6):
                            markdown += f"{j}. [правильный ответ]\n"
                        markdown += "\n"
                    
                    # Коммуникативное упражнение
                    if objectives:
                        markdown += "## Упражнение 3: Communication Activity\n\n"
                        markdown += "**Цель:** Практическое применение изученного материала\n\n"
                        markdown += f"**Задачи урока:** {', '.join(objectives)}\n\n"
                        markdown += "**Инструкции:** Работайте в парах и обсудите следующие вопросы:\n\n"
                        
                        for j in range(1, 4):
                            markdown += f"{j}. [Вопрос для обсуждения]\n"
                        markdown += "\n"
                    
                    markdown += "---\n\n"
        
        else:
            # Если это прямые упражнения без структуры урока
            markdown += "# Упражнения\n\n"
            markdown += "## Упражнение 1: Vocabulary Practice\n\n"
            markdown += "**Инструкции:** Заполните пропуски подходящими словами:\n\n"
            for i in range(1, 6):
                markdown += f"{i}. The athlete _______ quickly across the field.\n"
            markdown += "\n**Ответы:** 1. ran/sprinted 2. moved 3. [etc.]\n\n"
            
            markdown += "## Упражнение 2: Grammar Focus\n\n"
            markdown += "**Инструкции:** Исправьте ошибки в предложениях:\n\n"
            for i in range(1, 6):
                markdown += f"{i}. [Предложение с ошибкой]\n"
            markdown += "\n**Ответы:** [Исправленные предложения]\n\n"
        
        return markdown
    
    @staticmethod
    def _format_game_from_json(data: dict) -> str:
        """Форматирует игру из JSON в Markdown"""
        if not isinstance(data, dict):
            return str(data)
        
        # Попытка извлечь информацию об игре
        game_title = data.get('Название игры', data.get('game_title', 'Educational Game'))
        game_type = data.get('Тип игры', data.get('game_type', 'Interactive'))
        
        markdown = f"# {game_title}\n\n"
        markdown += f"**Тип игры:** {game_type}\n\n"
        
        markdown += "## Цель игры\n"
        markdown += "Практиковать изученную лексику и грамматику в интерактивной форме\n\n"
        
        markdown += "## Материалы\n"
        markdown += "- Карточки с заданиями\n"
        markdown += "- Доска или флипчарт\n"
        markdown += "- Таймер\n\n"
        
        markdown += "## Правила игры\n\n"
        markdown += "### Подготовка (5 минут)\n"
        markdown += "1. Разделите класс на команды по 3-4 человека\n"
        markdown += "2. Объясните правила игры\n"
        markdown += "3. Подготовьте необходимые материалы\n\n"
        
        markdown += "### Игровой процесс (20 минут)\n"
        markdown += "1. Команды по очереди выполняют задания\n"
        markdown += "2. За правильный ответ команда получает балл\n"
        markdown += "3. При неправильном ответе ход переходит к следующей команде\n"
        markdown += "4. Ведите счет на доске\n\n"
        
        markdown += "### Завершение (5 минут)\n"
        markdown += "1. Подсчитайте баллы\n"
        markdown += "2. Объявите победителя\n"
        markdown += "3. Обсудите сложные моменты\n\n"
        
        markdown += "## Вариации\n"
        markdown += "- Можно изменить сложность заданий в зависимости от уровня группы\n"
        markdown += "- Добавить временные ограничения для повышения динамики\n"
        markdown += "- Использовать мультимедийные материалы\n"
        
        return markdown
    
    @staticmethod
    def _format_generic_json(data: dict) -> str:
        """Форматирует общий JSON в читаемый формат"""
        def dict_to_markdown(obj, level=1):
            markdown = ""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    header = "#" * min(level, 6)
                    markdown += f"{header} {key}\n\n"
                    if isinstance(value, (dict, list)):
                        markdown += dict_to_markdown(value, level + 1)
                    else:
                        markdown += f"{value}\n\n"
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        markdown += dict_to_markdown(item, level)
                    else:
                        markdown += f"- {item}\n"
                markdown += "\n"
            return markdown
        
        return dict_to_markdown(data)

    @staticmethod
    def process_lesson_plan(content: str) -> str:
        """Обработка сгенерированного плана урока с валидацией полноты"""
        logger = logging.getLogger(__name__)
        
        # Сначала пытаемся извлечь и отформатировать JSON
        formatted_content = ContentProcessor._extract_and_format_json(content, "lesson_plan")
        
        # Если JSON был обработан, используем отформатированный контент
        if formatted_content != content:
            content = formatted_content
        
        # Базовая обработка
        content = clean_text(content)
        content = format_markdown(content)
        
        # Валидация обязательных разделов для детального плана урока
        required_sections = [
            "LESSON OVERVIEW",
            "DETAILED TIMING", 
            "LANGUAGE ANALYSIS",
            "MATERIALS AND RESOURCES",
            "ASSESSMENT AND FEEDBACK",
            "HOMEWORK AND FOLLOW-UP", 
            "CONTINGENCY PLANNING",
            "REFLECTION AND DEVELOPMENT"
        ]
        
        # Альтернативные названия разделов (для гибкости)
        section_alternatives = {
            "LESSON OVERVIEW": ["Обзор урока", "Описание урока", "Общая информация", "Введение"],
            "DETAILED TIMING": ["Подробное расписание", "Временные рамки", "План урока", "Структура урока"],
            "LANGUAGE ANALYSIS": ["Языковой анализ", "Грамматика и лексика", "Изучаемый материал"],
            "MATERIALS AND RESOURCES": ["Материалы", "Ресурсы", "Необходимые материалы"],
            "ASSESSMENT AND FEEDBACK": ["Оценивание", "Обратная связь", "Контроль знаний"],
            "HOMEWORK AND FOLLOW-UP": ["Домашнее задание", "Последующие действия", "Домашняя работа"],
            "CONTINGENCY PLANNING": ["План Б", "Резервные варианты", "Альтернативы"],
            "REFLECTION AND DEVELOPMENT": ["Рефлексия", "Развитие", "Заключение"]
        }
        
        # Проверка минимального объема (1500 слов)
        word_count = len(content.split())
        if word_count < 800:  # Понижен порог для более реалистичных требований
            logger.warning(f"Lesson plan may be too short: {word_count} words (recommended minimum 800)")
        
        # ОТКЛЮЧЕНО: Добавление недостающих разделов с шаблонами - работаем на качественный персонализированный контент
        # content = ContentProcessor._ensure_required_sections(content, required_sections, section_alternatives)
        
        # Улучшение структуры разделов
        content = ContentProcessor._improve_section_structure(content)
        
        # Применяем улучшенное форматирование планов уроков
        content = ContentProcessor._enhance_lesson_plan_formatting(content)
        
        return content
    
    @staticmethod
    def _ensure_required_sections(content: str, required_sections: list, alternatives: dict) -> str:
        """Добавляет недостающие разделы с базовыми шаблонами"""
        logger = logging.getLogger(__name__)
        
        for section in required_sections:
            section_found = False
            
            # Проверяем основное название
            if section.lower() in content.lower():
                section_found = True
            
            # Проверяем альтернативные названия
            if not section_found and section in alternatives:
                for alternative in alternatives[section]:
                    if alternative.lower() in content.lower():
                        section_found = True
                        break
            
            # Если раздел не найден, добавляем шаблон
            if not section_found:
                template = ContentProcessor._get_section_template(section)
                content += f"\n\n{template}"
                logger.info(f"Added missing section template: {section}")
        
        return content
    
    @staticmethod
    def _get_section_template(section: str) -> str:
        """Возвращает шаблон для недостающего раздела"""
        templates = {
            "LESSON OVERVIEW": """## 📋 Lesson Overview
*This section should provide a comprehensive summary of the lesson including key learning objectives, connections to previous lessons, and overview of skills covered.*

**Key Learning Objectives:**
- [Specify main learning goals]
- [Include language skills focus]
- [Connection to course objectives]

**Skills Integration:**
- Speaking: [Specify activities]
- Listening: [Specify activities] 
- Reading: [Specify activities]
- Writing: [Specify activities]""",

            "DETAILED TIMING": """## ⏰ Detailed Timing and Activities
*Each activity should include exact timing, step-by-step instructions, and interaction patterns.*

### Warm-up (5-10 minutes)
**Objective:** [Specify objective]
**Instructions:** [Step-by-step teacher instructions]
**Student Activity:** [What students will do]
**Materials:** [List needed materials]

### Main Activities (30-40 minutes)
**Activity 1: [Name] (15 minutes)**
- **Setup:** [How to organize]
- **Instructions:** [Teacher steps]
- **Student Task:** [Specific student actions]
- **Assessment:** [How to check understanding]

**Activity 2: [Name] (15 minutes)**
- **Setup:** [How to organize]
- **Instructions:** [Teacher steps]
- **Student Task:** [Specific student actions]
- **Assessment:** [How to check understanding]

### Wrap-up (10 minutes)
**Summary:** [How to conclude]
**Preview:** [Connection to next lesson]""",

            "LANGUAGE ANALYSIS": """## 🔍 Language Analysis
*Detailed breakdown of target language with potential difficulties and solutions.*

**Target Grammar:**
- Structure: [Grammatical form]
- Meaning: [When/why used]
- Pronunciation: [Key pronunciation points]
- Common Errors: [Typical mistakes and corrections]

**Target Vocabulary:**
- [Word 1]: Definition, pronunciation, example sentence
- [Word 2]: Definition, pronunciation, example sentence
- [Word 3]: Definition, pronunciation, example sentence

**Language Functions:**
- [Function]: [Context and examples]

**Anticipated Problems:**
- Problem: [Specific difficulty]
- Solution: [Teaching strategy]""",

            "MATERIALS AND RESOURCES": """## 📚 Materials and Resources
*Complete list of all materials needed with preparation instructions.*

**Required Materials:**
- Whiteboard/markers
- Student handouts (see templates below)
- Audio/video equipment
- [Additional materials]

**Handout Templates:**
[Include actual worksheet templates or detailed descriptions]

**Technology Requirements:**
- [Specify any tech needs]
- Backup options if technology fails

**Preparation Checklist:**
- [ ] Print handouts
- [ ] Set up technology
- [ ] Prepare visual aids
- [ ] [Additional preparation steps]""",

            "ASSESSMENT AND FEEDBACK": """## 📊 Assessment and Feedback
*Detailed assessment criteria and feedback strategies.*

**Formative Assessment:**
- During Activity 1: [Observation criteria]
- During Activity 2: [Checking method]
- Exit ticket: [Quick assessment]

**Assessment Criteria:**
- Accuracy: [Specific measures]
- Fluency: [Specific measures]
- Participation: [Specific measures]

**Feedback Strategies:**
- Immediate correction: [When and how]
- Delayed feedback: [Methods]
- Peer feedback: [Organization]
- Self-assessment: [Tools and methods]

**Error Correction:**
- Grammar errors: [Approach]
- Pronunciation errors: [Approach]
- Vocabulary errors: [Approach]""",

            "HOMEWORK AND FOLLOW-UP": """## 📝 Homework and Follow-up
*Detailed homework assignments with clear instructions and assessment criteria.*

**Homework Assignment:**
**Task:** [Specific instructions]
**Duration:** [Expected time]
**Materials needed:** [List]
**Assessment criteria:** [How it will be graded]

**Differentiation:**
- For stronger students: [Extension activities]
- For weaker students: [Additional support]

**Next Lesson Preparation:**
- Review: [What to review]
- Preview: [What to prepare]
- Materials: [What students should bring]

**Follow-up Activities:**
- [Additional practice options]
- [Extension resources]""",

            "CONTINGENCY PLANNING": """## 🔄 Contingency Planning
*Alternative activities and solutions for common problems.*

**If Technology Fails:**
- Alternative Activity 1: [Description]
- Alternative Activity 2: [Description]
- Materials needed: [List]

**If Running Short on Time:**
- Priority activities: [Which to keep]
- Quick alternatives: [5-minute activities]
- Key points to cover: [Essential content]

**If Ahead of Schedule:**
- Extension Activity 1: [Description]
- Extension Activity 2: [Description]
- Additional practice: [Options]

**Classroom Management:**
- Large class adaptations: [Strategies]
- Mixed-level adaptations: [Strategies]
- Low-energy students: [Engagement strategies]""",

            "REFLECTION AND DEVELOPMENT": """## 🤔 Reflection and Development
*Post-lesson reflection points and development opportunities.*

**Lesson Reflection Questions:**
- What worked well? [Observation points]
- What could be improved? [Areas for development]
- How did students respond? [Engagement measures]
- Were objectives met? [Assessment review]

**Student Feedback Collection:**
- Quick survey questions: [List]
- Observation notes: [What to look for]
- Performance indicators: [Measures]

**Professional Development:**
- Skills to develop: [Teaching areas]
- Resources to explore: [Materials/courses]
- Peer observation focus: [Areas]

**Next Iteration Improvements:**
- Timing adjustments: [Changes]
- Activity modifications: [Improvements]
- Material updates: [Enhancements]"""
        }
        
        return templates.get(section, f"## {section}\n*This section needs to be completed with detailed information.*")
    
    @staticmethod
    def _improve_section_structure(content: str) -> str:
        """Улучшает структуру разделов с помощью дополнительного форматирования"""
        # Добавляем отступы между основными разделами
        import re
        
        # Заменяем заголовки второго уровня на более заметные
        content = re.sub(r'^##\s+(.+)$', r'## 📚 \1', content, flags=re.MULTILINE)
        
        # Добавляем разделители между основными секциями
        content = re.sub(r'(## 📚 .+\n)', r'\n---\n\1', content)
        
        # Удаляем лишние разделители в начале
        content = re.sub(r'^---\n', '', content)
        
        return content
    
    @staticmethod
    def _enhance_lesson_plan_formatting(content: str) -> str:
        """Улучшает форматирование планов уроков"""
        # Добавляем разделители между основными секциями
        content = re.sub(r'\n(#{1,2}\s*[A-ZА-Я][A-ZА-Я\s]+)', r'\n\n---\n\n\1', content)
        
        # Добавляем эмодзи к основным разделам
        section_emojis = {
            'LESSON OVERVIEW': '📋',
            'DETAILED TIMING': '⏰',
            'LANGUAGE ANALYSIS': '📝',
            'MATERIALS AND RESOURCES': '🎯',
            'ASSESSMENT AND FEEDBACK': '✅',
            'HOMEWORK AND FOLLOW-UP': '📚',
            'CONTINGENCY PLANNING': '🔄',
            'REFLECTION AND DEVELOPMENT': '🤔',
            'Обзор урока': '📋',
            'Подробное расписание': '⏰',
            'Языковой анализ': '📝',
            'Материалы': '🎯',
            'Оценивание': '✅',
            'Домашнее задание': '📚',
            'План Б': '🔄',
            'Рефлексия': '🤔'
        }
        
        for section, emoji in section_emojis.items():
            content = re.sub(rf'^(#{1,2}\s*)({section})', rf'\1{emoji} \2', content, flags=re.MULTILINE)
        
        # Улучшаем форматирование временных рамок
        content = re.sub(r'(\d+)\s*(?:мин|min|минут)', r'**\1 мин**', content)
        
        # Выделяем цели урока
        content = re.sub(r'\*\*Цели?[:\s]*\*\*', r'**🎯 Цели урока:**', content)
        content = re.sub(r'\*\*Objectives?[:\s]*\*\*', r'**🎯 Objectives:**', content)
        
        # Выделяем этапы урока
        content = re.sub(r'^(\d+\.\s*)([А-Яа-я\w\s]+)(\s*\(.*?\))?$', 
                        r'### \1📍 \2\3', content, flags=re.MULTILINE)
        
        # Улучшаем списки материалов
        content = re.sub(r'^\s*[-•]\s*', '📌 ', content, flags=re.MULTILINE)
        
        # Добавляем выделение для важных заметок
        content = re.sub(r'\*\*Важно[:\s]*\*\*', r'> **⚠️ Важно:**', content)
        content = re.sub(r'\*\*Note[:\s]*\*\*', r'> **💡 Note:**', content)
        
        return content

    @staticmethod
    def process_exercise(content: str) -> str:
        """Обработка сгенерированных упражнений с улучшенным форматированием"""
        # Сначала пытаемся извлечь и отформатировать JSON
        formatted_content = ContentProcessor._extract_and_format_json(content, "exercise")
        
        # Если JSON был обработан, возвращаем отформатированный контент
        if formatted_content != content:
            return formatted_content
        
        # Очищаем и форматируем контент
        content = clean_text(content)
        content = format_markdown(content)
        
        # Улучшаем структуру упражнений
        content = ContentProcessor._enhance_exercise_formatting(content)
        
        return content
    
    @staticmethod
    def _enhance_exercise_formatting(content: str) -> str:
        """Улучшает форматирование упражнений"""
        # Добавляем разделители между упражнениями
        content = re.sub(r'\n(#{1,3}\s*[Уу]пражнение)', r'\n\n---\n\n\1', content)
        
        # Улучшаем заголовки упражнений с эмодзи
        content = re.sub(r'^(#{1,3})\s*([Уу]пражнение\s*\d+[:\s]*.*?)$', 
                        r'\1 📝 \2', content, flags=re.MULTILINE)
        
        # Добавляем эмодзи к основным секциям
        content = re.sub(r'\*\*Цель:\*\*\s*([^*\n]+)', r'**🎯 Цель:** \1', content)
        content = re.sub(r'\*\*Время:\*\*\s*([^*\n]+)', r'**⏱️ Время:** \1', content)
        content = re.sub(r'\*\*Уровень сложности:\*\*\s*([^*\n]+)', r'**📊 Уровень сложности:** \1', content)
        content = re.sub(r'\*\*Инструкции:\*\*', r'**📋 Инструкции:**', content)
        content = re.sub(r'\*\*Ответы:\*\*', r'**✅ Ответы:**', content)
        content = re.sub(r'\*\*Примеры:\*\*', r'**💡 Примеры:**', content)
        content = re.sub(r'\*\*Задания:\*\*', r'**📚 Задания:**', content)
        
        # Улучшаем нумерованные списки в заданиях
        content = ContentProcessor._enhance_exercise_numbering(content)
        
        # Добавляем выделение для ответов
        content = re.sub(r'(Ответ[ыи]?:?\s*)(.*?)(?=\n\n|\n\d+\.|\Z)', 
                        r'> **\1** \2', content, flags=re.DOTALL | re.MULTILINE)
        
        return content
    
    @staticmethod
    def _enhance_exercise_numbering(content: str) -> str:
        """Улучшает нумерацию в упражнениях"""
        # Находим блоки с заданиями и улучшаем их нумерацию
        def improve_numbering(match):
            text = match.group(0)
            lines = text.split('\n')
            improved_lines = []
            
            for line in lines:
                # Улучшаем нумерованные списки
                if re.match(r'^\s*\d+\.', line):
                    line = re.sub(r'^(\s*)(\d+)\.', r'\1**\2.** ', line)
                improved_lines.append(line)
            
            return '\n'.join(improved_lines)
        
        # Применяем улучшения к блокам заданий
        content = re.sub(r'(\*\*[📚💡]?\s*[Зз]адания?[:\s]*\*\*.*?)(?=\n\*\*|\n#{1,3}|\Z)', 
                        improve_numbering, content, flags=re.DOTALL)
        
        return content

    @staticmethod
    def process_game(content: str) -> str:
        """Обработка сгенерированных игр с улучшенным форматированием"""
        # Сначала пытаемся извлечь и отформатировать JSON
        formatted_content = ContentProcessor._extract_and_format_json(content, "game")
        
        # Если JSON был обработан, возвращаем отформатированный контент
        if formatted_content != content:
            return formatted_content
        
        # Очищаем и форматируем контент
        content = clean_text(content)
        content = format_markdown(content)
        
        # Улучшаем структуру игры
        content = ContentProcessor._enhance_game_formatting(content)
        
        return content
    
    @staticmethod
    def _enhance_game_formatting(content: str) -> str:
        """Улучшает форматирование игрового контента"""
        # Добавляем разделители между секциями
        content = re.sub(r'\n(#{1,3}\s*)', r'\n\n---\n\n\1', content)
        
        # Улучшаем форматирование списков материалов
        content = re.sub(r'\*\*Материалы:\*\*\s*(.*?)(?=\n\*\*|\n#{1,3}|\Z)', 
                        lambda m: f"**🎯 Материалы:**\n\n{ContentProcessor._format_materials_list(m.group(1))}\n", 
                        content, flags=re.DOTALL)
        
        # Улучшаем форматирование правил
        content = re.sub(r'\*\*Правила игры:\*\*\s*(.*?)(?=\n\*\*|\n#{1,3}|\Z)', 
                        lambda m: f"**📋 Правила игры:**\n\n{ContentProcessor._format_rules_list(m.group(1))}\n", 
                        content, flags=re.DOTALL)
        
        # Добавляем эмодзи к заголовкам
        content = re.sub(r'^(#{1,3})\s*(.+?)$', r'\1 🎮 \2', content, flags=re.MULTILINE)
        
        # Добавляем временные метки
        content = re.sub(r'\*\*Время:\*\*\s*([^*\n]+)', r'**⏱️ Время:** \1', content)
        content = re.sub(r'\*\*Участники:\*\*\s*([^*\n]+)', r'**👥 Участники:** \1', content)
        
        return content
    
    @staticmethod
    def _format_materials_list(materials_text: str) -> str:
        """Форматирует список материалов"""
        items = [item.strip() for item in materials_text.split(',') if item.strip()]
        if not items:
            return materials_text
        
        formatted_items = []
        for item in items:
            if not item.startswith('-') and not item.startswith('*'):
                item = f"• {item}"
            formatted_items.append(item)
        
        return '\n'.join(formatted_items)
    
    @staticmethod
    def _format_rules_list(rules_text: str) -> str:
        """Форматирует список правил"""
        # Разбиваем по пунктам
        rules = re.split(r'\n(?=\d+\.|\w+\))', rules_text)
        formatted_rules = []
        
        for i, rule in enumerate(rules, 1):
            rule = rule.strip()
            if rule:
                # Добавляем нумерацию если её нет
                if not re.match(r'^\d+\.', rule):
                    rule = f"{i}. {rule}"
                formatted_rules.append(rule)
        
        return '\n'.join(formatted_rules)
    
    @staticmethod
    async def process_game_content(content: str, game_data: dict, logger=None) -> dict:
        """
        Улучшенная функция для обработки контента игр с извлечением структурированной информации
        
        Args:
            content (str): Сгенерированный контент игры
            game_data (dict): Данные о типе игры и других параметрах
            logger: Логгер для вывода отладочной информации
            
        Returns:
            dict: Структурированная информация об игре
        """
        # Если логгер не передан, используем стандартный
        if logger is None:
            logger = logging.getLogger(__name__)
            
        try:
            # Логируем полученный контент для отладки
            logger.info(f"Обработка игрового контента (первые 500 символов): {content[:500]}...")
            
            # Дополнительное логирование метаданных запроса
            logger.info(f"Данные игры: язык={game_data.get('language', 'не указан')}, "
                      f"тип={game_data.get('game_type', 'не указан')}, "
                      f"уровень={game_data.get('level', 'не указан')}")
            
            # Логируем длину контента
            content_length = len(content) if content else 0
            logger.info(f"Длина полученного контента: {content_length} символов")
            
            # Ограничиваем размер контента для предотвращения проблем с парсингом
            max_content_length = 25000  # 25KB максимум для игр
            if content_length > max_content_length:
                logger.warning(f"Контент слишком длинный ({content_length} символов), обрезаем до {max_content_length}")
                content = content[:max_content_length] + "\n\n[Контент был обрезан из-за большого размера]"
            
            # Пытаемся извлечь структурированную информацию из игры
            game_info = ContentProcessor._parse_game_from_content(content, game_data, logger)
            
            logger.info(f"Игра обработана: тип='{game_info.get('game_type', 'не определен')}'")
            return game_info
            
        except Exception as e:
            logger.error(f"Ошибка при обработке контента игры: {str(e)}")
            # В случае ошибки возвращаем базовую структуру
            return {
                "game_type": game_data.get('game_type', 'unknown'),
                "title": "Game",
                "content": content,
                "materials": [],
                "instructions": "",
                "objectives": []
            }
    
    @staticmethod
    def _parse_game_from_content(content: str, game_data: dict, logger) -> dict:
        """Парсит информацию об игре из контента"""
        import re
        
        # Инициализируем структуру игры
        game_info = {
            "game_type": game_data.get('game_type', 'unknown'),
            "title": "Game",
            "content": content,
            "materials": [],
            "instructions": "",
            "objectives": []
        }
        
        try:
            # Ищем заголовок игры
            title_patterns = [
                r"(?i)^#+ *(?:game:?\s*)?(.+?)(?:\s*-\s*(.+))?$",
                r"(?i)(?:^|\n)(?:\*\*)?(?:game:?\s*)?(.+?)(?:\*\*)?(?:\s*-\s*(.+))?(?:\n|$)"
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    game_info["title"] = match.group(1).strip()
                    logger.info(f"Найден заглав: {game_info['title']}")
                    break
            
            # Ищем тип игры в контенте
            game_type_patterns = [
                r"(?i)(?:game\s*type|тип\s*игры)[:\s]*([^\n]+)",
                r"(?i)(?:^|\n)(?:\*\*)?(?:type|тип)(?:\*\*)?[:\s]*([^\n]+)"
            ]
            
            for pattern in game_type_patterns:
                match = re.search(pattern, content)
                if match:
                    extracted_type = match.group(1).strip()
                    if extracted_type.lower() not in ['not specified', 'не указан']:
                        game_info["game_type"] = extracted_type
                        logger.info(f"Найден тип игры: {extracted_type}")
                        break
            
            # Ищем материалы
            materials_patterns = [
                r"(?i)(?:^|\n)(?:\*\*)?(?:materials?|материалы)(?:\*\*)?[:\s]*\n?((?:[-*]\s*.+(?:\n|$))+)",
                r"(?i)(?:^|\n)(?:###?\s*)?(?:\*\*)?(?:materials?|материалы)(?:\*\*)?[:\s]*\n?((?:.+(?:\n|$))+?)(?=(?:\n#{1,3}\s|\n\*\*|$))"
            ]
            
            for pattern in materials_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                if match:
                    materials_text = match.group(1).strip()
                    # Извлекаем список материалов
                    materials = []
                    for line in materials_text.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('-') or line.startswith('*')):
                            material = re.sub(r'^[-*]\s*', '', line).strip()
                            if material:
                                materials.append(material)
                        elif line and not line.startswith('#'):
                            materials.append(line)
                    
                    if materials:
                        game_info["materials"] = materials[:10]  # Ограничиваем до 10 материалов
                        logger.info(f"Найдено {len(materials)} материалов")
                        break
            
            # Ищем инструкции
            instructions_patterns = [
                r"(?i)(?:^|\n)(?:\*\*)?(?:instructions?|инструкции|how\s*to\s*play|как\s*играть)(?:\*\*)?[:\s]*\n?((?:.+(?:\n|$))+?)(?=(?:\n#{1,3}\s|\n\*\*|$))",
                r"(?i)(?:^|\n)(?:###?\s*)?(?:\*\*)?(?:instructions?|инструкции)(?:\*\*)?[:\s]*\n?((?:.+(?:\n|$))+?)(?=(?:\n#{1,3}\s|\n\*\*|$))"
            ]
            
            for pattern in instructions_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                if match:
                    instructions = match.group(1).strip()[:1000]  # Ограничиваем длину
                    game_info["instructions"] = instructions
                    logger.info(f"Найдены инструкции (длина: {len(instructions)})")
                    break
            
            # Ищем цели/задачи
            objectives_patterns = [
                r"(?i)(?:^|\n)(?:\*\*)?(?:objective|цель|goal|задача)(?:\*\*)?[:\s]*\n?((?:[-*]\s*.+(?:\n|$))+)",
                r"(?i)(?:^|\n)(?:###?\s*)?(?:\*\*)?(?:objective|цель)(?:\*\*)?[:\s]*([^\n]+)"
            ]
            
            for pattern in objectives_patterns:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    objectives_text = match.group(1).strip()
                    objectives = []
                    
                    # Если это список
                    if objectives_text.startswith('-') or objectives_text.startswith('*'):
                        for line in objectives_text.split('\n'):
                            line = line.strip()
                            if line and (line.startswith('-') or line.startswith('*')):
                                objective = re.sub(r'^[-*]\s*', '', line).strip()
                                if objective:
                                    objectives.append(objective)
                    else:
                        # Если это одна строка
                        objectives.append(objectives_text)
                    
                    if objectives:
                        game_info["objectives"] = objectives[:5]  # Ограничиваем до 5 целей
                        logger.info(f"Найдено {len(objectives)} целей")
                        break
            
            logger.info(f"Парсинг игры завершен: тип={game_info['game_type']}, название={game_info['title']}")
            return game_info
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге игры: {str(e)}")
            return game_info

    @staticmethod
    async def process_exercise_content(content: str, exercise_data: dict, logger=None) -> list:
        """
        Улучшенная функция для обработки контента упражнений и разделения на отдельные упражнения

        Args:
            content (str): Сгенерированный контент упражнений
            exercise_data (dict): Данные о типе упражнений и других параметрах
            logger: Логгер для вывода отладочной информации

        Returns:
            list: Список упражнений с разделенным контентом, ответами и инструкциями
        """
        # Если логгер не передан, используем стандартный
        if logger is None:
            logger = logging.getLogger(__name__)

        try:
            # Логируем полученный контент для отладки
            logger.info(f"Полный контент (первые 500 символов): {content[:500]}...")

            # Дополнительное логирование метаданных запроса
            logger.info(f"Данные запроса: язык={exercise_data.get('language', 'не указан')}, "
                      f"тип={exercise_data.get('type', 'не указан')}, "
                      f"формат={exercise_data.get('individual_group', 'не указан')}, "
                      f"режим={exercise_data.get('online_offline', 'не указан')}")

            # Получаем метаданные
            meta = exercise_data.get('meta', {})
            include_answers = meta.get('includeAnswers', True)
            include_instructions = meta.get('includeInstructions', True)
            requested_quantity = exercise_data.get('quantity', 3)

            logger.info(f"Параметры контента: include_answers={include_answers}, include_instructions={include_instructions}, requested_quantity={requested_quantity}")

            # Логируем длину контента
            content_length = len(content) if content else 0
            logger.info(f"Длина полученного контента: {content_length} символов")

            # Ограничиваем размер контента для предотвращения проблем с парсингом
            max_content_length = 50000  # 50KB максимум
            if content_length > max_content_length:
                logger.warning(f"Контент слишком длинный ({content_length} символов), обрезаем до {max_content_length}")
                content = content[:max_content_length] + "\n\n[Контент был обрезан из-за большого размера]"
            
            # Пытаемся разделить контент на упражнения с улучшенными паттернами
            exercises = ContentProcessor._parse_exercises_from_content(content, exercise_data, logger)

            # Ограничиваем количество упражнений согласно запросу
            if len(exercises) > requested_quantity:
                logger.info(f"Обрезаем количество упражнений с {len(exercises)} до {requested_quantity}")
                exercises = exercises[:requested_quantity]

            logger.info(f"Отправляем {len(exercises)} упражнений")
            return exercises

        except Exception as e:
            logger.error(f"Ошибка при обработке контента упражнений: {str(e)}")
            # В случае ошибки возвращаем контент как есть в одном упражнении
            return [{
                "type": exercise_data.get('type', 'general') if exercise_data else "general",
                "content": content,
                "answers": "",
                "instructions": ""
            }]

    @staticmethod
    def _parse_exercises_from_content(content: str, exercise_data: dict, logger) -> list:
        """Парсит упражнения из контента с улучшенными паттернами"""
        exercises = []

        # Расширенные паттерны для разделения упражнений (в порядке приоритета)
        exercise_patterns = [
            # Самые специфичные паттерны сначала
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?exercise\s*(?:#?\d+|[ivx]+)[\.:\-\s]*(?:\*\*)?",  # Exercise 1, ### Exercise 1, **Exercise 1**
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?упражнение\s*(?:#?\d+|[ivx]+)[\.:\-\s]*(?:\*\*)?",  # Упражнение 1
            r"(?i)(?:^|\n)#{1,3}\s*exercise\s*(?:\d+|[ivx]+)?",  # # Exercise, ## Exercise 1, ### Exercise
            r"(?i)(?:^|\n)#{1,3}\s*упражнение\s*(?:\d+|[ivx]+)?",  # # Упражнение
            r"(?i)(?:^|\n)\d+\.\s*(?:exercise|упражнение)",  # 1. Exercise, 2. Упражнение
            r"(?i)(?:^|\n)(?:\*\*)?(?:exercise|упражнение)\s*(?:title|название|type|тип)[\.:\-\s]*(?:\*\*)?",  # Exercise Title:, Exercise Type:
            # Менее специфичные паттерны
            r"(?i)(?:^|\n)(?:task|задание)\s*(?:#?\d+|[ivx]+)[\.:\-\s]*",  # Task 1, Задание 1
            r"(?i)(?:^|\n)(?:activity|активность)\s*(?:#?\d+|[ivx]+)[\.:\-\s]*",  # Activity 1
        ]

        # Пробуем каждый паттерн
        for pattern in exercise_patterns:
            if re.search(pattern, content):
                parts = re.split(pattern, content)
                logger.info(f"Найдено {len(parts)-1 if parts else 0} упражнений с паттерном: {pattern}")

                # Удаляем пустую первую часть, если она есть
                if parts and not parts[0].strip():
                    parts = parts[1:]

                if len(parts) > 1:  # Если нашли разделения
                    for i, part in enumerate(parts, 1):
                        if not part.strip():
                            continue

                        exercise = ContentProcessor._parse_single_exercise(part.strip(), exercise_data, i, logger)
                        if exercise:
                            exercises.append(exercise)
                    break  # Используем первый успешный паттерн

        # Если не удалось разделить на упражнения, пробуем другие подходы
        if not exercises:
            exercises = ContentProcessor._parse_as_single_or_numbered_exercises(content, exercise_data, logger)

        return exercises

    @staticmethod
    def _parse_single_exercise(content: str, exercise_data: dict, exercise_num: int, logger) -> dict:
        """Парсит одно упражнение из контента"""

        # Получаем метаданные
        meta = exercise_data.get('meta', {})
        include_answers = meta.get('includeAnswers', True)
        include_instructions = meta.get('includeInstructions', True)

        # Расширенные паттерны для поиска ответов
        answer_patterns = [
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?(?:answer\s*key|answers?|ответы|решения?)(?:\*\*)?[\.:\-\s]*",
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?(?:complete\s*)?(?:answer\s*key|solutions?)(?:\*\*)?[\.:\-\s]*",
            r"(?i)(?:^|\n)\d+\.\s*(?:answer\s*key|answers?|ответы)[\.:\-\s]*",
            r"(?i)(?:^|\n)#{1,3}\s*(?:answer\s*key|answers?|ответы)",
        ]

        # Расширенные паттерны для поиска инструкций учителя
        instruction_patterns = [
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?(?:teacher\s*(?:instructions?|notes?)|teaching\s*tips|инструкции\s*учителю)(?:\*\*)?[\.:\-\s]*",
            r"(?i)(?:^|\n)(?:###\s*)?(?:\*\*)?(?:implementation\s*(?:guide|tips)|методические\s*рекомендации)(?:\*\*)?[\.:\-\s]*",
            r"(?i)(?:^|\n)\d+\.\s*(?:teacher\s*(?:instructions?|notes?)|инструкции)[\.:\-\s]*",
            r"(?i)(?:^|\n)#{1,3}\s*(?:teacher\s*(?:instructions?|notes?))",
        ]

        exercise_content = content
        answers = ""
        instructions = ""

        # Ищем ответы
        for pattern in answer_patterns:
            match = re.search(pattern, exercise_content)
            if match:
                split_pos = match.start()
                remaining_content = exercise_content[split_pos:]

                # Ищем конец секции ответов (начало следующей секции или конец)
                next_section_patterns = [
                    r"(?i)(?:\n|^)(?:###\s*)?(?:\*\*)?(?:teacher\s*(?:instructions?|notes?)|teaching\s*tips)",
                    r"(?i)(?:\n|^)(?:###\s*)?(?:\*\*)?(?:exercise|упражнение)",
                    r"(?i)(?:\n|^)#{1,3}\s*(?!answer|ответ)",  # Заголовок не про ответы
                ]

                end_pos = len(remaining_content)
                for end_pattern in next_section_patterns:
                    end_match = re.search(end_pattern, remaining_content[match.end()-split_pos:])
                    if end_match:
                        end_pos = match.end() - split_pos + end_match.start()
                        break

                answers = remaining_content[:end_pos].strip()
                exercise_content = exercise_content[:split_pos].strip()
                logger.info(f"Найдены ответы для упражнения {exercise_num}: {len(answers)} символов")
                break

        # Ищем инструкции учителя
        search_content = answers if answers else exercise_content
        for pattern in instruction_patterns:
            match = re.search(pattern, search_content)
            if match:
                if answers and match.string == answers:
                    # Инструкции в секции ответов
                    split_pos = match.start()
                    instructions = answers[split_pos:].strip()
                    answers = answers[:split_pos].strip()
                else:
                    # Инструкции в основном контенте
                    split_pos = match.start()
                    instructions = exercise_content[split_pos:].strip()
                    exercise_content = exercise_content[:split_pos].strip()

                logger.info(f"Найдены инструкции для упражнения {exercise_num}: {len(instructions)} символов")
                break

        # Определяем тип упражнения
        exercise_type = ContentProcessor._determine_exercise_type(exercise_content, exercise_data)

        return {
            "type": exercise_type,
            "content": exercise_content,
            "answers": answers if include_answers else "",
            "instructions": instructions if include_instructions else ""
        }

    @staticmethod
    def _parse_as_single_or_numbered_exercises(content: str, exercise_data: dict, logger) -> list:
        """Парсит контент как одно упражнение или пытается найти нумерованные упражнения"""

        # Получаем запрошенное количество упражнений
        requested_quantity = exercise_data.get('quantity', 3)

        # Пробуем различные паттерны для нумерованных упражнений
        numbered_patterns = [
            r"(?:^|\n)\s*(\d+)\.\s*",  # 1., 2., 3.
            r"(?:^|\n)\s*(\d+)\)\s*",  # 1), 2), 3)
            r"(?:^|\n)\s*\((\d+)\)\s*",  # (1), (2), (3)
            r"(?:^|\n)\s*(\d+)[\-\s]+",  # 1 -, 2 -, 3 -
        ]

        best_matches = []
        best_pattern = None

        # Ищем паттерн с наибольшим количеством совпадений
        for pattern in numbered_patterns:
            matches = list(re.finditer(pattern, content))
            if len(matches) > len(best_matches):
                best_matches = matches
                best_pattern = pattern

        # Если нашли достаточно нумерованных элементов
        if len(best_matches) >= 2:
            logger.info(f"Найдено {len(best_matches)} нумерованных элементов с паттерном: {best_pattern}")
            exercises = []

            # Ограничиваем количество упражнений запрошенным количеством
            matches_to_use = best_matches[:requested_quantity] if len(best_matches) > requested_quantity else best_matches

            for i, match in enumerate(matches_to_use):
                start_pos = match.start()
                # Определяем конец текущего упражнения
                if i + 1 < len(matches_to_use):
                    end_pos = matches_to_use[i + 1].start()
                else:
                    # Для последнего упражнения берем весь оставшийся текст
                    end_pos = len(content)

                part_content = content[start_pos:end_pos].strip()

                # Проверяем, что контент не слишком короткий
                if len(part_content) < 50:  # Минимум 50 символов для упражнения
                    logger.warning(f"Упражнение {i+1} слишком короткое ({len(part_content)} символов), пропускаем")
                    continue

                exercise = ContentProcessor._parse_single_exercise(part_content, exercise_data, i + 1, logger)
                if exercise:
                    exercises.append(exercise)

            # Если получили упражнения, возвращаем их
            if exercises:
                logger.info(f"Успешно разделено на {len(exercises)} нумерованных упражнений")
                return exercises

        # Пробуем разделить по длине, если контент очень большой
        if len(content) > 10000:  # Если контент больше 10KB
            logger.info("Контент очень большой, пробуем разделить по длине")
            return ContentProcessor._split_large_content_by_length(content, exercise_data, requested_quantity, logger)

        # Если не нашли нумерованные упражнения, возвращаем весь контент как одно упражнение
        logger.warning("Не удалось разделить на отдельные упражнения, возвращаем весь контент как одно")
        exercise = ContentProcessor._parse_single_exercise(content, exercise_data, 1, logger)
        return [exercise] if exercise else []

    @staticmethod
    def _split_large_content_by_length(content: str, exercise_data: dict, requested_quantity: int, logger) -> list:
        """Разделяет большой контент на части по длине"""

        # Вычисляем примерную длину каждой части
        content_length = len(content)
        part_length = content_length // requested_quantity

        exercises = []
        start_pos = 0

        for i in range(requested_quantity):
            if i == requested_quantity - 1:
                # Последняя часть - берем весь оставшийся контент
                part_content = content[start_pos:].strip()
            else:
                # Ищем хорошее место для разделения (конец предложения)
                target_end = start_pos + part_length

                # Ищем ближайший конец предложения в пределах ±200 символов
                search_start = max(target_end - 200, start_pos + 100)
                search_end = min(target_end + 200, content_length)
                search_area = content[search_start:search_end]

                # Ищем точки, восклицательные и вопросительные знаки
                sentence_ends = []
                for match in re.finditer(r'[.!?]\s+', search_area):
                    sentence_ends.append(search_start + match.end())

                if sentence_ends:
                    # Выбираем ближайший к целевой позиции конец предложения
                    best_end = min(sentence_ends, key=lambda x: abs(x - target_end))
                    part_content = content[start_pos:best_end].strip()
                    start_pos = best_end
                else:
                    # Если не нашли конец предложения, разделяем по целевой позиции
                    part_content = content[start_pos:target_end].strip()
                    start_pos = target_end

            if part_content and len(part_content) > 50:  # Минимум 50 символов
                exercise = ContentProcessor._parse_single_exercise(part_content, exercise_data, i + 1, logger)
                if exercise:
                    exercises.append(exercise)

        logger.info(f"Разделен большой контент на {len(exercises)} частей")
        return exercises

    @staticmethod
    def _determine_exercise_type(content: str, exercise_data: dict) -> str:
        """Определяет тип упражнения на основе контента"""

        # Сначала пробуем использовать переданный тип
        base_type = exercise_data.get('type', 'general')

        # Анализируем контент для более точного определения
        content_lower = content.lower()

        # Паттерны для определения типов упражнений
        type_patterns = {
            'grammar': ['grammar', 'грамматика', 'tense', 'verb', 'adjective', 'adverb', 'preposition', 'article'],
            'vocabulary': ['vocabulary', 'словарь', 'word', 'meaning', 'definition', 'synonym', 'antonym'],
            'reading': ['reading', 'чтение', 'text', 'passage', 'comprehension', 'article'],
            'writing': ['writing', 'письмо', 'write', 'essay', 'composition', 'paragraph'],
            'speaking': ['speaking', 'говорение', 'speak', 'conversation', 'dialogue', 'discussion'],
            'listening': ['listening', 'аудирование', 'listen', 'audio', 'sound', 'hear']
        }

        # Подсчитываем совпадения для каждого типа
        type_scores = {}
        for exercise_type, keywords in type_patterns.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                type_scores[exercise_type] = score

        # Возвращаем тип с наибольшим количеством совпадений
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            return best_type

        return base_type
