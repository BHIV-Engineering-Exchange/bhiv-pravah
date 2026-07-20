import React from 'react';
import { GraduationCap, BookOpen, Target, Settings } from 'lucide-react';

const BackgroundSelectionConfig = ({ config, includeBackground, onConfigChange, onIncludeChange }) => {
  const backgroundFields = [
    { key: 'field_of_study', label: 'Field of Study', icon: BookOpen },
    { key: 'class_level', label: 'Education Level', icon: GraduationCap },
    { key: 'learning_goals', label: 'Learning Goals', icon: Target }
  ];

  const updateFieldConfig = (fieldKey, property, value) => {
    const newConfig = {
      ...config,
      [fieldKey]: { ...config[fieldKey], [property]: value }
    };
    onConfigChange(newConfig);
  };

  return (
    <div className=\"space-y-6\">
      <div className=\"flex items-center justify-between\">
        <h3 className=\"text-lg font-semibold text-white flex items-center gap-2\">
          <GraduationCap className=\"w-5 h-5 text-orange-400\" />
          Background Selection
        </h3>
        
        <label className=\"flex items-center gap-2 cursor-pointer\">
          <span className=\"text-white text-sm\">Enable</span>
          <input
            type=\"checkbox\"
            checked={includeBackground}
            onChange={(e) => onIncludeChange(e.target.checked)}
            className=\"toggle\"
          />
        </label>
      </div>

      {includeBackground && (
        <div className=\"space-y-4\">
          {backgroundFields.map((field) => {
            const fieldConfig = config[field.key] || {};
            const IconComponent = field.icon;
            
            return (
              <div key={field.key} className=\"border border-white/20 rounded-xl p-4 bg-white/5\">
                <div className=\"flex items-center justify-between mb-4\">
                  <div className=\"flex items-center gap-3\">
                    <IconComponent className=\"w-5 h-5 text-orange-400\" />
                    <span className=\"font-medium text-white\">{field.label}</span>
                  </div>
                  
                  <label className=\"flex items-center gap-2\">
                    <span className=\"text-white/70 text-sm\">Enabled</span>
                    <input
                      type=\"checkbox\"
                      checked={fieldConfig.enabled !== false}
                      onChange={(e) => updateFieldConfig(field.key, 'enabled', e.target.checked)}
                      className=\"toggle\"
                    />
                  </label>
                </div>

                {fieldConfig.enabled !== false && (
                  <div className=\"grid grid-cols-2 gap-4\">
                    <label className=\"flex items-center justify-between p-2 bg-white/5 rounded\">
                      <span className=\"text-white/80 text-sm\">Required</span>
                      <input
                        type=\"checkbox\"
                        checked={fieldConfig.required !== false}
                        onChange={(e) => updateFieldConfig(field.key, 'required', e.target.checked)}
                        className=\"toggle\"
                      />
                    </label>
                    
                    <div>
                      <label className=\"block text-white/80 text-sm mb-1\">Order</label>
                      <input
                        type=\"number\"
                        value={fieldConfig.order || 0}
                        onChange={(e) => updateFieldConfig(field.key, 'order', parseInt(e.target.value))}
                        className=\"w-full p-2 bg-white/10 border border-white/20 rounded text-white text-sm\"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BackgroundSelectionConfig;