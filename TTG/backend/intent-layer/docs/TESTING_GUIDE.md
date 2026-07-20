# Day 1 Testing Guide

## 🚀 Quick Start

### Option 1: Run ALL Tests (Recommended)
```bash
cd backend/intent-compiler
node test_all.js
```
**Shows:** Complete Day 1 test suite with all validation

---

### Option 2: Interactive Browser Test (Best for Demo)
```bash
cd backend/intent-compiler
node test_server.js
```
**Then open:** http://localhost:3001

**Features:**
- ✅ Type your own prompts
- ✅ See extracted intent
- ✅ See compiled schema
- ✅ See validation results
- ✅ Beautiful UI

---

### Option 3: Interactive Terminal
```bash
cd backend/intent-compiler
node test_live.js
```
**Features:**
- ✅ Type prompts in terminal
- ✅ See results instantly
- ✅ Test multiple prompts
- ✅ Type 'exit' to quit

---

## 📋 Individual Test Suites

### Basic Compilation (5 examples)
```bash
node test.js
```
Tests: Genre, pacing, abilities, entities

### Validation Suite (9 tests)
```bash
node test_validation.js
```
Tests:
- ✅ Valid schemas
- ✅ Unsupported features (ignored)
- ✅ Edge cases (empty, nonsense)
- ✅ Over-specified prompts
- ✅ Schema validation details
- ✅ Enum validation
- ✅ Required fields
- ✅ Determinism
- ✅ Default values

### Error Handling (6 tests)
```bash
node test_errors.js
```
Tests:
- ❌ Missing required fields
- ❌ Invalid enum values
- ❌ Invalid entity structure
- ❌ Missing camera fields
- ❌ User-friendly error messages
- ✅ Valid schema (control)

---

## 🎯 What Gets Tested

### ✅ Valid Features
- Genres: runner, platformer, arena
- Pacing: slow, medium, fast
- Abilities: jump, dash, lane_switch
- Scoring: distance, time, collection
- Difficulty: easy, medium, hard
- Entities: obstacles, pickups

### ❌ Rejected/Ignored Features
- Enemies with AI
- Multiplayer
- Custom camera angles
- File loading
- Physics settings

### 🔍 Edge Cases
- Empty input
- Nonsense text
- Numbers only
- Over-specified prompts
- Repeated words

### 🔄 Validation Checks
- Required fields present
- Enum values valid
- Entity structure correct
- Camera fields present
- Deterministic output
- Default values applied

---

## 📊 Expected Results

### All Tests Should Show:
```
✅ Valid schemas: PASS
✅ Unsupported features ignored: PASS
✅ Edge cases handled: PASS
✅ Over-specified prompts: PASS
✅ Schema validation: PASS
✅ Enum validation: PASS
✅ Required fields: PASS
✅ Determinism: PASS
✅ Default values: PASS
✅ Error detection: PASS
```

---

## 🎮 Try These Prompts

### Basic
- `"Make a runner game"`
- `"Create a platformer"`
- `"Build an arena game"`

### With Abilities
- `"Fast runner with jump"`
- `"Platformer with jetpack"`
- `"Arena with dash and lane switch"`

### With Entities
- `"Runner with obstacles"`
- `"Platformer with coin collection"`
- `"Hard game with obstacles and pickups"`

### Complex
- `"Make a fast temple run game with jump and dash"`
- `"Create an easy side scroller with coin collection"`
- `"Build a hard arena game with all abilities"`

### Edge Cases (Should Still Work)
- `"game"` (minimal)
- `"asdfghjkl"` (nonsense)
- `""` (empty)
- `"super amazing game with everything"` (over-specified)

---

## 🐛 Debugging

If tests fail:

1. **Check Node version:**
   ```bash
   node --version
   ```
   Should be v14+ 

2. **Check files exist:**
   ```bash
   dir
   ```
   Should see: index.js, parser.js, compiler.js, validator.js, intent_taxonomy.json

3. **Check JSON syntax:**
   ```bash
   node -e "require('./intent_taxonomy.json')"
   ```
   Should show no errors

---

## ✅ Day 1 Checklist

- [x] Day 1a: Boundary Lock (`docs/intent_layer_scope.md`)
- [x] Day 1b: Intent Taxonomy (`intent_taxonomy.json`)
- [x] Day 1c: Compiler (`compiler.js`)
- [x] Day 1d: Text Parser (`parser.js`)
- [x] Day 1e: Validation (`validator.js`)
- [x] All tests passing
- [x] Interactive tests working
- [x] Browser test working

---

**Status:** ✅ Day 1 Complete and Fully Tested
