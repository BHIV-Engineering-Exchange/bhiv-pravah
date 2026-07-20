// Minimal sample data aligned with the manager's prompt

export const assessmentQuestions = [
  {
    id: 'q1',
    question_text: 'Which data structure uses FIFO?',
    options: ['Stack', 'Queue', 'Tree', 'Graph'],
    correct_answer: 'Queue',
    category: 'Coding',
    difficulty: 'Easy',
  },
  {
    id: 'q2',
    question_text: '2x + 4 = 10. What is x?',
    options: ['2', '3', '4', '5'],
    correct_answer: '3',
    category: 'Math',
    difficulty: 'Easy',
  },
  {
    id: 'q3',
    question_text: 'Bhagavad Gita emphasizes which leadership quality?',
    options: ['Attachment', 'Indecision', 'Dharma (duty)', 'Avoidance'],
    correct_answer: 'Dharma (duty)',
    category: 'Vedic',
    difficulty: 'Easy',
  },
]

export const syllabus = {
  Seed: [
    {
      lesson_id: 'seed-1',
      title: 'Variables and Types',
      description: 'Understand variables, types, and simple operations.',
      content_type: 'Interactive',
      resources: ['https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/Variables'],
      vedic_link: 'Basics of discipline and clarity',
    },
    {
      lesson_id: 'seed-2',
      title: 'Logic Puzzles 101',
      description: 'Practice beginner-friendly logical reasoning.',
      content_type: 'Text',
      resources: ['https://projecteuler.net/'],
      vedic_link: 'Nyaya (logic) fundamentals',
    },
  ],
  Tree: [
    {
      lesson_id: 'tree-1',
      title: 'Data Structures Basics',
      description: 'Arrays, stacks, queues, and maps.',
      content_type: 'Video',
      resources: ['https://www.youtube.com/results?search_query=data+structures+basics'],
      vedic_link: 'Order and structure in Shastras',
    },
  ],
  Sky: [
    {
      lesson_id: 'sky-1',
      title: 'Intro to AI Systems',
      description: 'What is AI? Overview of models, training, and inference.',
      content_type: 'Video',
      resources: ['https://ai.google/education/'],
      vedic_link: 'Sankhya (enumeration) and systems thinking',
    },
  ],
}

export const knowledgebase = [
  {
    id: 'kb-arthashastra',
    title: 'Arthashastra on Economics',
    description: 'Insights on governance, taxation, and prudent resource allocation.',
    category: 'Economics',
    modern_application: 'Public finance, policy design, organizational governance',
    related_lessons: ['tree-1'],
  },
  {
    id: 'kb-gita-leadership',
    title: 'Bhagavad Gita on Leadership',
    description: 'Duty (Dharma), clarity in action, and equanimity under pressure.',
    category: 'Leadership',
    modern_application: 'Responsible decision-making, ethical leadership',
    related_lessons: ['seed-2'],
  },
]

// Reference JSON schema snippet for internal documentation or validation scaffolding
export const gurukulSchemaV1_1 = {
  user: {
    id: 'string',
    name: 'string',
    email: 'string',
    tier: 'Seed | Tree | Sky',
    progress: { Seed: 'number', Tree: 'number', Sky: 'number' },
    badges: ['string'],
    referral_code: 'string',
  },
  assessment: {
    id: 'string',
    questions: [
      {
        id: 'string',
        question_text: 'string',
        options: ['string'],
        correct_answer: 'string',
        category: 'Coding | Logic | Math | Language | Culture | Vedic | Current Affairs',
        difficulty: 'Easy | Medium | Hard',
      },
    ],
    user_responses: [
      {
        question_id: 'string',
        selected_option: 'string',
        is_correct: 'boolean',
        explanation: 'string',
        ai_score: 'number',
      },
    ],
  },
  syllabus: {
    Seed: [
      {
        lesson_id: 'string',
        title: 'string',
        description: 'string',
        content_type: 'Video | Text | Interactive',
        resources: ['string'],
        vedic_link: 'string',
      },
    ],
    Tree: [],
    Sky: [],
  },
  vedic_knowledgebase: [
    {
      id: 'string',
      title: 'string',
      description: 'string',
      category: 'Philosophy | Science | Economics | Leadership | Culture',
      modern_application: 'string',
      related_lessons: ['lesson_id'],
    },
  ],
}


