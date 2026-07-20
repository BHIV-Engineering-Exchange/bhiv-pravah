# Dynamic Form Configuration Setup Guide

This guide explains how to set up and use the dynamic form configuration feature that allows admins to customize student intake forms.

## Overview

The form configuration system allows administrators to:

- Create custom intake forms with various field types
- Set validation rules and requirements
- Reorder fields and customize labels
- Use different input types (text, number, select, radio, checkbox, etc.)
- Make changes that immediately reflect for all students

## Setup Instructions

### 1. Database Setup

First, you need to create the `form_configurations` table in your Supabase database:

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Run the SQL script located at `src/sql/create_form_configurations_table.sql`

This will create:

- The `form_configurations` table
- Necessary indexes for performance
- Row Level Security policies
- A default form configuration matching the original intake form
- Automatic timestamp updating

### 2. Environment Variables

Ensure your `.env.local` file has the required Supabase configuration:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_SUPABASE_TABLE=students

# Admin Credentials (change these for security)
VITE_ADMIN_USERNAME=admin
VITE_ADMIN_PASSWORD=admin123
```

### 3. Admin Access

The admin panel is accessible at `/admin` with the credentials configured in your `.env.local` file:

- Username: Set via `VITE_ADMIN_USERNAME` (default: `admin`)
- Password: Set via `VITE_ADMIN_PASSWORD` (default: `admin123`)

**Security Note:** Change these default credentials in your `.env.local` file for production use.

## Using the Form Configuration Feature

### Accessing Form Configuration

1. Navigate to `http://localhost:5174/admin`
2. Log in with admin credentials
3. Click on the "Form Configuration" tab

### Creating a New Form Configuration

1. Click "Create Form" button
2. Fill in the form name and description
3. Add fields using the "Add Field" button
4. Configure each field:
   - **Field ID**: Unique identifier (e.g., `student_name`)
   - **Field Type**: Choose from text, number, email, textarea, select, radio, checkbox, multi-select
   - **Label**: Display name for the field
   - **Placeholder**: Hint text for users
   - **Required**: Whether the field is mandatory
   - **Help Text**: Additional guidance for users
   - **Options**: For select/radio/checkbox fields
   - **Validation**: Min/max values or lengths

### Field Types Available

- **Text**: Single-line text input
- **Email**: Email validation
- **Number**: Numeric input with min/max validation
- **Textarea**: Multi-line text input
- **Select**: Dropdown selection
- **Radio**: Single choice from options
- **Checkbox**: Multiple choice from options
- **Multi-select**: Multiple selection dropdown

### Managing Form Configurations

- **Edit**: Modify existing configurations
- **Delete**: Remove configurations (except active ones)
- **Activate**: Only one configuration can be active at a time
- **Reorder**: Use up/down arrows to change field order

### Form Configuration Structure

Each form configuration contains:

```json
{
  "id": "unique_identifier",
  "name": "Form Name",
  "description": "Form description",
  "fields": [
    {
      "id": "field_id",
      "type": "text|number|email|textarea|select|radio|checkbox|multi_select",
      "label": "Field Label",
      "placeholder": "Placeholder text",
      "required": true|false,
      "order": 1,
      "helpText": "Additional help",
      "options": [
        {"value": "option1", "label": "Option 1"},
        {"value": "option2", "label": "Option 2"}
      ],
      "validation": {
        "min": 0,
        "max": 100,
        "minLength": 2,
        "maxLength": 255,
        "pattern": "regex_pattern"
      }
    }
  ],
  "is_active": true,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## How It Works

### Real-time Updates

When an admin saves a form configuration:

1. The configuration is stored in Supabase
2. The previous active configuration is deactivated
3. The new configuration becomes active
4. All students immediately see the new form when they visit `/intake`

### Data Storage

Student responses are stored in the existing `students` table in the `responses` JSONB field. The dynamic form system:

- Processes different field types appropriately
- Handles arrays for multi-select fields
- Converts comma-separated values for skills/interests
- Validates data according to field rules

### Backward Compatibility

The system maintains backward compatibility:

- Existing student data remains accessible
- Default configuration matches the original form
- Missing fields are handled gracefully

## Troubleshooting

### Common Issues

1. **Form not loading**: Check Supabase connection and table creation
2. **Changes not reflecting**: Ensure only one configuration is active
3. **Validation errors**: Check field configuration and validation rules
4. **Data not saving**: Verify Supabase permissions and table structure

### Database Permissions

Ensure your Supabase RLS policies allow:

- Reading form configurations for all users
- Writing form configurations for admin users
- Reading/writing student data for authenticated users

### Development Tips

- Use the browser's developer tools to inspect form data
- Check the Network tab for API calls to Supabase
- Verify form configuration JSON structure
- Test with different field types and validation rules

## API Reference

### FormConfigService Methods

- `getActiveFormConfig()`: Get the currently active form configuration
- `saveFormConfig(config)`: Save a new or updated configuration
- `getAllFormConfigs()`: Get all form configurations
- `deleteFormConfig(id)`: Delete a configuration
- `validateFormConfig(config)`: Validate configuration structure

### Field Types Constants

```javascript
import { FIELD_TYPES } from "../lib/formConfigService";

FIELD_TYPES.TEXT; // 'text'
FIELD_TYPES.EMAIL; // 'email'
FIELD_TYPES.NUMBER; // 'number'
FIELD_TYPES.TEXTAREA; // 'textarea'
FIELD_TYPES.SELECT; // 'select'
FIELD_TYPES.RADIO; // 'radio'
FIELD_TYPES.CHECKBOX; // 'checkbox'
FIELD_TYPES.MULTI_SELECT; // 'multi_select'
```

## Security Considerations

- Admin authentication is basic (username/password)
- Consider implementing proper authentication for production
- RLS policies should be configured according to your security requirements
- Validate form configurations on the server side
- Sanitize user inputs appropriately

## Future Enhancements

Potential improvements:

- Drag-and-drop field reordering
- Field templates and presets
- Form preview functionality
- Advanced validation rules
- Conditional field display
- Form analytics and submission tracking
- Export/import form configurations
- Multi-language support
