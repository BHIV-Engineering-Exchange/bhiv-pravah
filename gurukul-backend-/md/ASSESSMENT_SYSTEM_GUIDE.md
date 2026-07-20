# 13-Domain Multi-Select Assessment System - Implementation Guide

## 🎯 Overview

This system transforms the assessment platform from fixed study fields to a **13-domain multi-select system** with:
- ✅ 13 specialized domains (IoT, Blockchain, AI/ML/DS, etc.)
- ✅ 70 curated questions across all domains
- ✅ Multi-domain selection (minimum 1, maximum 13)
- ✅ Adaptive difficulty based on domain count
- ✅ AI assistance detection (balanced approach)
- ✅ Multi-domain performance analytics

---

## 🏗️ System Architecture

### **13 Domains**
1. **IoT** - Internet of Things
2. **Blockchain** - Blockchain Technology
3. **Humanoid Robotics**
4. **AI/ML/DS** - AI, Machine Learning, Data Science
5. **Drone Tech** - Drone Technology
6. **Biotechnology**
7. **Pharma Tech** - Pharmaceutical Technology
8. **Gaming** - Gaming & Game Development
9. **VR/AR** - VR/AR/Immersive Tech
10. **CyberSecurity**
11. **Web Development** - Full-stack + AI
12. **3D Printing** - Additive Manufacturing
13. **Quantum Computing**

### **Question Distribution** (70 Total)
- IoT: 5 questions
- Blockchain: 5 questions
- Humanoid Robotics: 4 questions
- AI/ML/DS: 6 questions
- Drone Tech: 4 questions
- Biotechnology: 6 questions
- Pharma Tech: 6 questions
- Gaming: 4 questions
- VR/AR: 4 questions
- CyberSecurity: 5 questions
- Web Development: 5 questions
- 3D Printing: 4 questions
- Quantum Computing: 4 questions

---

## 📦 Installation & Setup

### **Step 1: Run Database Migration**

Execute the SQL scripts in this order:

```bash
# 1. Migrate to 13-domain system
psql -h your-supabase-host -U your-user -d your-db -f src/sql/migrate_to_13_domains.sql

# 2. Insert 70 questions
psql -h your-supabase-host -U your-user -d your-db -f src/sql/insert_70_domain_questions.sql
```

**Or use Supabase Dashboard:**
1. Go to SQL Editor
2. Copy content from `src/sql/migrate_to_13_domains.sql`
3. Execute
4. Copy content from `src/sql/insert_70_domain_questions.sql`
5. Execute

### **Step 2: Verify Database**

```sql
-- Check domains
SELECT * FROM study_fields;

-- Check question distribution
SELECT 
  category, 
  difficulty, 
  COUNT(*) as count 
FROM question_banks 
GROUP BY category, difficulty 
ORDER BY category, difficulty;
```

Expected output:
- 13 domains in `study_fields`
- 70 questions distributed across domains
- Questions tagged with difficulty (easy, medium, hard)

---

## 🚀 Frontend Integration

### **Component Structure**

```
src/
├── components/
│   ├── DomainSelector.jsx          ← Multi-domain selection UI
│   ├── MultiDomainResults.jsx      ← Results with domain performance
│   └── Assignment.jsx              ← Updated to use multi-domain
├── lib/
│   ├── multiDomainAssessmentService.js  ← Core assessment logic
│   ├── aiAssistanceDetector.js          ← AI detection service
│   └── supabaseClient.js
└── sql/
    ├── migrate_to_13_domains.sql
    └── insert_70_domain_questions.sql
```

### **Usage Example**

```jsx
import React, { useState } from 'react';
import DomainSelector from './components/DomainSelector';
import MultiDomainAssessmentService from './lib/multiDomainAssessmentService';

function AssessmentFlow() {
  const [selectedDomains, setSelectedDomains] = useState([]);
  const [assessment, setAssessment] = useState(null);

  const handleDomainsSelected = async (domains) => {
    setSelectedDomains(domains);
    
    // Generate adaptive assessment
    const result = await MultiDomainAssessmentService.generateMultiDomainAssessment(
      domains,
      10, // total questions
      userId
    );
    
    setAssessment(result);
    console.log('Assessment Metadata:', result.metadata);
    // Start assessment with result.questions
  };

  return (
    <div>
      {!selectedDomains.length ? (
        <DomainSelector onDomainsSelected={handleDomainsSelected} />
      ) : (
        <AssessmentComponent 
          questions={assessment.questions}
          metadata={assessment.metadata}
        />
      )}
    </div>
  );
}
```

---

## 🎓 Adaptive Difficulty System

The system automatically adjusts difficulty based on domain selection:

### **Single Domain (Depth Focus)**
- Easy: 20%
- Medium: 50%
- Hard: 30%
- **Focus**: Testing deep expertise

### **2 Domains (Balanced)**
- Easy: 30%
- Medium: 50%
- Hard: 20%
- **Focus**: Balanced assessment

### **3-4 Domains (Multi-Disciplinary)**
- Easy: 40%
- Medium: 40%
- Hard: 20%
- **Focus**: Broad knowledge

### **5+ Domains (Breadth Focus)**
- Easy: 50%
- Medium: 40%
- Hard: 10%
- **Focus**: Survey knowledge

```javascript
// Automatic calculation
const difficulty = MultiDomainAssessmentService.calculateAdaptiveDifficulty(
  selectedDomains,
  totalQuestions
);
```

---

## 🤖 AI Assistance Detection

### **Detection Factors**

1. **Response Length**
   - Too short: Low effort
   - 100-200 words: AI pattern
   - 300+ words: Possible AI elaboration

2. **Language Patterns**
   - AI phrases: "as an ai", "however, it is important to note"
   - Perfect grammar without typos
   - Overly formal language

3. **Time Analysis**
   - Response speed vs. length
   - Suspiciously consistent timing

4. **Context Relevance**
   - Keyword overlap with question
   - Generic/templated responses

5. **Structural Patterns**
   - Numbered lists
   - Markdown formatting
   - Intro-body-conclusion structure

### **Detection Levels**

- **Clean** (0-30 points): Authentic effort
- **Possible Assistance** (30-50): Some indicators
- **Likely Assistance** (50-70): Multiple red flags
- **High Probability AI** (70+): Strong indicators

### **Balanced Feedback**

```javascript
import AIAssistanceDetector from './lib/aiAssistanceDetector';

const analysis = AIAssistanceDetector.analyzeResponse(
  studentAnswer,
  question,
  timeSpent
);

const feedback = AIAssistanceDetector.generateFeedback(analysis);
// Returns: { feedback, recommendation, effortScore, contextScore, flags }
```

**Feedback Examples:**
- ✅ Clean: "Your response shows genuine effort and understanding."
- ⚠️ Possible: "Try to express ideas in your own words."
- ⚠️ Likely: "We value authentic responses. Consider revising."
- ❌ High Probability: "Please provide responses in your own words."

**NOT harsh bans** - Measures effort, flags laziness, encourages improvement.

---

## 📊 Results & Analytics

### **Multi-Domain Performance**

```jsx
<MultiDomainResults 
  results={{
    total_score: 85,
    max_score: 100,
    time_taken_seconds: 450
  }}
  questions={assessmentQuestions}
  userResponses={studentResponses}
  selectedDomains={['iot', 'ai_ml_ds', 'blockchain']}
  onRetake={handleRetake}
  onClose={handleClose}
/>
```

**Displays:**
- Overall score & grade (A+ to F)
- Domain-wise performance breakdown
- Difficulty analysis (easy/medium/hard)
- AI assistance detection results
- AI-generated feedback from Groq API

---

## 🔧 API Reference

### **MultiDomainAssessmentService**

```javascript
// Get all domains
const domains = await MultiDomainAssessmentService.getAllDomains();

// Validate selection
const validation = MultiDomainAssessmentService.validateDomainSelection(
  ['iot', 'blockchain']
);

// Generate assessment
const assessment = await MultiDomainAssessmentService.generateMultiDomainAssessment(
  selectedDomains,  // ['iot', 'ai_ml_ds']
  totalQuestions,   // 10
  userId            // 'user-123'
);

// Save student selection
await MultiDomainAssessmentService.saveStudentDomainSelection(
  userId,
  selectedDomains,
  assessmentId
);
```

### **AIAssistanceDetector**

```javascript
// Analyze single response
const analysis = AIAssistanceDetector.analyzeResponse(
  response,
  question,
  timeSpent
);

// Analyze multiple responses
const batchAnalysis = AIAssistanceDetector.analyzeMultipleResponses(
  responses,
  questions,
  timeSpents
);

// Generate feedback
const feedback = AIAssistanceDetector.generateFeedback(analysis);
```

---

## 🎨 UI Components

### **DomainSelector**
- Multi-select cards with icons
- Visual feedback for selected domains
- Adaptive mode indicator
- Minimum 1 domain validation

### **MultiDomainResults**
- Overall grade card (A+ to F)
- Domain performance charts
- Difficulty breakdown
- AI detection with expandable details
- Groq AI feedback display

---

## 📝 Database Schema

### **study_fields**
```sql
field_id              TEXT PRIMARY KEY
name                  TEXT NOT NULL
short_name            TEXT NOT NULL
description           TEXT
subcategories         JSONB
question_weights      JSONB
difficulty_distribution JSONB
is_active             BOOLEAN
```

### **question_banks**
```sql
id                    UUID PRIMARY KEY
question_id           TEXT UNIQUE
category              TEXT (domain name)
difficulty            TEXT (easy/medium/hard)
question_text         TEXT
options               JSONB (4 options)
correct_answer        TEXT
explanation           TEXT
vedic_connection      TEXT
modern_application    TEXT
tags                  JSONB
is_active             BOOLEAN
```

### **question_field_mapping**
```sql
id              UUID PRIMARY KEY
question_id     TEXT → question_banks
field_id        TEXT → study_fields
weight          INTEGER
is_primary      BOOLEAN
```

---

## ✅ Testing Checklist

- [ ] Database migration successful
- [ ] 70 questions inserted correctly
- [ ] Domain selector loads 13 domains
- [ ] Can select multiple domains
- [ ] Cannot proceed without selecting ≥1 domain
- [ ] Adaptive difficulty adjusts correctly
- [ ] Assessment generates mixed questions
- [ ] AI detection runs on submission
- [ ] Results show domain breakdown
- [ ] Groq API feedback displays
- [ ] Can retake assessment

---

## 🚀 Deployment Steps

1. **Backup existing data**
   ```sql
   CREATE TABLE backup_question_banks AS SELECT * FROM question_banks;
   ```

2. **Run migrations**
   - Execute `migrate_to_13_domains.sql`
   - Execute `insert_70_domain_questions.sql`

3. **Update frontend**
   - Deploy new components
   - Update routing

4. **Test thoroughly**
   - Test domain selection
   - Test assessment generation
   - Test AI detection
   - Test results display

5. **Monitor**
   - Check error logs
   - Verify question distribution
   - Monitor AI detection accuracy

---

## 🎯 Key Features Summary

✅ **13 Specialized Domains** - IoT to Quantum Computing  
✅ **70 Curated Questions** - Real-world applications + Vedic connections  
✅ **Multi-Domain Selection** - Pick 1 to 13 domains  
✅ **Adaptive Difficulty** - Depth vs. Breadth focus  
✅ **AI Detection** - Balanced, non-punitive approach  
✅ **Performance Analytics** - Domain-wise breakdown  
✅ **Groq AI Feedback** - Personalized recommendations  

---

## 📞 Support

For issues or questions:
1. Check database logs
2. Verify Supabase RLS policies
3. Check browser console for errors
4. Review API rate limits (Groq)

---

**Status**: ✅ Ready for Implementation  
**Version**: 1.0  
**Last Updated**: November 5, 2025
