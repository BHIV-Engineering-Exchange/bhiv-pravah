import { supabase } from './supabaseClient';

/**
 * Dynamic Category Service - Manages form categories/sections dynamically from database
 * Similar to DynamicFieldService but for form organization and sections
 */
export class DynamicCategoryService {
  static instance = null;
  static categories = [];
  static categoryMap = new Map();
  static initialized = false;

  static getInstance() {
    if (!this.instance) {
      this.instance = new DynamicCategoryService();
    }
    return this.instance;
  }

  /**
   * Initialize the service by loading categories from database
   */
  static async initialize() {
    if (this.initialized) return;
    
    try {
      await this.loadCategories();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize DynamicCategoryService:', error);
      // Fallback to default categories if database fails
      this.initializeFallbackCategories();
      this.initialized = true;
    }
  }

  /**
   * Load all active categories from database
   */
  static async loadCategories() {
    const { data, error } = await supabase
      .from('form_categories')
      .select('*')
      .eq('is_active', true)
      .order('display_order', { ascending: true });

    if (error) throw error;

    this.categories = data || [];
    this.buildCategoryMap();
    
    console.log(`Loaded ${this.categories.length} dynamic form categories`);
    return this.categories;
  }

  /**
   * Build internal category map for quick lookups
   */
  static buildCategoryMap() {
    this.categoryMap.clear();
    this.categories.forEach(category => {
      this.categoryMap.set(category.category_id, category);
      // Also map by name for backward compatibility
      this.categoryMap.set(category.name.toLowerCase(), category);
    });
  }

  /**
   * Fallback categories if database is unavailable
   */
  static initializeFallbackCategories() {
    this.categories = [
      {
        category_id: 'background_selection',
        name: 'Background Selection',
        description: 'Tell us about your academic background and goals',
        icon: 'GraduationCap',
        color: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
        display_order: -3,
        is_active: true,
        is_system: true
      },
      {
        category_id: 'personal_info',
        name: 'Personal Information',
        description: 'Basic information about you',
        icon: 'User',
        color: 'text-green-400 bg-green-400/10 border-green-400/20',
        display_order: 0,
        is_active: true,
        is_system: true
      },
      {
        category_id: 'academic_info',
        name: 'Academic Details',
        description: 'Your educational background and preferences',
        icon: 'BookOpen',
        color: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
        display_order: 1,
        is_active: true,
        is_system: true
      },
      {
        category_id: 'preferences',
        name: 'Learning Preferences',
        description: 'How you prefer to learn',
        icon: 'Settings',
        color: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
        display_order: 2,
        is_active: true,
        is_system: true
      },
      {
        category_id: 'general',
        name: 'Additional Information',
        description: 'Other relevant details',
        icon: 'FileText',
        color: 'text-gray-400 bg-gray-400/10 border-gray-400/20',
        display_order: 3,
        is_active: true,
        is_system: true
      }
    ];
    this.buildCategoryMap();
  }

  /**
   * Get all active categories
   */
  static async getAllCategories() {
    if (!this.initialized) await this.initialize();
    return this.categories;
  }

  /**
   * Get category by ID
   */
  static async getCategoryById(categoryId) {
    if (!this.initialized) await this.initialize();
    return this.categoryMap.get(categoryId) || null;
  }

  /**
   * Get category by name (case insensitive)
   */
  static async getCategoryByName(name) {
    if (!this.initialized) await this.initialize();
    return this.categoryMap.get(name.toLowerCase()) || null;
  }

  /**
   * Get categories for dropdown/selection components
   */
  static async getCategoryOptions() {
    const categories = await this.getAllCategories();
    return categories.map(category => ({
      value: category.category_id,
      label: `${category.icon ? category.icon + ' ' : ''}${category.name}`,
      description: category.description,
      icon: category.icon,
      color: category.color
    }));
  }

  /**
   * Get organized sections object for form configuration
   * Maintains compatibility with existing form system
   */
  static async getOrganizedSections() {
    const categories = await this.getAllCategories();
    const sections = {};
    
    categories.forEach(category => {
      sections[category.category_id] = {
        title: category.name,
        description: category.description,
        icon: category.icon,
        order: category.display_order,
        color: category.color,
        isSystem: category.is_system
      };
    });
    
    return sections;
  }

  /**
   * Create a new category if it doesn't exist
   * Used for dynamic section creation in forms
   */
  static async ensureCategoryExists(categoryId, categoryData = {}) {
    const existing = await this.getCategoryById(categoryId);
    if (existing) return existing;
    
    // Create basic category data
    const defaultCategory = {
      category_id: categoryId,
      name: categoryData.name || categoryId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      description: categoryData.description || `Section for ${categoryId} fields`,
      icon: categoryData.icon || 'Settings',
      color: categoryData.color || 'text-gray-400 bg-gray-400/10 border-gray-400/20',
      display_order: categoryData.order || 10,
      is_active: true,
      is_system: false
    };
    
    // Add to local cache first (for immediate use)
    this.categories.push(defaultCategory);
    this.buildCategoryMap();
    
    // Try to persist to database (non-blocking)
    try {
      await this.addCategory(defaultCategory);
    } catch (error) {
      console.warn(`Could not persist category ${categoryId} to database:`, error);
    }
    
    return defaultCategory;
  }

  /**
   * Detect appropriate category from field metadata
   */
  static async detectCategoryFromField(field) {
    const fieldId = field.id?.toLowerCase() || '';
    const fieldLabel = field.label?.toLowerCase() || '';
    const fieldSection = field.section;
    
    // If field already has a section, use it
    if (fieldSection) {
      return await this.ensureCategoryExists(fieldSection);
    }
    
    // Define category mapping based on common field patterns
    const categoryMappings = {
      'background_selection': ['field_of_study', 'class_level', 'learning_goals'],
      'personal_info': ['name', 'email', 'phone', 'age', 'gender'],
      'academic_info': ['education', 'grade', 'school', 'major', 'gpa', 'year'],
      'preferences': ['style', 'pace', 'schedule', 'preference', 'availability'],
      'general': ['other', 'additional', 'comments', 'notes']
    };
    
    // Find matching category
    for (const [categoryId, keywords] of Object.entries(categoryMappings)) {
      if (keywords.some(keyword => 
        fieldId.includes(keyword) || fieldLabel.includes(keyword)
      )) {
        return await this.getCategoryById(categoryId);
      }
    }
    
    // Default to general category
    return await this.getCategoryById('general');
  }

  /**
   * Get category statistics (field counts, usage, etc.)
   */
  static async getCategoryStatistics() {
    const categories = await this.getAllCategories();
    const stats = {};

    for (const category of categories) {
      stats[category.category_id] = {
        ...category,
        fieldCount: 0, // Will be populated when integrated with form configs
        usageCount: 0
      };
    }

    return stats;
  }

  /**
   * Refresh categories from database
   */
  static async refresh() {
    this.initialized = false;
    await this.initialize();
  }

  /**
   * Add a new category (admin function)
   */
  static async addCategory(categoryData) {
    const { data, error } = await supabase
      .from('form_categories')
      .insert([{
        category_id: categoryData.category_id,
        name: categoryData.name,
        description: categoryData.description,
        icon: categoryData.icon,
        color: categoryData.color,
        display_order: categoryData.display_order || 0,
        is_active: true,
        is_system: false,
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
   * Update a category (admin function)
   */
  static async updateCategory(categoryId, updates) {
    const { data, error } = await supabase
      .from('form_categories')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('category_id', categoryId)
      .select()
      .single();

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return data;
  }

  /**
   * Delete a category (admin function)
   * System categories cannot be deleted
   */
  static async deleteCategory(categoryId) {
    // Check if it's a system category
    const category = await this.getCategoryById(categoryId);
    if (category?.is_system) {
      throw new Error(`Cannot delete system category: ${categoryId}`);
    }

    // TODO: Check if category has fields assigned when form system is integrated
    // For now, allow deletion
    
    const { error } = await supabase
      .from('form_categories')
      .delete()
      .eq('category_id', categoryId);

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return true;
  }

  /**
   * Reorder categories (admin function)
   */
  static async reorderCategories(categoryOrders) {
    const updates = categoryOrders.map(({ categoryId, order }) => ({
      category_id: categoryId,
      display_order: order,
      updated_at: new Date().toISOString()
    }));

    const { error } = await supabase
      .from('form_categories')
      .upsert(updates, { onConflict: 'category_id' });

    if (error) throw error;

    // Refresh local cache
    await this.refresh();
    return true;
  }

  /**
   * Toggle category active status (admin function)
   */
  static async toggleCategoryStatus(categoryId, isActive) {
    return await this.updateCategory(categoryId, { is_active: isActive });
  }
}

// Export convenience functions
export const {
  initialize,
  getAllCategories,
  getCategoryById,
  getCategoryByName,
  getCategoryOptions,
  getOrganizedSections,
  ensureCategoryExists,
  detectCategoryFromField,
  getCategoryStatistics,
  refresh,
  addCategory,
  updateCategory,
  deleteCategory,
  reorderCategories,
  toggleCategoryStatus
} = DynamicCategoryService;

export default DynamicCategoryService;