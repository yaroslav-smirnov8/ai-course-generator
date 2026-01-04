const teachingMethods = {
  // Универсальные методики
  universal: [
    {
      id: 'celta',
      name: 'CELTA',
      description: 'Cambridge Certificate in Teaching English to Speakers of Other Languages',
      features: [
        'Student-centered approach',
        'Communicative methodology',
        'Focus on authentic materials',
        'Integrated skills development'
      ]
    },
    {
      id: 'clil',
      name: 'CLIL',
      description: 'Content and Language Integrated Learning',
      features: [
        'Subject-matter focus',
        'Dual-focused educational approach',
        'Cross-curricular teaching',
        'Authentic materials'
      ]
    },
    {
      id: 'tbl',
      name: 'TBL',
      description: 'Task-Based Learning',
      features: [
        'Real-world tasks',
        'Problem-solving activities',
        'Authentic communication',
        'Goal-oriented learning'
      ]
    },
    {
      id: 'tblt',
      name: 'TBLT',
      description: 'Task-Based Language Teaching',
      features: [
        'Pre-task preparation',
        'Task cycle',
        'Language focus',
        'Performance analysis'
      ]
    },
    {
      id: 'cbi',
      name: 'CBI',
      description: 'Content-Based Instruction',
      features: [
        'Integration of content learning',
        'Language acquisition through content',
        'Authentic materials',
        'Academic skill development'
      ]
    },
    {
      id: 'tpr',
      name: 'TPR',
      description: 'Total Physical Response',
      features: [
        'Physical movement',
        'Command-based learning',
        'Stress-free environment',
        'Natural language acquisition'
      ]
    },
    {
      id: 'dm',
      name: 'Direct Method',
      description: 'Direct Language Teaching Method',
      features: [
        'Target language only',
        'Everyday vocabulary',
        'Grammar through demonstration',
        'Emphasis on oral skills'
      ]
    },
    {
      id: 'suggestopedia',
      name: 'Suggestopedia',
      description: 'Suggestive-Accelerative Learning',
      features: [
        'Comfortable environment',
        'Music and rhythm',
        'Positive suggestion',
        'Art and emotion'
      ]
    },
    {
      id: 'silentWay',
      name: 'Silent Way',
      description: 'Learning through Problem-Solving',
      features: [
        'Teacher silence',
        'Student discovery',
        'Cuisenaire rods',
        'Color-coding'
      ]
    },
    {
      id: 'ali',
      name: 'Audio-Lingual Method',
      description: 'Habit Formation through Drilling',
      features: [
        'Pattern drills',
        'Mimicry and memorization',
        'Structure emphasis',
        'Language laboratory use'
      ]
    },
  ],

  // Методики для английского языка
  english: [
    {
      id: 'esl',
      name: 'ESL Method',
      description: 'English as a Second Language',
      features: [
        'Immersive environment',
        'Natural communication',
        'Cultural integration',
        'Practical application'
      ]
    },
    {
      id: 'efl',
      name: 'EFL Method',
      description: 'English as a Foreign Language',
      features: [
        'Structured learning',
        'Grammar focus',
        'Controlled practice',
        'Regular assessment'
      ]
    },
    {
      id: 'esp',
      name: 'ESP',
      description: 'English for Specific Purposes',
      variants: [
        'Business English',
        'Medical English',
        'Legal English',
        'Technical English',
        'Aviation English',
        'Maritime English',
        'Academic English'
      ]
    },
    {
      id: 'eap',
      name: 'EAP',
      description: 'English for Academic Purposes',
      features: [
        'Academic writing',
        'Research skills',
        'Presentation skills',
        'Critical thinking'
      ]
    },
    {
      id: 'ieltsPrep',
      name: 'IELTS Preparation',
      features: [
        'Test strategies',
        'Academic skills',
        'Time management',
        'Score improvement'
      ]
    },
    {
      id: 'toeflPrep',
      name: 'TOEFL Preparation',
      features: [
        'Integrated skills',
        'Academic English',
        'Test-taking strategies',
        'University preparation'
      ]
    }
  ],

  // Методики для азиатских языков
  asian: [
    {
      id: 'hanyu',
      name: 'Hanyu Method',
      description: 'Chinese Character Learning',
      features: [
        'Character writing',
        'Radical analysis',
        'Stroke order',
        'Character etymology'
      ]
    },
    {
      id: 'pinyin',
      name: 'Pinyin Method',
      description: 'Chinese Phonetic System',
      features: [
        'Tone practice',
        'Pronunciation drills',
        'Sound recognition',
        'Romanization skills'
      ]
    },
    {
      id: 'kanji',
      name: 'Kanji Method',
      description: 'Japanese Character Learning',
      features: [
        'Radicals learning',
        'Stroke order',
        'Memory techniques',
        'Reading practice'
      ]
    },
    {
      id: 'jlpt',
      name: 'JLPT Preparation',
      description: 'Japanese Language Proficiency Test',
      features: [
        'Level-specific vocabulary',
        'Grammar patterns',
        'Reading comprehension',
        'Listening practice'
      ]
    }
  ],

  // Методики для европейских языков
  european: [
    {
      id: 'delf',
      name: 'DELF Method',
      description: 'Diplôme d études en langue française',
      features: [
        'French proficiency',
        'Cultural competence',
        'Communication skills',
        'Test preparation'
      ]
    },
    {
      id: 'dalf',
      name: 'DALF Method',
      description: 'Diplôme approfondi de langue française',
      features: [
        'Advanced French',
        'Academic skills',
        'Cultural knowledge',
        'Professional French'
      ]
    },
    {
      id: 'dele',
      name: 'DELE Method',
      description: 'Diplomas of Spanish as a Foreign Language',
      features: [
        'Spanish proficiency',
        'Cultural awareness',
        'Communication practice',
        'Test strategies'
      ]
    },
    {
      id: 'goethe',
      name: 'Goethe Method',
      description: 'German Language Certification',
      features: [
        'German proficiency',
        'Cultural studies',
        'Communication skills',
        'Exam preparation'
      ]
    }
  ],

  // Методики для арабского языка
  arabic: [
    {
      id: 'quranic',
      name: 'Quranic Arabic Method',
      description: 'Classical Arabic Teaching',
      features: [
        'Classical texts',
        'Grammar focus',
        'Recitation practice',
        'Vocabulary building'
      ]
    },
    {
      id: 'msa',
      name: 'Modern Standard Arabic',
      description: 'Contemporary Arabic Teaching',
      features: [
        'Modern usage',
        'Media Arabic',
        'Business Arabic',
        'Cultural context'
      ]
    }
  ],

  // Современные инновационные подходы
  innovative: [
    {
      id: 'flipped',
      name: 'Flipped Classroom',
      description: 'Reversed Traditional Teaching',
      features: [
        'Pre-class materials',
        'In-class practice',
        'Digital resources',
        'Interactive learning'
      ]
    },
    {
      id: 'blended',
      name: 'Blended Learning',
      description: 'Combined Online and Offline Learning',
      features: [
        'Digital tools',
        'Face-to-face interaction',
        'Self-paced learning',
        'Mixed resources'
      ]
    },
    {
      id: 'gamification',
      name: 'Gamified Learning',
      description: 'Game-Based Language Acquisition',
      features: [
        'Game mechanics',
        'Rewards system',
        'Competition elements',
        'Progress tracking'
      ]
    },
    {
      id: 'projectBased',
      name: 'Project-Based Learning',
      description: 'Learning through Projects',
      features: [
        'Real-world tasks',
        'Collaborative work',
        'Research skills',
        'Presentation skills'
      ]
    },
    {
      id: 'microLearning',
      name: 'Micro-Learning',
      description: 'Bite-Sized Learning Units',
      features: [
        'Short lessons',
        'Mobile learning',
        'Regular practice',
        'Quick feedback'
      ]
    }
  ],

  // Фреймворки для структурирования уроков
  frameworks: [
    {
      id: 'ppp',
      name: 'PPP',
      description: 'Presentation, Practice, Production',
      stages: [
        'Present new language',
        'Controlled practice',
        'Free production'
      ]
    },
    {
      id: 'esr',
      name: 'ESR',
      description: 'Engage, Study, Reflect',
      stages: [
        'Engagement phase',
        'Study phase',
        'Reflection phase'
      ]
    },
    {
      id: 'easa',
      name: 'EASA',
      description: 'Engage, Activate, Study, Activate',
      stages: [
        'Initial engagement',
        'First activation',
        'Study phase',
        'Final activation'
      ]
    },
    {
      id: 'arc',
      name: 'ARC',
      description: 'Authentic use, Restricted use, Clarification and focus',
      stages: [
        'Authentic material use',
        'Restricted practice',
        'Clarification of rules'
      ]
    },
    {
      id: 'test',
      name: 'Test-Teach-Test',
      description: 'Assessment-Driven Approach',
      stages: [
        'Initial assessment',
        'Targeted teaching',
        'Progress assessment'
      ]
    }
  ]
}

// Специфические элементы методик
const methodComponents = {
  // Типы заданий
  taskTypes: [
    'Information gap',
    'Opinion sharing',
    'Problem-solving',
    'Role-play',
    'Simulation',
    'Case study',
    'Project work',
    'Presentation',
    'Debate',
    'Discussion'
  ],

  // Типы оценивания
  assessmentTypes: [
    'Formative',
    'Summative',
    'Diagnostic',
    'Peer assessment',
    'Self-assessment',
    'Portfolio assessment',
    'Performance assessment',
    'Project assessment'
  ],

  // Типы материалов
  materialTypes: [
    'Authentic texts',
    'Graded readers',
    'Audio materials',
    'Video materials',
    'Realia',
    'Digital resources',
    'Interactive exercises',
    'Games',
    'Worksheets',
    'Flash cards'
  ],

  // Типы взаимодействия
  interactionPatterns: [
    'Individual work',
    'Pair work',
    'Small groups',
    'Whole class',
    'Online collaboration',
    'Teacher-student',
    'Student-student',
    'Mixed ability groups'
  ]
}

// Методики обучения языкам
const teachingMethodologies = [
  // Добавляем методики из teachingMethods.universal
  {
    id: 'celta',
    name: 'CELTA',
    description: 'Cambridge Certificate in Teaching English to Speakers of Other Languages',
    languages: ['all'],
    features: [
      'Student-centered approach',
      'Communicative methodology',
      'Focus on authentic materials',
      'Integrated skills development'
    ]
  },
  {
    id: 'clil',
    name: 'CLIL',
    description: 'Content and Language Integrated Learning',
    languages: ['all'],
    features: [
      'Subject-matter focus',
      'Dual-focused educational approach',
      'Cross-curricular teaching',
      'Authentic materials'
    ]
  },
  {
    id: 'tbl',
    name: 'TBL',
    description: 'Task-Based Learning',
    languages: ['all'],
    features: [
      'Real-world tasks',
      'Problem-solving activities',
      'Authentic communication',
      'Goal-oriented learning'
    ]
  },
  {
    id: 'tblt',
    name: 'TBLT',
    description: 'Task-Based Language Teaching',
    languages: ['all'],
    features: [
      'Pre-task preparation',
      'Task cycle',
      'Language focus',
      'Performance analysis'
    ]
  },
  {
    id: 'cbi',
    name: 'CBI',
    description: 'Content-Based Instruction',
    languages: ['all'],
    features: [
      'Integration of content learning',
      'Language acquisition through content',
      'Authentic materials',
      'Academic skill development'
    ]
  },
  {
    id: 'tpr',
    name: 'TPR',
    description: 'Total Physical Response',
    languages: ['all'],
    features: [
      'Physical movement',
      'Command-based learning',
      'Stress-free environment',
      'Natural language acquisition'
    ]
  },
  {
    id: 'dm',
    name: 'Direct Method',
    description: 'Direct Language Teaching Method',
    languages: ['all'],
    features: [
      'Target language only',
      'Everyday vocabulary',
      'Grammar through demonstration',
      'Emphasis on oral skills'
    ]
  },
  {
    id: 'suggestopedia',
    name: 'Suggestopedia',
    description: 'Suggestive-Accelerative Learning',
    languages: ['all'],
    features: [
      'Comfortable environment',
      'Music and rhythm',
      'Positive suggestion',
      'Art and emotion'
    ]
  },
  {
    id: 'silentWay',
    name: 'Silent Way',
    description: 'Learning through Problem-Solving',
    languages: ['all'],
    features: [
      'Teacher silence',
      'Student discovery',
      'Cuisenaire rods',
      'Color-coding'
    ]
  },
  {
    id: 'ali',
    name: 'Audio-Lingual Method',
    description: 'Habit Formation through Drilling',
    languages: ['all'],
    features: [
      'Pattern drills',
      'Mimicry and memorization',
      'Structure emphasis',
      'Language laboratory use'
    ]
  },
  // Существующие методики
  {
    id: 'communicative',
    name: 'Communicative Approach',
    description: 'Фокусируется на развитии коммуникативных навыков через реальное общение',
    languages: ['all'],
    features: [
      'Акцент на разговорной практике',
      'Использование аутентичных материалов',
      'Минимальное использование родного языка',
      'Ситуативное обучение'
    ]
  },
  {
    id: 'grammar-translation',
    name: 'Grammar-Translation Method',
    description: 'Традиционный подход с фокусом на грамматику и перевод',
    languages: ['all'],
    features: [
      'Детальное изучение грамматики',
      'Перевод текстов',
      'Заучивание правил',
      'Работа с литературными текстами'
    ]
  },
  {
    id: 'direct',
    name: 'Direct Method',
    description: 'Обучение без использования родного языка учащихся',
    languages: ['all'],
    features: [
      'Только целевой язык',
      'Индуктивное изучение грамматики',
      'Акцент на устной речи',
      'Демонстрация вместо перевода'
    ]
  },
  {
    id: 'audio-lingual',
    name: 'Audio-Lingual Method',
    description: 'Основан на многократном повторении и формировании языковых привычек',
    languages: ['all'],
    features: [
      'Повторение и запоминание',
      'Диалоги и шаблоны',
      'Минимальное объяснение грамматики',
      'Лабораторные работы'
    ]
  },
  {
    id: 'natural',
    name: 'Natural Approach',
    description: 'Имитирует естественный процесс освоения языка',
    languages: ['all'],
    features: [
      'Понимание перед говорением',
      'Низкий уровень стресса',
      'Фокус на значении, а не форме',
      'Постепенное развитие навыков'
    ]
  },
  {
    id: 'task-based',
    name: 'Task-Based Learning',
    description: 'Обучение через выполнение практических задач',
    languages: ['all'],
    features: [
      'Реальные задачи',
      'Проблемно-ориентированное обучение',
      'Коллаборативная работа',
      'Фокус на результате'
    ]
  },
  {
    id: 'lexical',
    name: 'Lexical Approach',
    description: 'Фокусируется на изучении лексических блоков и коллокаций',
    languages: ['all'],
    features: [
      'Лексические блоки',
      'Коллокации и фразы',
      'Контекстное изучение',
      'Аутентичные тексты'
    ]
  },
  {
    id: 'immersion',
    name: 'Immersion Method',
    description: 'Полное погружение в языковую среду',
    languages: ['all'],
    features: [
      'Только целевой язык',
      'Культурный контекст',
      'Интенсивная практика',
      'Реальные ситуации общения'
    ]
  },
  {
    id: 'suggestopedia',
    name: 'Suggestopedia',
    description: 'Использует внушение и расслабление для ускорения обучения',
    languages: ['all'],
    features: [
      'Комфортная обстановка',
      'Музыка и ритм',
      'Ролевые игры',
      'Позитивное внушение'
    ]
  },
  {
    id: 'silent-way',
    name: 'Silent Way',
    description: 'Преподаватель говорит минимально, поощряя самостоятельность учащихся',
    languages: ['all'],
    features: [
      'Минимальное участие учителя',
      'Самостоятельное открытие',
      'Визуальные подсказки',
      'Проблемно-ориентированное обучение'
    ]
  }
];

// Определяем интерфейс Method для типизации
export interface Method {
  id: string;
  name: string;
  description: string;
  features: string[];
  variants?: string[];
}

// Методики для конкретных языков
const languageSpecificMethodologies: Record<string, Method[]> = {
  english: [
    {
      id: 'callan',
      name: 'Callan Method',
      description: 'Интенсивный метод обучения английскому языку',
      features: [
        'Высокая скорость обучения',
        'Постоянное повторение',
        'Строгая структура уроков',
        'Быстрые вопросы и ответы'
      ]
    },
    {
      id: 'ielts-focused',
      name: 'IELTS-focused Approach',
      description: 'Подготовка к экзамену IELTS',
      features: [
        'Стратегии сдачи теста',
        'Практика всех компонентов',
        'Типовые задания',
        'Временные ограничения'
      ]
    }
  ],
  chinese: [
    {
      id: 'character-based',
      name: 'Character-Based Method',
      description: 'Фокус на изучении китайских иероглифов',
      features: [
        'Порядок черт',
        'Радикалы',
        'Этимология иероглифов',
        'Каллиграфия'
      ]
    },
    {
      id: 'pinyin-first',
      name: 'Pinyin-First Method',
      description: 'Начало с фонетической системы пиньинь',
      features: [
        'Тоны',
        'Произношение',
        'Фонетические упражнения',
        'Постепенный переход к иероглифам'
      ]
    }
  ],
  japanese: [
    {
      id: 'direct-method-japanese',
      name: 'Direct Method',
      description: 'Метод обучения японскому языку, при котором преподавание ведется только на изучаемом языке с использованием визуальных материалов и ассоциаций.',
      features: ['Полное погружение в языковую среду', 'Отсутствие перевода', 'Акцент на разговорную речь', 'Использование визуальных материалов']
    },
    {
      id: 'minna-no-nihongo',
      name: 'Minna no Nihongo',
      description: 'Популярная методика обучения японскому языку, основанная на структурированном подходе к грамматике и лексике с постепенным усложнением материала.',
      features: ['Структурированная подача грамматики', 'Тематические словарные блоки', 'Интегрированные упражнения', 'Культурологический компонент']
    },
    {
      id: 'kanji-kentei',
      name: 'Kanji Kentei',
      description: 'Методика, фокусирующаяся на изучении японских иероглифов (кандзи) с использованием системы уровней сложности и мнемонических техник.',
      features: ['Систематическое изучение иероглифов', 'Мнемонические техники', 'Градация по уровням сложности', 'Регулярное повторение']
    },
    {
      id: 'shadowing-japanese',
      name: 'Shadowing',
      description: 'Техника обучения японскому языку, при которой учащийся повторяет за диктором в режиме реального времени, имитируя произношение и интонацию.',
      features: ['Улучшение произношения', 'Развитие беглости речи', 'Тренировка слухового восприятия', 'Имитация носителей языка']
    }
  ],
  korean: [
    {
      id: 'topik-oriented',
      name: 'TOPIK-oriented Approach',
      description: 'Методика, направленная на подготовку к экзамену на знание корейского языка (TOPIK) с акцентом на развитие всех языковых навыков.',
      features: ['Структурированная программа', 'Тестовые задания', 'Комплексное развитие навыков', 'Практика экзаменационных заданий']
    },
    {
      id: 'k-pop-culture',
      name: 'K-Pop Culture Method',
      description: 'Инновационный подход к изучению корейского языка через популярную культуру, включая K-Pop музыку, дорамы и развлекательные шоу.',
      features: ['Использование аутентичных материалов', 'Высокая мотивация учащихся', 'Погружение в современную культуру', 'Изучение разговорного языка']
    },
    {
      id: 'hangul-first',
      name: 'Hangul-First Method',
      description: 'Методика, начинающаяся с освоения корейского алфавита (хангыль) и фонетики перед переходом к грамматике и лексике.',
      features: ['Быстрое освоение письменности', 'Фокус на правильное произношение', 'Постепенное наращивание сложности', 'Систематический подход']
    }
  ],
  turkish: [
    {
      id: 'communicative-turkish',
      name: 'Communicative Approach',
      description: 'Подход к изучению турецкого языка, основанный на развитии коммуникативных навыков через диалоги и ситуативные упражнения.',
      features: ['Акцент на разговорную речь', 'Ситуативные диалоги', 'Минимум теории', 'Максимум практики']
    },
    {
      id: 'structural-approach',
      name: 'Structural Approach',
      description: 'Методика изучения турецкого языка, основанная на последовательном освоении грамматических структур от простых к сложным.',
      features: ['Систематическое изучение грамматики', 'Постепенное усложнение материала', 'Практические упражнения', 'Контроль усвоения']
    },
    {
      id: 'yunus-emre-method',
      name: 'Yunus Emre Method',
      description: 'Официальная методика обучения турецкому языку, разработанная Институтом Юнуса Эмре, сочетающая коммуникативный подход с культурологическим компонентом.',
      features: ['Интеграция культурных элементов', 'Аутентичные материалы', 'Баланс всех языковых навыков', 'Современный подход']
    }
  ],
  arabic: [
    {
      id: 'msa-focus',
      name: 'Modern Standard Arabic Focus',
      description: 'Фокус на литературном арабском языке',
      features: [
        'Формальный арабский',
        'Грамматические правила',
        'Классические тексты',
        'Письменная практика'
      ]
    },
    {
      id: 'dialect-based',
      name: 'Dialect-Based Approach',
      description: 'Изучение конкретного арабского диалекта',
      features: [
        'Разговорный арабский',
        'Региональные особенности',
        'Практическая лексика',
        'Аутентичные материалы'
      ]
    }
  ]
};

export { teachingMethods, methodComponents, teachingMethodologies, languageSpecificMethodologies }
