import { FIELD_TYPES } from "./formConfigService";
import { DynamicFieldService } from './dynamicFieldService';

// Base fields that are common across all forms
const BASE_FIELDS = [
  {
    id: "name",
    type: FIELD_TYPES.TEXT,
    label: "Full Name",
    placeholder: "e.g., Asha Gupta",
    required: true,
    order: 1,
    validation: {
      minLength: 2,
      maxLength: 100,
    },
  },
  {
    id: "age",
    type: FIELD_TYPES.NUMBER,
    label: "Age",
    placeholder: "17",
    required: false,
    order: 2,
    validation: {
      min: 5,
      max: 100,
    },
  },
  {
    id: "email",
    type: FIELD_TYPES.EMAIL,
    label: "Email",
    placeholder: "your.email@example.com",
    required: false,
    order: 3,
  },
  {
    id: "phone",
    type: FIELD_TYPES.TEXT,
    label: "Phone",
    placeholder: "999-000-1234",
    required: false,
    order: 4,
    validation: {
      pattern: "^[\\d\\s\\-\\+\\(\\)\\.]+$",
    },
  },
];

// Dynamic field-specific configurations
const FIELD_SPECIFIC_CONFIGS = {
  stem: {
    name: "STEM Student Intake",
    description: "Help us understand your technical background and interests in Science, Technology, Engineering, and Math.",
    fields: [
      {
        id: "programming_languages",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Programming Languages (if any)",
        required: false,
        order: 5,
        options: [
          { value: "python", label: "Python" },
          { value: "javascript", label: "JavaScript" },
          { value: "java", label: "Java" },
          { value: "cpp", label: "C++" },
          { value: "c", label: "C" },
          { value: "r", label: "R" },
          { value: "matlab", label: "MATLAB" },
          { value: "sql", label: "SQL" },
          { value: "none", label: "None" },
        ],
      },
      {
        id: "math_level",
        type: FIELD_TYPES.SELECT,
        label: "Highest Math Level Completed",
        required: false,
        order: 6,
        options: [
          { value: "algebra", label: "Algebra" },
          { value: "geometry", label: "Geometry" },
          { value: "trigonometry", label: "Trigonometry" },
          { value: "precalculus", label: "Pre-Calculus" },
          { value: "calculus1", label: "Calculus I" },
          { value: "calculus2", label: "Calculus II" },
          { value: "calculus3", label: "Calculus III" },
          { value: "linear_algebra", label: "Linear Algebra" },
          { value: "differential_equations", label: "Differential Equations" },
          { value: "statistics", label: "Statistics" },
        ],
      },
      {
        id: "technical_interests",
        type: FIELD_TYPES.TEXTAREA,
        label: "Technical Interests & Specializations",
        placeholder: "e.g., Machine Learning, Web Development, Robotics, Data Science",
        required: false,
        order: 7,
        helpText: "What specific areas of technology or science interest you most?",
      },
      {
        id: "project_experience",
        type: FIELD_TYPES.TEXTAREA,
        label: "Project Experience",
        placeholder: "Describe any technical projects you've worked on",
        required: false,
        order: 8,
      },
      {
        id: "preferred_learning_tools",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Preferred Learning Tools",
        required: false,
        order: 9,
        options: [
          { value: "hands_on_coding", label: "Hands-on Coding" },
          { value: "video_tutorials", label: "Video Tutorials" },
          { value: "documentation", label: "Documentation Reading" },
          { value: "interactive_labs", label: "Interactive Labs" },
          { value: "peer_collaboration", label: "Peer Collaboration" },
          { value: "theory_first", label: "Theory First, Then Practice" },
        ],
      },
    ]
  },

  business: {
    name: "Business & Economics Student Intake",
    description: "Share your business interests and career aspirations.",
    fields: [
      {
        id: "business_areas",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Areas of Business Interest",
        required: false,
        order: 5,
        options: [
          { value: "marketing", label: "Marketing" },
          { value: "finance", label: "Finance" },
          { value: "management", label: "Management" },
          { value: "entrepreneurship", label: "Entrepreneurship" },
          { value: "consulting", label: "Consulting" },
          { value: "operations", label: "Operations" },
          { value: "hr", label: "Human Resources" },
          { value: "strategy", label: "Business Strategy" },
          { value: "analytics", label: "Business Analytics" },
        ],
      },
      {
        id: "business_experience",
        type: FIELD_TYPES.SELECT,
        label: "Business Experience Level",
        required: false,
        order: 6,
        options: [
          { value: "none", label: "No formal business experience" },
          { value: "academic", label: "Academic coursework only" },
          { value: "internship", label: "Internship experience" },
          { value: "part_time", label: "Part-time work experience" },
          { value: "full_time", label: "Full-time work experience" },
          { value: "leadership", label: "Leadership/Management experience" },
          { value: "entrepreneur", label: "Entrepreneurial experience" },
        ],
      },
      {
        id: "industry_interests",
        type: FIELD_TYPES.TEXTAREA,
        label: "Industry Interests",
        placeholder: "e.g., Technology, Healthcare, Retail, Financial Services",
        required: false,
        order: 7,
        helpText: "Which industries or sectors interest you most?",
      },
      {
        id: "career_goals",
        type: FIELD_TYPES.RADIO,
        label: "Primary Career Goal",
        required: false,
        order: 8,
        options: [
          { value: "corporate", label: "Corporate Career Advancement" },
          { value: "startup", label: "Start My Own Business" },
          { value: "consulting", label: "Management Consulting" },
          { value: "finance", label: "Finance/Investment Banking" },
          { value: "nonprofit", label: "Nonprofit/Social Impact" },
          { value: "exploring", label: "Still Exploring Options" },
        ],
      },
      {
        id: "analytical_tools",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Analytical Tools Experience",
        required: false,
        order: 9,
        options: [
          { value: "excel", label: "Microsoft Excel" },
          { value: "powerpoint", label: "PowerPoint" },
          { value: "tableau", label: "Tableau" },
          { value: "sql", label: "SQL" },
          { value: "python", label: "Python for Business" },
          { value: "r", label: "R for Statistics" },
          { value: "none", label: "None of the above" },
        ],
      },
    ]
  },

  social_sciences: {
    name: "Social Sciences & Humanities Student Intake",
    description: "Help us understand your research interests and social focus.",
    fields: [
      {
        id: "social_science_areas",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Areas of Social Science Interest",
        required: false,
        order: 5,
        options: [
          { value: "psychology", label: "Psychology" },
          { value: "sociology", label: "Sociology" },
          { value: "anthropology", label: "Anthropology" },
          { value: "political_science", label: "Political Science" },
          { value: "economics", label: "Economics" },
          { value: "international_relations", label: "International Relations" },
          { value: "criminology", label: "Criminology" },
          { value: "social_work", label: "Social Work" },
        ],
      },
      {
        id: "research_methods",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Research Methods Experience",
        required: false,
        order: 6,
        options: [
          { value: "surveys", label: "Surveys & Questionnaires" },
          { value: "interviews", label: "Interviews" },
          { value: "focus_groups", label: "Focus Groups" },
          { value: "statistical_analysis", label: "Statistical Analysis" },
          { value: "qualitative_analysis", label: "Qualitative Analysis" },
          { value: "literature_review", label: "Literature Reviews" },
          { value: "none", label: "No formal research experience" },
        ],
      },
      {
        id: "social_issues",
        type: FIELD_TYPES.TEXTAREA,
        label: "Social Issues of Interest",
        placeholder: "e.g., Mental Health, Social Justice, Education Policy, Climate Change",
        required: false,
        order: 7,
        helpText: "What social issues or problems are you passionate about?",
      },
      {
        id: "career_path",
        type: FIELD_TYPES.RADIO,
        label: "Intended Career Path",
        required: false,
        order: 8,
        options: [
          { value: "research", label: "Academic Research" },
          { value: "clinical", label: "Clinical Practice (Psychology/Social Work)" },
          { value: "policy", label: "Policy Analysis/Government" },
          { value: "nonprofit", label: "Nonprofit Organizations" },
          { value: "private_sector", label: "Private Sector (HR, Consulting)" },
          { value: "education", label: "Education/Teaching" },
          { value: "undecided", label: "Still Deciding" },
        ],
      },
    ]
  },

  health_medicine: {
    name: "Health & Medicine Student Intake",
    description: "Tell us about your healthcare interests and science background.",
    fields: [
      {
        id: "health_specialties",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Areas of Health Interest",
        required: false,
        order: 5,
        options: [
          { value: "medicine", label: "Medicine/Physician" },
          { value: "nursing", label: "Nursing" },
          { value: "pharmacy", label: "Pharmacy" },
          { value: "dentistry", label: "Dentistry" },
          { value: "public_health", label: "Public Health" },
          { value: "physical_therapy", label: "Physical Therapy" },
          { value: "mental_health", label: "Mental Health/Psychology" },
          { value: "research", label: "Medical Research" },
          { value: "administration", label: "Healthcare Administration" },
        ],
      },
      {
        id: "science_background",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Science Coursework Completed",
        required: false,
        order: 6,
        options: [
          { value: "biology", label: "Biology" },
          { value: "chemistry", label: "Chemistry" },
          { value: "organic_chemistry", label: "Organic Chemistry" },
          { value: "physics", label: "Physics" },
          { value: "anatomy", label: "Anatomy & Physiology" },
          { value: "microbiology", label: "Microbiology" },
          { value: "biochemistry", label: "Biochemistry" },
          { value: "statistics", label: "Statistics/Biostatistics" },
        ],
      },
      {
        id: "healthcare_experience",
        type: FIELD_TYPES.SELECT,
        label: "Healthcare Experience",
        required: false,
        order: 7,
        options: [
          { value: "none", label: "No healthcare experience" },
          { value: "volunteer", label: "Hospital/Clinic Volunteer" },
          { value: "shadowing", label: "Job Shadowing" },
          { value: "internship", label: "Healthcare Internship" },
          { value: "work", label: "Healthcare Work Experience" },
          { value: "research", label: "Medical Research Experience" },
        ],
      },
      {
        id: "patient_interaction",
        type: FIELD_TYPES.RADIO,
        label: "Interest in Patient Interaction",
        required: false,
        order: 8,
        options: [
          { value: "high", label: "High - Direct patient care is my priority" },
          { value: "moderate", label: "Moderate - Some patient interaction is fine" },
          { value: "low", label: "Low - Prefer behind-the-scenes work" },
          { value: "research", label: "Research-focused - Minimal patient contact" },
        ],
      },
    ]
  },

  creative_arts: {
    name: "Creative Arts Student Intake",
    description: "Share your artistic journey and creative goals.",
    fields: [
      {
        id: "art_mediums",
        type: FIELD_TYPES.MULTI_SELECT,
        label: "Artistic Mediums",
        required: false,
        order: 5,
        options: [
          { value: "drawing", label: "Drawing" },
          { value: "painting", label: "Painting" },
          { value: "sculpture", label: "Sculpture" },
          { value: "photography", label: "Photography" },
          { value: "digital_art", label: "Digital Art" },
          { value: "graphic_design", label: "Graphic Design" },
          { value: "music", label: "Music" },
          { value: "dance", label: "Dance" },
          { value: "theater", label: "Theater" },
          { value: "film", label: "Film/Video" },
        ],
      },
      {
        id: "skill_level",
        type: FIELD_TYPES.SELECT,
        label: "Overall Skill Level",
        required: false,
        order: 6,
        options: [
          { value: "beginner", label: "Beginner - Just starting out" },
          { value: "intermediate", label: "Intermediate - Some experience" },
          { value: "advanced", label: "Advanced - Significant experience" },
          { value: "professional", label: "Professional - Working artist" },
        ],
      },
      {
        id: "artistic_goals",
        type: FIELD_TYPES.RADIO,
        label: "Primary Artistic Goal",
        required: false,
        order: 7,
        options: [
          { value: "personal", label: "Personal Expression & Enjoyment" },
          { value: "professional", label: "Professional Career in Arts" },
          { value: "academic", label: "Academic Study & Art History" },
          { value: "commercial", label: "Commercial/Applied Arts" },
          { value: "teaching", label: "Teaching Arts to Others" },
        ],
      },
      {
        id: "portfolio_status",
        type: FIELD_TYPES.RADIO,
        label: "Portfolio Status",
        required: false,
        order: 8,
        options: [
          { value: "none", label: "No portfolio yet" },
          { value: "building", label: "Currently building portfolio" },
          { value: "complete", label: "Have a complete portfolio" },
          { value: "professional", label: "Professional portfolio for work" },
        ],
      },
    ]
  }
};

// Common fields that appear at the end of all forms
const COMMON_END_FIELDS = [
  {
    id: "availability_per_week_hours",
    type: FIELD_TYPES.NUMBER,
    label: "Availability per week (hours)",
    placeholder: "6",
    required: false,
    order: 100,
    validation: {
      min: 0,
      max: 168,
    },
  },
  {
    id: "preferred_learning_style",
    type: FIELD_TYPES.RADIO,
    label: "Preferred Learning Style",
    required: false,
    order: 101,
    options: [
      { value: "video", label: "Video Tutorials" },
      { value: "text", label: "Text-based Learning" },
      { value: "interactive", label: "Interactive Exercises" },
      { value: "mixed", label: "Mixed Approach" },
    ],
  },
  {
    id: "additional_info",
    type: FIELD_TYPES.TEXTAREA,
    label: "Additional Information",
    placeholder: "Anything else you'd like us to know about your background or goals?",
    required: false,
    order: 102,
  },
];

// Function to generate form configuration based on field category
export async function generateFormConfigForField(fieldCategory, classLevel, learningGoals) {
  let specificFields = [];
  let formName = "Student Intake Form";
  let formDescription = "Tell us about yourself so we can personalize your learning experience.";

  // Try to get field information from database
  try {
    const field = await DynamicFieldService.getFieldById(fieldCategory);
    if (field) {
      formName = `${field.name} Student Intake`;
      formDescription = `Help us understand your background and interests in ${field.name.toLowerCase()}.`;
    }
  } catch (error) {
    console.error('Error getting field info:', error);
  }

  // Get field-specific configuration
  const fieldConfig = FIELD_SPECIFIC_CONFIGS[fieldCategory];
  if (fieldConfig) {
    specificFields = fieldConfig.fields;
    formName = fieldConfig.name;
    formDescription = fieldConfig.description;
  } else {
    // For unknown categories, create a generic form
    specificFields = [
      {
        id: "field_of_study",
        type: FIELD_TYPES.TEXT,
        label: "Field of Study",
        placeholder: "Please specify your field of study",
        required: true,
        order: 5,
      },
      {
        id: "current_skills",
        type: FIELD_TYPES.TEXTAREA,
        label: "Current Skills & Knowledge",
        placeholder: "Tell us about your current skills and areas of knowledge",
        required: false,
        order: 6,
      },
      {
        id: "interests",
        type: FIELD_TYPES.TEXTAREA,
        label: "Interests & Goals",
        placeholder: "What are you interested in learning or achieving?",
        required: false,
        order: 7,
      },
    ];
    formName = "General Student Intake";
    formDescription = "Tell us about your academic background and learning goals.";
  }

  // Add class level and learning goals context to description
  const levelContext = classLevel ? ` (${classLevel.replace('_', ' ')})` : '';
  const goalContext = learningGoals ? ` focused on ${learningGoals.replace('_', ' ')}` : '';
  formDescription += levelContext + goalContext + '.';

  // Create education level field with pre-selected value from background selection
  const educationLevelField = {
    id: "education_level",
    type: FIELD_TYPES.SELECT,
    label: "Education Level",
    placeholder: "Select your education level",
    required: false,
    order: 5,
    defaultValue: classLevel, // Pre-populate from background selection
    options: [
      { value: "high_school", label: "High School" },
      { value: "undergraduate", label: "Undergraduate" },
      { value: "graduate", label: "Graduate" },
      { value: "postgraduate", label: "Postgraduate" },
      { value: "professional", label: "Professional/Working" },
      { value: "other", label: "Other" }
    ]
  };

  // Create goals field with pre-selected value from background selection
  const goalsField = {
    id: "goals",
    type: FIELD_TYPES.TEXTAREA,
    label: "Goals",
    placeholder: "What do you want to achieve?",
    required: false,
    order: 90,
    defaultValue: getLearningGoalDescription(learningGoals), // Pre-populate from background selection
  };

  // Combine all fields and sort by order
  const allFields = [...BASE_FIELDS, educationLevelField, ...specificFields, goalsField, ...COMMON_END_FIELDS.filter(f => f.id !== 'additional_info')] // Remove duplicate goals
    .sort((a, b) => (a.order || 0) - (b.order || 0));

  return {
    id: `dynamic_${fieldCategory}_${Date.now()}`,
    name: formName,
    description: formDescription,
    fields: allFields,
    metadata: {
      fieldCategory,
      classLevel,
      learningGoals,
      generatedAt: new Date().toISOString(),
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_active: true,
  };
}

// Helper function to convert learning goals to description
function getLearningGoalDescription(learningGoals) {
  const goalDescriptions = {
    'skill_building': 'Build specific skills for career advancement',
    'academic_support': 'Get academic support and exam preparation',
    'career_change': 'Transition to a new career path',
    'personal_growth': 'Focus on personal growth and learning',
    'certification': 'Obtain professional certification',
    'exploration': 'Explore new interests and subjects'
  };
  
  return goalDescriptions[learningGoals] || learningGoals;
}

// Function to add new field configuration (for admin use)
export async function addFieldConfiguration(fieldId, config) {
  FIELD_SPECIFIC_CONFIGS[fieldId] = config;
}

// Function to get available field configurations
export function getAvailableFieldConfigurations() {
  return Object.keys(FIELD_SPECIFIC_CONFIGS);
}

// Function to get field configuration
export function getFieldConfiguration(fieldId) {
  return FIELD_SPECIFIC_CONFIGS[fieldId] || null;
}