# Supabase Storage Setup Script

A comprehensive Node.js script for configuring Supabase Storage buckets with security policies, backup scheduling, and integration testing. Designed for secure file storage in the AI Integration Platform.

## 🚀 Features

- **Secure Bucket Creation**: Private bucket with RLS policies for authenticated access
- **File Type Validation**: Restricted to PDF/JSON previews with size limits
- **Backup Automation**: Daily backup scheduling with retention policies
- **Access Testing**: Comprehensive read/write/delete validation
- **Error Resilience**: Retry logic with graceful degradation
- **AIM/PROGRESS Logging**: Integrated task tracking for Day 2 activities
- **User Confirmation**: Interactive verification of setup completion

## 📦 Installation & Setup

```bash
# Install dependencies
npm install

# Ensure AI_integration/.env contains:
# SUPABASE_URL=your-project-url
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 🛠️ Usage

### Complete Storage Setup
```bash
npm run setup-storage
```

### Individual Components
```bash
# Run backup manually
npm run backup-storage

# Show backup scheduling help
node backup_schedule.js --schedule

# Test backup cleanup only
node backup_schedule.js --cleanup-only
```

## 🗄️ Storage Configuration

### Bucket: `reports-previews`

**Settings:**
- **Public Access**: ❌ Disabled (Private)
- **File Size Limit**: 10MB per file
- **Allowed MIME Types**: `application/pdf`, `application/json`, `text/plain`
- **RLS Policies**: ✅ Enabled

### Security Policies

**Row-Level Security (RLS) Policies Applied:**

1. **Upload Policy**: Users can upload to their own folder
   ```sql
   CREATE POLICY "Users can upload their own files" ON storage.objects
   FOR INSERT WITH CHECK (
     bucket_id = 'reports-previews' AND
     auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

2. **Read Policy**: Users can view their own files
   ```sql
   CREATE POLICY "Users can view their own files" ON storage.objects
   FOR SELECT USING (
     bucket_id = 'reports-previews' AND
     auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

3. **Update Policy**: Users can modify their own files
4. **Delete Policy**: Users can remove their own files

## 🔧 File Organization

### Expected File Structure
```
reports-previews/
├── {user_id}/
│   ├── reports/
│   │   ├── monthly_report_2025-01.pdf
│   │   └── weekly_summary_2025-01.json
│   └── previews/
│       ├── spec_preview_123.json
│       └── analysis_preview_456.pdf
```

### Naming Convention
- **User Isolation**: Files stored in `{user_id}/` subfolders
- **Type Separation**: `reports/` and `previews/` subdirectories
- **Descriptive Names**: Clear, timestamped filenames

## 💾 Backup System

### Automated Daily Backups
- **Schedule**: Midnight UTC daily
- **Retention**: 7 days rolling window
- **Storage**: Separate dated backup buckets
- **Cleanup**: Automatic old backup removal

### Backup Process
1. **List** all files in `reports-previews` bucket
2. **Download** each file
3. **Upload** to dated backup bucket (`backups-YYYY-MM-DD`)
4. **Verify** successful transfers
5. **Clean up** backups older than 7 days

### Manual Backup Testing
```bash
# Run backup immediately
npm run backup-storage

# View backup schedule options
node backup_schedule.js --schedule
```

## 🧪 Testing & Validation

### Automated Tests Included
- ✅ **Bucket Creation**: Verifies bucket exists and is configured
- ✅ **File Upload**: Tests authenticated upload with validation
- ✅ **File Download**: Confirms read access and content integrity
- ✅ **File Listing**: Validates directory browsing
- ✅ **File Deletion**: Ensures cleanup works properly
- ✅ **RLS Enforcement**: Confirms security policies work

### Test File Details
- **Name**: `test-{timestamp}.json`
- **Content**: JSON with test metadata
- **Path**: `test/test-{timestamp}.json`
- **Cleanup**: Automatic removal after testing

## 🚨 Error Handling

### Retry Logic
- **Max Retries**: 3 attempts for all operations
- **Backoff**: Progressive delay (1s, 2s, 3s)
- **Transient Errors**: Network timeouts, temporary unavailability
- **Permanent Errors**: Permission denied, invalid configuration

### Error Categories
- **Storage Errors**: Bucket creation, file operations
- **Permission Errors**: RLS policy violations, auth failures
- **Network Errors**: Connection timeouts, API limits
- **Validation Errors**: File type, size limit violations

### Critical Failure Notifications
- **Email Stub**: Configurable for production email services
- **Logging**: Comprehensive error details in task logs
- **Graceful Degradation**: Continues with available functionality

## 🔗 Integration with Anmol's Backend

### File Upload Endpoint
```javascript
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Upload report/preview file
app.post('/api/upload-file', async (req, res) => {
  try {
    const { file, type, userId } = req.body; // file as base64 or buffer

    // Validate file type and size
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      return res.status(400).json({ error: 'Invalid file type' });
    }

    if (file.size > MAX_FILE_SIZE) {
      return res.status(400).json({ error: 'File too large' });
    }

    // Upload to user-specific path
    const filePath = `${userId}/${type}/${Date.now()}_${file.name}`;
    const { data, error } = await supabase.storage
      .from('reports-previews')
      .upload(filePath, file.buffer, {
        contentType: file.type,
        upsert: false
      });

    if (error) throw error;

    res.json({
      success: true,
      filePath,
      publicUrl: data.path // For private files, use signed URLs
    });

  } catch (error) {
    console.error('Upload failed:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});
```

### File Access with Signed URLs
```javascript
// Generate temporary access URL for private files
app.get('/api/file-url/:filePath', async (req, res) => {
  try {
    const { filePath } = req.params;
    const { data, error } = await supabase.storage
      .from('reports-previews')
      .createSignedUrl(filePath, 3600); // 1 hour expiry

    if (error) throw error;

    res.json({ signedUrl: data.signedUrl });

  } catch (error) {
    res.status(500).json({ error: 'Could not generate file URL' });
  }
});
```

### File Management
```javascript
// List user files
app.get('/api/files/:userId/:type', async (req, res) => {
  try {
    const { userId, type } = req.params;
    const { data, error } = await supabase.storage
      .from('reports-previews')
      .list(`${userId}/${type}/`);

    if (error) throw error;

    res.json({ files: data });

  } catch (error) {
    res.status(500).json({ error: 'Could not list files' });
  }
});

// Delete file
app.delete('/api/files/:filePath', async (req, res) => {
  try {
    const { filePath } = req.params;
    const { error } = await supabase.storage
      .from('reports-previews')
      .remove([filePath]);

    if (error) throw error;

    res.json({ success: true });

  } catch (error) {
    res.status(500).json({ error: 'Could not delete file' });
  }
});
```

## 📊 Monitoring & Analytics

### Storage Usage Tracking
```javascript
// Get bucket statistics
const { data: files, error } = await supabase.storage
  .from('reports-previews')
  .list('', { limit: 1000 });

const totalFiles = files.length;
const totalSize = files.reduce((sum, file) => sum + file.metadata.size, 0);
const fileTypes = files.reduce((types, file) => {
  const type = file.metadata.mimetype;
  types[type] = (types[type] || 0) + 1;
  return types;
}, {});
```

### Backup Status Monitoring
```javascript
// Check backup bucket exists and is current
const backupBucket = `backups-${new Date().toISOString().split('T')[0]}`;
const { data: backupFiles, error } = await supabase.storage
  .from(backupBucket)
  .list('');

if (error) {
  console.warn('Backup verification failed:', error.message);
} else {
  console.log(`Backup contains ${backupFiles.length} files`);
}
```

## 🔐 Security Considerations

### Access Control
- **Authentication Required**: All operations need valid Supabase Auth
- **User Isolation**: Files stored in user-specific directories
- **Path Validation**: Prevent directory traversal attacks
- **File Type Validation**: Server-side MIME type checking

### Data Protection
- **Encryption**: Files encrypted at rest in Supabase
- **Private Access**: No public URLs for sensitive files
- **Signed URLs**: Temporary access for file downloads
- **Backup Security**: Backup buckets also private

### Compliance
- **Data Residency**: Files stored in Supabase's infrastructure
- **Retention Policies**: Configurable backup retention
- **Audit Logging**: All operations logged via AIM/PROGRESS system
- **Access Monitoring**: Track file access patterns

## 🚀 Deployment & Scheduling

### Production Deployment
```bash
# Environment setup
export SUPABASE_URL="your-production-url"
export SUPABASE_SERVICE_ROLE_KEY="your-production-service-key"

# Run setup
npm run setup-storage
```

### Cron Job Setup (Linux/Mac)
```bash
# Daily backup at midnight UTC
crontab -e
# Add: 0 0 * * * cd /path/to/project && npm run backup-storage
```

### Windows Task Scheduler
```powershell
# Create daily backup task
schtasks /create /tn "SupabaseStorageBackup" /tr "npm run backup-storage" /sc daily /st 00:00
```

### Docker Integration
```yaml
# docker-compose.yml
services:
  backup-service:
    build: .
    command: node backup_schedule.js
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    restart: unless-stopped
```

## 📋 Troubleshooting

### Common Issues

**"Bucket already exists"**
- ✅ Expected behavior - script handles idempotent operations
- ✅ Verify bucket settings match requirements

**"RLS policy creation failed"**
- 🔧 Apply policies manually in Supabase SQL Editor
- 🔧 Check service role permissions

**"File upload failed: Invalid file type"**
- ✅ Verify file MIME type is in allowed list
- ✅ Check file size is under 10MB limit

**"Backup creation failed"**
- 🔧 Check service role has storage admin permissions
- 🔧 Verify backup bucket naming doesn't conflict

**"Signed URL generation failed"**
- 🔧 Ensure user is authenticated
- 🔧 Check RLS policies allow file access

### Debug Mode
```bash
# Enable verbose logging
DEBUG=supabase-storage node supabase_storage_setup.js
```

### Health Checks
```javascript
// Storage health check endpoint
app.get('/api/storage/health', async (req, res) => {
  try {
    // Test bucket access
    const { data, error } = await supabase.storage
      .from('reports-previews')
      .list('', { limit: 1 });

    if (error) throw error;

    // Test backup access
    const backupBucket = `backups-${new Date().toISOString().split('T')[0]}`;
    const { data: backupData, error: backupError } = await supabase.storage
      .from(backupBucket)
      .list('', { limit: 1 });

    res.json({
      status: 'healthy',
      bucket: 'reports-previews',
      backup_bucket: backupBucket,
      can_access_bucket: !error,
      can_access_backup: !backupError
    });

  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});
```

## 🎯 Success Metrics

After successful setup, verify:

- ✅ Bucket `reports-previews` exists and is private
- ✅ RLS policies are active (test with different users)
- ✅ File upload/download works for authenticated users
- ✅ Backup script runs without errors
- ✅ Old backups are automatically cleaned up
- ✅ Task logging shows Day 2 completion

## 📞 Support & Maintenance

### Regular Maintenance
- **Monitor Storage Usage**: Check Supabase dashboard regularly
- **Review Backup Logs**: Ensure backups complete successfully
- **Update Policies**: Modify RLS rules as requirements change
- **Security Audits**: Regular review of access patterns

### Emergency Procedures
- **Data Recovery**: Use backup buckets for file restoration
- **Access Issues**: Check RLS policies and user permissions
- **Storage Full**: Implement cleanup or upgrade plans
- **Security Breach**: Immediate policy review and access revocation

---

**Ready to secure your file storage? Run `npm run setup-storage` to begin!** 🚀

The storage setup provides enterprise-grade file management with comprehensive security, backup, and monitoring capabilities for your AI Integration Platform.