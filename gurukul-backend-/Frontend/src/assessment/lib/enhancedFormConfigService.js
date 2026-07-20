import { FIELD_TYPES } from "./formConfigService";
import { DynamicFieldService } from './dynamicFieldService';
import { DynamicCategoryService } from './dynamicCategoryService';

// Background selection field configurations that can be included at the start of any form
export const BACKGROUND_SELECTION_FIELDS = {
  field_of_study: {
    id: "field_of_study",
    type: FIELD_TYPES.RADIO,
    label: "What field are you studying or working in?",
    required: true,
    order: -3, // Negative order to ensure it comes first
    section: "background_selection",
    helpText: "This helps us personalize your learning experience",
    options: [], // Will be populated dynamically from database
    validation: {
      required: true
    },
    styling: {
      displayType: "card_grid", // Special styling for visual cards
      gridCols: "2", // 2 columns on larger screens
      showIcons: true,
      showDescriptions: true
    }
  },
  
  class_level: {
    id: "class_level",
    type: FIELD_TYPES.RADIO,
    label: "What's your current education level?",
    required: true,
    order: -2,
    section: "background_selection",
    options: [
      { value: 'high_school', label: 'High School (9th-12th Grade)' },
      { value: 'undergraduate', label: 'Undergraduate (Bachelor\'s)' },
      { value: 'graduate', label: 'Graduate (Master\'s)' },
      { value: 'postgraduate', label: 'Postgraduate (PhD/Doctorate)' },
      { value: 'professional', label: 'Professional/Working' }
    ],
    styling: {
      displayType: "card_grid",
      gridCols: "2"
    }
  },
  
  learning_goals: {
    id: "learning_goals",
    type: FIELD_TYPES.RADIO,
    label: "What's your main learning goal?",
    required: true,
    order: -1,
    section: "background_selection",
    options: [
      { value: 'skill_building', label: 'Build specific skills for career' },
      { value: 'academic_support', label: 'Academic support & exam prep' },
      { value: 'career_change', label: 'Career change or transition' },
      { value: 'personal_growth', label: 'Personal growth & learning' },
      { value: 'certification', label: 'Professional certification' },
      { value: 'exploration', label: 'Explore new interests' }
    ],
    styling: {
      displayType: "card_grid",
      gridCols: "2"
    }
  },
  
  // New: let students choose a question category (required)
  question_category: {
    id: "question_category",
    type: FIELD_TYPES.SELECT,
    label: "Which question category do you prefer?",
    required: true,
    order: 0,
    section: "background_selection",
    options: [] // Loaded dynamically in DynamicForm
  }
};

// Enhanced form configuration service that integrates background selection
export class EnhancedFormConfigService {
  
  /**
   * Load dynamic study fields and populate field_of_study options
   */
  static async loadDynamicStudyFields() {
    try {
      const fields = await DynamicFieldService.getAllFields();
      const options = fields.map(field => ({
        value: field.field_id,
        label: field.name,
        icon: field.icon,
        description: field.description
      }));
      
      // Update the background selection field with dynamic options
      BACKGROUND_SELECTION_FIELDS.field_of_study.options = options;
      
      return options;
    } catch (error) {
      console.error('Error loading dynamic study fields:', error);
      // Fallback to default options
      const fallbackOptions = [
        { value: 'stem', label: 'STEM', icon: '🔬', description: 'Science, Technology, Engineering, Math' },
        { value: 'business', label: 'Business', icon: '💼', description: 'Business & Economics' },
        { value: 'social_sciences', label: 'Social Sciences', icon: '🏛️', description: 'Social Sciences & Humanities' },
        { value: 'health_medicine', label: 'Health & Medicine', icon: '⚕️', description: 'Healthcare and Medical Sciences' },
        { value: 'creative_arts', label: 'Creative Arts', icon: '🎨', description: 'Arts, Design, and Creative Fields' }
      ];
      
      BACKGROUND_SELECTION_FIELDS.field_of_study.options = fallbackOptions;
      return fallbackOptions;
    }
  }

  /**
   * Get background selection fields configuration
   * @param {Object} adminConfig - Admin configuration overrides
   * @returns {Array} Array of background selection field configurations
   */
  static async getBackgroundSelectionFields(adminConfig = {}) {
    // Load dynamic study fields first
    await this.loadDynamicStudyFields();
    
    const fields = Object.values(BACKGROUND_SELECTION_FIELDS);
    
    // Apply admin configuration overrides
    return fields.map(field => {
      const fieldId = field.id;
      const adminOverrides = adminConfig[fieldId] || {};
      
      return {
        ...field,
        ...adminOverrides,
        // Ensure some properties are preserved
        section: "background_selection",
        order: adminOverrides.order !== undefined ? adminOverrides.order : field.order
      };
    });
  }

  /**
   * Create a complete form configuration with background selection and field-specific fields
   * @param {Object} baseConfig - Base form configuration
   * @param {Object} adminBackgroundConfig - Admin configuration for background fields
   * @param {boolean} includeBackground - Whether to include background selection fields
   * @returns {Object} Complete form configuration
   */
  static async createEnhancedFormConfig(baseConfig, adminBackgroundConfig = {}, includeBackground = true) {
    let allFields = [...(baseConfig.fields || [])];
    
    if (includeBackground) {
      const backgroundFields = await this.getBackgroundSelectionFields(adminBackgroundConfig);
      
      // Remove any duplicate fields from baseConfig that exist in backgroundFields
      const backgroundFieldIds = backgroundFields.map(f => f.id);
      allFields = allFields.filter(field => !backgroundFieldIds.includes(field.id));
      
      // Combine background fields with remaining base fields
      allFields = [...backgroundFields, ...allFields];
    }
    
    // Ensure no duplicate field IDs exist
    const uniqueFields = [];
    const seenIds = new Set();
    
    allFields.forEach(field => {
      if (!seenIds.has(field.id)) {
        seenIds.add(field.id);
        uniqueFields.push(field);
      } else {
        console.warn(`Duplicate field detected and removed: ${field.id}`);
      }
    });
    
    // Sort fields by order
    uniqueFields.sort((a, b) => (a.order || 0) - (b.order || 0));
    
    return {
      ...baseConfig,
      fields: uniqueFields,
      sections: await this.organizeSections(uniqueFields),
      hasBackgroundSelection: includeBackground
    };
  }

  /**
   * Organize fields into sections for better form structure using dynamic categories
   * @param {Array} fields - Array of field configurations
   * @returns {Object} Organized sections
   */
  static async organizeSections(fields) {
    try {
      // Get dynamic categories from the service
      const sections = await DynamicCategoryService.getOrganizedSections();
      
      // Ensure all field sections have corresponding categories
      for (const field of fields) {
        const sectionName = field.section || 'general';
        if (!sections[sectionName]) {
          // Create dynamic category if it doesn't exist
          const newCategory = await DynamicCategoryService.ensureCategoryExists(sectionName, {
            name: sectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            description: `Section for ${sectionName} fields`,
            icon: "Settings",
            order: 10
          });
          
          sections[sectionName] = {
            title: newCategory.name,
            description: newCategory.description,
            icon: newCategory.icon,
            order: newCategory.display_order,
            color: newCategory.color
          };
        }
      }
      
      return sections;
    } catch (error) {
      console.error('Error loading dynamic categories, falling back to default:', error);
      
      // Fallback to basic sections if dynamic categories fail
      const fallbackSections = {
        background_selection: {
          title: "Background Selection",
          description: "Tell us about your academic background and goals",
          icon: "GraduationCap",
          order: -3
        },
        personal_info: {
          title: "Personal Information",
          description: "Basic information about you",
          icon: "User",
          order: 0
        },
        academic_info: {
          title: "Academic Details",
          description: "Your educational background and preferences",
          icon: "BookOpen",
          order: 1
        },
        preferences: {
          title: "Learning Preferences",
          description: "How you prefer to learn",
          icon: "Settings",
          order: 2
        },
        general: {
          title: "Additional Information",
          description: "Other relevant details",
          icon: "FileText",
          order: 3
        }
      };
      
      // Add any missing sections for fields
      fields.forEach(field => {
        const sectionName = field.section || 'general';
        if (!fallbackSections[sectionName] && sectionName !== 'general') {
          fallbackSections[sectionName] = {
            title: sectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            description: `Section for ${sectionName} fields`,
            icon: "Settings",
            order: 10
          };
        }
      });
      
      return fallbackSections;
    }
  }

  /**
   * Get field-specific form configuration based on background selection
   * @param {string} fieldOfStudy - Selected field of study
   * @param {string} classLevel - Selected class level  
   * @param {string} learningGoals - Selected learning goals
   * @param {Object} adminConfig - Admin configuration
   * @returns {Object} Field-specific form configuration
   */
  static async getFieldSpecificFormConfig(fieldOfStudy, classLevel, learningGoals, adminConfig = {}) {
    try {
      // Import the dynamic field specific form configs
      const { generateFormConfigForField } = await import('./dynamicFieldSpecificFormConfigs');
      
      // Get the field-specific configuration
      const fieldConfig = generateFormConfigForField(fieldOfStudy, classLevel, learningGoals);
      
      // Create enhanced configuration with background selection
      const enhancedConfig = await this.createEnhancedFormConfig(
        fieldConfig,
        adminConfig.backgroundFields,
        adminConfig.includeBackground !== false
      );
      
      // Add metadata about the configuration
      enhancedConfig.metadata = {
        fieldOfStudy,
        classLevel,
        learningGoals,
        generatedAt: new Date().toISOString(),
        configType: 'field_specific'
      };
      
      return enhancedConfig;
    } catch (error) {
      console.error('Error generating field-specific form config:', error);
      throw error;
    }
  }

  /**
   * Check if background selection is complete in form data
   * @param {Object} formData - Current form data
   * @returns {boolean} Whether background selection is complete
   */
  static isBackgroundSelectionComplete(formData) {
    return !!(
      formData.field_of_study && 
      formData.class_level && 
      formData.learning_goals
    );
  }

  /**
   * Get next form section based on current progress
   * @param {Object} formData - Current form data
   * @param {Object} formConfig - Form configuration
   * @returns {string} Next section name or null if complete
   */
  static getNextSection(formData, formConfig) {
    const sections = formConfig.sections || {};
    const sectionOrder = ['background_selection', 'personal_info', 'academic_info', 'preferences'];
    
    for (const sectionName of sectionOrder) {
      if (!sections[sectionName]) continue;
      
      const sectionFields = sections[sectionName];
      const isComplete = sectionFields.every(field => {
        if (!field.required) return true;
        return formData[field.id] && formData[field.id] !== '';
      });
      
      if (!isComplete) {
        return sectionName;
      }
    }
    
    return null; // All sections complete
  }

  /**
   * Validate form data against configuration
   * @param {Object} formData - Form data to validate
   * @param {Object} formConfig - Form configuration
   * @returns {Object} Validation result with errors
   */
  static validateFormData(formData, formConfig) {
    const errors = {};
    
    formConfig.fields?.forEach(field => {
      const value = formData[field.id];
      
      // Required field validation
      if (field.required && (!value || value === '')) {
        errors[field.id] = `${field.label} is required`;
        return;
      }
      
      // Skip further validation if field is empty and not required
      if (!value || value === '') return;
      
      // Type-specific validation
      if (field.validation) {
        const validation = field.validation;
        
        // String length validation
        if (validation.minLength && value.length < validation.minLength) {
          errors[field.id] = `${field.label} must be at least ${validation.minLength} characters`;
        }
        
        if (validation.maxLength && value.length > validation.maxLength) {
          errors[field.id] = `${field.label} must be no more than ${validation.maxLength} characters`;
        }
        
        // Number validation
        if (validation.min && Number(value) < validation.min) {
          errors[field.id] = `${field.label} must be at least ${validation.min}`;
        }
        
        if (validation.max && Number(value) > validation.max) {
          errors[field.id] = `${field.label} must be no more than ${validation.max}`;
        }
        
        // Pattern validation
        if (validation.pattern && !new RegExp(validation.pattern).test(value)) {
          errors[field.id] = `${field.label} format is invalid`;
        }
      }
    });
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }
}

export default EnhancedFormConfigService;