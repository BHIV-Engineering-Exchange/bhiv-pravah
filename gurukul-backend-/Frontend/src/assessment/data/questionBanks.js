// Comprehensive question banks for field-based assessment system

import { ASSIGNMENT_CATEGORIES, DIFFICULTY_LEVELS } from './assignment.js';

// Question bank structure - organized by category and difficulty
export const QUESTION_BANKS = {
  // CODING QUESTIONS
  [ASSIGNMENT_CATEGORIES.CODING]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'code_easy_1',
        question_text: 'What is the output of the following Python code?\n\nprint("Hello" + " " + "World")',
        options: ['A) Hello World', 'B) HelloWorld', 'C) Hello + World', 'D) Error'],
        correct_answer: 'A) Hello World',
        explanation: 'String concatenation with + operator joins the strings together.',
        vedic_connection: '',
        modern_application: 'String manipulation is fundamental in all programming languages and web development.'
      },
      {
        id: 'code_easy_2',
        question_text: 'Which of the following is the correct syntax to declare a variable in JavaScript?',
        options: ['A) var myVariable;', 'B) variable myVariable;', 'C) declare myVariable;', 'D) int myVariable;'],
        correct_answer: 'A) var myVariable;',
        explanation: 'JavaScript uses var, let, or const keywords to declare variables.',
        vedic_connection: '',
        modern_application: 'Variable declaration is essential for storing and manipulating data in web applications.'
      },
      {
        id: 'code_easy_3',
        question_text: 'What does HTML stand for?',
        options: ['A) Hyper Text Markup Language', 'B) High Tech Modern Language', 'C) Home Tool Markup Language', 'D) Hyperlink and Text Markup Language'],
        correct_answer: 'A) Hyper Text Markup Language',
        explanation: 'HTML is the standard markup language for creating web pages.',
        vedic_connection: '',
        modern_application: 'HTML forms the backbone of all web content and is essential for web development.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'code_medium_1',
        question_text: 'What is the time complexity of searching for an element in a balanced binary search tree?',
        options: ['A) O(log n)', 'B) O(n)', 'C) O(n²)', 'D) O(1)'],
        correct_answer: 'A) O(log n)',
        explanation: 'In a balanced BST, the height is log n, so search operations take O(log n) time.',
        vedic_connection: '',
        modern_application: 'Binary search trees are used in databases, file systems, and search algorithms.'
      },
      {
        id: 'code_medium_2',
        question_text: 'In object-oriented programming, what is inheritance?',
        options: ['A) The ability of a class to inherit properties and methods from another class', 'B) The process of hiding implementation details', 'C) The ability to use the same interface for different types', 'D) The bundling of data and methods together'],
        correct_answer: 'A) The ability of a class to inherit properties and methods from another class',
        explanation: 'Inheritance allows a class to inherit characteristics from a parent class, promoting code reuse.',
        vedic_connection: '',
        modern_application: 'Inheritance is fundamental in modern software architecture, enabling code reusability.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'code_hard_1',
        question_text: 'In a microservices architecture, what is the main challenge with distributed transactions?',
        options: ['A) Ensuring ACID properties across multiple services', 'B) Network latency', 'C) Service discovery', 'D) Load balancing'],
        correct_answer: 'A) Ensuring ACID properties across multiple services',
        explanation: 'Distributed transactions are complex because maintaining ACID properties across multiple services is challenging.',
        vedic_connection: '',
        modern_application: 'This is crucial for designing robust distributed systems in cloud computing.'
      }
    ]
  },

  // LOGIC QUESTIONS
  [ASSIGNMENT_CATEGORIES.LOGIC]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'logic_easy_1',
        question_text: 'If all cats are animals, and Fluffy is a cat, what can we conclude?',
        options: ['A) Fluffy is an animal', 'B) All animals are cats', 'C) Fluffy is not an animal', 'D) We cannot conclude anything'],
        correct_answer: 'A) Fluffy is an animal',
        explanation: 'This is a basic syllogism. If all cats are animals and Fluffy is a cat, then Fluffy must be an animal.',
        vedic_connection: 'The Vedic tradition emphasizes logical reasoning through the Nyaya school of philosophy.',
        modern_application: 'Logical reasoning is fundamental in computer programming, legal arguments, and scientific research.'
      },
      {
        id: 'logic_easy_2',
        question_text: 'What comes next in the sequence: 2, 4, 6, 8, ?',
        options: ['A) 10', 'B) 12', 'C) 9', 'D) 14'],
        correct_answer: 'A) 10',
        explanation: 'This is a sequence of even numbers increasing by 2 each time.',
        vedic_connection: 'Pattern recognition was central to Vedic mathematics and astronomy.',
        modern_application: 'Pattern recognition is crucial in data analysis, machine learning, and problem-solving.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'logic_medium_1',
        question_text: 'In a logic puzzle, if "Some doctors are teachers" and "All teachers are patient," what can we definitely conclude?',
        options: ['A) Some doctors are patient', 'B) All doctors are patient', 'C) No doctors are patient', 'D) All patient people are doctors'],
        correct_answer: 'A) Some doctors are patient',
        explanation: 'Since some doctors are teachers, and all teachers are patient, those doctors who are teachers must be patient.',
        vedic_connection: 'Logical deduction was systematized in ancient Indian logic (Nyaya).',
        modern_application: 'Logical reasoning is essential in database queries, legal reasoning, and system design.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'logic_hard_1',
        question_text: 'In a country where every person either always tells the truth or always lies, you meet three people. A says "B is a liar." B says "C is a liar." C says "A and B are both liars." Who is telling the truth?',
        options: ['A) Only C', 'B) Only A', 'C) Only B', 'D) A and B'],
        correct_answer: 'A) Only C',
        explanation: 'If A were telling the truth, then B is a liar. If B is a liar, then C is truthful. If C is truthful, then A and B are both liars, which contradicts A being truthful. So A must be a liar. Following this logic, only C is telling the truth.',
        vedic_connection: 'Complex logical paradoxes were explored in ancient Indian philosophical debates.',
        modern_application: 'Such logical puzzles help develop analytical thinking crucial for programming and system design.'
      }
    ]
  },

  // MATHEMATICS QUESTIONS
  [ASSIGNMENT_CATEGORIES.MATHEMATICS]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'math_easy_1',
        question_text: 'What is 15% of 200?',
        options: ['A) 30', 'B) 25', 'C) 35', 'D) 40'],
        correct_answer: 'A) 30',
        explanation: '15% of 200 = (15/100) × 200 = 0.15 × 200 = 30',
        vedic_connection: 'Percentage calculations were efficiently handled in Vedic mathematics using mental calculation techniques.',
        modern_application: 'Percentage calculations are essential in finance, statistics, and data analysis.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'math_medium_1',
        question_text: 'Solve for x: 2x + 5 = 17',
        options: ['A) x = 6', 'B) x = 5', 'C) x = 7', 'D) x = 8'],
        correct_answer: 'A) x = 6',
        explanation: '2x + 5 = 17, so 2x = 17 - 5 = 12, therefore x = 12/2 = 6',
        vedic_connection: 'Algebraic problem-solving techniques were developed in ancient Indian mathematics.',
        modern_application: 'Linear equations are fundamental in engineering, economics, and optimization problems.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'math_hard_1',
        question_text: 'What is the derivative of f(x) = x³ + 2x² - 5x + 3?',
        options: ['A) f\'(x) = 3x² + 4x - 5', 'B) f\'(x) = 3x² + 2x - 5', 'C) f\'(x) = x² + 4x - 5', 'D) f\'(x) = 3x² + 4x - 3'],
        correct_answer: 'A) f\'(x) = 3x² + 4x - 5',
        explanation: 'Using the power rule: d/dx(x³) = 3x², d/dx(2x²) = 4x, d/dx(-5x) = -5, d/dx(3) = 0',
        vedic_connection: 'Calculus concepts have roots in the infinite series work of medieval Indian mathematicians.',
        modern_application: 'Calculus is essential in physics, engineering, machine learning, and optimization.'
      }
    ]
  },

  // Continue with other categories...
  [ASSIGNMENT_CATEGORIES.LANGUAGE]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'lang_easy_1',
        question_text: 'Which of the following is a synonym for "happy"?',
        options: ['A) Joyful', 'B) Sad', 'C) Angry', 'D) Confused'],
        correct_answer: 'A) Joyful',
        explanation: 'Joyful means feeling happiness and is therefore a synonym of happy.',
        vedic_connection: 'Sanskrit has rich vocabulary for emotional states, with words like "ananda" meaning bliss.',
        modern_application: 'Vocabulary skills are essential for effective communication in all professional fields.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'lang_medium_1',
        question_text: 'What is the main theme of this passage: "Despite facing numerous challenges, the young entrepreneur continued to pursue her dreams with unwavering determination."',
        options: ['A) Perseverance and determination', 'B) Business challenges', 'C) Youth and age', 'D) Dreams and reality'],
        correct_answer: 'A) Perseverance and determination',
        explanation: 'The passage emphasizes continuing to pursue goals despite challenges, which demonstrates perseverance.',
        vedic_connection: 'The concept of dharma in Vedic literature emphasizes persistent pursuit of righteous goals.',
        modern_application: 'Reading comprehension is vital for academic success and professional document analysis.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'lang_hard_1',
        question_text: 'In the sentence "The CEO, who founded the company in 1985, announced her retirement," the clause "who founded the company in 1985" is:',
        options: ['A) A non-restrictive relative clause', 'B) A restrictive relative clause', 'C) An adverbial clause', 'D) A noun clause'],
        correct_answer: 'A) A non-restrictive relative clause',
        explanation: 'The clause is set off by commas and provides additional information about the CEO but is not essential to identify which CEO.',
        vedic_connection: '',
        modern_application: 'Understanding sentence structure is important for clear technical writing and legal documentation.'
      }
    ]
  },

  // Additional categories with sample questions
  [ASSIGNMENT_CATEGORIES.CULTURE]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'culture_easy_1',
        question_text: 'Which festival is known as the "Festival of Lights" in Indian culture?',
        options: ['A) Diwali', 'B) Holi', 'C) Dussehra', 'D) Eid'],
        correct_answer: 'A) Diwali',
        explanation: 'Diwali is celebrated with oil lamps and lights, symbolizing the victory of light over darkness.',
        vedic_connection: 'Diwali has roots in ancient Vedic traditions and celebrates the return of Lord Rama to Ayodhya.',
        modern_application: 'Understanding cultural festivals promotes diversity and inclusion in global workplaces.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'culture_medium_1',
        question_text: 'Which ancient civilization is credited with the invention of democracy?',
        options: ['A) Ancient Greece', 'B) Ancient Rome', 'C) Ancient Egypt', 'D) Ancient India'],
        correct_answer: 'A) Ancient Greece',
        explanation: 'Ancient Athens is credited with developing the first known democratic system around 508 BCE.',
        vedic_connection: 'Ancient Indian texts like the Arthashastra also discussed various forms of governance.',
        modern_application: 'Understanding the origins of democracy helps appreciate modern democratic institutions.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'culture_hard_1',
        question_text: 'The concept of "Ubuntu" from African philosophy means:',
        options: ['A) "I am because we are" - interconnectedness of humanity', 'B) Individual achievement and success', 'C) Separation of communities', 'D) Economic prosperity'],
        correct_answer: 'A) "I am because we are" - interconnectedness of humanity',
        explanation: 'Ubuntu emphasizes the interconnectedness of all people and the importance of community.',
        vedic_connection: 'Similar to the Vedic concept of "Vasudhaiva Kutumbakam" - the world is one family.',
        modern_application: 'Ubuntu philosophy influences modern approaches to leadership, conflict resolution, and social justice.'
      }
    ]
  },

  [ASSIGNMENT_CATEGORIES.VEDIC_KNOWLEDGE]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'vedic_easy_1',
        question_text: 'What is the meaning of "Yoga" in Sanskrit?',
        options: ['A) Union or connection', 'B) Exercise', 'C) Meditation', 'D) Breathing'],
        correct_answer: 'A) Union or connection',
        explanation: 'Yoga comes from the Sanskrit root "yuj" meaning to unite or connect, referring to the union of individual consciousness with universal consciousness.',
        vedic_connection: 'Yoga is one of the six orthodox schools of Hindu philosophy mentioned in ancient Vedic texts.',
        modern_application: 'Yoga is now practiced worldwide for physical health, mental well-being, and stress management.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'vedic_medium_1',
        question_text: 'What is the significance of the number 108 in Vedic tradition?',
        options: ['A) It represents cosmic harmony and completeness', 'B) It is just a random sacred number', 'C) It represents the number of gods', 'D) It is the number of Vedic verses'],
        correct_answer: 'A) It represents cosmic harmony and completeness',
        explanation: '108 has multiple significance: distance from Earth to Sun is about 108 times the Sun\'s diameter, and there are 108 Upanishads.',
        vedic_connection: '108 is considered sacred in many Vedic practices including the number of beads in a mala.',
        modern_application: 'Understanding such symbolism helps in appreciating cultural practices and meditation techniques.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'vedic_hard_1',
        question_text: 'In Vedic philosophy, what is the relationship between Atman and Brahman?',
        options: ['A) Atman (individual soul) is identical to Brahman (universal consciousness)', 'B) They are completely separate entities', 'C) Atman is superior to Brahman', 'D) Brahman is a part of Atman'],
        correct_answer: 'A) Atman (individual soul) is identical to Brahman (universal consciousness)',
        explanation: 'The Upanishads teach "Tat tvam asi" (Thou art That), indicating the fundamental unity of individual consciousness with universal consciousness.',
        vedic_connection: 'This is the core teaching of Advaita Vedanta philosophy.',
        modern_application: 'This philosophical understanding influences modern approaches to consciousness studies and psychology.'
      }
    ]
  },

  [ASSIGNMENT_CATEGORIES.CURRENT_AFFAIRS]: {
    [DIFFICULTY_LEVELS.EASY]: [
      {
        id: 'current_easy_1',
        question_text: 'Which technology has become most prominent in recent years for creating realistic conversational AI?',
        options: ['A) Large Language Models (LLMs)', 'B) Blockchain', 'C) Virtual Reality', 'D) Quantum Computing'],
        correct_answer: 'A) Large Language Models (LLMs)',
        explanation: 'Large Language Models like GPT and similar technologies have revolutionized conversational AI and natural language processing.',
        vedic_connection: '',
        modern_application: 'LLMs are transforming education, customer service, content creation, and many other industries.'
      }
    ],
    [DIFFICULTY_LEVELS.MEDIUM]: [
      {
        id: 'current_medium_1',
        question_text: 'Which international agreement focuses on limiting global warming to well below 2°C above pre-industrial levels?',
        options: ['A) Paris Agreement', 'B) Kyoto Protocol', 'C) Montreal Protocol', 'D) Geneva Convention'],
        correct_answer: 'A) Paris Agreement',
        explanation: 'The Paris Agreement, adopted in 2015, aims to limit global temperature rise to well below 2°C, preferably 1.5°C.',
        vedic_connection: 'The Vedic concept of living in harmony with nature aligns with climate action goals.',
        modern_application: 'Climate agreements drive policy changes, renewable energy adoption, and sustainable business practices.'
      }
    ],
    [DIFFICULTY_LEVELS.HARD]: [
      {
        id: 'current_hard_1',
        question_text: 'What is the potential impact of quantum computing on current cryptographic security systems?',
        options: ['A) It could break many current encryption methods, requiring new quantum-resistant algorithms', 'B) It will make all systems completely secure', 'C) It has no impact on cryptography', 'D) It only affects blockchain technology'],
        correct_answer: 'A) It could break many current encryption methods, requiring new quantum-resistant algorithms',
        explanation: 'Quantum computers could potentially break RSA and other current encryption methods, leading to the development of post-quantum cryptography.',
        vedic_connection: '',
        modern_application: 'Organizations are preparing for quantum-resistant security to protect sensitive data and communications.'
      }
    ]
  }
};

// Helper functions for question bank management
export function getQuestionsByCategory(category) {
  return QUESTION_BANKS[category] || {};
}

export function getQuestionsByCategoryAndDifficulty(category, difficulty) {
  return QUESTION_BANKS[category]?.[difficulty] || [];
}

export function getAllQuestions() {
  const allQuestions = [];
  Object.entries(QUESTION_BANKS).forEach(([category, difficulties]) => {
    Object.entries(difficulties).forEach(([difficulty, questions]) => {
      questions.forEach(question => {
        allQuestions.push({
          ...question,
          category,
          difficulty
        });
      });
    });
  });
  return allQuestions;
}

export function getRandomQuestions(category, difficulty, count) {
  const questions = getQuestionsByCategoryAndDifficulty(category, difficulty);
  const shuffled = [...questions].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

export function searchQuestions(searchTerm) {
  const allQuestions = getAllQuestions();
  return allQuestions.filter(question =>
    question.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    question.explanation.toLowerCase().includes(searchTerm.toLowerCase())
  );
}

export default QUESTION_BANKS;