# PRANA-G → Karma Tracker Integration Setup

## ✅ What's Done

I've wired PRANA-G (Gurukul frontend) to automatically send events to Karma Tracker when users are actively learning.

## 🔧 Configuration

### Environment Variable (Optional)

Add to your `.env` file in the `Frontend` directory:

```env
VITE_KARMA_TRACKER_URL=http://localhost:8000
```

If not set, it defaults to `http://localhost:8000`.

## 📊 How It Works

1. **PRANA-G builds packets every 5 seconds** (already working)
2. **When user is in DEEP_FOCUS or ON_TASK state** with high activity → sends `completing_lessons` action to Karma Tracker
3. **Karma Tracker scores it** → User gets DharmaPoints
4. **Non-blocking**: If Karma Tracker is down, PRANA continues working normally

## 🎯 Current Mapping

- **DEEP_FOCUS / ON_TASK** (with ≥3s active time, focus ≥60) → `completing_lessons` → **+5 DharmaPoints**
- **IDLE / AWAY / OFF_TASK** → No karma event (to avoid spam)

## 🧪 Testing

1. **Start Karma Tracker**: `cd "Karma Tracker" && uvicorn main:app --reload`
2. **Start Gurukul frontend**: Your normal dev server
3. **Use Gurukul normally** (read lessons, interact with content)
4. **Check browser console**: You should see `[PRANA→KARMA] Event sent successfully` messages
5. **Check Karma Tracker**: Call `GET /api/v1/karma/{your_user_id}` to see accumulated karma

## 📈 Next Steps (Optional Enhancements)

1. **Add more action mappings**:
   - `helping_peers` when user interacts with community features
   - `solving_doubts` when user answers questions
   - Negative actions for extended idle/away time

2. **Add karma display to UI**:
   - Show user's karma score on dashboard
   - Display role badges (learner → volunteer → seva → guru)
   - Show corrective guidance messages

3. **Use feedback signals**:
   - Call `GET /api/v1/feedback_signal/{user_id}` to get personalized recommendations
   - Adjust UI/UX based on karma state

## 🔍 Debugging

- **Check browser console** for `[PRANA→KARMA]` messages
- **Check Karma Tracker logs** for incoming events
- **Verify user_id** is being passed correctly from AuthContext
- **Test manually** with Swagger at `http://localhost:8000/docs`

## 🚀 Production Notes

- Make sure Karma Tracker URL is set correctly in production `.env`
- Consider adding retry logic for failed events
- Monitor Karma Tracker health in production
- Consider batching events if volume is high

