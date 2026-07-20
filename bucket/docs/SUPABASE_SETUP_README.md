# Supabase Database Setup Script

A production-ready Node.js script for automated Supabase PostgreSQL database setup with comprehensive error handling, security features, and integration contracts for the AI Integration Platform.

## 🚀 Features

- **Programmatic Setup**: Automated Supabase project provisioning with manual fallbacks
- **Production-Ready Tables**: Three core tables with constraints, indexes, and RLS policies
- **Security First**: Row-level security, encrypted credential sharing, input validation
- **Error Resilience**: Retry logic, transaction rollbacks, graceful degradation
- **Comprehensive Logging**: Structured JSON logging with AIM/PROGRESS format
- **Testing**: Built-in test queries and validation
- **Modular Design**: Testable functions and clean separation of concerns

## 📋 Prerequisites

- Node.js 16.0.0 or higher
- npm or yarn
- Supabase account (free tier available)
- Environment variables configured

## 🛠️ Installation

```bash
# Navigate to the project root directory
cd /path/to/agentBASKETS

# Install dependencies
npm install

# The script will automatically read from AI_integration/.env
# Add your Supabase credentials to that file
```

## ⚙️ Environment Configuration

The script reads environment variables from `AI_integration/.env`. Add the following variables to that file:

```env
# Required: Supabase Project Credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Optional: Encryption for credential sharing
ENCRYPTION_KEY=your-secure-encryption-key-here

# Environment
NODE_ENV=development
```

### Getting Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and sign in
2. Create a new project or select existing one
3. Go to Settings → API
4. Copy the following values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY`
   - **service_role secret** → `SUPABASE_SERVICE_ROLE_KEY`

## 🗄️ Database Schema

### Tables Created

#### 1. `specs` Table
```sql
- id: UUID (Primary Key, auto-generated)
- prompt: TEXT (Required)
- json_spec: JSONB (Required, validated structure)
- created_at: TIMESTAMP (Default: NOW())
- updated_at: TIMESTAMP (Auto-updated)
- user_id: UUID (Foreign Key to auth.users)
```

**Features:**
- JSON schema validation for `json_spec`
- Automatic `updated_at` timestamp
- Row-level security (RLS) enabled
- Indexes on frequently queried fields

#### 2. `evaluations` Table
```sql
- id: UUID (Primary Key, auto-generated)
- spec_id: UUID (Foreign Key to specs, CASCADE delete)
- rating: INTEGER (Required, 1-10 range)
- feedback: TEXT
- evaluator_id: UUID (Foreign Key to auth.users)
- created_at: TIMESTAMP (Default: NOW())
```

**Features:**
- Rating constraint (1-10)
- Cascade delete on spec deletion
- RLS policies for authenticated access

#### 3. `iterations` Table
```sql
- id: UUID (Primary Key, auto-generated)
- spec_id: UUID (Foreign Key to specs, CASCADE delete)
- iteration_number: INTEGER (Required, unique per spec)
- changes: JSONB
- status: ENUM ('pending', 'in_progress', 'completed', 'failed')
- created_at: TIMESTAMP (Default: NOW())
```

**Features:**
- Unique constraint on `(spec_id, iteration_number)`
- Status enum validation
- RLS policies for data isolation

### Security Policies

All tables include Row-Level Security (RLS) policies ensuring:
- Users can only access their own data
- Authenticated access required
- Proper foreign key relationships
- Cascade delete protection

## 🚀 Usage

### Basic Setup
```bash
# Ensure you're in the project root directory
cd /path/to/agentBASKETS

# Make sure AI_integration/.env exists with your Supabase credentials
# Then run the complete setup
npm run setup

# Or directly with node
node supabase_setup.js
```

### Command Line Options
```bash
# Show help
npm run help
node supabase_setup.js --help

# Show manual setup instructions
npm run manual-setup
node supabase_setup.js --manual-setup

# Run only tests (assumes tables exist)
npm run test
node supabase_setup.js --test-only

# Show cleanup instructions
npm run cleanup
node supabase_setup.js --cleanup
```

### Example Output
```json
{"timestamp":"2025-01-15T10:30:00.000Z","type":"AIM","day":1,"note":"Starting Supabase PostgreSQL database setup..."}
{"timestamp":"2025-01-15T10:30:01.000Z","type":"PROGRESS","step":"Initializing Supabase client"}
{"timestamp":"2025-01-15T10:30:02.000Z","type":"SUCCESS","message":"Supabase client initialized and connected"}
{"timestamp":"2025-01-15T10:30:03.000Z","type":"PROGRESS","step":"Creating specs table"}
{"timestamp":"2025-01-15T10:30:05.000Z","type":"SUCCESS","table":"specs","message":"Table created with constraints and RLS"}
{"timestamp":"2025-01-15T10:30:10.000Z","type":"PROGRESS","day":1,"done":["specs_table","evaluations_table","iterations_table","test_queries","encrypted_credentials"],"failed":[],"grateful":"Successfully set up Supabase database with all tables, constraints, and RLS policies"}
```

## 🔐 Secure Credential Sharing

The script automatically generates encrypted credentials for secure sharing with Anmol:

1. **Automatic Encryption**: Credentials are encrypted using AES-256-CBC
2. **File Output**: Encrypted data saved to timestamped `.enc` file
3. **Secure Sharing**: Share the encrypted file via secure channels
4. **Decryption**: Anmol can decrypt using the shared secret

### Manual Credential Sharing (Fallback)
If automation fails, share credentials manually:
1. Never share credentials in plain text
2. Use encrypted email or secure file sharing
3. Rotate credentials after sharing
4. Use environment variables in production

## 🧪 Testing & Validation

The script includes comprehensive testing:

### Built-in Tests
- **Table Creation**: Validates all tables and constraints
- **RLS Policies**: Ensures security policies work
- **Foreign Keys**: Tests referential integrity
- **Data Operations**: CRUD operations validation
- **Join Queries**: Complex query testing

### Manual Testing
```javascript
// Example integration test queries for Anmol's backend
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Create a spec
const { data, error } = await supabase
  .from('specs')
  .insert({
    prompt: 'Generate a web app specification',
    json_spec: { type: 'web_app', components: ['frontend', 'backend'] },
    user_id: userId
  });

// Add evaluation
const { data, error } = await supabase
  .from('evaluations')
  .insert({
    spec_id: specId,
    rating: 9,
    feedback: 'Excellent structure',
    evaluator_id: userId
  });

// Create iteration
const { data, error } = await supabase
  .from('iterations')
  .insert({
    spec_id: specId,
    iteration_number: 1,
    changes: { added: 'validation', modified: 'structure' },
    status: 'completed'
  });
```

## 🔧 Integration Contracts

### For Anmol's Backend

#### Reading Data
```javascript
// Get specs with evaluations and iterations
const { data, error } = await supabase
  .from('specs')
  .select(`
    *,
    evaluations (
      rating,
      feedback,
      created_at
    ),
    iterations (
      iteration_number,
      status,
      changes
    )
  `)
  .eq('user_id', userId);
```

#### Writing Data
```javascript
// Insert operations (specs, evaluations, iterations)
const { data, error } = await supabase
  .from('table_name')
  .insert(recordData);
```

#### Real-time Subscriptions
```javascript
// Subscribe to spec changes
const subscription = supabase
  .channel('specs_changes')
  .on('postgres_changes',
    { event: '*', schema: 'public', table: 'specs' },
    (payload) => console.log('Change received!', payload)
  )
  .subscribe();
```

## 🚨 Error Handling

### Common Issues & Solutions

#### 1. Connection Failed
```
Error: Supabase connection failed
```
**Solution**: Check credentials and network connectivity

#### 2. Permission Denied
```
Error: permission denied for table
```
**Solution**: Use service role key for schema changes

#### 3. RLS Policy Violation
```
Error: new row violates row-level security policy
```
**Solution**: Ensure user is authenticated and owns the data

#### 4. Foreign Key Constraint
```
Error: insert or update violates foreign key constraint
```
**Solution**: Ensure referenced records exist

### Retry Logic
- **Max Retries**: 3 attempts
- **Backoff**: Exponential delay (1s, 2s, 3s)
- **Transient Errors**: Network timeouts, temporary unavailability

## 🧹 Cleanup

### Automatic Cleanup
The script handles cleanup on failures automatically.

### Manual Cleanup
```bash
# Show cleanup instructions
npm run cleanup

# Or connect to Supabase SQL editor and run:
DROP TABLE IF EXISTS iterations CASCADE;
DROP TABLE IF EXISTS evaluations CASCADE;
DROP TABLE IF EXISTS specs CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column();
```

## 📊 Monitoring & Logging

### Log Types
- **AIM**: Setup objectives and progress notes
- **PROGRESS**: Step-by-step execution status
- **SUCCESS**: Completed operations
- **ERROR**: Failures with stack traces
- **TEST**: Test query results

### Log Analysis
```bash
# View recent logs
tail -f setup.log

# Parse JSON logs
cat setup.log | jq '.'

# Filter by type
cat setup.log | jq 'select(.type == "ERROR")'
```

## 🔒 Security Considerations

1. **Never commit credentials** to version control
2. **Use environment variables** for all secrets
3. **Rotate credentials** regularly
4. **Enable RLS** in production
5. **Use HTTPS** for all connections
6. **Validate inputs** on both client and server
7. **Monitor access logs** for suspicious activity

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] SSL/TLS enabled
- [ ] RLS policies active
- [ ] Backups configured
- [ ] Monitoring alerts set up
- [ ] Rate limiting configured

### CI/CD Integration
```yaml
# Example GitHub Actions
- name: Setup Supabase Database
  run: |
    npm ci
    npm run setup
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the structured logs for error details
3. Ensure all prerequisites are met
4. Try the manual setup process
5. Check Supabase status page for outages

## 📝 Changelog

### v1.0.0
- Initial production release
- Complete table schema with constraints
- RLS policies implementation
- Encrypted credential sharing
- Comprehensive error handling
- Built-in testing suite

---

**Ready to set up your Supabase database? Run `npm run setup` and let the automation handle the rest!** 🚀