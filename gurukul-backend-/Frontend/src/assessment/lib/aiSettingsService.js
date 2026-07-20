// AI Settings Service - Manages global AI enablement for the system
import { supabase } from './supabaseClient.js';

/**
 * Service to manage global AI settings that affect both admin and student experiences
 * When AI is disabled:
 * - Students see only admin-created questions
 * - AI question generation is skipped
 * - Grok service still works for other features (summaries, dashboard, etc.)
 */
class AISettingsService {
  constructor() {
    this.aiEnabled = true; // Default to enabled
    this.settingsLoaded = false;
    this.cacheTime = null;
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes cache
  }

  /**
   * Check if AI is globally enabled for question generation
   * @returns {Promise<boolean>}
   */
  async isAIEnabled() {
    try {
      // Check cache first
      if (this.settingsLoaded && this.cacheTime && (Date.now() - this.cacheTime) < this.cacheDuration) {
        return this.aiEnabled;
      }

      // Try to get setting from database (ai_settings table)
      const { data, error } = await supabase
        .from('ai_settings')
        .select('ai_enabled')
        .eq('setting_key', 'global_question_generation')
        .single();

      if (error && error.code === 'PGRST205') {
        console.warn('🤖 AI Settings table not found (PGRST205). Defaulting to false (local fallback mode).');
        this.aiEnabled = false;
        this.settingsLoaded = true;
        this.cacheTime = Date.now();
        return this.aiEnabled;
      }

      if (!error && data) {
        this.aiEnabled = data.ai_enabled;
        this.settingsLoaded = true;
        this.cacheTime = Date.now();
        console.log('🤖 AI Settings loaded from database:', { ai_enabled: this.aiEnabled });
        return this.aiEnabled;
      }

      // Fallback: check localStorage for admin override
      const localSetting = localStorage.getItem('ai_question_generation_enabled');
      if (localSetting !== null) {
        this.aiEnabled = localSetting === 'true';
        this.settingsLoaded = true;
        this.cacheTime = Date.now();
        console.log('🤖 AI Settings loaded from localStorage:', { ai_enabled: this.aiEnabled });
        return this.aiEnabled;
      }

      // Default to false (safe) if no setting found and no db table
      this.aiEnabled = false;
      this.settingsLoaded = true;
      this.cacheTime = Date.now();
      console.log('🤖 AI Settings defaulted to disabled for safety');
      return this.aiEnabled;

    } catch (error) {
      console.error('Error loading AI settings:', error);
      // Default to false on error 
      this.aiEnabled = false;
      return this.aiEnabled;
    }
  }

  /**
   * Set global AI enablement (admin only)
   * @param {boolean} enabled
   * @returns {Promise<boolean>} Success status
   */
  async setAIEnabled(enabled) {
    try {
      // Update database setting
      const { error } = await supabase
        .from('ai_settings')
        .upsert({
          setting_key: 'global_question_generation',
          ai_enabled: enabled,
          updated_at: new Date().toISOString()
        }, { onConflict: 'setting_key' });

      if (error) {
        console.error('Failed to update AI settings in database:', error);
        // Fallback to localStorage
        localStorage.setItem('ai_question_generation_enabled', enabled.toString());
      }

      // Update cache
      this.aiEnabled = enabled;
      this.settingsLoaded = true;
      this.cacheTime = Date.now();

      console.log(`🤖 AI question generation ${enabled ? 'enabled' : 'disabled'} globally`);
      return true;

    } catch (error) {
      console.error('Error setting AI enabled status:', error);

      // Fallback to localStorage
      try {
        localStorage.setItem('ai_question_generation_enabled', enabled.toString());
        this.aiEnabled = enabled;
        this.settingsLoaded = true;
        this.cacheTime = Date.now();
        return true;
      } catch {
        return false;
      }
    }
  }

  /**
   * Clear cache to force reload of settings
   */
  clearCache() {
    this.settingsLoaded = false;
    this.cacheTime = null;
  }

  /**
   * Get AI settings for display in admin panel
   * @returns {Promise<Object>}
   */
  async getAISettings() {
    const aiEnabled = await this.isAIEnabled();
    return {
      aiEnabled,
      lastUpdated: this.cacheTime ? new Date(this.cacheTime).toISOString() : null,
      source: this.settingsLoaded ? 'cache' : 'default'
    };
  }

  /**
   * Check if AI question generation should be used for a specific context
   * This method can be extended to support per-field or per-category AI settings
   * @returns {Promise<boolean>}
   */
  async shouldUseAIGeneration() {
    const globalEnabled = await this.isAIEnabled();

    // For now, all contexts use the global setting
    // Future enhancement: could have per-context settings
    return globalEnabled;
  }

  /**
   * Create default AI settings table if it doesn't exist
   * This should be called during app initialization
   */
  async initializeAISettings() {
    try {
      // Check if ai_settings table exists by trying to query it
      const { error: checkError } = await supabase
        .from('ai_settings')
        .select('setting_key')
        .limit(1);

      if (checkError && checkError.code === '42P01') {
        // Table doesn't exist - this is expected if not created yet
        console.log('🤖 AI settings table not found - using fallback storage');
        return;
      }

      // Ensure default setting exists
      const { error: selectError } = await supabase
        .from('ai_settings')
        .select('*')
        .eq('setting_key', 'global_question_generation')
        .single();

      if (selectError && selectError.code === 'PGRST116') {
        // Setting doesn't exist, create it
        const { error: insertError } = await supabase
          .from('ai_settings')
          .insert({
            setting_key: 'global_question_generation',
            ai_enabled: true,
            description: 'Global toggle for AI question generation in assignments',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          });

        if (!insertError) {
          console.log('🤖 Created default AI settings');
        }
      }

    } catch (error) {
      console.log('🤖 AI settings table not available, using fallback storage');
    }
  }
}

// Export singleton instance
export const aiSettingsService = new AISettingsService();
export default aiSettingsService;