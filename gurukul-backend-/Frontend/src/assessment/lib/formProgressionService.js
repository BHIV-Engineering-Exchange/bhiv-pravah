import { EnhancedFormConfigService } from './enhancedFormConfigService';
import toast from 'react-hot-toast';

/**
 * Service for managing seamless form progression and dynamic field updates
 * based on background selection and other conditional logic
 */
export class FormProgressionService {
  
  /**
   * Handle field change and determine if form should be updated dynamically
   * @param {string} fieldName - Name of the changed field
   * @param {any} fieldValue - New value of the field
   * @param {Object} formData - Current form data
   * @param {Object} currentConfig - Current form configuration
   * @param {Function} onConfigUpdate - Callback to update form configuration
   * @param {Function} onProgressUpdate - Callback to update progress
   * @returns {Promise<Object>} Updated form state
   */
  static async handleFieldChange(fieldName, fieldValue, formData, currentConfig, onConfigUpdate, onProgressUpdate) {
    const updatedFormData = { ...formData, [fieldName]: fieldValue };
    
    try {
      // Check if this is a background selection field
      if (['field_of_study', 'class_level', 'learning_goals'].includes(fieldName)) {
        return await this.handleBackgroundSelectionChange(
          updatedFormData, 
          currentConfig, 
          onConfigUpdate, 
          onProgressUpdate
        );
      }
      
      // Handle other conditional field changes
      return await this.handleConditionalFieldChange(
        fieldName,
        fieldValue,
        updatedFormData,
        currentConfig,
        onConfigUpdate
      );
      
    } catch (error) {
      console.error('Error handling field change:', error);
      return { formData: updatedFormData, configUpdated: false };
    }
  }
  
  /**
   * Handle background selection field changes
   */
  static async handleBackgroundSelectionChange(formData, currentConfig, onConfigUpdate, onProgressUpdate) {
    const isComplete = EnhancedFormConfigService.isBackgroundSelectionComplete(formData);
    
    if (isComplete) {
      try {
        // Show loading state
        onProgressUpdate && onProgressUpdate({
          stage: 'loading_personalization',
          message: 'Personalizing your form...'
        });
        
        // Load field-specific configuration
        const fieldSpecificConfig = await EnhancedFormConfigService.getFieldSpecificFormConfig(
          formData.field_of_study,
          formData.class_level,
          formData.learning_goals
        );
        
        // Update configuration
        if (onConfigUpdate) {
          onConfigUpdate(fieldSpecificConfig);
        }
        
        // Update progress
        onProgressUpdate && onProgressUpdate({
          stage: 'personalization_complete',
          message: 'Form personalized based on your background!'
        });
        
        // Show success message
        toast.success('Form personalized for your field of study!', {
          duration: 3000,
          icon: '🎯'
        });
        
        return {
          formData,
          configUpdated: true,
          newConfig: fieldSpecificConfig,
          progression: {
            backgroundComplete: true,
            nextSection: this.getNextSection(formData, fieldSpecificConfig)
          }
        };
        
      } catch (error) {
        console.error('Error loading field-specific configuration:', error);
        toast.error('Failed to personalize form. Using default configuration.');
        
        onProgressUpdate && onProgressUpdate({
          stage: 'personalization_error',
          message: 'Using default form configuration'
        });
        
        return { formData, configUpdated: false };
      }
    }
    
    // Background selection not yet complete
    onProgressUpdate && onProgressUpdate({
      stage: 'background_selection_in_progress',
      message: this.getBackgroundSelectionProgress(formData)
    });
    
    return { formData, configUpdated: false };
  }
  
  /**
   * Handle other conditional field changes
   */
  static async handleConditionalFieldChange(fieldName, fieldValue, formData, currentConfig, onConfigUpdate) {
    // Example: Show/hide fields based on education level
    if (fieldName === 'education_level') {
      return this.handleEducationLevelChange(fieldValue, formData, currentConfig, onConfigUpdate);
    }
    
    // Example: Update available options based on field of study
    if (fieldName === 'field_of_study') {
      return this.handleFieldOfStudyDependentFields(fieldValue, formData, currentConfig, onConfigUpdate);
    }
    
    return { formData, configUpdated: false };
  }
  
  /**
   * Handle education level dependent field visibility
   */
  static handleEducationLevelChange(educationLevel, formData, currentConfig, onConfigUpdate) {
    const updatedConfig = { ...currentConfig };
    let configUpdated = false;
    
    // Example: Show work experience fields for professional level
    if (educationLevel === 'professional') {
      const hasWorkExperienceField = updatedConfig.fields.some(f => f.id === 'work_experience');
      
      if (!hasWorkExperienceField) {
        updatedConfig.fields.push({
          id: 'work_experience',
          type: 'textarea',
          label: 'Work Experience',
          placeholder: 'Describe your relevant work experience',
          required: false,
          order: 100,
          section: 'academic_info'
        });
        configUpdated = true;
      }
    } else {
      // Remove work experience field for non-professionals
      const originalLength = updatedConfig.fields.length;
      updatedConfig.fields = updatedConfig.fields.filter(f => f.id !== 'work_experience');
      configUpdated = updatedConfig.fields.length !== originalLength;
    }
    
    if (configUpdated && onConfigUpdate) {
      onConfigUpdate(updatedConfig);
    }
    
    return { formData, configUpdated, newConfig: configUpdated ? updatedConfig : null };
  }
  
  /**
   * Get background selection progress message
   */
  static getBackgroundSelectionProgress(formData) {
    const completed = [];
    const remaining = [];
    
    if (formData.field_of_study) completed.push('Field of Study');
    else remaining.push('Field of Study');
    
    if (formData.class_level) completed.push('Education Level');
    else remaining.push('Education Level');
    
    if (formData.learning_goals) completed.push('Learning Goals');
    else remaining.push('Learning Goals');
    
    if (remaining.length === 0) {
      return 'Background selection complete!';
    }
    
    return `Complete: ${completed.join(', ')} | Remaining: ${remaining.join(', ')}`;
  }
  
  /**
   * Get next section user should focus on
   */
  static getNextSection(formData, formConfig) {
    return EnhancedFormConfigService.getNextSection(formData, formConfig);
  }
  
  /**
   * Validate current form section completion
   */
  static validateSectionCompletion(sectionName, formData, formConfig) {
    const sectionFields = formConfig.fields?.filter(field => 
      field.section === sectionName && field.required
    ) || [];
    
    const completedFields = sectionFields.filter(field => {
      const value = formData[field.id];
      return value && value !== '' && !(Array.isArray(value) && value.length === 0);
    });
    
    return {
      isComplete: completedFields.length === sectionFields.length,
      completedCount: completedFields.length,
      totalCount: sectionFields.length,
      missingFields: sectionFields
        .filter(field => {
          const value = formData[field.id];
          return !value || value === '' || (Array.isArray(value) && value.length === 0);
        })
        .map(field => field.label)
    };
  }
  
  /**
   * Get form completion percentage
   */
  static getFormCompletionPercentage(formData, formConfig) {
    const requiredFields = formConfig.fields?.filter(field => field.required) || [];
    
    if (requiredFields.length === 0) return 100;
    
    const completedFields = requiredFields.filter(field => {
      const value = formData[field.id];
      return value && value !== '' && !(Array.isArray(value) && value.length === 0);
    });
    
    return Math.round((completedFields.length / requiredFields.length) * 100);
  }
  
  /**
   * Get form submission readiness
   */
  static getSubmissionReadiness(formData, formConfig) {
    const percentage = this.getFormCompletionPercentage(formData, formConfig);
    const validation = EnhancedFormConfigService.validateFormData(formData, formConfig);
    
    return {
      isReady: validation.isValid && percentage === 100,
      completionPercentage: percentage,
      validationErrors: validation.errors,
      canSubmit: validation.isValid
    };
  }
}

export default FormProgressionService;"