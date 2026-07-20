// Study fields configuration for field-based assessment system

export const STUDY_FIELDS = {
  STEM: {
    id: 'stem',
    name: 'STEM (Science, Technology, Engineering, Mathematics)',
    shortName: 'STEM',
    description: 'Science, Technology, Engineering, and Mathematics fields including Computer Science, Physics, Chemistry, Biology, Engineering, and Mathematical Sciences',
    subcategories: [
      'Computer Science',
      'Software Engineering',
      'Data Science',
      'Cybersecurity',
      'Artificial Intelligence',
      'Physics',
      'Chemistry',
      'Biology',
      'Mathematics',
      'Engineering',
      'Information Technology'
    ]
  },
  BUSINESS: {
    id: 'business',
    name: 'Business & Economics',
    shortName: 'Business',
    description: 'Business administration, economics, finance, marketing, entrepreneurship, and related commercial fields',
    subcategories: [
      'Business Administration',
      'Economics',
      'Finance',
      'Marketing',
      'Accounting',
      'Entrepreneurship',
      'Management',
      'International Business',
      'Supply Chain Management',
      'Human Resources'
    ]
  },
  SOCIAL_SCIENCES: {
    id: 'social_sciences',
    name: 'Social Sciences',
    shortName: 'Social Sciences',
    description: 'Psychology, sociology, political science, anthropology, and other social science disciplines',
    subcategories: [
      'Psychology',
      'Sociology',
      'Political Science',
      'Anthropology',
      'International Relations',
      'Social Work',
      'Criminology',
      'Geography',
      'History',
      'Philosophy'
    ]
  },
  HEALTH_MEDICINE: {
    id: 'health_medicine',
    name: 'Health & Medicine',
    shortName: 'Health & Medicine',
    description: 'Medicine, nursing, pharmacy, public health, and other healthcare-related fields',
    subcategories: [
      'Medicine',
      'Nursing',
      'Pharmacy',
      'Public Health',
      'Dentistry',
      'Veterinary Medicine',
      'Physical Therapy',
      'Occupational Therapy',
      'Medical Technology',
      'Health Administration'
    ]
  },
  CREATIVE_ARTS: {
    id: 'creative_arts',
    name: 'Creative Arts & Humanities',
    shortName: 'Creative Arts',
    description: 'Fine arts, literature, languages, music, theater, design, and other creative and humanities disciplines',
    subcategories: [
      'Fine Arts',
      'Literature',
      'Languages',
      'Music',
      'Theater',
      'Film Studies',
      'Graphic Design',
      'Creative Writing',
      'Art History',
      'Linguistics'
    ]
  },
  OTHER: {
    id: 'other',
    name: 'Other Fields',
    shortName: 'Other',
    description: 'Agriculture, environmental studies, sports science, and other specialized fields',
    subcategories: [
      'Agriculture',
      'Environmental Studies',
      'Sports Science',
      'Hospitality Management',
      'Tourism',
      'Architecture',
      'Urban Planning',
      'Library Science',
      'Education',
      'Law'
    ]
  }
};

// Mapping study fields to question categories with weights
export const FIELD_QUESTION_MAPPING = {
  [STUDY_FIELDS.STEM.id]: {
    // STEM fields get more coding, logic, and mathematics questions
    primary: ['Coding', 'Logic', 'Mathematics'],
    secondary: ['Current Affairs', 'Vedic Knowledge'],
    weights: {
      'Coding': 35,
      'Logic': 25,
      'Mathematics': 25,
      'Language': 5,
      'Culture': 5,
      'Vedic Knowledge': 3,
      'Current Affairs': 2
    }
  },
  [STUDY_FIELDS.BUSINESS.id]: {
    // Business gets more logic, current affairs, and language
    primary: ['Logic', 'Current Affairs', 'Language'],
    secondary: ['Mathematics', 'Culture'],
    weights: {
      'Logic': 30,
      'Current Affairs': 25,
      'Language': 20,
      'Mathematics': 10,
      'Culture': 10,
      'Coding': 3,
      'Vedic Knowledge': 2
    }
  },
  [STUDY_FIELDS.SOCIAL_SCIENCES.id]: {
    // Social sciences get more language, culture, and current affairs
    primary: ['Language', 'Culture', 'Current Affairs'],
    secondary: ['Logic', 'Vedic Knowledge'],
    weights: {
      'Language': 30,
      'Culture': 25,
      'Current Affairs': 20,
      'Logic': 15,
      'Vedic Knowledge': 5,
      'Mathematics': 3,
      'Coding': 2
    }
  },
  [STUDY_FIELDS.HEALTH_MEDICINE.id]: {
    // Health/Medicine gets balanced questions with focus on logic and current affairs
    primary: ['Logic', 'Current Affairs', 'Language'],
    secondary: ['Mathematics', 'Vedic Knowledge'],
    weights: {
      'Logic': 30,
      'Current Affairs': 20,
      'Language': 20,
      'Mathematics': 15,
      'Vedic Knowledge': 8,
      'Culture': 5,
      'Coding': 2
    }
  },
  [STUDY_FIELDS.CREATIVE_ARTS.id]: {
    // Creative arts get more language, culture, and vedic knowledge
    primary: ['Language', 'Culture', 'Vedic Knowledge'],
    secondary: ['Current Affairs', 'Logic'],
    weights: {
      'Language': 35,
      'Culture': 25,
      'Vedic Knowledge': 15,
      'Current Affairs': 10,
      'Logic': 10,
      'Mathematics': 3,
      'Coding': 2
    }
  },
  [STUDY_FIELDS.OTHER.id]: {
    // Other fields get balanced distribution
    primary: ['Language', 'Logic', 'Current Affairs'],
    secondary: ['Culture', 'Mathematics'],
    weights: {
      'Language': 20,
      'Logic': 20,
      'Current Affairs': 20,
      'Culture': 15,
      'Mathematics': 10,
      'Vedic Knowledge': 10,
      'Coding': 5
    }
  }
};

// Question difficulty distribution by field
export const FIELD_DIFFICULTY_DISTRIBUTION = {
  [STUDY_FIELDS.STEM.id]: {
    easy: 25,
    medium: 50,
    hard: 25
  },
  [STUDY_FIELDS.BUSINESS.id]: {
    easy: 30,
    medium: 50,
    hard: 20
  },
  [STUDY_FIELDS.SOCIAL_SCIENCES.id]: {
    easy: 35,
    medium: 45,
    hard: 20
  },
  [STUDY_FIELDS.HEALTH_MEDICINE.id]: {
    easy: 30,
    medium: 50,
    hard: 20
  },
  [STUDY_FIELDS.CREATIVE_ARTS.id]: {
    easy: 35,
    medium: 45,
    hard: 20
  },
  [STUDY_FIELDS.OTHER.id]: {
    easy: 30,
    medium: 50,
    hard: 20
  }
};

// Helper functions
export function getStudyFieldById(fieldId) {
  return Object.values(STUDY_FIELDS).find(field => field.id === fieldId);
}

export function getStudyFieldByName(fieldName) {
  return Object.values(STUDY_FIELDS).find(
    field => field.name.toLowerCase().includes(fieldName.toLowerCase()) ||
             field.subcategories.some(sub => sub.toLowerCase().includes(fieldName.toLowerCase()))
  );
}

export function getQuestionWeightsForField(fieldId) {
  return FIELD_QUESTION_MAPPING[fieldId]?.weights || FIELD_QUESTION_MAPPING[STUDY_FIELDS.OTHER.id].weights;
}

export function getDifficultyDistributionForField(fieldId) {
  return FIELD_DIFFICULTY_DISTRIBUTION[fieldId] || FIELD_DIFFICULTY_DISTRIBUTION[STUDY_FIELDS.OTHER.id];
}

export function detectStudyFieldFromBackground(studentData) {
  // Pull from both top-level and responses JSON
  const pick = (primary, fallback) => {
    const val = primary ?? fallback ?? '';
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'object' && val !== null) return Object.values(val).join(' ');
    return String(val || '');
  };

  // Prioritize background selection data if available
  const backgroundField = studentData.background_field_of_study;
  if (backgroundField) {
    console.log(`🎯 Using background selection field: ${backgroundField}`);
    // Direct mapping from background selection to study field IDs
    const fieldMapping = {
      'stem': STUDY_FIELDS.STEM.id,
      'business': STUDY_FIELDS.BUSINESS.id,
      'social_sciences': STUDY_FIELDS.SOCIAL_SCIENCES.id,
      'health_medicine': STUDY_FIELDS.HEALTH_MEDICINE.id,
      'creative_arts': STUDY_FIELDS.CREATIVE_ARTS.id,
      'other': STUDY_FIELDS.OTHER.id
    };
    
    if (fieldMapping[backgroundField]) {
      return fieldMapping[backgroundField];
    }
  }

  // Fallback to text analysis if no background selection
  const field = pick(studentData.field_of_study, studentData.responses?.field_of_study);
  const skills = pick(studentData.current_skills, studentData.responses?.current_skills);
  const interests = pick(studentData.interests, studentData.responses?.interests);
  const goals = pick(studentData.goals, studentData.responses?.goals);
  const edu = pick(studentData.education_level, studentData.responses?.education_level);
  const bgGoals = pick(studentData.background_learning_goals, '');
  const bgClass = pick(studentData.background_class_level, '');

  const combinedText = `${field} ${skills} ${interests} ${goals} ${edu} ${bgGoals} ${bgClass}`.toLowerCase();

  // STEM keywords incl. common abbreviations
  const stemKeywords = [
    'computer', 'software', 'programming', 'coding', 'developer', 'data science', 'data scientist',
    'engineering', 'engineer', 'physics', 'chemistry', 'biology', 'biotech', 'mathematics', 'math',
    'science', 'technology', 'ai', 'machine learning', 'ml', 'deep learning', 'cybersecurity',
    'cs', 'comp sci', 'it', 'ict', 'information technology'
  ];
  if (stemKeywords.some(keyword => combinedText.includes(keyword))) {
    return STUDY_FIELDS.STEM.id;
  }

  // Business
  const businessKeywords = [
    'business', 'finance', 'marketing', 'economics', 'management', 'entrepreneurship', 'accounting',
    'mba', 'sales', 'operations', 'supply chain', 'hr', 'human resources', 'commerce', 'bba'
  ];
  if (businessKeywords.some(keyword => combinedText.includes(keyword))) {
    return STUDY_FIELDS.BUSINESS.id;
  }

  // Social Sciences
  const socialKeywords = [
    'psychology', 'psych', 'sociology', 'political', 'international relations', 'social work',
    'anthropology', 'history', 'philosophy', 'geography', 'criminology'
  ];
  if (socialKeywords.some(keyword => combinedText.includes(keyword))) {
    return STUDY_FIELDS.SOCIAL_SCIENCES.id;
  }

  // Health/Medicine
  const healthKeywords = [
    'medicine', 'medical', 'med', 'pre-med', 'nursing', 'pharmacy', 'health', 'public health',
    'doctor', 'physician', 'dentistry', 'vet', 'veterinary', 'therapy', 'physiotherapy'
  ];
  if (healthKeywords.some(keyword => combinedText.includes(keyword))) {
    return STUDY_FIELDS.HEALTH_MEDICINE.id;
  }

  // Creative Arts & Humanities
  const artsKeywords = [
    'art', 'design', 'graphic design', 'ui', 'ux', 'music', 'literature', 'linguistics', 'creative',
    'writing', 'theater', 'film', 'languages', 'fine arts', 'humanities', 'philosophy'
  ];
  if (artsKeywords.some(keyword => combinedText.includes(keyword))) {
    return STUDY_FIELDS.CREATIVE_ARTS.id;
  }

  // Default to OTHER
  return STUDY_FIELDS.OTHER.id;
}

export default STUDY_FIELDS;