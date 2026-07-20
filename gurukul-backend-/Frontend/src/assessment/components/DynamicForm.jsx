import React, { useState, useEffect } from "react";
import { FIELD_TYPES } from "../lib/formConfigService";
import {
  GraduationCap,
  BookOpen,
  Target,
  User,
  Settings,
  Loader,
  FileText,
  Heart,
  Star,
  Shield,
  Clock,
  Calendar,
  Camera,
  Music,
  Palette,
  Code,
  Database,
  Globe,
  Mail,
  Phone,
  Home,
} from "lucide-react";
import { DynamicFieldService } from "../lib/dynamicFieldService";
import { DynamicCategoryService } from "../lib/dynamicCategoryService";
import { DynamicQuestionCategoryService } from "../lib/dynamicQuestionCategoryService";
import { i18n } from "../lib/i18n";

// Localized strings for generic form UI
const FORM_I18N = {
  en: {
    selectAnOption: "Select an option",
    loadingStudyFields: "Loading study fields...",
    loadingCategories: "Loading categories...",
    holdCtrl: "Hold Ctrl/Cmd to select multiple options",
    submit: "Submit Assessment",
    submitting: "Submitting...",
    selectFieldOfStudy: "Select your field of study",
    selectCategory: "Select a category",
    noConfig: "No form configuration available",
    isRequired: "is required",
  },
  hi: {
    selectAnOption: "विकल्प चुनें",
    loadingStudyFields: "अध्ययन क्षेत्र लोड हो रहे हैं...",
    loadingCategories: "श्रेणियाँ लोड हो रही हैं...",
    holdCtrl: "एकाधिक विकल्प चुनने के लिए Ctrl/Cmd दबाकर रखें",
    submit: "मूल्यांकन जमा करें",
    submitting: "जमा किया जा रहा है...",
    selectFieldOfStudy: "अपना अध्ययन क्षेत्र चुनें",
    selectCategory: "एक श्रेणी चुनें",
    noConfig: "कोई फॉर्म कॉन्फ़िगरेशन उपलब्ध नहीं",
    isRequired: "अनिवार्य है",
  },
  mr: {
    selectAnOption: "पर्याय निवडा",
    loadingStudyFields: "अभ्यास क्षेत्र लोड होत आहेत...",
    loadingCategories: "विभाग लोड होत आहेत...",
    holdCtrl: "एकापेक्षा जास्त पर्याय निवडण्यासाठी Ctrl/Cmd धरून ठेवा",
    submit: "मूल्यमापन सादर करा",
    submitting: "सादर करत आहे...",
    selectFieldOfStudy: "तुमचा अभ्यास क्षेत्र निवडा",
    selectCategory: "एक विभाग निवडा",
    noConfig: "कोणतेही फॉर्म कॉन्फिगरेशन उपलब्ध नाही",
    isRequired: "आवश्यक आहे",
  },
};
const f = (key) => {
  const lang = i18n.getLang();
  return (FORM_I18N[lang] && FORM_I18N[lang][key]) || FORM_I18N.en[key] || key;
};

// Field-level translation helpers
const translateField = (field) => {
  const copy = { ...field };
  const labelKey = `form.labels.${field.id}`;
  if (i18n.has && i18n.has(labelKey)) copy.label = i18n.t(labelKey);
  const helpKey = `form.help.${field.id}`;
  if (i18n.has && i18n.has(helpKey)) copy.helpText = i18n.t(helpKey);
  const phKey = `form.placeholders.${field.id}`;
  if (i18n.has && i18n.has(phKey)) copy.placeholder = i18n.t(phKey);
  if (Array.isArray(field.options)) {
    copy.options = field.options.map((opt) => {
      const key = `form.options.${field.id}.${opt.value}`;
      return { ...opt, label: i18n.has && i18n.has(key) ? i18n.t(key) : opt.label };
    });
  }
  return copy;
};

// Individual field components
const TextField = ({ field, value, onChange, error }) => (
  <div>
    <label className="label">
      {field.label} {field.required && <span className="text-orange-300">*</span>}
    </label>
    {field.helpText && <div className="help">{field.helpText}</div>}
    <input
      type={field.type}
      name={field.id}
      value={value || ""}
      onChange={onChange}
      required={field.required}
      placeholder={field.placeholder}
      className={`input ${error ? "border-red-400" : ""}`}
      min={field.validation?.min}
      max={field.validation?.max}
      minLength={field.validation?.minLength}
      maxLength={field.validation?.maxLength}
      pattern={field.validation?.pattern}
    />
    {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
  </div>
);

const TextAreaField = ({ field, value, onChange, error }) => (
  <div>
    <label className="label">
      {field.label} {field.required && <span className="text-orange-300">*</span>}
    </label>
    {field.helpText && <div className="help">{field.helpText}</div>}
    <textarea
      name={field.id}
      value={value || ""}
      onChange={onChange}
      required={field.required}
      placeholder={field.placeholder}
      className={`input min-h-[100px] ${error ? "border-red-400" : ""}`}
      minLength={field.validation?.minLength}
      maxLength={field.validation?.maxLength}
    />
    {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
  </div>
);

const SelectField = ({ field, value, onChange, error }) => (
  <div>
    <label className="label">
      {field.label} {field.required && <span className="text-orange-300">*</span>}
    </label>
    {field.helpText && <div className="help">{field.helpText}</div>}
    <select
      name={field.id}
      value={value || ""}
      onChange={onChange}
      required={field.required}
      className={`input ${error ? "border-red-400" : ""}`}
    >
      <option value="">{field.placeholder || f("selectAnOption")}</option>
      {field.options?.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
  </div>
);

const CardGridField = ({ field, value, onChange, error, options = null }) => {
  const displayOptions = options || field.options || [];
  const styling = field.styling || {};
  const gridCols = styling.gridCols === "2" ? "sm:grid-cols-2" : "grid-cols-1";
  const showIcons = styling.showIcons;
  const showDescriptions = styling.showDescriptions;

  return (
    <div>
      <label className="flex items-center gap-2 text-white font-medium mb-3">
        {field.section === "background_selection" && field.id === "field_of_study" && (
          <BookOpen className="w-5 h-5 text-orange-400" />
        )}
        {field.section === "background_selection" && field.id === "class_level" && (
          <GraduationCap className="w-5 h-5 text-orange-400" />
        )}
        {field.section === "background_selection" && field.id === "learning_goals" && (
          <Target className="w-5 h-5 text-orange-400" />
        )}
        {field.label}
        {field.required && <span className="text-orange-300">*</span>}
      </label>
      {field.helpText && (
        <div className="text-white/70 text-sm mb-3">{field.helpText}</div>
      )}

      <div className={`grid grid-cols-1 ${gridCols} gap-3`}>
        {displayOptions.map((option) => (
          <label
            key={option.value}
            className={`relative flex flex-col items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 hover:scale-[1.02] min-h-[80px] text-center ${value === option.value
                ? "border-orange-400 bg-gradient-to-r from-orange-500/20 to-orange-600/20 text-white shadow-lg shadow-orange-500/20"
                : "border-white/20 bg-white/5 text-white/80 hover:bg-white/10 hover:border-white/30"
              }`}
          >
            <input
              type="radio"
              name={field.id}
              value={option.value}
              checked={value === option.value}
              onChange={onChange}
              required={field.required}
              className="sr-only"
            />
            <div className="flex items-center gap-2 mb-1">
              {showIcons && option.icon && <span className="text-lg">{option.icon}</span>}
              <span className="text-sm font-medium">{option.label}</span>
            </div>
            {showDescriptions && option.description && (
              <span className="text-xs text-white/60 leading-tight">
                {option.description}
              </span>
            )}
            {value === option.value && (
              <div className="absolute top-2 right-2">
                <div className="w-2 h-2 rounded-full bg-orange-400"></div>
              </div>
            )}
          </label>
        ))}
      </div>
      {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
    </div>
  );
};

const RadioField = ({ field, value, onChange, error }) => {
  // Use card grid styling for background selection fields
  if (
    field.section === "background_selection" ||
    field.styling?.displayType === "card_grid"
  ) {
    return (
      <CardGridField field={field} value={value} onChange={onChange} error={error} />
    );
  }

  return (
    <div>
      <label className="label">
        {field.label} {field.required && <span className="text-orange-300">*</span>}
      </label>
      {field.helpText && <div className="help">{field.helpText}</div>}
      <div className="space-y-3">
        {field.options?.map((option) => (
          <label
            key={option.value}
            className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all duration-300 hover:scale-[1.02] ${value === option.value
                ? "border-orange-400 bg-orange-500/20 text-white shadow-lg"
                : "border-white/20 bg-white/5 text-white/80 hover:bg-white/10 hover:border-white/30"
              }`}
          >
            <input
              type="radio"
              name={field.id}
              value={option.value}
              checked={value === option.value}
              onChange={onChange}
              required={field.required}
              className="sr-only"
            />
            <span className="text-sm font-medium">{option.label}</span>
          </label>
        ))}
      </div>
      {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
    </div>
  );
};

const CheckboxField = ({ field, value, onChange, error }) => {
  // When rendering radio fields with checkbox UI, enforce single selection
  const isSingle = field.type === FIELD_TYPES.RADIO;

  return (
    <div>
      <label className="label">
        {field.label} {field.required && <span className="text-orange-300">*</span>}
      </label>
      {field.helpText && <div className="help">{field.helpText}</div>}
      <div className="space-y-3 pl-4">
        {field.options?.map((option) => {
          const isChecked = isSingle
            ? value === option.value
            : Array.isArray(value) && value.includes(option.value);

          return (
            <label
              key={option.value}
              className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] ${isChecked
                  ? "border-orange-400 bg-orange-500/20 text-white"
                  : "border-white/20 bg-white/5 text-white/80 hover:bg-white/10 hover:border-white/30"
                }`}
            >
              <input
                type="checkbox"
                name={field.id}
                value={option.value}
                checked={isChecked}
                onChange={(e) => {
                  if (isSingle) {
                    const newValue = e.target.checked ? option.value : "";
                    onChange({ target: { name: field.id, value: newValue } });
                  } else {
                    const currentValues = Array.isArray(value) ? value : [];
                    const newValues = e.target.checked
                      ? [...currentValues, option.value]
                      : currentValues.filter((v) => v !== option.value);
                    onChange({ target: { name: field.id, value: newValues } });
                  }
                }}
                className="absolute opacity-0 w-0 h-0"
              />
              <div
                className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center transition-all flex-shrink-0 ${isChecked ? "border-orange-400 bg-orange-500" : "border-white/30 bg-transparent"
                  }`}
              >
                {isChecked && (
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <span className="text-sm font-medium text-left flex-1">{option.label}</span>
            </label>
          );
        })}
      </div>
      {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
    </div>
  );
};

const MultiSelectField = ({ field, value, onChange, error }) => {
  // Use card grid styling for multi-select fields in background section
  if (
    field.section === "background_selection" ||
    field.styling?.displayType === "card_grid"
  ) {
    return (
      <div>
        <label className="flex items-center gap-2 text-white font-medium mb-3">
          {field.label}
          {field.required && <span className="text-orange-300">*</span>}
        </label>
        {field.helpText && (
          <div className="text-white/70 text-sm mb-3">{field.helpText}</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-4">
          {field.options?.map((option) => {
            const isChecked = Array.isArray(value) && value.includes(option.value);

            return (
              <label
                key={option.value}
                className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] ${isChecked
                    ? "border-orange-400 bg-orange-500/20 text-white"
                    : "border-white/20 bg-white/5 text-white/80 hover:bg-white/10 hover:border-white/30"
                  }`}
              >
                <input
                  type="checkbox"
                  name={field.id}
                  value={option.value}
                  checked={isChecked}
                  onChange={(e) => {
                    const currentValues = Array.isArray(value) ? value : [];
                    const newValues = e.target.checked
                      ? [...currentValues, option.value]
                      : currentValues.filter((v) => v !== option.value);
                    onChange({ target: { name: field.id, value: newValues } });
                  }}
                  className="absolute opacity-0 w-0 h-0"
                />
                <div
                  className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center transition-all flex-shrink-0 ${isChecked ? "border-orange-400 bg-orange-500" : "border-white/30 bg-transparent"
                    }`}
                >
                  {isChecked && (
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <span className="text-sm font-medium text-left flex-1">{option.label}</span>
              </label>
            );
          })}
        </div>
        {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
      </div>
    );
  }

  return (
    <div>
      <label className="label">
        {field.label} {field.required && <span className="text-orange-300">*</span>}
      </label>
      {field.helpText && <div className="help">{field.helpText}</div>}
      <select
        name={field.id}
        multiple
        value={Array.isArray(value) ? value : []}
        onChange={(e) => {
          const selectedValues = Array.from(
            e.target.selectedOptions,
            (option) => option.value
          );
          onChange({ target: { name: field.id, value: selectedValues } });
        }}
        required={field.required}
        className={`input min-h-[120px] ${error ? "border-red-400" : ""}`}
      >
        {field.options?.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <div className="text-xs text-white/60 mt-1">{f("holdCtrl")}</div>
      {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
    </div>
  );
};

const SectionHeader = ({ section, sections }) => {
  const sectionConfig = sections?.[section];
  if (!sectionConfig) return null;

  // Dynamic icon mapping for all Lucide icons
  const IconComponent =
    {
      GraduationCap,
      BookOpen,
      Target,
      User,
      Settings,
      FileText,
      Heart,
      Star,
      Shield,
      Clock,
      Calendar,
      Camera,
      Music,
      Palette,
      Code,
      Database,
      Globe,
      Mail,
      Phone,
      Home,
    }[sectionConfig.icon] || BookOpen;

  // Extract color classes from sectionConfig.color if available
  const colorClasses = sectionConfig.color || "text-orange-400 bg-orange-500/20";
  const [textColor, bgColor] = colorClasses
    .split(" ")
    .filter((cls) => cls.startsWith("text-") || cls.startsWith("bg-"));

  const title =
    i18n.has && i18n.has(`form.sections.${section}.title`)
      ? i18n.t(`form.sections.${section}.title`)
      : sectionConfig.title;
  const description =
    i18n.has && i18n.has(`form.sections.${section}.description`)
      ? i18n.t(`form.sections.${section}.description`)
      : sectionConfig.description;

  return (
    <div className="mb-6 pb-4 border-b border-white/20">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${bgColor || "bg-orange-500/20"}`}>
          <IconComponent className={`w-5 h-5 ${textColor || "text-orange-400"}`} />
        </div>
        <h3 className="text-xl font-semibold text-white">{title}</h3>
      </div>
      {description && <p className="text-white/70 text-sm">{description}</p>}
    </div>
  );
};

// Main dynamic form component
export default function DynamicForm({
  config,
  onSubmit,
  initialData = {},
  isLoading = false,
  onFieldChange = null,
}) {
  const [formData, setFormData] = useState(() => {
    const initial = { ...initialData };
    // Initialize empty values for all fields
    config.fields?.forEach((field) => {
      if (initial[field.id] === undefined) {
        initial[field.id] = field.type === FIELD_TYPES.MULTI_SELECT ? [] : "";
      }
    });
    return initial;
  });

  const [loadingStudyFields, setLoadingStudyFields] = useState(false);
  const [studyFieldOptions, setStudyFieldOptions] = useState([]);
  const [errors, setErrors] = useState({});
  const [categoryOrder, setCategoryOrder] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [categorySelectOptions, setCategorySelectOptions] = useState([]);

  // Load dynamic study fields for field_of_study field
  useEffect(() => {
    const loadStudyFields = async () => {
      try {
        setLoadingStudyFields(true);
        const fields = await DynamicFieldService.getAllFields();
        const options = fields.map((field) => {
          const displayName =
            field.field_id === "stem"
              ? "STEM (Science, Technology, Engineering, Mathematics)"
              : field.field_id === "business"
                ? "Business & Commerce"
                : field.name;
          return {
            value: field.field_id,
            label: displayName,
            icon: field.icon,
            description: field.description,
          };
        });
        setStudyFieldOptions(options);
      } catch (error) {
        console.error("Error loading study fields:", error);
        // Fallback options
        setStudyFieldOptions([
          {
            value: "stem",
            label: "STEM (Science, Technology, Engineering, Mathematics)",
            icon: "🔬",
            description: "Science, Technology, Engineering, Math",
          },
          {
            value: "business",
            label: "Business & Commerce",
            icon: "💼",
            description: "Business & Economics",
          },
          {
            value: "social_sciences",
            label: "Social Sciences",
            icon: "🏛️",
            description: "Social Sciences & Humanities",
          },
          {
            value: "health_medicine",
            label: "Health & Medicine",
            icon: "⚕️",
            description: "Healthcare and Medical Sciences",
          },
          {
            value: "creative_arts",
            label: "Creative Arts",
            icon: "🎨",
            description: "Arts, Design, and Creative Fields",
          },
        ]);
      } finally {
        setLoadingStudyFields(false);
      }
    };

    // Only load if we have a field_of_study field in the config
    const hasFieldOfStudy = config.fields?.some(
      (field) => field.id === "field_of_study"
    );
    if (hasFieldOfStudy) {
      loadStudyFields();
    }
  }, [config.fields]);

  // Load dynamic categories for question_category select
  useEffect(() => {
    const hasCategoryField = config.fields?.some(
      (field) => field.id === "question_category"
    );
    if (!hasCategoryField) return;
    const loadCategories = async () => {
      try {
        setLoadingCategories(true);
        const categories = await DynamicQuestionCategoryService.getAllCategories();
        const options = (categories || [])
          .filter((c) => c.is_active !== false)
          .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
          .map((c) => ({ value: c.category_id, label: c.name }));
        setCategorySelectOptions(options);
      } catch (error) {
        console.error("Error loading categories for select:", error);
        setCategorySelectOptions([]);
      } finally {
        setLoadingCategories(false);
      }
    };
    loadCategories();
  }, [config.fields]);

  // Load dynamic category order
  useEffect(() => {
    const loadCategoryOrder = async () => {
      try {
        const categories = await DynamicCategoryService.getAllCategories();
        const order = categories
          .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
          .map((cat) => cat.category_id);
        setCategoryOrder(order);
      } catch (error) {
        console.error("Error loading category order:", error);
        // Fallback to default order
        setCategoryOrder([
          "background_selection",
          "personal_info",
          "academic_info",
          "preferences",
          "general",
        ]);
      }
    };

    loadCategoryOrder();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }

    // Call parent field change handler if provided
    if (onFieldChange) {
      onFieldChange(name, value, { ...formData, [name]: value });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    config.fields?.forEach((field) => {
      const value = formData[field.id];

      const isReq =
        field.required ||
        ["field_of_study", "question_category", "name", "email", "grade"].includes(field.id);
      if (isReq && (!value || value === "")) {
        const tf = translateField(field);
        newErrors[field.id] = `${tf.label} ${f("isRequired")}`;
      }
    });

    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const formErrors = validateForm();
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }

    onSubmit(formData);
  };

  const renderField = (field) => {
    const isAlwaysRequired =
      ["field_of_study", "question_category", "name", "email", "grade"].includes(
        field.id
      );
    const effectiveField = isAlwaysRequired ? { ...field, required: true } : field;
    const tField = translateField(effectiveField);

    const commonProps = {
      field: tField,
      value: formData[tField.id],
      onChange: handleInputChange,
      error: errors[tField.id],
    };

    // Special handling for field_of_study with dynamic options (dropdown)
    if (tField.id === "field_of_study") {
      if (loadingStudyFields) {
        return (
          <div key={tField.id} className="flex items-center justify-center py-8">
            <Loader className="w-6 h-6 text-orange-400 animate-spin" />
            <span className="ml-2 text-white/70">{f("loadingStudyFields")}</span>
          </div>
        );
      }
      const fieldWithOptions = {
        ...tField,
        type: FIELD_TYPES.SELECT,
        options: studyFieldOptions.map((opt) => ({ ...opt, label: opt.label })),
        placeholder: tField.placeholder || f("selectFieldOfStudy"),
      };
      return (
        <SelectField
          key={fieldWithOptions.id}
          field={fieldWithOptions}
          value={formData[fieldWithOptions.id]}
          onChange={handleInputChange}
          error={errors[fieldWithOptions.id]}
        />
      );
    }

    // Special handling for question_category with dynamic options (dropdown)
    if (tField.id === "question_category") {
      if (loadingCategories) {
        return (
          <div key={tField.id} className="flex items-center justify-center py-8">
            <Loader className="w-6 h-6 text-orange-400 animate-spin" />
            <span className="ml-2 text-white/70">{f("loadingCategories")}</span>
          </div>
        );
      }
      const categoryField = {
        ...tField,
        type: FIELD_TYPES.SELECT,
        options: categorySelectOptions,
        placeholder: tField.placeholder || f("selectCategory"),
      };
      return (
        <SelectField
          key={categoryField.id}
          field={categoryField}
          value={formData[categoryField.id]}
          onChange={handleInputChange}
          error={errors[categoryField.id]}
        />
      );
    }

    switch (tField.type) {
      case FIELD_TYPES.TEXT:
      case FIELD_TYPES.EMAIL:
      case FIELD_TYPES.PASSWORD:
      case FIELD_TYPES.NUMBER:
        return <TextField key={tField.id} {...commonProps} />;
      case FIELD_TYPES.TEXTAREA:
        return <TextAreaField key={tField.id} {...commonProps} />;
      case FIELD_TYPES.SELECT:
        return <SelectField key={tField.id} {...commonProps} />;
      case FIELD_TYPES.RADIO:
        return <RadioField key={tField.id} {...commonProps} />;
      case FIELD_TYPES.CHECKBOX:
        return <CheckboxField key={tField.id} {...commonProps} />;
      case FIELD_TYPES.MULTI_SELECT:
        return <MultiSelectField key={tField.id} {...commonProps} />;
      default:
        return null;
    }
  };

  if (!config || !config.fields) {
    return (
      <div className="text-white text-center py-8">
        <p>{f("noConfig")}</p>
      </div>
    );
  }

  // Group fields by section for organized rendering
  const fieldsBySection = config.fields.reduce((acc, field) => {
    const section = field.section || "general";
    if (!acc[section]) {
      acc[section] = [];
    }
    acc[section].push(field);
    return acc;
  }, {});

  // Use dynamic category order, falling back to sections that exist in fields
  const allSectionsInFields = Object.keys(fieldsBySection);
  const orderedSections = [
    ...categoryOrder.filter((section) => fieldsBySection[section]),
    ...allSectionsInFields.filter((section) => !categoryOrder.includes(section)),
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {orderedSections.map((sectionName) => {
        const sectionFields = fieldsBySection[sectionName].sort(
          (a, b) => (a.order || 0) - (b.order || 0)
        );

        return (
          <div key={sectionName} className="space-y-6">
            <SectionHeader section={sectionName} sections={config.sections} />
            <div className="space-y-6">{sectionFields.map(renderField)}</div>
          </div>
        );
      })}

      <div className="flex justify-end pt-6 border-t border-white/20">
        <button
          type="submit"
          disabled={isLoading}
          className="px-8 py-3 bg-gradient-to-r from-orange-600 via-orange-500 to-red-600 hover:from-orange-700 hover:via-orange-600 hover:to-red-700 disabled:from-orange-500/50 disabled:via-orange-500/50 disabled:to-red-500/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          {isLoading ? f("submitting") : f("submit")}
        </button>
      </div>
    </form>
  );
}
