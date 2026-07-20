# Gurukul Backend API Documentation

Complete API documentation for frontend developers to integrate with the Gurukul Backend.

## Table of Contents

1. [Overview](#overview)
2. [Setup & Installation](#setup--installation)
3. [Environment Variables](#environment-variables)
4. [Starting the Server](#starting-the-server)
5. [Base URL & API Endpoints](#base-url--api-endpoints)
6. [API Endpoints](#api-endpoints)
   - [Health & Status](#health--status)
   - [Subject Explorer](#subject-explorer)
   - [Text Summarization](#text-summarization)
   - [Document Summarization](#document-summarization)
   - [Chatbot API](#chatbot-api)
   - [RAG Knowledge Store](#rag-knowledge-store)
   - [Saved Summaries & Questions](#saved-summaries--questions)
   - [Spaced Repetition System](#spaced-repetition-system)
   - [Quiz/Test API](#quiztest-api)
   - [Agent Simulators](#agent-simulators)
7. [Error Handling](#error-handling)
8. [Tools & Technologies](#tools--technologies)
9. [Frontend Integration Guide](#frontend-integration-guide)

---

## Overview

The Gurukul Backend API is a comprehensive FastAPI-based REST API that provides:

- **Educational Content Generation**: AI-powered lesson generation, summaries, and study materials
- **Chatbot with Memory**: Conversational AI with conversation history and RAG support
- **Document Processing**: PDF and DOCX summarization with OCR support
- **Question Generation**: Automatic generation of Q&A, MCQs, flashcards, and case-based questions
- **Spaced Repetition**: Review scheduling system for effective learning
- **Quiz System**: Generate and grade quizzes with detailed results
- **Agent Simulators**: Specialized AI agents for education, finance, and wellness

### Key Features

- ✅ RESTful API design
- ✅ Automatic API documentation (Swagger UI)
- ✅ CORS enabled for frontend integration
- ✅ Multiple AI provider support (Groq, Ollama, Local LLaMA)
- ✅ Conversation memory and RAG (Retrieval Augmented Generation)
- ✅ File upload support (PDF, DOCX)
- ✅ In-memory data storage (can be upgraded to database)

---

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd Gurukul
   ```

2. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory (see [Environment Variables](#environment-variables) section)

5. **Verify installation**:
   ```bash
   python main.py
   ```

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Server Configuration
HOST=0.0.0.0
PORT=3000
RELOAD=True
API_TITLE=Gurukul Backend API

# CORS (optional, defaults to *)
CORS_ORIGINS=*

# Groq API (for AI chat and content generation)
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_ENDPOINT=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Ollama (Local LLM - optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_PRIMARY=llama2

# Local LLaMA API (optional)
LOCAL_LLAMA_API_URL=http://localhost:8080/v1/chat/completions

# YouTube API (for video recommendations - optional)
YOUTUBE_API_KEY=your_youtube_api_key_here

# OpenAI API (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Gemini API (optional)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Getting API Keys

- **Groq API**: Sign up at https://console.groq.com/ and get your API key
- **YouTube API**: Get from Google Cloud Console
- **Ollama**: Install locally from https://ollama.ai/

---

## Starting the Server

### Option 1: Using Python directly
```bash
python main.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

The server will start on **http://localhost:3000**

### Verify Server is Running

1. **Check root endpoint**:
   ```bash
   curl http://localhost:3000/
   ```

2. **Check health**:
   ```bash
   curl http://localhost:3000/health
   ```

3. **Access Swagger UI**:
   Open browser: http://localhost:3000/docs

---

## Base URL & API Endpoints

### Base URL
```
http://localhost:3000
```

### API Documentation
- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc

### Common Headers
```javascript
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## API Endpoints

### Health & Status

#### GET `/`
Root endpoint - API information

**Response:**
```json
{
  "message": "Welcome to Gurukul Backend API",
  "status": "running"
}
```

#### GET `/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy"
}
```

---

### Subject Explorer

#### POST `/subject-explorer`
Generate educational notes for a subject and topic with YouTube recommendations.

**Request Body:**
```json
{
  "subject": "Physics",
  "topic": "Newton's Laws",
  "provider": "auto"  // "groq", "ollama", "llama", or "auto"
}
```

**Response:**
```json
{
  "subject": "Physics",
  "topic": "Newton's Laws",
  "notes": "Comprehensive educational notes...",
  "provider": "groq",
  "youtube_recommendations": [
    {
      "title": "Newton's Laws Explained",
      "video_id": "abc123",
      "url": "https://youtube.com/watch?v=abc123",
      "thumbnail": "https://...",
      "channel_title": "Physics Channel"
    }
  ],
  "success": true
}
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:3000/subject-explorer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subject: 'Physics',
    topic: "Newton's Laws",
    provider: 'auto'
  })
});
const data = await response.json();
```

---

### Text Summarization

#### POST `/summarize`
Summarize plain text input.

**Request Body:**
```json
{
  "text": "Long text to summarize...",
  "max_length": 150,
  "min_length": 50
}
```

**Response:**
```json
{
  "summary": "Summarized text...",
  "original_length": 500,
  "summary_length": 120,
  "compression_ratio": 0.24
}
```

---

### Document Summarization

#### POST `/summarize-pdf`
Summarize PDF documents with OCR support for scanned PDFs.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file (binary)
  - `max_length`: Optional integer (default: 150)
  - `min_length`: Optional integer (default: 50)
  - `improve_grammar`: Optional boolean (default: true)
  - `save_summary`: Optional boolean (default: false)
  - `summary_title`: Optional string

**Response:**
```json
{
  "summary": "PDF summary...",
  "pages_processed": 5,
  "total_pages": 5,
  "summary_id": "uuid-if-saved",
  "success": true
}
```

**Frontend Example:**
```javascript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('max_length', '200');
formData.append('save_summary', 'true');
formData.append('summary_title', 'My PDF Summary');

const response = await fetch('http://localhost:3000/summarize-pdf', {
  method: 'POST',
  body: formData
});
const data = await response.json();
```

#### POST `/summarize-doc`
Summarize DOCX documents.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: DOCX file (binary)
  - `max_length`: Optional integer
  - `min_length`: Optional integer
  - `save_summary`: Optional boolean
  - `summary_title`: Optional string

**Response:**
```json
{
  "summary": "DOCX summary...",
  "sections_processed": 3,
  "summary_id": "uuid-if-saved",
  "success": true
}
```

---

### Chatbot API

#### POST `/chat`
Chat with AI model with conversation memory and RAG support.

**Request Body:**
```json
{
  "message": "What is machine learning?",
  "conversation_id": "optional-existing-id",  // Optional: creates new if not provided
  "provider": "auto",  // "groq", "ollama", "llama", or "auto"
  "use_rag": true,  // Use RAG knowledge store
  "max_history": 10  // Number of previous messages to include
}
```

**Response:**
```json
{
  "response": "Machine learning is...",
  "conversation_id": "uuid",
  "provider": "groq",
  "timestamp": "2025-12-25T10:00:00"
}
```

**Frontend Example:**
```javascript
// Start a new conversation
const response = await fetch('http://localhost:3000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello!',
    provider: 'auto',
    use_rag: true,
    max_history: 10
  })
});
const data = await response.json();
const conversationId = data.conversation_id;

// Continue conversation
const nextResponse = await fetch('http://localhost:3000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Tell me more',
    conversation_id: conversationId,
    provider: 'auto',
    use_rag: true,
    max_history: 10
  })
});
```

#### GET `/chat/history/{conversation_id}`
Get conversation history.

**Response:**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-12-25T10:00:00"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-12-25T10:00:01"
    }
  ],
  "created_at": "2025-12-25T10:00:00",
  "updated_at": "2025-12-25T10:00:01"
}
```

#### DELETE `/chat/history/{conversation_id}`
Delete a conversation.

**Response:**
```json
{
  "message": "Conversation deleted successfully"
}
```

---

### RAG Knowledge Store

#### POST `/rag/knowledge`
Add knowledge to the RAG store for context retrieval.

**Request Body:**
```json
{
  "text": "Knowledge content to store...",
  "metadata": {
    "source": "textbook",
    "subject": "Physics",
    "topic": "Mechanics"
  }
}
```

**Response:**
```json
{
  "message": "Knowledge added successfully",
  "knowledge_id": "hash-id"
}
```

**Frontend Example:**
```javascript
await fetch('http://localhost:3000/rag/knowledge', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Important study material...',
    metadata: {
      source: 'lecture notes',
      subject: 'Mathematics',
      topic: 'Calculus'
    }
  })
});
```

---

### Saved Summaries & Questions

#### POST `/summaries/save`
Save a summary for later use.

**Request Body:**
```json
{
  "title": "My Study Summary",
  "content": "Summary content...",
  "source": "PDF or DOCX or Manual"
}
```

**Response:**
```json
{
  "summary_id": "uuid",
  "title": "My Study Summary",
  "content": "Summary content...",
  "source": "PDF",
  "created_at": "2025-12-25T10:00:00"
}
```

#### GET `/summaries`
Get all saved summaries.

**Response:**
```json
[
  {
    "summary_id": "uuid",
    "title": "My Study Summary",
    "content": "Summary content...",
    "source": "PDF",
    "created_at": "2025-12-25T10:00:00"
  }
]
```

#### GET `/summaries/{summary_id}`
Get a specific summary by ID.

#### POST `/summaries/{summary_id}/questions/generate`
Generate practice questions from a saved summary.

**Request Body:**
```json
{
  "question_types": ["qa", "mcq", "flashcard", "case_based"],
  "num_questions": 10,
  "difficulty": "medium"  // "easy", "medium", "hard"
}
```

**Response:**
```json
{
  "summary_id": "uuid",
  "questions_generated": 10,
  "questions": [
    {
      "question_id": "uuid",
      "type": "mcq",
      "question": "What is...?",
      "answer": "Answer...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "difficulty": "medium"
    }
  ],
  "success": true
}
```

#### GET `/summaries/{summary_id}/questions`
Get all questions for a summary.

---

### Spaced Repetition System

#### GET `/reviews/pending`
Get all pending reviews (questions due for review).

**Response:**
```json
[
  {
    "question_id": "uuid",
    "summary_id": "uuid",
    "question": "What is...?",
    "type": "mcq",
    "due_date": "2025-12-25T10:00:00",
    "review_count": 2
  }
]
```

#### POST `/reviews/submit`
Submit a review (mark question as reviewed).

**Request Body:**
```json
{
  "question_id": "uuid",
  "correct": true  // Whether user got it correct
}
```

**Response:**
```json
{
  "question_id": "uuid",
  "next_review_date": "2025-12-26T10:00:00",
  "review_count": 3,
  "mastery_level": "good"
}
```

#### GET `/reviews/stats`
Get review statistics.

**Response:**
```json
{
  "total_questions": 50,
  "pending_reviews": 10,
  "mastered": 30,
  "learning": 15,
  "new": 5
}
```

**Frontend Example:**
```javascript
// Get pending reviews
const reviews = await fetch('http://localhost:3000/reviews/pending').then(r => r.json());

// Submit review
await fetch('http://localhost:3000/reviews/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question_id: 'uuid',
    correct: true
  })
});
```

---

### Quiz/Test API

#### POST `/quiz/generate`
Generate a quiz with 10 questions.

**Request Body:**
```json
{
  "subject": "Mathematics",
  "topic": "Algebra",
  "difficulty": "medium",  // "easy", "medium", "hard"
  "provider": "auto"
}
```

**Response:**
```json
{
  "quiz_id": "uuid",
  "subject": "Mathematics",
  "topic": "Algebra",
  "questions": [
    {
      "question_id": "uuid",
      "question_number": 1,
      "question": "What is 2x + 3 = 7?",
      "options": ["x = 2", "x = 3", "x = 4", "x = 5"],
      "question_type": "mcq"
    }
  ],
  "created_at": "2025-12-25T10:00:00",
  "difficulty": "medium"
}
```

#### POST `/quiz/submit`
Submit quiz answers for grading.

**Request Body:**
```json
{
  "quiz_id": "uuid",
  "answers": {
    "question_id_1": "option_a",
    "question_id_2": "option_b"
  }
}
```

**Response:**
```json
{
  "quiz_id": "uuid",
  "total_questions": 10,
  "correct_answers": 7,
  "incorrect_answers": 3,
  "score_percentage": 70.0,
  "results": [
    {
      "question_id": "uuid",
      "user_answer": "option_a",
      "correct_answer": "option_a",
      "is_correct": true
    }
  ],
  "submitted_at": "2025-12-25T10:05:00"
}
```

#### GET `/quiz/{quiz_id}`
Get quiz details (without answers).

**Frontend Example:**
```javascript
// Generate quiz
const quiz = await fetch('http://localhost:3000/quiz/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subject: 'Mathematics',
    topic: 'Algebra',
    difficulty: 'medium'
  })
}).then(r => r.json());

// Submit answers
const result = await fetch('http://localhost:3000/quiz/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    quiz_id: quiz.quiz_id,
    answers: {
      'question_id_1': 'option_a',
      'question_id_2': 'option_b'
    }
  })
}).then(r => r.json());
```

---

### Agent Simulators

#### EduMentor - Learning Assistant

##### POST `/agent/edumentor/generate`
Generate personalized educational lessons.

**Request Body:**
```json
{
  "subject": "Physics",
  "topic": "Newton's Laws",
  "include_wikipedia": true,
  "use_knowledge_store": false,
  "use_orchestration": false,
  "provider": "auto"
}
```

**Response:**
```json
{
  "subject": "Physics",
  "topic": "Newton's Laws",
  "lesson_content": "Comprehensive lesson content...",
  "wikipedia_sources": [
    {
      "title": "Newton's Laws",
      "url": "https://en.wikipedia.org/...",
      "summary": "..."
    }
  ],
  "knowledge_store_used": false,
  "orchestration_used": false,
  "provider": "groq",
  "created_at": "2025-12-25T10:00:00",
  "success": true
}
```

#### Financial Agent - FinancialCrew

##### POST `/agent/financial/advice`
Get personalized financial advice.

**Request Body:**
```json
{
  "name": "John Doe",
  "monthly_income": 50000,
  "monthly_expenses": 30000,
  "expense_categories": [
    {
      "name": "Food",
      "amount": 5000
    },
    {
      "name": "Rent",
      "amount": 15000
    }
  ],
  "financial_goal": "Buy a house worth ₹50,00,000",
  "financial_type": "Moderate",
  "risk_level": "moderate"
}
```

**Response:**
```json
{
  "name": "John Doe",
  "monthly_income": 50000.0,
  "monthly_expenses": 30000.0,
  "monthly_savings": 20000.0,
  "expense_breakdown": [
    {
      "name": "Food",
      "amount": 5000.0,
      "percentage": 10.0
    }
  ],
  "financial_advice": "Comprehensive financial advice...",
  "recommendations": [
    "Save ₹20,000 per month consistently",
    "Build an emergency fund..."
  ],
  "goal_analysis": {
    "goal": "Buy a house worth ₹50,00,000",
    "estimated_cost": 5000000.0,
    "monthly_savings": 20000.0,
    "estimated_months": 250,
    "estimated_years": 20.8,
    "feasibility": "Achievable"
  },
  "provider": "groq",
  "created_at": "2025-12-25T10:00:00"
}
```

#### Wellness Bot

##### POST `/agent/wellness/support`
Get emotional support and wellness guidance.

**Request Body:**
```json
{
  "emotional_wellness_score": 6,  // 1-10 (1=bad, 10=good)
  "financial_wellness_score": 7,
  "current_mood_score": 5,
  "stress_level": 4,  // 1-10 (1=bad, 10=good)
  "concerns": "Feeling overwhelmed with studies"
}
```

**Response:**
```json
{
  "emotional_support": "Warm, empathetic support message...",
  "motivational_message": "Inspiring motivational content...",
  "life_importance": "Message about the value of life...",
  "study_importance": "Encouragement about education...",
  "goal_importance": "Motivation about completing goals...",
  "positive_affirmations": [
    "I am capable of overcoming challenges",
    "Every day brings new opportunities"
  ],
  "recommendations": [
    "Practice deep breathing exercises",
    "Take regular breaks"
  ],
  "overall_assessment": "Overall wellness assessment...",
  "provider": "groq",
  "created_at": "2025-12-25T10:00:00"
}
```

**Frontend Example:**
```javascript
// EduMentor
const lesson = await fetch('http://localhost:3000/agent/edumentor/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subject: 'Physics',
    topic: "Newton's Laws",
    include_wikipedia: true,
    provider: 'auto'
  })
}).then(r => r.json());

// Financial Advice
const advice = await fetch('http://localhost:3000/agent/financial/advice', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'John Doe',
    monthly_income: 50000,
    monthly_expenses: 30000,
    expense_categories: [
      { name: 'Food', amount: 5000 }
    ],
    financial_goal: 'Buy a house',
    financial_type: 'Moderate',
    risk_level: 'moderate'
  })
}).then(r => r.json());

// Wellness Support
const support = await fetch('http://localhost:3000/agent/wellness/support', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    emotional_wellness_score: 6,
    financial_wellness_score: 7,
    current_mood_score: 5,
    stress_level: 4,
    concerns: 'Feeling overwhelmed'
  })
}).then(r => r.json());
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

1. **Missing Required Fields**:
   ```json
   {
     "detail": "Subject and topic are required"
   }
   ```

2. **Invalid Data**:
   ```json
   {
     "detail": [
       {
         "loc": ["body", "emotional_wellness_score"],
         "msg": "value is not a valid integer",
         "type": "type_error.integer"
       }
     ]
   }
   ```

3. **AI Provider Error**:
   ```json
   {
     "detail": "All AI providers failed. Please check your configuration."
   }
   ```

### Frontend Error Handling Example

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

---

## Tools & Technologies

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI

### AI/ML Libraries
- **Transformers (Hugging Face)**: For BART summarization model
- **PyTorch**: Deep learning framework
- **SentencePiece**: Tokenization for summarization

### Document Processing
- **PyPDF2**: PDF file reading
- **python-docx**: DOCX file processing
- **Pillow (PIL)**: Image processing
- **pytesseract**: OCR for scanned PDFs
- **pdf2image**: Convert PDF pages to images

### API Integration
- **requests**: HTTP library for external API calls
- **Groq API**: AI chat and content generation
- **Ollama**: Local LLM integration
- **YouTube API**: Video recommendations

### Data Validation
- **Pydantic**: Data validation using Python type hints

### Environment Management
- **python-dotenv**: Load environment variables from .env file

### CORS
- **CORSMiddleware**: Enable Cross-Origin Resource Sharing for frontend

---

## Frontend Integration Guide

### 1. Base Configuration

```javascript
// config.js
const API_BASE_URL = 'http://localhost:3000';

export const apiConfig = {
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};
```

### 2. API Service Class

```javascript
// apiService.js
class ApiService {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Chat API
  async sendMessage(message, conversationId = null, options = {}) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        provider: options.provider || 'auto',
        use_rag: options.useRag || false,
        max_history: options.maxHistory || 10
      })
    });
  }

  async getConversationHistory(conversationId) {
    return this.request(`/chat/history/${conversationId}`);
  }

  async deleteConversation(conversationId) {
    return this.request(`/chat/history/${conversationId}`, {
      method: 'DELETE'
    });
  }

  // Document Summarization
  async summarizePDF(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    if (options.maxLength) formData.append('max_length', options.maxLength);
    if (options.saveSummary) formData.append('save_summary', 'true');
    if (options.summaryTitle) formData.append('summary_title', options.summaryTitle);

    return this.request('/summarize-pdf', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData
    });
  }

  // Quiz API
  async generateQuiz(subject, topic, difficulty = 'medium') {
    return this.request('/quiz/generate', {
      method: 'POST',
      body: JSON.stringify({ subject, topic, difficulty })
    });
  }

  async submitQuiz(quizId, answers) {
    return this.request('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId, answers })
    });
  }

  // Agent Simulators
  async generateLesson(subject, topic, options = {}) {
    return this.request('/agent/edumentor/generate', {
      method: 'POST',
      body: JSON.stringify({
        subject,
        topic,
        include_wikipedia: options.includeWikipedia || false,
        provider: options.provider || 'auto'
      })
    });
  }

  async getFinancialAdvice(profile) {
    return this.request('/agent/financial/advice', {
      method: 'POST',
      body: JSON.stringify(profile)
    });
  }

  async getWellnessSupport(scores) {
    return this.request('/agent/wellness/support', {
      method: 'POST',
      body: JSON.stringify(scores)
    });
  }
}

export const apiService = new ApiService('http://localhost:3000');
```

### 3. React Example Usage

```javascript
// ChatComponent.jsx
import { useState } from 'react';
import { apiService } from './apiService';

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiService.sendMessage(
        input,
        conversationId,
        { provider: 'auto', useRag: true }
      );

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response
      }]);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage} disabled={loading}>
        Send
      </button>
    </div>
  );
}
```

### 4. File Upload Example

```javascript
// FileUploadComponent.jsx
import { useState } from 'react';
import { apiService } from './apiService';

function FileUploadComponent() {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    try {
      const result = await apiService.summarizePDF(file, {
        maxLength: 200,
        saveSummary: true,
        summaryTitle: 'My Summary'
      });
      setSummary(result);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to summarize PDF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input type="file" accept=".pdf" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Processing...' : 'Summarize PDF'}
      </button>
      {summary && (
        <div>
          <h3>Summary:</h3>
          <p>{summary.summary}</p>
        </div>
      )}
    </div>
  );
}
```

### 5. Error Handling Wrapper

```javascript
// errorHandler.js
export const handleApiError = (error) => {
  if (error.message.includes('Failed to fetch')) {
    return 'Unable to connect to server. Please check if the server is running.';
  }
  
  if (error.message.includes('422')) {
    return 'Invalid data provided. Please check your input.';
  }
  
  if (error.message.includes('500')) {
    return 'Server error. Please try again later.';
  }
  
  return error.message || 'An unexpected error occurred';
};
```

### 6. CORS Configuration

The backend already has CORS enabled for all origins (`*`). If you need to restrict it:

```python
# In main.py, change:
allow_origins=["http://localhost:3000", "http://localhost:5173"]  # Your frontend URLs
```

---

## Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:3000/health

# Chat
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "auto"}'

# Generate quiz
curl -X POST http://localhost:3000/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"subject": "Math", "topic": "Algebra", "difficulty": "medium"}'
```

### Using Postman

1. Import the collection from Swagger UI: http://localhost:3000/docs
2. Set base URL: `http://localhost:3000`
3. Test endpoints with sample data

---

## Important Notes

1. **Data Storage**: Currently using in-memory storage. Data is lost on server restart. Consider upgrading to a database for production.

2. **API Keys**: Make sure to set up your API keys in the `.env` file for AI features to work.

3. **File Size Limits**: Large PDF/DOCX files may take time to process. Consider adding file size limits in production.

4. **Rate Limiting**: Currently no rate limiting. Add rate limiting for production use.

5. **Authentication**: Currently no authentication. Add authentication/authorization for production.

6. **Error Logging**: Add proper logging and monitoring for production.

---

## Support & Resources

- **API Documentation**: http://localhost:3000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:3000/redoc (ReDoc)
- **GitHub Repository**: [Your repository URL]

---

## Changelog

### Version 1.0.0
- Initial release
- Chatbot with conversation memory
- Document summarization (PDF/DOCX)
- Question generation with spaced repetition
- Quiz system
- Agent simulators (EduMentor, Financial, Wellness)

---

**Last Updated**: December 25, 2025

**API Version**: 1.0.0

**Maintained by**: Gurukul Development Team

