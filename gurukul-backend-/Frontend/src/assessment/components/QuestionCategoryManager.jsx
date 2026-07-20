import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Save, X, ArrowUp, ArrowDown, Code, Brain, Calculator, MessageCircle, Globe, BookOpen, Newspaper, HelpCircle, Target, Clock, Star, Shield, Heart, Palette, Database, Music, Camera, Calendar, Home, Mail, Phone } from 'lucide-react';
import toast from 'react-hot-toast';
import { DynamicQuestionCategoryService } from '../lib/dynamicQuestionCategoryService';
import { supabase } from '../lib/supabaseClient';

const QuestionCategoryManager = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    category_id: '',
    name: '',
    description: '',
    icon: 'HelpCircle',
    color: 'text-gray-400 bg-gray-400/10 border-gray-400/20',
    display_order: 0
  });

  // Available icons for question categories
  const availableIcons = [
    'Code', 'Brain', 'Calculator', 'MessageCircle', 'Globe', 'BookOpen', 'Newspaper',
    'HelpCircle', 'Target', 'Clock', 'Star', 'Shield', 'Heart', 'Palette', 'Database',
    'Music', 'Camera', 'Calendar', 'Home', 'Mail', 'Phone'
  ];

  // Icon components mapping
  const iconComponents = {
    Code, Brain, Calculator, MessageCircle, Globe, BookOpen, Newspaper,
    HelpCircle, Target, Clock, Star, Shield, Heart, Palette, Database,
    Music, Camera, Calendar, Home, Mail, Phone
  };

  // Available color schemes for question categories
  const colorSchemes = [
    { name: 'Blue', value: 'text-blue-400 bg-blue-400/10 border-blue-400/20' },
    { name: 'Green', value: 'text-green-400 bg-green-400/10 border-green-400/20' },
    { name: 'Purple', value: 'text-purple-400 bg-purple-400/10 border-purple-400/20' },
    { name: 'Red', value: 'text-red-400 bg-red-400/10 border-red-400/20' },
    { name: 'Orange', value: 'text-orange-400 bg-orange-400/10 border-orange-400/20' },
    { name: 'Pink', value: 'text-pink-400 bg-pink-400/10 border-pink-400/20' },
    { name: 'Yellow', value: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20' },
    { name: 'Cyan', value: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20' },
    { name: 'Indigo', value: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20' },
    { name: 'Teal', value: 'text-teal-400 bg-teal-400/10 border-teal-400/20' },
    { name: 'Gray', value: 'text-gray-400 bg-gray-400/10 border-gray-400/20' }
  ];

  useEffect(() => {
    loadCategories();
  }, []);

  // Realtime updates: refresh when categories change in DB
  useEffect(() => {
    const channel = supabase
      .channel('question_categories_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'question_categories' },
        () => {
          // Ensure we always fetch fresh data after any change
          loadCategories();
        }
      )
      .subscribe();

    return () => {
      try { supabase.removeChannel(channel); } catch {}
    };
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const categoryList = await DynamicQuestionCategoryService.loadCategories();
      setCategories(categoryList);
    } catch (error) {
      console.error('Error loading question categories:', error);
      toast.error('Failed to load question categories');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = async (data) => {
    try {
      const input = data || formData;

      // Validate required fields
      if (!input.name || input.name.trim() === '') {
        toast.error('Name is required');
        return;
      }

      
      // Generate a slugified, unique category_id if missing
      const slugify = (str) =>
        (str || '')
          .toLowerCase()
          .trim()
          .replace(/[^a-z0-9]+/g, '_')
          .replace(/^_+|_+$/g, '')
          .replace(/_+/g, '_')
          .slice(0, 100);

      const maxLen = 100;
      let baseId = input.category_id && input.category_id.trim()
        ? slugify(input.category_id)
        : slugify(input.name) || `category_${Date.now()}`;
      if (!baseId) baseId = `category_${Date.now()}`;

      // Ensure uniqueness against currently loaded categories
      const existingIds = new Set(categories.map(c => c.category_id));
      let uniqueId = baseId;
      let suffix = 2;
      while (existingIds.has(uniqueId)) {
        const suffixStr = `_${suffix}`;
        const trimmedBase = baseId.slice(0, Math.max(1, maxLen - suffixStr.length));
        uniqueId = `${trimmedBase}${suffixStr}`;
        suffix++;
      }

      const newCategory = {
        ...input,
        category_id: uniqueId,
        display_order: typeof input.display_order === 'number' ? input.display_order : categories.length
      };

      await DynamicQuestionCategoryService.addCategory(newCategory);
      toast.success('Question category added successfully');
      setShowAddForm(false);
      setFormData({
        category_id: '',
        name: '',
        description: '',
        icon: 'HelpCircle',
        color: 'text-gray-400 bg-gray-400/10 border-gray-400/20',
        display_order: 0
      });
      await loadCategories();
    } catch (error) {
      console.error('Error adding question category:', error);
      toast.error('Failed to add question category');
    }
  };

  const handleUpdateCategory = async (categoryId, updates) => {
    try {
      
      const { category_id, ...rest } = updates;
      await DynamicQuestionCategoryService.updateCategory(categoryId, rest);
      toast.success('Question category updated successfully');
      setEditingCategory(null);
      await loadCategories();
    } catch (error) {
      console.error('Error updating question category:', error);
      toast.error('Failed to update question category');
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    try {
      if (!confirm('Are you sure you want to delete this question category? This will affect all questions assigned to this category.')) {
        return;
      }

      await DynamicQuestionCategoryService.deleteCategory(categoryId);
      toast.success('Question category deleted successfully');
      await loadCategories();
    } catch (error) {
      console.error('Error deleting question category:', error);
      toast.error(error.message || 'Failed to delete question category');
    }
  };

  const handleToggleStatus = async (categoryId, currentStatus) => {
    try {
      await DynamicQuestionCategoryService.toggleCategoryStatus(categoryId, !currentStatus);
      toast.success(`Question category ${!currentStatus ? 'activated' : 'deactivated'}`);
      await loadCategories();
    } catch (error) {
      console.error('Error toggling question category status:', error);
      toast.error('Failed to update question category status');
    }
  };

  const handleReorder = async (categoryId, direction) => {
    try {
      const categoryIndex = categories.findIndex(cat => cat.category_id === categoryId);
      if (categoryIndex === -1) return;

      const newCategories = [...categories];
      const targetIndex = direction === 'up' ? categoryIndex - 1 : categoryIndex + 1;
      
      if (targetIndex < 0 || targetIndex >= newCategories.length) return;

      // Swap the categories
      [newCategories[categoryIndex], newCategories[targetIndex]] = 
      [newCategories[targetIndex], newCategories[categoryIndex]];

      // Update display orders
      const reorderData = newCategories.map((cat, index) => ({
        categoryId: cat.category_id,
        order: index
      }));

      await DynamicQuestionCategoryService.reorderCategories(reorderData);
      toast.success('Question categories reordered successfully');
      await loadCategories();
    } catch (error) {
      console.error('Error reordering question categories:', error);
      toast.error('Failed to reorder question categories');
    }
  };

  const CategoryForm = ({ category, onSave, onCancel }) => {
    const [localFormData, setLocalFormData] = useState(
      category || {
        category_id: '',
        name: '',
        description: '',
        icon: 'HelpCircle',
        color: 'text-gray-400 bg-gray-400/10 border-gray-400/20',
        display_order: categories.length
      }
    );

    const handleSubmit = () => {
      onSave(localFormData);
    };

    const IconComponent = iconComponents[localFormData.icon] || HelpCircle;

    return (
      <div className="space-y-4 p-4 bg-white/5 rounded-lg border border-white/20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {category && (
          <div>
            <label className="block text-sm text-white/80 mb-2">Category ID</label>
            <input
              type="text"
              value={localFormData.category_id}
              onChange={(e) => setLocalFormData(prev => ({ ...prev, category_id: e.target.value }))}
              disabled={!!category} // Can't change ID when editing
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400"
              placeholder="unique_category_id"
            />
          </div>
          )}

          <div>
            <label className="block text-sm text-white/80 mb-2">Name</label>
            <input
              type="text"
              value={localFormData.name}
              onChange={(e) => setLocalFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400"
              placeholder="Category Name"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-white/80 mb-2">Description</label>
          <textarea
            value={localFormData.description}
            onChange={(e) => setLocalFormData(prev => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400"
            placeholder="Brief description of this question category"
            rows={2}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-white/80 mb-2">Icon</label>
            <div className="relative">
              <select
                value={localFormData.icon}
                onChange={(e) => setLocalFormData(prev => ({ ...prev, icon: e.target.value }))}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-400 appearance-none"
              >
                {availableIcons.map(icon => (
                  <option key={icon} value={icon} className="bg-gray-800">
                    {icon}
                  </option>
                ))}
              </select>
              <div className="absolute right-8 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <IconComponent className="w-4 h-4 text-white/60" />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm text-white/80 mb-2">Color Scheme</label>
            <select
              value={localFormData.color}
              onChange={(e) => setLocalFormData(prev => ({ ...prev, color: e.target.value }))}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-400"
            >
              {colorSchemes.map(scheme => (
                <option key={scheme.value} value={scheme.value} className="bg-gray-800">
                  {scheme.name}
                </option>
              ))}
            </select>
          </div>

                  </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-white/70 hover:text-white transition-colors"
          >
            <X className="w-4 h-4 inline mr-1" />
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
          >
            <Save className="w-4 h-4 inline mr-1" />
            Save
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-white">Question Categories</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Category
        </button>
      </div>

      {showAddForm && (
        <CategoryForm
          onSave={handleAddCategory}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      <div className="space-y-3">
        {categories.map((category, index) => {
          const IconComponent = iconComponents[category.icon] || HelpCircle;
          
          return (
            <div
              key={category.category_id}
              className={`p-4 rounded-lg border transition-colors ${
                category.is_active 
                  ? 'bg-white/5 border-white/20' 
                  : 'bg-white/2 border-white/10 opacity-60'
              }`}
            >
              {editingCategory === category.category_id ? (
                <CategoryForm
                  category={category}
                  onSave={(data) => handleUpdateCategory(category.category_id, data)}
                  onCancel={() => setEditingCategory(null)}
                />
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-md ${category.color}`}>
                      <IconComponent className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-white">{category.name}</h3>
                        <span className="text-xs px-2 py-1 bg-white/10 rounded text-white/70">
                          {category.category_id}
                        </span>
                        {category.is_system && (
                          <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                            System
                          </span>
                        )}
                        {!category.is_active && (
                          <span className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded">
                            Inactive
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-white/70">{category.description}</p>
                      <div className="text-xs text-white/50 mt-1">
                        Order: {category.display_order} | Icon: {category.icon}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleReorder(category.category_id, 'up')}
                      disabled={index === 0}
                      className="p-1 text-white/50 hover:text-white disabled:opacity-30"
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleReorder(category.category_id, 'down')}
                      disabled={index === categories.length - 1}
                      className="p-1 text-white/50 hover:text-white disabled:opacity-30"
                    >
                      <ArrowDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingCategory(category.category_id)}
                      className="p-2 text-white/70 hover:text-white transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleToggleStatus(category.category_id, category.is_active)}
                      className={`px-3 py-1 text-xs rounded transition-colors ${
                        category.is_active
                          ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                          : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                      }`}
                    >
                      {category.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    {!category.is_system && (
                      <button
                        onClick={() => handleDeleteCategory(category.category_id)}
                        className="p-2 text-red-400 hover:text-red-300 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {categories.length === 0 && (
        <div className="text-center py-8 text-white/70">
          <HelpCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No question categories found. Add your first category to get started.</p>
        </div>
      )}
    </div>
  );
};

export default QuestionCategoryManager;