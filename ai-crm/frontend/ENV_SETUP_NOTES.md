# 🔑 Environment Variables Setup

## ✅ Your .env File is Configured

Your `.env` file has been created with the following credentials:

```
VITE_SUPABASE_URL=https://kiagdfmpxndpmykyxrey.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_f0mEh_o7FS81Ucn5fWZnFQ_Ar1hKpti
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## ⚠️ Important: Verify Your Anon Key

The anon key you provided starts with `sb_publishable_` which is unusual. Supabase anon keys typically:
- Start with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT format)
- Are long strings (200+ characters)

### To Get the Correct Anon Key:

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project: `kiagdfmpxndpmykyxrey`
3. Go to **Settings** (⚙️ icon) → **API**
4. Look for **"Project API keys"** section
5. Find **"anon public"** key
6. It should look like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpYWdkZm1weG5kcG15a3l4cmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTI5ODQ2MDAsImV4cCI6MjAyODU2MDYwMH0.xxxxx`

### If Your Key Doesn't Work:

1. Copy the correct **anon public** key from Supabase Dashboard
2. Update `frontend/.env` file
3. Replace the `VITE_SUPABASE_ANON_KEY` value
4. **Restart your frontend server** (stop with Ctrl+C, then run `npm run dev` again)

## 🚀 Next Steps

1. **Restart Frontend Server** (if it's running):
   ```powershell
   # Stop the server (Ctrl+C), then:
   cd frontend
   npm run dev
   ```

2. **Test the Connection**:
   - Open http://localhost:3000
   - Try to sign up or log in
   - If you see connection errors, check the anon key

3. **Verify Supabase Setup**:
   - Make sure you've run the SQL setup scripts
   - Check that authentication is enabled in Supabase Dashboard

## 📝 File Location

Your `.env` file is located at:
```
frontend/.env
```

**Note:** The `.env` file is in `.gitignore` so it won't be committed to git (this is good for security!).

---

**Need help?** If you encounter any connection errors, double-check the anon key in Supabase Dashboard → Settings → API.

