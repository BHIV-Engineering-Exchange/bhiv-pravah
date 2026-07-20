# Intent Compiler User Guide

**Version:** 1.0  
**Last Updated:** 2025-02-13  
**Status:** Production Ready

---

## What is the Intent Compiler?

The Intent Compiler converts natural language descriptions into playable game schemas. Simply describe your game idea in plain English, and the system will extract supported features and generate a valid TG Engine Gameplay Contract.

---

## ✅ What Users Can Say

### **Genres**
```
"Make a runner game"
"Create a platformer"
"Build an arena game"
```

**Keywords:** runner, running, run, temple run, platformer, platform, side scroller, arena, battle arena

**Result:** Sets `game_mode` to `infinite_runner`, `side_scroller`, or `arena_loop`

---

### **Pacing/Speed**
```
"Make a fast runner"
"Create a slow platformer"
"Build a medium speed game"
```

**Keywords:**
- **Fast:** fast, quick, speedy, rapid → `global_speed: 8`
- **Medium:** medium, normal, moderate → `global_speed: 5`
- **Slow:** slow, easy, casual → `global_speed: 3`

**Result:** Sets `gameplay.global_speed`

---

### **Abilities**
```
"Runner with jump"
"Platformer with dash"
"Arena with lane switching"
"Runner with jetpack"
```

**Keywords:**
- **Jump:** jump, jumping, leap → `jump_force: 5.0`
- **Dash:** dash, jetpack, jet pack, sprint, boost → `dash_speed: 10.0`
- **Lane Switch:** lane, lanes, switch lanes → `lane_switch_speed: 3.0`

**Result:** Adds abilities to `player.abilities`

---

### **Difficulty**
```
"Make an easy game"
"Create a hard runner"
"Build a medium difficulty platformer"
```

**Keywords:**
- **Easy:** easy, simple, beginner → Lower spawn rates
- **Medium:** medium, normal, moderate → Default spawn rates
- **Hard:** hard, difficult, challenging → Higher spawn rates

**Result:** Affects entity `spawn_rate` values

---

### **Entities**
```
"Runner with obstacles"
"Platformer with coins"
"Game with pickups and obstacles"
```

**Keywords:**
- **Obstacles:** obstacle, obstacles, barrier, block → Adds obstacle entity
- **Pickups:** pickup, pickups, coin, coins, collectible → Adds pickup entity

**Result:** Populates `entities` array

---

### **Scoring**
```
"Score by distance"
"Score by collecting coins"
"Score by time survived"
```

**Keywords:**
- **Distance:** distance, far, length → `score_metric: "distance"`
- **Collection:** collect, collection, coins, pickups → `score_metric: "collection"`
- **Time:** time, survive, survival → `score_metric: "time"`

**Result:** Sets `gameplay.score_metric`

---

## 🔇 What Gets Ignored (Silently)

These features are not supported but won't cause errors. The system extracts what it understands and ignores the rest:

### **Unsupported but Ignored**
- Custom camera angles (uses default camera)
- File loading requests (uses default meshes)
- Physics settings (uses default physics)
- AI behavior descriptions (not applicable)
- Visual effects (not supported)
- Sound/music requests (not supported)
- Story/narrative elements (not supported)

**Example:**
```
"Fast runner with realistic physics and epic music"
```
**Result:** ✅ Compiles successfully
- Extracts: "fast runner"
- Ignores: "realistic physics", "epic music"
- Generates: Valid infinite_runner schema with speed 8

---

## ❌ What Gets Rejected (With Explanation)

These features are explicitly unsupported and will cause compilation to fail with a clear error message:

### **1. Enemies/Monsters**
```
"Make a runner with enemies"
"Game with zombies chasing player"
```

**Error:** ❌ Enemies/Monsters not supported yet.

**Keywords:** enemy, enemies, monster, monsters, zombie, zombies, alien, aliens

---

### **2. Weapons/Shooting**
```
"Arena game with guns"
"Runner with shooting ability"
```

**Error:** ❌ Weapons/Shooting not supported yet.

**Keywords:** weapon, weapons, gun, guns, shoot, shooting, sword, swords

---

### **3. Multiplayer**
```
"2 player game"
"Multiplayer arena battle"
```

**Error:** ❌ Multiplayer not supported yet.

**Keywords:** multiplayer, multi player, 2 player, two player, pvp, versus

---

### **4. Power-ups**
```
"Runner with power-ups"
"Game with special buffs"
```

**Error:** ❌ Power-ups not supported yet.

**Keywords:** powerup, power-up, power up, buff, buffs

---

### **5. Empty/Nonsense Input**
```
""
"asdfghjkl"
"12345"
```

**Error:** ❌ No recognizable game features found.

**Reason:** Input must contain at least one supported keyword

---

## 📝 Example Prompts

### ✅ Valid Prompts

**1. Minimal**
```
"runner"
```
**Result:** Basic infinite_runner with default settings

---

**2. Simple**
```
"fast runner with jump"
```
**Result:** 
- Game Mode: infinite_runner
- Speed: 8
- Abilities: jump_force

---

**3. Detailed**
```
"Make a hard temple run style game with jump and obstacles"
```
**Result:**
- Game Mode: infinite_runner
- Speed: 5 (medium default)
- Difficulty: hard
- Abilities: jump_force
- Entities: obstacles (high spawn rate)

---

**4. Complete**
```
"Fast runner with jump, dash, obstacles, and coin pickups"
```
**Result:**
- Game Mode: infinite_runner
- Speed: 8
- Abilities: jump_force, dash_speed
- Entities: obstacles, pickups
- Score: distance

---

**5. Platformer**
```
"Easy side scroller with coin collection"
```
**Result:**
- Game Mode: side_scroller
- Speed: 3
- Difficulty: easy
- Entities: pickups
- Score: collection

---

**6. With Jetpack**
```
"Runner with jetpack and obstacles"
```
**Result:**
- Game Mode: infinite_runner
- Speed: 5 (medium default)
- Abilities: dash_speed (jetpack → dash)
- Entities: obstacles

---

### ❌ Invalid Prompts

**1. Unsupported Features**
```
"Runner with enemies and weapons"
```
**Error:** ❌ Enemies/Monsters, Weapons/Shooting not supported yet.

---

**2. Empty Input**
```
"   "
```
**Error:** ❌ Please provide a game description.

---

**3. No Recognizable Features**
```
"qwerty asdfgh"
```
**Error:** ❌ No recognizable game features found.

---

## 🎯 Best Practices

### **1. Be Specific**
✅ Good: "Fast runner with jump and obstacles"  
❌ Vague: "Make a game"

### **2. Use Supported Keywords**
✅ Good: "Runner with dash ability"  
✅ Good: "Runner with jetpack" (maps to dash)

### **3. Keep It Simple**
✅ Good: "Easy platformer with coins"  
❌ Over-specified: "Ultra mega super fast extreme hardcore..."

### **4. One Genre at a Time**
✅ Good: "Fast runner"  
⚠️ Confusing: "Runner platformer arena" (first match wins)

### **5. Check the Error Message**
If compilation fails, read the explanation. It tells you:
- What features are not supported
- What features ARE supported
- Example of a valid prompt

---

## 🔄 Compilation Flow

```
User Input
    ↓
Parse Text (extract keywords)
    ↓
Check for Unsupported Features
    ↓
    ├─ Found? → ❌ Reject with explanation
    ↓
    └─ None? → Continue
    ↓
Extract Intent (genre, pacing, abilities, etc.)
    ↓
Check for Recognizable Features
    ↓
    ├─ None? → ❌ Reject with explanation
    ↓
    └─ Found? → Continue
    ↓
Compile to TG Engine Schema
    ↓
Validate Schema
    ↓
✅ Return Compiled Schema
```

---

## 🛠️ Supported Features Summary

| Category | Supported | Count |
|----------|-----------|-------|
| Genres | runner, platformer, arena | 3 |
| Pacing | slow, medium, fast | 3 |
| Abilities | jump, dash, lane_switch | 3 |
| Difficulty | easy, medium, hard | 3 |
| Entities | obstacles, pickups | 2 |
| Scoring | distance, time, collection | 3 |

**Total Combinations:** 486 possible valid games!

---

## 🚫 Unsupported Features Summary

| Feature | Status | Reason |
|---------|--------|--------|
| Enemies/Monsters | ❌ Not Supported | Requires AI system |
| Weapons/Shooting | ❌ Not Supported | Combat system needed |
| Multiplayer | ❌ Not Supported | Network infrastructure |
| Power-ups | ❌ Not Supported | Item system needed |
| Custom Camera | 🔇 Ignored | Uses default camera |
| Custom Physics | 🔇 Ignored | Uses default physics |
| Visual Effects | 🔇 Ignored | Not applicable |
| Sound/Music | 🔇 Ignored | Not applicable |

---

## 💡 Tips & Tricks

### **Tip 1: Start Simple**
Begin with basic prompts like "runner" or "platformer", then add features incrementally.

### **Tip 2: Use Examples**
The dashboard has quick example buttons. Click them to see valid prompts.

### **Tip 3: Read Error Messages**
Error messages include:
- What went wrong
- List of supported features
- Example of a valid prompt

### **Tip 4: Experiment**
Try different combinations! The system is deterministic - same input always produces the same output.

### **Tip 5: Check the Preview**
After compilation, review the "Extracted Intent" panel to see what the system understood.

---

## 🐛 Troubleshooting

### **Problem: "No recognizable game features found"**
**Solution:** Add at least one supported keyword (runner, jump, obstacles, etc.)

### **Problem: "Unsupported features: Enemies/Monsters"**
**Solution:** Remove enemy-related keywords, use "obstacles" instead

### **Problem: "Empty input"**
**Solution:** Type a game description with actual text

### **Problem: Compilation succeeds but game is not what I expected**
**Solution:** Check the "Extracted Intent" panel to see what features were detected

---

## 📚 Additional Resources

- **Demo Prompts:** See `demo_prompts.md` for 5 tested examples
- **Consistency Tests:** See `test_consistency.js` for determinism verification
- **Abuse Tests:** See `test_abuse.js` for edge case handling
- **API Endpoints:** 
  - `POST /api/ttg/compile` - Compile text to schema
  - `POST /api/ttg/start-game` - Compile and start game
  - `GET /api/ttg/features` - Get supported features

---

## 🎓 Learning Path

### **Beginner**
1. Try: "runner"
2. Try: "fast runner"
3. Try: "fast runner with jump"

### **Intermediate**
4. Try: "fast runner with jump and obstacles"
5. Try: "easy platformer with coin collection"

### **Advanced**
6. Try: "hard runner with jump, dash, obstacles, and pickups"
7. Try: "arena game with dash and lane switching"

---

## ✅ Success Criteria

Your prompt is valid if:
- ✅ Contains at least one supported keyword
- ✅ Does not contain unsupported features (enemies, weapons, etc.)
- ✅ Is not empty or just whitespace
- ✅ Contains alphabetic characters

---

## 📞 Support

If you encounter issues:
1. Check this guide
2. Read the error message carefully
3. Try a simpler prompt
4. Use the quick example buttons
5. Review the "Extracted Intent" panel

---

**Version:** 1.0  
**Author:** Rudra Parmeshwar  
**Date:** 2025-02-13  
**Status:** ✅ Production Ready
