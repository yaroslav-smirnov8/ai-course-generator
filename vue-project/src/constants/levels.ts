// Common CEFR (Common European Framework of Reference for Languages) levels
export const cefrLevels = [
  { id: 'a1', name: 'A1 (Beginner)', description: 'Can understand and use familiar everyday expressions and very basic phrases' },
  { id: 'a2', name: 'A2 (Elementary)', description: 'Can communicate in simple and routine tasks requiring a simple and direct exchange of information' },
  { id: 'b1', name: 'B1 (Intermediate)', description: 'Can cope with most situations that arise while traveling in an area where the language is spoken' },
  { id: 'b2', name: 'B2 (Upper-Intermediate)', description: 'Can communicate with a certain degree of fluency and spontaneity, making regular interaction with native speakers possible' },
  { id: 'c1', name: 'C1 (Advanced)', description: 'Can express ideas fluently and spontaneously without much difficulty in finding the right expressions' },
  { id: 'c2', name: 'C2 (Proficient)', description: 'Can easily understand virtually everything heard or read' }
];

// Levels for Chinese language (HSK - Hanyu Shuiping Kaoshi)
export const chineseLevels = [
  { id: 'hsk1', name: 'HSK 1', description: 'Can understand and use very simple Chinese phrases' },
  { id: 'hsk2', name: 'HSK 2', description: 'Can communicate in simple and routine tasks' },
  { id: 'hsk3', name: 'HSK 3', description: 'Can communicate in Chinese on familiar topics' },
  { id: 'hsk4', name: 'HSK 4', description: 'Can speak freely on a wide range of topics' },
  { id: 'hsk5', name: 'HSK 5', description: 'Can read Chinese newspapers and magazines' },
  { id: 'hsk6', name: 'HSK 6', description: 'Can easily understand written and spoken Chinese' },
  { id: 'hsk7-9', name: 'HSK 7-9', description: 'Advanced professional proficiency' }
];

// Levels for Japanese language (JLPT - Japanese Language Proficiency Test)
export const japaneseLevels = [
  { id: 'n5', name: 'JLPT N5', description: 'Can understand some basic expressions of the Japanese language' },
  { id: 'n4', name: 'JLPT N4', description: 'Can understand basic Japanese used in everyday situations' },
  { id: 'n3', name: 'JLPT N3', description: 'Can understand Japanese used in everyday situations to a certain degree' },
  { id: 'n2', name: 'JLPT N2', description: 'Can understand Japanese used in everyday situations and in various circumstances' },
  { id: 'n1', name: 'JLPT N1', description: 'Can understand Japanese used in various circumstances' }
];

// Levels for Korean language (TOPIK - Test of Proficiency in Korean)
export const koreanLevels = [
  { id: 'topik1', name: 'TOPIK I (1)', description: 'Can understand and use familiar everyday expressions in Korean' },
  { id: 'topik2', name: 'TOPIK I (2)', description: 'Can communicate in simple and routine tasks in Korean' },
  { id: 'topik3', name: 'TOPIK II (3)', description: 'Can communicate in Korean in everyday situations' },
  { id: 'topik4', name: 'TOPIK II (4)', description: 'Can express thoughts on various topics in Korean' },
  { id: 'topik5', name: 'TOPIK II (5)', description: 'Can communicate freely in Korean in professional situations' },
  { id: 'topik6', name: 'TOPIK II (6)', description: 'Can understand and use Korean at a level close to a native speaker' }
];

// Levels for Turkish language
export const turkishLevels = [
  { id: 'a1', name: 'A1 (Beginner)', description: 'Can understand and use familiar everyday expressions in Turkish' },
  { id: 'a2', name: 'A2 (Elementary)', description: 'Can communicate in simple and routine tasks in Turkish' },
  { id: 'b1', name: 'B1 (Intermediate)', description: 'Can cope with most situations in Turkish while traveling' },
  { id: 'b2', name: 'B2 (Upper-Intermediate)', description: 'Can communicate in Turkish with a certain degree of fluency' },
  { id: 'c1', name: 'C1 (Advanced)', description: 'Can express ideas fluently and spontaneously in Turkish' },
  { id: 'c2', name: 'C2 (Proficient)', description: 'Can easily understand practically everything in Turkish' }
];

// Levels for Arabic language
export const arabicLevels = [
  { id: 'beginner', name: 'Beginner', description: 'Can understand and use familiar everyday expressions' },
  { id: 'elementary', name: 'Elementary', description: 'Can communicate in simple and routine tasks' },
  { id: 'intermediate', name: 'Intermediate', description: 'Can interact with native speakers on familiar topics' },
  { id: 'advanced', name: 'Advanced', description: 'Can fluently express ideas on a wide range of topics' },
  { id: 'superior', name: 'Superior', description: 'Can communicate with accuracy and fluency' },
  { id: 'native', name: 'Native-like', description: 'Can function as an educated native speaker' }
];

// Levels for Russian language (TORFL - Test of Russian as a Foreign Language)
export const russianLevels = [
  { id: 'tea', name: 'TORFL A (Elementary)', description: 'Basic communication in Russian' },
  { id: 'tba', name: 'TORFL B (Basic)', description: 'Everyday communication in Russian' },
  { id: 't1', name: 'TORFL-I', description: 'Communication in Russian in all social contexts' },
  { id: 't2', name: 'TORFL-II', description: 'Advanced communication in Russian in professional contexts' },
  { id: 't3', name: 'TORFL-III', description: 'Proficiency in Russian close to a native speaker' },
  { id: 't4', name: 'TORFL-IV', description: 'Proficiency in Russian at a native speaker level' }
];

// Функция для получения уровней в зависимости от языка
export const getLevelsByLanguage = (language: string) => {
  switch (language) {
    case 'chinese':
      return chineseLevels;
    case 'japanese':
      return japaneseLevels;
    case 'korean':
      return koreanLevels;
    case 'turkish':
      return turkishLevels;
    case 'arabic':
      return arabicLevels;
    case 'russian':
      return russianLevels;
    default:
      return cefrLevels; // По умолчанию используем CEFR для большинства европейских языков
  }
}; 