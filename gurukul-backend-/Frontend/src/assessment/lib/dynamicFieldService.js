import { supabase } from './supabaseClient';

/**
 * Dynamic Field Service - Manages study fields dynamically from database
 * Replaces all hardcoded field references with database-driven approach
 */
export class DynamicFieldService {
  static instance = null;
  static fields = [];
  static fieldMap = new Map();
  static initialized = false;

  static getInstance() {
    if (!this.instance) {
      this.instance = new DynamicFieldService();
    }
    return this.instance;
  }

  /**
   * Initialize the service by loading fields from database
   */
  static async initialize() {
    if (this.initialized) return;

    try {
      await this.loadFields();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize DynamicFieldService:', error);
      // Fallback to default fields if database fails
      this.initializeFallbackFields();
      this.initialized = true;
    }
  }

  /**
   * Load all active study fields from database
   */
  static async loadFields() {
    const { data, error } = await supabase
      .from('study_fields')
      .select('*')
      .eq('is_active', true)
      .order('created_at', { ascending: true });

    if (error) throw error;

    this.fields = data || [];

    // Fall back to defaults if the table is empty
    if (this.fields.length === 0) {
      console.log('No study fields found in database, using fallbacks');
      this.initializeFallbackFields();
      return this.fields;
    }

    this.buildFieldMap();

    console.log(`Loaded ${this.fields.length} dynamic study fields`);
    return this.fields;
  }

  /**
   * Build internal field map for quick lookups
   */
  static buildFieldMap() {
    this.fieldMap.clear();
    this.fields.forEach(field => {
      this.fieldMap.set(field.field_id, field);
      // Also map by name for backward compatibility
      this.fieldMap.set(field.name.toLowerCase(), field);
    });
  }

  /**
   * Fallback fields if database is unavailable
   */
  static initializeFallbackFields() {
    this.fields = [
      {
        field_id: 'stem',
        name: 'STEM',
        icon: '🔬',
        description: 'Science, Technology, Engineering, and Mathematics',
        color: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
        is_active: true
      },
      {
        field_id: 'business',
        name: 'Business',
        icon: '💼',
        description: 'Business and Economics',
        color: 'text-green-400 bg-green-400/10 border-green-400/20',
        is_active: true
      },
      {
        field_id: 'social_sciences',
        name: 'Social Sciences',
        icon: '🏛️',
        description: 'Social Sciences and Humanities',
        color: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
        is_active: true
      },
      {
        field_id: 'health_medicine',
        name: 'Health & Medicine',
        icon: '⚕️',
        description: 'Healthcare and Medical Sciences',
        color: 'text-red-400 bg-red-400/10 border-red-400/20',
        is_active: true
      },
      {
        field_id: 'creative_arts',
        name: 'Creative Arts',
        icon: '🎨',
        description: 'Arts, Design, and Creative Fields',
        color: 'text-pink-400 bg-pink-400/10 border-pink-400/20',
        is_active: true
      }
    ];
    this.buildFieldMap();
  }

  /**
   * Get all active study fields
   */
  static async getAllFields() {
    if (!this.initialized) await this.initialize();
    return this.fields;
  }

  /**
   * Get field by ID
   */
  static async getFieldById(fieldId) {
    if (!this.initialized) await this.initialize();
    return this.fieldMap.get(fieldId) || null;
  }

  /**
   * Get field by name (case insensitive)
   */
  static async getFieldByName(name) {
    if (!this.initialized) await this.initialize();
    return this.fieldMap.get(name.toLowerCase()) || null;
  }

  /**
   * Get fields for dropdown/selection components
   */
  static async getFieldOptions() {
    const fields = await this.getAllFields();
    return fields.map(field => ({
      value: field.field_id,
      label: `${field.icon} ${field.name}`,
      description: field.description
    }));
  }

  /**
   * Get field statistics (question counts, etc.)
   */
  static async getFieldStatistics() {
    const fields = await this.getAllFields();
    const stats = {};

    for (const field of fields) {
      try {
        // Get question count for this field
        const { count, error } = await supabase
          .from('question_field_mapping')
          .select('*', { count: 'exact', head: true })
          .eq('field_id', field.field_id);

        if (!error) {
          stats[field.field_id] = {
            ...field,
            questionCount: count || 0
          };
        }
      } catch (error) {
        console.error(`Error getting stats for field ${field.field_id}:`, error);
        stats[field.field_id] = {
          ...field,
          questionCount: 0
        };
      }
    }

    return stats;
  }

  /**
   * Detect field from user input (background, interests, etc.)
   */
  static async detectFieldFromText(text) {
    if (!text) return null;

    const fields = await this.getAllFields();
    const normalizedText = text.toLowerCase();

    // Define keywords for each field type
    const fieldKeywords = {
      stem: [
        'computer', 'software', 'programming', 'coding', 'developer', 'data science',
        'engineering', 'mathematics', 'physics', 'chemistry', 'biology', 'technology',
        'science', 'math', 'algorithm', 'ai', 'machine learning', 'robotics'
      ],
      business: [
        'business', 'finance', 'marketing', 'economics', 'management', 'entrepreneurship',
        'accounting', 'mba', 'sales', 'operations', 'supply chain', 'hr', 'commerce'
      ],
      social_sciences: [
        'psychology', 'sociology', 'political', 'anthropology', 'history', 'philosophy',
        'social work', 'criminology', 'geography', 'international relations'
      ],
      health_medicine: [
        'medicine', 'medical', 'health', 'nursing', 'pharmacy', 'doctor', 'healthcare',
        'biology', 'anatomy', 'physiology', 'dentistry', 'veterinary'
      ],
      creative_arts: [
        'art', 'design', 'music', 'theater', 'film', 'creative', 'literature',
        'writing', 'painting', 'sculpture', 'photography', 'dance'
      ]
    };

    // Score each field based on keyword matches
    const fieldScores = {};

    for (const field of fields) {
      const keywords = fieldKeywords[field.field_id] || [];
      let score = 0;

      // Check field name match
      if (normalizedText.includes(field.name.toLowerCase())) {
        score += 10;
      }

      // Check description match
      if (field.description && normalizedText.includes(field.description.toLowerCase())) {
        score += 5;
      }

      // Check keyword matches
      keywords.forEach(keyword => {
        if (normalizedText.includes(keyword)) {
          score += 1;
        }
      });

      if (score > 0) {
        fieldScores[field.field_id] = score;
      }
    }

    // Return field with highest score
    if (Object.keys(fieldScores).length === 0) return null;

    const bestFieldId = Object.keys(fieldScores).reduce((a, b) =>
      fieldScores[a] > fieldScores[b] ? a : b
    );

    return await this.getFieldById(bestFieldId);
  }

  /**
   * Get question weights for a field (for AI generation)
   */
  static async getQuestionWeights(fieldId) {
    const field = await this.getFieldById(fieldId);
    if (!field) return this.getDefaultQuestionWeights();

    // Default weights based on field type
    const defaultWeights = {
      stem: {
        'Coding': 35,
        'Logic': 25,
        'Mathematics': 25,
        'Language': 5,
        'Culture': 5,
        'Vedic Knowledge': 3,
        'Current Affairs': 2
      },
      business: {
        'Logic': 30,
        'Current Affairs': 25,
        'Language': 20,
        'Mathematics': 10,
        'Culture': 10,
        'Coding': 3,
        'Vedic Knowledge': 2
      },
      social_sciences: {
        'Language': 30,
        'Culture': 25,
        'Current Affairs': 20,
        'Logic': 15,
        'Vedic Knowledge': 5,
        'Mathematics': 3,
        'Coding': 2
      },
      health_medicine: {
        'Logic': 30,
        'Current Affairs': 20,
        'Language': 20,
        'Mathematics': 15,
        'Vedic Knowledge': 8,
        'Culture': 5,
        'Coding': 2
      },
      creative_arts: {
        'Language': 35,
        'Culture': 25,
        'Vedic Knowledge': 15,
        'Current Affairs': 10,
        'Logic': 10,
        'Mathematics': 3,
        'Coding': 2
      }
    };

    return defaultWeights[fieldId] || this.getDefaultQuestionWeights();
  }

  /**
   * Get difficulty distribution for a field
   */
  static async getDifficultyDistribution(fieldId) {
    const field = await this.getFieldById(fieldId);
    if (!field) return this.getDefaultDifficultyDistribution();

    // Default distributions based on field type
    const defaultDistributions = {
      stem: { easy: 25, medium: 50, hard: 25 },
      business: { easy: 30, medium: 50, hard: 20 },
      social_sciences: { easy: 35, medium: 45, hard: 20 },
      health_medicine: { easy: 30, medium: 50, hard: 20 },
      creative_arts: { easy: 35, medium: 45, hard: 20 }
    };

    return defaultDistributions[fieldId] || this.getDefaultDifficultyDistribution();
  }

  /**
   * Default question weights
   */
  static getDefaultQuestionWeights() {
    return {
      'Language': 20,
      'Logic': 20,
      'Current Affairs': 20,
      'Culture': 15,
      'Mathematics': 10,
      'Vedic Knowledge': 10,
      'Coding': 5
    };
  }

  /**
   * Default difficulty distribution
   */
  static getDefaultDifficultyDistribution() {
    return { easy: 30, medium: 50, hard: 20 };
  }

  /**
   * Refresh fields from database
   */
  static async refresh() {
    this.initialized = false;
    await this.initialize();
  }

  /**
   * Add a new field (admin function)
   */
  static async addField(fieldData) {
    const { data, error } = await supabase
      .from('study_fields')
      .insert([{
        field_id: fieldData.field_id,
        name: fieldData.name,
        icon: fieldData.icon,
        description: fieldData.description,
        color: fieldData.color,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return data;
  }

  /**
   * Update a field (admin function)
   */
  static async updateField(fieldId, updates) {
    const { data, error } = await supabase
      .from('study_fields')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('field_id', fieldId)
      .select()
      .single();

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return data;
  }

  /**
   * Delete a field (admin function)
   */
  static async deleteField(fieldId) {
    // Check if field has questions assigned
    const { count } = await supabase
      .from('question_field_mapping')
      .select('*', { count: 'exact', head: true })
      .eq('field_id', fieldId);

    if (count > 0) {
      throw new Error(`Cannot delete field - it has ${count} questions assigned`);
    }

    const { error } = await supabase
      .from('study_fields')
      .delete()
      .eq('field_id', fieldId);

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return true;
  }
}

// Export convenience functions
export const {
  initialize,
  getAllFields,
  getFieldById,
  getFieldByName,
  getFieldOptions,
  getFieldStatistics,
  detectFieldFromText,
  getQuestionWeights,
  getDifficultyDistribution,
  refresh,
  addField,
  updateField,
  deleteField
} = DynamicFieldService;