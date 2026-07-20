# 📧 Email Setup Guide for EMS Dashboard

## 🎯 Goal
Enable **real email sending** so employees receive emails when you send them from the EMS Dashboard.

---

## 📋 Step-by-Step Instructions

### **Step 1: Get Your Gmail App Password**

#### A. Enable 2-Step Verification
1. Go to: https://myaccount.google.com/security
2. Click on **"2-Step Verification"**
3. Follow the prompts to enable it (you'll need your phone)

#### B. Create App Password
1. After 2-Step is enabled, go back to: https://myaccount.google.com/security
2. In the search bar at the top, type: **"App passwords"**
3. Click on **"App passwords"**
4. You might need to sign in again
5. Click **"Select app"** → Choose **"Mail"**
6. Click **"Select device"** → Choose **"Windows Computer"** or **"Other"**
7. Type: **"Infiverse Workflow"**
8. Click **"Generate"**
9. **COPY the 16-character password** (it looks like: `abcd efgh ijkl mnop`)
10. **SAVE IT** - you'll need it in Step 2!

---

### **Step 2: Create Your `.env` File**

#### A. Copy the Example File
1. Open File Explorer
2. Navigate to: `C:\Users\Microsoft\Desktop\Complete-Infiverse-2\server`
3. Find the file: `.env.example`
4. **Right-click** → **Copy**
5. **Right-click** in the same folder → **Paste**
6. **Rename** the copy to: `.env` (remove the `.example` part)

#### B. Edit the `.env` File
1. **Right-click** the `.env` file → **Open with** → **Notepad**
2. Find these lines:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASS=your-16-character-app-password
   ```
3. **Replace** with YOUR information:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=yourname@gmail.com
   EMAIL_PASS=abcdefghijklmnop
   ```
   
   ⚠️ **IMPORTANT:**
   - Use your **actual Gmail address** for `EMAIL_USER`
   - Use the **16-character app password** (from Step 1) for `EMAIL_PASS`
   - Remove any spaces from the app password
   - Do NOT use your regular Gmail password!

4. **Save** the file (`Ctrl + S`)
5. **Close** Notepad

---

### **Step 3: Restart the Server**

#### A. Stop the Current Server
1. Click on **Terminal 11** (where the server is running)
2. Press: **`Ctrl + C`**
3. Wait for it to stop (you'll see the prompt return)

#### B. Start with New Configuration
1. In the same terminal, type:
   ```bash
   npm start
   ```
2. Press **Enter**

#### C. Verify Success
Look for these messages:
```
✅ Server running on port 5000
✅ Connected to MongoDB
```

You should **NOT** see:
```
⚠️ EMS: Email credentials not configured. Running in MOCK MODE.
```

If you still see the MOCK MODE warning, your `.env` file is not configured correctly.

---

### **Step 4: Test Sending Real Emails**

#### A. Send a Test Email
1. Open your browser
2. Go to: http://localhost:5173/ems-dashboard
3. Click **"Send Custom Email"** button
4. Fill in:
   - **Subject:** "Test Email from Infiverse"
   - **Message:** "This is a test to verify email sending works!"
   - **Select Recipients:** Check your own email (test on yourself first!)
5. Click **"Send Now"**

#### B. Check Results

**In Terminal 11, you should see:**
```
✅ Email sent successfully to 1 recipients
```

**In your email inbox:**
- Check your inbox (the one you selected as recipient)
- Wait 1-2 minutes
- Look for the email
- Check spam folder if not in inbox

---

## ✅ Success Indicators

**Email sending is working if:**
- ✅ No MOCK MODE warning when server starts
- ✅ Terminal shows "Email sent successfully"
- ✅ Employee receives the email in their inbox

---

## ❌ Troubleshooting

### Problem: Still seeing "MOCK MODE" warning
**Solution:**
- Make sure `.env` file exists in `server` folder (not `server/.env.example`)
- Make sure you saved the file after editing
- Restart the server again

### Problem: "Invalid credentials" error
**Solution:**
- Double-check your Gmail address in `EMAIL_USER`
- Make sure you're using the **App Password**, not your regular password
- Ensure 2-Step Verification is enabled on your Google account
- Try generating a new App Password

### Problem: Email not received
**Solution:**
- Check spam/junk folder
- Wait 2-3 minutes (sometimes delayed)
- Try sending to your own email first
- Check Terminal 11 for error messages

### Problem: "Connection refused" error
**Solution:**
- Check if your antivirus/firewall is blocking port 587
- Try port 465 with `secure: true` in the configuration
- Check your internet connection

---

## 🔐 Security Notes

1. **Never commit `.env` file to Git** - it's already in `.gitignore`
2. **Keep your App Password secret** - it gives full email access
3. **Don't share your `.env` file** with anyone
4. If compromised, **revoke the App Password** at: https://myaccount.google.com/apppasswords

---

## 📞 Need Help?

If you're stuck:
1. Check Terminal 11 for error messages
2. Make sure all steps were followed exactly
3. Try using a different Gmail account
4. Test with the Gmail web interface to ensure the account works

---

**Good luck! 🚀**

