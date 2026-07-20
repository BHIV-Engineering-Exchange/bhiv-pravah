import React, { useState, useEffect, useRef } from "react";
import toast from "react-hot-toast";
import { FIELD_TYPES, FormConfigService } from "../lib/formConfigService";
import { EnhancedFormConfigService, BACKGROUND_SELECTION_FIELDS } from "../lib/enhancedFormConfigService";
import { DynamicFieldService } from "../lib/dynamicFieldService";
import { DynamicQuestionCategoryService } from "../lib/dynamicQuestionCategoryService";
import DynamicForm from "./DynamicForm";
import {
  Type,
  Mail,
  Hash,
  FileText,
  ChevronDown,
  Circle,
  CheckSquare,
  List,
  Plus,
  Settings,
  Eye,
  Trash2,
  ChevronUp,
  ChevronDown as ChevronDownIcon,
  GripVertical,
  Save,
  X,
  Sparkles,
  User,
  GraduationCap,
  BookOpen,
  Target,
} from "lucide-react";

// Type-specific defaults for auto-buffing fields
const TYPE_DEFAULTS = {
  [FIELD_TYPES.EMAIL]: {
    label: "Email",
    placeholder: "your.email@example.com",
    validation: { pattern: "^[^\\\s@]+@[^\\\s@]+\\\.[^\\\s@]+$" }
  },
  [FIELD_TYPES.NUMBER]: {
    label: "Number",
    placeholder: "Enter a number"
  },
  [FIELD_TYPES.TEXT]: {
    label: "Text Field",
    placeholder: "Enter text here"
  },
  [FIELD_TYPES.TEXTAREA]: {
    label: "Long Text",
    placeholder: "Enter text here"
  },
  [FIELD_TYPES.SELECT]: { label: "Dropdown" },
  [FIELD_TYPES.RADIO]: { label: "Radio Buttons" },
  [FIELD_TYPES.CHECKBOX]: { label: "Checkboxes" },
  [FIELD_TYPES.MULTI_SELECT]: { label: "Multi-Select" }
};

// Keyword-driven semantic defaults for common fields
const KEYWORD_DEFAULTS = {
  name: {
    type: FIELD_TYPES.TEXT,
    label: "Full Name",
    placeholder: "e.g., Asha Gupta",
    validation: { minLength: 2, maxLength: 100 }
  },
  full_name: {
    type: FIELD_TYPES.TEXT,
    label: "Full Name",
    placeholder: "e.g., Asha Gupta",
    validation: { minLength: 2, maxLength: 100 }
  },
  age: {
    type: FIELD_TYPES.NUMBER,
    label: "Age",
    placeholder: "17",
    validation: { min: 5, max: 100 }
  },
  phone: {
    type: FIELD_TYPES.TEXT,
    label: "Phone",
    placeholder: "999-000-1234",
    validation: { pattern: "^[\\\d\\\s\\\-\\\+\\\(\\\)\\\.]+$" }
  },
  email: {
    type: FIELD_TYPES.EMAIL,
    label: "Email",
    placeholder: "your.email@example.com",
    validation: TYPE_DEFAULTS[FIELD_TYPES.EMAIL].validation
  },
  student_id: { label: "Student ID", placeholder: "STU001" },
  grade: { label: "Grade", placeholder: "10th, 11th, etc." },
  education_level: { label: "Education Level", placeholder: "High school, Undergraduate, etc." },
  field_of_study: { label: "Field of Study" },
  current_skills: {
    type: FIELD_TYPES.TEXTAREA,
    label: "Current Skills (comma separated)",
    placeholder: "JavaScript, Algebra, Writing"
  },
  interests: {
    type: FIELD_TYPES.TEXTAREA,
    label: "Interests (comma separated)",
    placeholder: "Programming, Mathematics, Art"
  },
  goals: {
    type: FIELD_TYPES.TEXTAREA,
    label: "Goals",
    placeholder: "What do you want to achieve?"
  },
  preferred_learning_style: { label: "Preferred Learning Style" },
  availability_per_week_hours: {
    type: FIELD_TYPES.NUMBER,
    label: "Availability per week (hours)",
    placeholder: "6",
    validation: { min: 0, max: 168 }
  },
  experience_years: {
    type: FIELD_TYPES.NUMBER,
    label: "Prior experience (years)",
    placeholder: "0",
    validation: { min: 0, max: 50 }
  }
};

// Fields that students must always provide and cannot be removed
const PROTECTED_FIELD_IDS = ['question_category','grade','field_of_study'];

function mergeValidation(existing, extra) {
  return { ...(existing || {}), ...(extra || {}) };
}

function applySemanticDefaults(field) {
  const text = `${field.id || ""} ${field.label || ""}`.toLowerCase();
  let updated = { ...field };

  for (const [keyword, defs] of Object.entries(KEYWORD_DEFAULTS)) {
    if (text.includes(keyword)) {
      // Type
      if (defs.type && (!updated.type || updated.type === FIELD_TYPES.TEXT || updated._autoType)) {
        updated.type = defs.type;
        updated._autoType = true;
      }
      // Label
      if (defs.label && (!updated.label || updated._autoLabel)) {
        updated.label = defs.label;
        updated._autoLabel = true;
      }
      // Placeholder
      if (defs.placeholder && (!updated.placeholder || updated._autoPlaceholder)) {
        updated.placeholder = defs.placeholder;
        updated._autoPlaceholder = true;
      }
      // Validation
      if (defs.validation) {
        updated.validation = mergeValidation(updated.validation, defs.validation);
      }
    }
  }

  return updated;
}

// Custom Dropdown Component
const CustomDropdown = ({ onSelect, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const fieldTypes = [
    { value: FIELD_TYPES.TEXT, label: "Text Input", icon: "📝" },
    { value: FIELD_TYPES.EMAIL, label: "Email", icon: "📧" },
    { value: FIELD_TYPES.NUMBER, label: "Number", icon: "🔢" },
    { value: FIELD_TYPES.TEXTAREA, label: "Long Text", icon: "📄" },
    { value: FIELD_TYPES.SELECT, label: "Dropdown", icon: "📋" },
    { value: FIELD_TYPES.RADIO, label: "Radio Buttons", icon: "⚪" },
    { value: FIELD_TYPES.CHECKBOX, label: "Checkboxes", icon: "☑️" },
    { value: FIELD_TYPES.MULTI_SELECT, label: "Multi-Select", icon: "📝" },
  ];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (fieldType) => {
    onSelect(fieldType);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="appearance-none bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold py-3 px-4 pr-10 rounded-xl border-none cursor-pointer transition-all duration-200 shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2 focus:ring-offset-transparent flex items-center gap-2"
      >
        <span>Add Field Type</span>
        <ChevronDown
          className={`w-4 h-4 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          {fieldTypes.map((fieldType) => (
            <button
              key={fieldType.value}
              onClick={() => handleSelect(fieldType.value)}
              className="w-full text-left px-4 py-3 text-white hover:bg-gray-700 transition-colors duration-150 flex items-center gap-3 border-b border-gray-700 last:border-b-0"
            >
              <span className="text-lg">{fieldType.icon}</span>
              <span className="font-medium">{fieldType.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const FieldEditor = ({
  field,
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  isMovedUp = false,
  isMovedDown = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localField, setLocalField] = useState(field);

  useEffect(() => {
    setLocalField(field);
  }, [field]);

  const handleChange = (key, value) => {
    let updatedField = { ...localField, [key]: value };
    if (key === "id" || key === "label") {
      updatedField = applySemanticDefaults(updatedField);
    }
    setLocalField(updatedField);
    onUpdate(updatedField);
  };

  const handleOptionChange = (index, key, value) => {
    const newOptions = [...(localField.options || [])];
    newOptions[index] = { ...newOptions[index], [key]: value };
    handleChange("options", newOptions);
  };

  const addOption = () => {
    const newOptions = [
      ...(localField.options || []),
      { value: "", label: "" },
    ];
    handleChange("options", newOptions);
  };

  const removeOption = (index) => {
    const newOptions = localField.options?.filter((_, i) => i !== index) || [];
    handleChange("options", newOptions);
  };

  const needsOptions = [
    FIELD_TYPES.SELECT,
    FIELD_TYPES.RADIO,
    FIELD_TYPES.CHECKBOX,
    FIELD_TYPES.MULTI_SELECT,
  ].includes(localField.type);

  const getFieldTypeIcon = (type, className = "w-4 h-4") => {
    const iconProps = { className, strokeWidth: 2 };
    const icons = {
      [FIELD_TYPES.TEXT]: <Type {...iconProps} />,
      [FIELD_TYPES.EMAIL]: <Mail {...iconProps} />,
      [FIELD_TYPES.NUMBER]: <Hash {...iconProps} />,
      [FIELD_TYPES.TEXTAREA]: <FileText {...iconProps} />,
      [FIELD_TYPES.SELECT]: <ChevronDown {...iconProps} />,
      [FIELD_TYPES.RADIO]: <Circle {...iconProps} />,
      [FIELD_TYPES.CHECKBOX]: <CheckSquare {...iconProps} />,
      [FIELD_TYPES.MULTI_SELECT]: <List {...iconProps} />,
    };
    return icons[type] || <Type {...iconProps} />;
  };

  const getFieldTypeName = (type) => {
    const names = {
      [FIELD_TYPES.TEXT]: "Text Input",
      [FIELD_TYPES.EMAIL]: "Email",
      [FIELD_TYPES.NUMBER]: "Number",
      [FIELD_TYPES.TEXTAREA]: "Long Text",
      [FIELD_TYPES.SELECT]: "Dropdown",
      [FIELD_TYPES.RADIO]: "Radio Buttons",
      [FIELD_TYPES.CHECKBOX]: "Checkboxes",
      [FIELD_TYPES.MULTI_SELECT]: "Multi-Select",
    };
    return names[type] || type;
  };

  const handleTypeChange = (newType) => {
    const defaults = TYPE_DEFAULTS[newType] || {};
    const updated = { ...localField, type: newType };

    if ((!localField.label || localField._autoLabel) && defaults.label) {
      updated.label = defaults.label;
      updated._autoLabel = true;
    }
    if (defaults.placeholder && (!localField.placeholder || localField._autoPlaceholder)) {
      updated.placeholder = defaults.placeholder;
      updated._autoPlaceholder = true;
    }

    // Clear options when switching to non-option types
    if (![FIELD_TYPES.SELECT, FIELD_TYPES.RADIO, FIELD_TYPES.CHECKBOX, FIELD_TYPES.MULTI_SELECT].includes(newType)) {
      if (updated.options) delete updated.options;
    }

    // Add basic email validation pattern
    if (newType === FIELD_TYPES.EMAIL) {
      updated.validation = {
        ...(localField.validation || {}),
        pattern: (localField.validation && localField.validation.pattern) || TYPE_DEFAULTS[FIELD_TYPES.EMAIL].validation.pattern
      };
    }

    setLocalField(updated);
    onUpdate(updated);
  };

  return (
    <div className={`group border border-white/20 rounded-xl p-5 bg-gradient-to-r from-white/5 to-white/8 hover:from-white/8 hover:to-white/12 transition-all duration-300 shadow-lg hover:shadow-xl will-change-transform ${isMovedUp ? 'animate-move-up ring-1 ring-orange-400/40' : ''} ${isMovedDown ? 'animate-move-down ring-1 ring-orange-400/40' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4 flex-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 hover:text-orange-300 transition-all duration-200"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </button>

          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500/20 to-orange-600/20 border border-orange-500/30">
              {getFieldTypeIcon(localField.type, "w-5 h-5 text-orange-400")}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white text-lg">
                  {localField.label || "Untitled Field"}
                </span>
                {localField.required && (
                  <span className="px-2 py-1 text-xs bg-red-500/20 text-red-300 rounded-full border border-red-500/30">
                    Required
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-sm text-white/60 mt-1">
                <span className="px-2 py-1 bg-white/10 rounded-md">
                  {getFieldTypeName(localField.type)}
                </span>
                {localField.options && (
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded-md">
                    {localField.options.length} options
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center bg-white/10 rounded-lg p-1">
            <button
              onClick={onMoveUp}
              disabled={!canMoveUp}
              className="flex items-center justify-center w-8 h-8 rounded-md text-white/70 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
              title="Move up"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
            <button
              onClick={onMoveDown}
              disabled={!canMoveDown}
              className="flex items-center justify-center w-8 h-8 rounded-md text-white/70 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
              title="Move down"
            >
              <ChevronDownIcon className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={onDelete}
            disabled={PROTECTED_FIELD_IDS.includes(localField.id)}
            className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200 ${PROTECTED_FIELD_IDS.includes(localField.id) ? 'bg-red-500/10 text-red-400/40 cursor-not-allowed' : 'bg-red-500/20 text-red-400 hover:bg-red-500/30 hover:text-red-300'}`}
            title={PROTECTED_FIELD_IDS.includes(localField.id) ? "This field is required and cannot be deleted" : "Delete field"}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 border-t border-white/10 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Field ID</label>
              <input
                type="text"
                value={localField.id}
                onChange={(e) => handleChange("id", e.target.value)}
                className="input"
                placeholder="field_id"
              />
            </div>
            <div>
              <label className="label">Field Type</label>
              <select
                value={localField.type}
                onChange={(e) => handleTypeChange(e.target.value)}
                className="input"
              >
                {Object.entries(FIELD_TYPES).map(([key, value]) => (
                  <option key={value} value={value}>
                    {key.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="label">Label</label>
            <input
              type="text"
              value={localField.label}
              onChange={(e) => handleChange("label", e.target.value)}
              className="input"
              placeholder="Field Label"
            />
          </div>

          <div>
            <label className="label">Placeholder</label>
            <input
              type="text"
              value={localField.placeholder || ""}
              onChange={(e) => handleChange("placeholder", e.target.value)}
              className="input"
              placeholder="Placeholder text"
            />
          </div>

          <div>
            <label className="label">Help Text</label>
            <input
              type="text"
              value={localField.helpText || ""}
              onChange={(e) => handleChange("helpText", e.target.value)}
              className="input"
              placeholder="Additional help text"
            />
          </div>

          
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={PROTECTED_FIELD_IDS.includes(localField.id) ? true : (localField.required || false)}
                onChange={(e) => !PROTECTED_FIELD_IDS.includes(localField.id) && handleChange("required", e.target.checked)}
                className="text-orange-500"
                disabled={PROTECTED_FIELD_IDS.includes(localField.id)}
              />
              <span className="text-white/90">
                Required{PROTECTED_FIELD_IDS.includes(localField.id) ? ' (locked)' : ''}
              </span>
            </label>
          </div>

          {needsOptions && (
            <div>
              <label className="label">Options</label>
              <div className="space-y-2">
                {localField.options?.map((option, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={option.value}
                      onChange={(e) =>
                        handleOptionChange(index, "value", e.target.value)
                      }
                      className="input flex-1"
                      placeholder="Value"
                    />
                    <input
                      type="text"
                      value={option.label}
                      onChange={(e) =>
                        handleOptionChange(index, "label", e.target.value)
                      }
                      className="input flex-1"
                      placeholder="Label"
                    />
                    <button
                      onClick={() => removeOption(index)}
                      className="btn-sm bg-red-500 hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                ))}
                <button
                  onClick={addOption}
                  className="btn-sm bg-green-500 hover:bg-green-600"
                >
                  Add Option
                </button>
              </div>
            </div>
          )}

          {(localField.type === FIELD_TYPES.TEXT ||
            localField.type === FIELD_TYPES.TEXTAREA ||
            localField.type === FIELD_TYPES.NUMBER) && (
            <div>
              <label className="label">Validation</label>
              <div className="grid grid-cols-2 gap-4">
                {localField.type === FIELD_TYPES.NUMBER && (
                  <>
                    <div>
                      <label className="text-sm text-white/70">Min Value</label>
                      <input
                        type="number"
                        value={localField.validation?.min || ""}
                        onChange={(e) =>
                          handleChange("validation", {
                            ...localField.validation,
                            min: e.target.value
                              ? Number(e.target.value)
                              : undefined,
                          })
                        }
                        className="input"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-white/70">Max Value</label>
                      <input
                        type="number"
                        value={localField.validation?.max || ""}
                        onChange={(e) =>
                          handleChange("validation", {
                            ...localField.validation,
                            max: e.target.value
                              ? Number(e.target.value)
                              : undefined,
                          })
                        }
                        className="input"
                        placeholder="100"
                      />
                    </div>
                  </>
                )}
                {(localField.type === FIELD_TYPES.TEXT ||
                  localField.type === FIELD_TYPES.TEXTAREA) && (
                  <>
                    <div>
                      <label className="text-sm text-white/70">
                        Min Length
                      </label>
                      <input
                        type="number"
                        value={localField.validation?.minLength || ""}
                        onChange={(e) =>
                          handleChange("validation", {
                            ...localField.validation,
                            minLength: e.target.value
                              ? Number(e.target.value)
                              : undefined,
                          })
                        }
                        className="input"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-white/70">
                        Max Length
                      </label>
                      <input
                        type="number"
                        value={localField.validation?.maxLength || ""}
                        onChange={(e) =>
                          handleChange("validation", {
                            ...localField.validation,
                            maxLength: e.target.value
                              ? Number(e.target.value)
                              : undefined,
                          })
                        }
                        className="input"
                        placeholder="255"
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function FormBuilder({
  onSave,
  onCancel,
  initialConfig = null,
}) {
  const [config, setConfig] = useState(
    initialConfig || {
      name: "Student Intake Form",
      description: "Customize the fields students will see when they register",
      fields: [],
    }
  );
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState([]);
  const [activeTab, setActiveTab] = useState("builder");
  const [previewData, setPreviewData] = useState({});
  const [fieldOptions, setFieldOptions] = useState([]);
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [defaultStudyField, setDefaultStudyField] = useState("");
  const [defaultCategory, setDefaultCategory] = useState("");
  const prevDefaultsRef = useRef({ studyField: "", category: "" });
  const [moved, setMoved] = useState({ id: null, dir: null });

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [fields, categories] = await Promise.all([
          DynamicFieldService.getFieldOptions(),
          DynamicQuestionCategoryService.getCategoryOptions(),
        ]);
        if (mounted) {
          setFieldOptions(fields);
          setCategoryOptions(categories);
          // Initialize defaults if not set
          setDefaultStudyField((prev) => prev || fields?.[0]?.value || "");
          setDefaultCategory((prev) => prev || categories?.[0]?.value || "");
          if (!prevDefaultsRef.current.studyField) {
            prevDefaultsRef.current.studyField = fields?.[0]?.value || "";
          }
          if (!prevDefaultsRef.current.category) {
            prevDefaultsRef.current.category = categories?.[0]?.value || "";
          }
        }
      } catch (e) {
        console.error("Failed to load dynamic options:", e);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Ensure mandatory fields exist by default
  useEffect(() => {
    setConfig((prev) => {
      const present = new Set((prev.fields || []).map(f => f.id));
      const toAdd = [];

      if (!present.has('name')) {
        toAdd.push({
          id: 'name',
          type: FIELD_TYPES.TEXT,
          label: 'Full Name',
          placeholder: 'e.g., Asha Gupta',
          required: true,
          section: 'personal_info',
          order: -10,
          validation: { minLength: 2, maxLength: 100 },
          study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
          category_id: defaultCategory || categoryOptions?.[0]?.value || ''
        });
      }
      if (!present.has('email')) {
        toAdd.push({
          id: 'email',
          type: FIELD_TYPES.EMAIL,
          label: 'Email',
          placeholder: 'your.email@example.com',
          required: true,
          section: 'personal_info',
          order: -9,
          validation: { pattern: "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$" },
          study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
          category_id: defaultCategory || categoryOptions?.[0]?.value || ''
        });
      }
      if (!present.has('grade')) {
        toAdd.push({
          id: 'grade',
          type: FIELD_TYPES.SELECT,
          label: 'Grade',
          placeholder: 'Select your grade',
          required: true,
          section: 'personal_info',
          order: -8,
          options: [
            { value: '9', label: '9th Grade' },
            { value: '10', label: '10th Grade' },
            { value: '11', label: '11th Grade' },
            { value: '12', label: '12th Grade' },
            { value: 'undergraduate', label: 'Undergraduate' },
            { value: 'graduate', label: 'Graduate' },
            { value: 'postgraduate', label: 'Postgraduate' },
            { value: 'other', label: 'Other' }
          ],
          study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
          category_id: defaultCategory || categoryOptions?.[0]?.value || ''
        });
      }
            // Ensure field_of_study is present and required
            if (!present.has('field_of_study')) {
              toAdd.push({
                id: 'field_of_study',
                type: FIELD_TYPES.SELECT,
                label: 'What field are you studying or working in?',
                placeholder: 'Select your field of study',
                required: true,
                section: 'academic_info',
                order: -7,
                study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
                category_id: defaultCategory || categoryOptions?.[0]?.value || ''
              });
            }
            if (!present.has('question_category')) {
        const templ = BACKGROUND_SELECTION_FIELDS?.question_category;
        const fallback = {
          id: 'question_category',
          type: FIELD_TYPES.SELECT,
          label: 'Question Category',
          section: 'background_selection',
          order: 0,
          options: []
        };
        toAdd.push({
          ...(templ || fallback),
          required: true,
          section: (templ && templ.section) || 'background_selection',
          order: (templ && (templ.order ?? 0)) ?? 0,
          study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
          category_id: defaultCategory || categoryOptions?.[0]?.value || ''
        });
      }

      if (toAdd.length === 0) return prev;
      const merged = [...prev.fields, ...toAdd].reduce((acc, f) => {
        if (!acc.find(x => x.id === f.id)) acc.push(f);
        return acc;
      }, []);
      merged.sort((a,b)=>(a.order||0)-(b.order||0));
      return { ...prev, fields: merged };
    });
  }, [fieldOptions, categoryOptions, defaultStudyField, defaultCategory]);

  useEffect(() => {
    // Auto-assign study field and question category for fields that are missing them
    if (!fieldOptions.length || !categoryOptions.length) return;

    const run = async () => {
      setConfig((prev) => {
        const updated = { ...prev };
        updated.fields = prev.fields.map((f) => {
          let sf = f.study_field_id;
          let cat = f.category_id;

          // Default to first options if missing
          if (!sf) sf = defaultStudyField || fieldOptions[0]?.value || "";
          if (!cat) cat = defaultCategory || categoryOptions[0]?.value || "";

          const typeDefaults = TYPE_DEFAULTS[f.type] || {};
          let label = f.label;
          let placeholder = f.placeholder;
          let validation = f.validation;

          if ((!label || f._autoLabel) && typeDefaults.label) {
            label = typeDefaults.label;
          }
          if ((!placeholder || f._autoPlaceholder) && typeDefaults.placeholder) {
            placeholder = typeDefaults.placeholder;
          }
          if (f.type === FIELD_TYPES.EMAIL) {
            validation = {
              ...(f.validation || {}),
              pattern: (f.validation && f.validation.pattern) || TYPE_DEFAULTS[FIELD_TYPES.EMAIL].validation.pattern
            };
          }

          let buffed = { ...f, study_field_id: sf, category_id: cat, label, placeholder, validation };
          // Apply semantic defaults based on id/label content
          buffed = applySemanticDefaults(buffed);
          return buffed;
        });
        return updated;
      });

      // Try to refine study field using detection on label/helpText
      for (let i = 0; i < config.fields.length; i++) {
        const f = config.fields[i];
        if (f.label && !f._autoDetected) {
          try {
            const hint = `${f.label} ${f.helpText || ""}`;
            const detected = await DynamicFieldService.detectFieldFromText(hint);
            if (detected?.field_id) {
              setConfig((prev) => {
                const copy = { ...prev };
                copy.fields = prev.fields.map((fld, idx) => idx === i ? { ...fld, study_field_id: fld.study_field_id || detected.field_id, _autoDetected: true } : fld);
                return copy;
              });
            }
          } catch {}
        }
      }
    };

    run();
  }, [fieldOptions, categoryOptions, defaultStudyField, defaultCategory]);

  // When defaults change, propagate to fields that were using previous defaults or unset
  useEffect(() => {
    if (!fieldOptions.length || !categoryOptions.length) return;

    const prevStudy = prevDefaultsRef.current.studyField;
    const prevCat = prevDefaultsRef.current.category;

    if (prevStudy === defaultStudyField && prevCat === defaultCategory) return;

    setConfig((prev) => {
      const updated = { ...prev };
      updated.fields = prev.fields.map((f) => {
        const nf = { ...f };
        if (!nf.study_field_id || nf.study_field_id === prevStudy) {
          nf.study_field_id = defaultStudyField || fieldOptions[0]?.value || "";
        }
        if (!nf.category_id || nf.category_id === prevCat) {
          nf.category_id = defaultCategory || categoryOptions[0]?.value || "";
        }
        return nf;
      });
      return updated;
    });

    prevDefaultsRef.current = { studyField: defaultStudyField, category: defaultCategory };
  }, [defaultStudyField, defaultCategory, fieldOptions, categoryOptions]);

  const addField = (fieldType = FIELD_TYPES.TEXT) => {
    const fieldTypeNames = {
      [FIELD_TYPES.TEXT]: "Text Field",
      [FIELD_TYPES.EMAIL]: "Email Field",
      [FIELD_TYPES.NUMBER]: "Number Field",
      [FIELD_TYPES.TEXTAREA]: "Text Area",
      [FIELD_TYPES.SELECT]: "Dropdown",
      [FIELD_TYPES.RADIO]: "Radio Buttons",
      [FIELD_TYPES.CHECKBOX]: "Checkboxes",
      [FIELD_TYPES.MULTI_SELECT]: "Multi-Select",
    };

    const defaults = TYPE_DEFAULTS[fieldType] || {};
    const newField = {
      id: `field_${Date.now()}`,
      type: fieldType,
      label: defaults.label || fieldTypeNames[fieldType] || "New Field",
      placeholder:
        (defaults.placeholder) ||
        (fieldType === FIELD_TYPES.NUMBER
          ? "Enter a number"
          : "Enter text here"),
      _autoLabel: !!defaults.label,
      _autoPlaceholder: !!defaults.placeholder,
      required: false,
      study_field_id: defaultStudyField || fieldOptions?.[0]?.value || "",
      category_id: defaultCategory || categoryOptions?.[0]?.value || "",
      order: config.fields.length + 1,
      ...(fieldType === FIELD_TYPES.EMAIL && defaults.validation
        ? { validation: { ...defaults.validation } }
        : {})
    };

    // Add default options for select/radio/checkbox fields
    if (
      [
        FIELD_TYPES.SELECT,
        FIELD_TYPES.RADIO,
        FIELD_TYPES.CHECKBOX,
        FIELD_TYPES.MULTI_SELECT,
      ].includes(fieldType)
    ) {
      newField.options = [
        { value: "option1", label: "Option 1" },
        { value: "option2", label: "Option 2" },
      ];
    }

    setConfig((prev) => ({
      ...prev,
      fields: [...prev.fields, newField],
    }));

    // Show success toast
    toast.success(`${fieldTypeNames[fieldType]} added successfully`);
  };

  const updateField = (index, updatedField) => {
    setConfig((prev) => ({
      ...prev,
      fields: prev.fields.map((field, i) =>
        i === index ? updatedField : field
      ),
    }));
  };

  const deleteField = (index) => {
    const fieldToDelete = config.fields[index];
    setConfig((prev) => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index),
    }));

    // Show success toast
    toast.success(`${fieldToDelete.label || "Field"} deleted successfully`);
  };

  const moveField = (index, direction) => {
    const newFields = [...config.fields];
    const targetIndex = direction === "up" ? index - 1 : index + 1;

    if (targetIndex >= 0 && targetIndex < newFields.length) {
      const movedId = newFields[index]?.id;
      const fieldName = newFields[index].label || "Field";

      [newFields[index], newFields[targetIndex]] = [
        newFields[targetIndex],
        newFields[index],
      ];

      // Update order values
      newFields.forEach((field, i) => {
        field.order = i + 1;
      });

      setConfig((prev) => ({ ...prev, fields: newFields }));

      // Trigger animation on moved field
      if (movedId) {
        setMoved({ id: movedId, dir: direction });
        setTimeout(() => setMoved({ id: null, dir: null }), 400);
      }

      // Show success toast
      toast.success(`${fieldName} moved ${direction} successfully`);
    }
  };

  // Add student-facing background selection fields to the form
  const addBackgroundField = (fieldId) => {
    const template = BACKGROUND_SELECTION_FIELDS[fieldId];
    if (!template) return;

    setConfig((prev) => {
      // Skip if already present
      if (prev.fields.some((f) => f.id === fieldId)) {
        toast.success(`${template.label} is already in the form`);
        return prev;
      }

      // Determine order
      const nextOrder = (prev.fields?.length || 0) + 1;

      const newField = {
        ...template,
        // Ensure validation and section are preserved
        section: template.section || 'background_selection',
        order: template.order ?? nextOrder,
        // Satisfy internal classification metadata for validation
        study_field_id: defaultStudyField || fieldOptions?.[0]?.value || '',
        category_id: defaultCategory || categoryOptions?.[0]?.value || ''
      };

      return {
        ...prev,
        fields: [...prev.fields, newField],
      };
    });

    toast.success(`${template.label} added to the form`);
  };

  const addAllBackgroundFields = () => {
    ['field_of_study', 'class_level', 'learning_goals', 'question_category'].forEach(addBackgroundField);
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors([]);

    // Validate configuration
    const validationErrors = FormConfigService.validateFormConfig(config);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      toast.error("Please fix the validation errors before saving");
      setSaving(false);
      return;
    }

    // Show loading toast
    const loadingToast = toast.loading("Saving form configuration...");

    try {
      const savedConfig = await FormConfigService.saveFormConfig({
        ...config,
        id: config.id || `config_${Date.now()}`,
      });

      toast.success("Form configuration saved successfully", {
        id: loadingToast,
      });

      onSave(savedConfig);
    } catch (error) {
      toast.error(error.message || "Failed to save configuration", {
        id: loadingToast,
      });
      setErrors([error.message || "Failed to save configuration"]);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <style>{`
        @keyframes fb-move-up { 0% { transform: translateY(0); } 50% { transform: translateY(-8px); } 100% { transform: translateY(0); } }
        @keyframes fb-move-down { 0% { transform: translateY(0); } 50% { transform: translateY(8px); } 100% { transform: translateY(0); } }
        .animate-move-up { animation: fb-move-up 300ms ease-out; }
        .animate-move-down { animation: fb-move-down 300ms ease-out; }
      `}</style>
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          Form Configuration
        </h3>

        {errors.length > 0 && (
          <div className="mb-4 p-3 bg-red-500/15 border border-red-400/30 rounded-md">
            <div className="text-red-200 text-sm">
              <div className="font-medium mb-1">
                Please fix the following errors:
              </div>
              <ul className="list-disc list-inside space-y-1">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="label">Form Name</label>
            <input
              type="text"
              value={config.name}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, name: e.target.value }))
              }
              className="input"
              placeholder="Form Name"
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              type="text"
              value={config.description}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, description: e.target.value }))
              }
              className="input"
              placeholder="Form description"
            />
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="flex border-b border-white/20 bg-white/5 rounded-t-xl">
            <button
              onClick={() => setActiveTab("builder")}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-semibold border-b-2 transition-all duration-200 rounded-tl-xl ${
                activeTab === "builder"
                  ? "border-orange-500 text-orange-400 bg-orange-500/10"
                  : "border-transparent text-white/70 hover:text-white hover:bg-white/10"
              }`}
            >
              <Settings className="w-4 h-4" />
              Form Builder
            </button>
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-semibold border-b-2 transition-all duration-200 ${
                activeTab === "preview"
                  ? "border-orange-500 text-orange-400 bg-orange-500/10"
                  : "border-transparent text-white/70 hover:text-white hover:bg-white/10"
              }`}
            >
              <Eye className="w-4 h-4" />
              Preview
              <span className="px-2 py-1 text-xs bg-white/20 rounded-full">
                {config.fields.length}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Form Builder Tab */}
      {activeTab === "builder" && (
        <div>
          
          
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-medium text-white">
              Form Fields ({config.fields.length})
            </h4>
            <CustomDropdown onSelect={addField} />
          </div>

          {config.fields.length === 0 && (
            <div className="text-center py-16 border-2 border-dashed border-white/20 rounded-2xl mb-6 bg-gradient-to-br from-white/5 to-white/10">
              <div className="text-white/60 mb-8">
                <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-orange-500/20 to-orange-600/20 rounded-2xl">
                  <Settings className="w-8 h-8 text-orange-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-white">
                  No fields added yet
                </h3>
                <p className="text-sm mb-6 max-w-md mx-auto">
                  Choose a field type above to start building your custom form,
                  or use one of our quick start templates below
                </p>
              </div>

              <div className="max-w-lg mx-auto">
                <h4 className="text-white font-semibold mb-4 flex items-center justify-center gap-2">
                  <Sparkles className="w-5 h-5 text-orange-400" />
                  Quick Start Templates
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => {
                      addField(FIELD_TYPES.TEXT);
                      setTimeout(() => addField(FIELD_TYPES.EMAIL), 100);
                      setTimeout(() => addField(FIELD_TYPES.TEXTAREA), 200);
                    }}
                    className="group p-4 bg-gradient-to-br from-blue-500/10 to-blue-600/10 hover:from-blue-500/20 hover:to-blue-600/20 rounded-xl border border-blue-500/20 hover:border-blue-500/30 transition-all duration-200 text-left"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex items-center justify-center w-8 h-8 bg-blue-500/20 rounded-lg">
                        <User className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="font-semibold text-white group-hover:text-blue-200">
                        Basic Contact Form
                      </div>
                    </div>
                    <div className="text-xs text-white/60 group-hover:text-white/80">
                      Name, Email, Message fields
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      addField(FIELD_TYPES.TEXT);
                      setTimeout(() => addField(FIELD_TYPES.NUMBER), 100);
                      setTimeout(() => addField(FIELD_TYPES.SELECT), 200);
                      setTimeout(() => addField(FIELD_TYPES.RADIO), 300);
                    }}
                    className="group p-4 bg-gradient-to-br from-green-500/10 to-green-600/10 hover:from-green-500/20 hover:to-green-600/20 rounded-xl border border-green-500/20 hover:border-green-500/30 transition-all duration-200 text-left"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex items-center justify-center w-8 h-8 bg-green-500/20 rounded-lg">
                        <GraduationCap className="w-4 h-4 text-green-400" />
                      </div>
                      <div className="font-semibold text-white group-hover:text-green-200">
                        Student Registration
                      </div>
                    </div>
                    <div className="text-xs text-white/60 group-hover:text-white/80">
                      Name, Age, Education, Preferences
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {config.fields.map((field, index) => (
              <FieldEditor
                key={field.id || index}
                field={field}
                onUpdate={(updatedField) => updateField(index, updatedField)}
                onDelete={() => deleteField(index)}
                onMoveUp={() => moveField(index, "up")}
                onMoveDown={() => moveField(index, "down")}
                canMoveUp={index > 0}
                canMoveDown={index < config.fields.length - 1}
                isMovedUp={moved.id === field.id && moved.dir === 'up'}
                isMovedDown={moved.id === field.id && moved.dir === 'down'}
              />
            ))}

            {config.fields.length === 0 && (
              <div className="text-center py-8 text-white/60">
                No fields added yet. Click "Add Field" to get started.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Preview Tab */}
      {activeTab === "preview" && (
        <div>
          {config.fields.length === 0 ? (
            <div className="text-center py-16 bg-gradient-to-br from-white/5 to-white/10 rounded-2xl border-2 border-dashed border-white/20">
              <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-2xl">
                <Eye className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">
                No Preview Available
              </h3>
              <p className="text-sm text-white/60 max-w-md mx-auto">
                Add some fields in the Form Builder tab to see how your form
                will look to students
              </p>
            </div>
          ) : (
            <div>
              <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <div className="flex items-center gap-2 text-blue-300 mb-2">
                  <Eye className="w-5 h-5" />
                  <span className="font-semibold">Live Preview</span>
                </div>
                <p className="text-sm text-blue-200/80">
                  This is exactly how your form will appear to students. You can
                  interact with it to test the user experience.
                </p>
              </div>
              <div className="bg-gradient-to-br from-white/5 to-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl">
                <DynamicForm
                  config={config}
                  formData={previewData}
                  onChange={setPreviewData}
                  onSubmit={(e) => {
                    e.preventDefault();
                    toast.info(
                      "This is just a preview - form submission is disabled"
                    );
                  }}
                  loading={false}
                  submitButtonText="Submit (Preview Only)"
                  resetButtonText="Reset"
                  onReset={() => setPreviewData({})}
                />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-end gap-3 pt-6 border-t border-white/20">
        <button
          onClick={onCancel}
          className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-all duration-200"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          {saving ? "Saving..." : "Save Configuration"}
        </button>
      </div>
    </div>
  );
}
