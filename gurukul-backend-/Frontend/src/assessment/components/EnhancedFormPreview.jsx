import React, { useState, useEffect } from 'react';
import { EnhancedFormConfigService } from '../lib/enhancedFormConfigService';
import DynamicForm from './DynamicForm';

const EnhancedFormPreview = ({ config }) => {
  const [enhancedConfig, setEnhancedConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [previewData, setPreviewData] = useState({});

  useEffect(() => {
    const createPreviewConfig = async () => {
      try {
        setLoading(true);
        
        // Create enhanced configuration with background selection
        const enhanced = await EnhancedFormConfigService.createEnhancedFormConfig(
          config,
          config.background_selection_config || {},
          config.include_background_selection !== false
        );
        
        setEnhancedConfig(enhanced);
      } catch (error) {
        console.error('Error creating preview config:', error);
        setEnhancedConfig(config); // Fallback to original config
      } finally {
        setLoading(false);
      }
    };

    createPreviewConfig();
  }, [config]);

  const handlePreviewFieldChange = (fieldName, fieldValue, updatedFormData) => {
    setPreviewData(updatedFormData);
  };

  const handlePreviewSubmit = (formData) => {
    console.log('Preview form submission:', formData);
    alert('This is a preview - form submission is disabled');
  };

  if (loading) {
    return (
      <div className=\"flex items-center justify-center py-12\">
        <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-orange-400\"></div>
        <span className=\"ml-3 text-white/70\">Loading preview...</span>
      </div>
    );
  }

  if (!enhancedConfig) {
    return (
      <div className=\"text-center py-12 text-white/60\">
        <p>Preview not available</p>
      </div>
    );
  }

  return (
    <div className=\"space-y-6\">
      <div className=\"p-4 bg-blue-500/10 border border-blue-400/30 rounded-xl\">
        <p className=\"text-blue-200 text-sm\">
          📋 This is a preview of your form. Background selection fields are {enhancedConfig.hasBackgroundSelection ? 'enabled' : 'disabled'}.
        </p>
      </div>
      
      <div className=\"bg-black/20 border border-white/10 rounded-xl p-6\">
        <DynamicForm
          config={enhancedConfig}
          onSubmit={handlePreviewSubmit}
          initialData={previewData}
          isLoading={false}
          onFieldChange={handlePreviewFieldChange}
        />
      </div>
    </div>
  );
};

export default EnhancedFormPreview;"