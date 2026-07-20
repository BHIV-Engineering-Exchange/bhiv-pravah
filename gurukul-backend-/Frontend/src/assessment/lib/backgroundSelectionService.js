import { supabase } from './supabaseClient';
import { generateFormConfigForField } from './dynamicFieldSpecificFormConfigs';

const BACKGROUND_SELECTION_TABLE = 'background_selections';

export const backgroundSelectionService = {
  async saveBackgroundSelection(selection, userId = null) {
    try {
      let user_id = userId;

      if (!user_id) {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error('User not authenticated');
        user_id = user.id;
      }

      const selectionData = {
        user_id,
        field_of_study: selection.fieldOfStudy,
        class_level: selection.classLevel,
        learning_goals: selection.learningGoals,
        updated_at: new Date().toISOString()
      };

      const { data, error } = await supabase
        .from(BACKGROUND_SELECTION_TABLE)
        .upsert(selectionData, { onConflict: 'user_id' })
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error saving background selection:', error);
      throw error;
    }
  },

  async getBackgroundSelection(userId = null) {
    try {
      let user_id = userId;

      if (!user_id) {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return null;
        user_id = user.id;
      }

      const { data, error } = await supabase
        .from(BACKGROUND_SELECTION_TABLE)
        .select('*')
        .eq('user_id', user_id)
        .single();

      if (error && error.code !== 'PGRST116') throw error; // Ignore 'no rows found' error
      return data;
    } catch (error) {
      console.error('Error getting background selection:', error);
      return null;
    }
  },

  async hasBackgroundSelection(userId = null) {
    const selection = await this.getBackgroundSelection(userId);
    return !!selection;
  },

  async getFormConfigForUser(userId = null) {
    try {
      const selection = await this.getBackgroundSelection(userId);

      if (!selection) {
        // Return default form config if no background selection
        return null;
      }

      // Generate form configuration based on background selection (now async)
      const formConfig = await generateFormConfigForField(
        selection.field_of_study,
        selection.class_level,
        selection.learning_goals
      );

      return formConfig;
    } catch (error) {
      console.error('Error getting form config for user:', error);
      return null;
    }
  },

  async deleteBackgroundSelection(userId = null) {
    try {
      let user_id = userId;

      if (!user_id) {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error('User not authenticated');
        user_id = user.id;
      }

      const { error } = await supabase
        .from(BACKGROUND_SELECTION_TABLE)
        .delete()
        .eq('user_id', user_id);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error deleting background selection:', error);
      throw error;
    }
  }
};