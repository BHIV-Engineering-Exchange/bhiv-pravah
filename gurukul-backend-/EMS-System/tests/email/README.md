# Email Testing Suite

This folder contains tests for email functionality in the School Management System.

## Test Files

### 1. `test_email_config.py`

Tests email configuration and SMTP connection.

**Usage**:
```bash
python tests/email/test_email_config.py
```

**What it does**:
- Checks email configuration from `.env`
- Validates SMTP settings
- Sends a test email to `MAIL_USERNAME`
- Reports success or failure

**Expected Output** (Success):
```
[SUCCESS] Email sent successfully!
Please check your inbox: your-email@example.com
Also check spam/junk folder!
```

### 2. `test_admin_invitation.py`

Tests the complete admin invitation email flow.

**Usage**:
```bash
python tests/email/test_admin_invitation.py <admin-email>
```

**Example**:
```bash
python tests/email/test_admin_invitation.py admin@example.com
```

**What it does**:
- Finds admin user by email
- Generates password setup token
- Creates setup link
- Sends invitation email
- Shows next steps

**Prerequisites**:
- Admin user must exist in database
- Email configuration must be correct

## Running All Tests

### Quick Test (Email Config Only)

```bash
python tests/email/test_email_config.py
```

### Full Test (With Admin Invitation)

1. Make sure an admin user exists:
   ```sql
   -- Check in database or create via Super Admin dashboard
   ```

2. Run the test:
   ```bash
   python tests/email/test_admin_invitation.py admin@example.com
   ```

## Troubleshooting

### Test Fails: Authentication Error

**Problem**: `SMTPAuthenticationError: Authentication failed`

**Solution**:
1. Check `.env` file credentials
2. Verify `MAIL_USERNAME` is Brevo account email
3. Verify `MAIL_PASSWORD` is Brevo SMTP key
4. Restart backend server

### Test Fails: Email Not Sent

**Problem**: Email sending fails silently

**Solution**:
1. Check backend logs
2. Verify email configuration
3. Check Brevo dashboard
4. Verify SMTP is enabled in Brevo

### Test Succeeds But Email Not Received

**Problem**: Test shows success but no email

**Solution**:
1. Check spam/junk folder
2. Wait 2-5 minutes
3. Check Brevo dashboard for delivery status
4. Verify recipient email is correct

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Test Email Configuration
  run: python tests/email/test_email_config.py
  env:
    MAIL_USERNAME: ${{ secrets.MAIL_USERNAME }}
    MAIL_PASSWORD: ${{ secrets.MAIL_PASSWORD }}
```

## Best Practices

1. **Run tests before production deployment**
2. **Test with real email addresses**
3. **Check spam folders**
4. **Monitor Brevo dashboard**
5. **Keep test results for reference**

## Notes

- Tests use actual email sending (not mocked)
- Tests require valid email configuration
- Tests may be rate-limited by email provider
- Free tier limits: 300 emails/day (Brevo)
