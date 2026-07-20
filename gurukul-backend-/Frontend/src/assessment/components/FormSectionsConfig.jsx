import React from 'react';
import { Settings, Plus, Trash2, GraduationCap, User, BookOpen } from 'lucide-react';

const FormSectionsConfig = ({ sections, onSectionsChange }) => {
  const iconOptions = [
    { value: 'GraduationCap', label: 'Graduation Cap', component: GraduationCap },
    { value: 'User', label: 'User', component: User },
    { value: 'BookOpen', label: 'Book', component: BookOpen },
    { value: 'Settings', label: 'Settings', component: Settings }
  ];

  const updateSection = (sectionKey, property, value) => {
    const newSections = {
      ...sections,
      [sectionKey]: {
        ...sections[sectionKey],
        [property]: value
      }
    };
    onSectionsChange(newSections);
  };

  const deleteSection = (sectionKey) => {
    const newSections = { ...sections };
    delete newSections[sectionKey];
    onSectionsChange(newSections);
  };

  const addSection = () => {
    const newKey = `section_${Date.now()}`;
    const newSections = {
      ...sections,
      [newKey]: {
        title: 'New Section',
        description: 'Section description',
        order: Object.keys(sections).length,
        icon: 'Settings'
      }
    };
    onSectionsChange(newSections);
  };

  return (
    <div className=\"space-y-6\">
      <div className=\"flex items-center justify-between\">
        <h3 className=\"text-lg font-semibold text-white flex items-center gap-2\">
          <Settings className=\"w-5 h-5 text-orange-400\" />
          Form Sections
        </h3>
        
        <button
          onClick={addSection}
          className=\"flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg text-white transition-colors\"
        >
          <Plus className=\"w-4 h-4\" />
          Add Section
        </button>
      </div>

      <div className=\"space-y-4\">
        {Object.entries(sections || {}).map(([key, section]) => {
          const IconComponent = iconOptions.find(opt => opt.value === section.icon)?.component || Settings;
          
          return (
            <div key={key} className=\"border border-white/20 rounded-xl p-4 bg-white/5\">
              <div className=\"flex items-center justify-between mb-4\">
                <div className=\"flex items-center gap-3\">
                  <IconComponent className=\"w-5 h-5 text-orange-400\" />
                  <span className=\"font-medium text-white\">{section.title}</span>
                </div>
                
                <button
                  onClick={() => deleteSection(key)}
                  className=\"p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors\"
                >
                  <Trash2 className=\"w-4 h-4\" />
                </button>
              </div>

              <div className=\"grid grid-cols-1 md:grid-cols-2 gap-4\">
                <div>
                  <label className=\"block text-white/80 text-sm mb-2\">Title</label>
                  <input
                    type=\"text\"
                    value={section.title || ''}
                    onChange={(e) => updateSection(key, 'title', e.target.value)}
                    className=\"w-full p-2 bg-white/10 border border-white/20 rounded text-white\"
                  />
                </div>
                
                <div>
                  <label className=\"block text-white/80 text-sm mb-2\">Icon</label>
                  <select
                    value={section.icon || 'Settings'}
                    onChange={(e) => updateSection(key, 'icon', e.target.value)}
                    className=\"w-full p-2 bg-white/10 border border-white/20 rounded text-white\"
                  >
                    {iconOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className=\"md:col-span-2\">
                  <label className=\"block text-white/80 text-sm mb-2\">Description</label>
                  <input
                    type=\"text\"
                    value={section.description || ''}
                    onChange={(e) => updateSection(key, 'description', e.target.value)}
                    className=\"w-full p-2 bg-white/10 border border-white/20 rounded text-white\"
                  />
                </div>
                
                <div>
                  <label className=\"block text-white/80 text-sm mb-2\">Order</label>
                  <input
                    type=\"number\"
                    value={section.order || 0}
                    onChange={(e) => updateSection(key, 'order', parseInt(e.target.value))}
                    className=\"w-full p-2 bg-white/10 border border-white/20 rounded text-white\"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FormSectionsConfig;"