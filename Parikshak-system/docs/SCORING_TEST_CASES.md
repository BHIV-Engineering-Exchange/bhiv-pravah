# 🧪 Live Task Review Agent - Scoring Test Cases

## Dynamic Scoring Model Breakdown
- **Title Analysis**: 20 points (Technical keywords, clarity, alignment)
- **Description Analysis**: 40 points (Content depth, structure, technical density)
- **Repository Analysis**: 40 points (Code quality, architecture, documentation)
- **Total**: 100 points

## Score Classifications
- **PASS**: ≥ 80 points ✅
- **BORDERLINE**: 50-79 points ⚠️
- **FAIL**: < 50 points ❌

---

## 🎯 TEST CASE 1: PASS Score (80-90 points)

### Input Parameters:
```json
{
  "task_title": "REST API Authentication System with JWT and Database Integration",
  "task_description": "Comprehensive authentication system implementation featuring:\n\n## Core Features\n- JWT token-based authentication with refresh tokens\n- Secure password hashing using bcrypt\n- Database integration with user management\n- Role-based access control (RBAC)\n- API rate limiting and security middleware\n\n## Technical Stack\n- Backend: Node.js with Express framework\n- Database: PostgreSQL with Sequelize ORM\n- Authentication: JWT with passport.js\n- Security: Helmet.js, CORS, input validation\n\n## Implementation Steps\n1. Database schema design for users and roles\n2. Authentication middleware development\n3. JWT token generation and validation\n4. Password encryption and verification\n5. API endpoint protection and testing\n\n## Architecture\nFollows MVC pattern with clear separation:\n- Controllers: Handle HTTP requests\n- Services: Business logic implementation\n- Models: Database entity definitions\n- Middleware: Authentication and validation\n\nComplete with comprehensive testing suite and documentation.",
  "github_repo_link": "https://github.com/example/jwt-auth-system",
  "module_id": "core-development",
  "schema_version": "1.0"
}
```

### Expected Score Breakdown:
- **Title Analysis**: ~18/20 points
  - High technical keyword density (JWT, API, authentication, database)
  - Clear and descriptive (12+ words)
  - Strong alignment with description
- **Description Analysis**: ~36/40 points
  - Excellent content depth (300+ words)
  - Clear structure with headers and steps
  - High technical density
  - Comprehensive requirements
- **Repository Analysis**: ~32/40 points
  - Well-structured with clear layers
  - Good documentation (README, comments)
  - Multiple file types and organization
  - Architecture patterns evident

**Total Expected Score**: ~86/100 ✅ **PASS**

---

## ⚠️ TEST CASE 2: BORDERLINE Score (50-70 points)

### Input Parameters:
```json
{
  "task_title": "User Login System",
  "task_description": "Built a basic login system for users. The system allows users to register and login with username and password. Used some security features and database to store user information. The frontend has forms for registration and login. Backend handles the authentication process.\n\nFeatures:\n- User registration\n- User login\n- Password storage\n- Basic security\n\nTechnology used: JavaScript, HTML, CSS, Node.js, and database.",
  "github_repo_link": "https://github.com/example/basic-login",
  "module_id": "core-development",
  "schema_version": "1.0"
}
```

### Expected Score Breakdown:
- **Title Analysis**: ~8/20 points
  - Few technical keywords (system, login)
  - Short and basic (3 words)
  - Moderate alignment with description
- **Description Analysis**: ~22/40 points
  - Moderate content depth (100-150 words)
  - Basic structure with simple list
  - Low technical density
  - Incomplete requirements
- **Repository Analysis**: ~25/40 points
  - Basic file structure
  - Minimal documentation
  - Simple organization
  - Limited architecture patterns

**Total Expected Score**: ~55/100 ⚠️ **BORDERLINE**

---

## ❌ TEST CASE 3: FAIL Score (20-40 points)

### Input Parameters:
```json
{
  "task_title": "My Project",
  "task_description": "I made a website. It works and has some features. Users can do things on it. I used some programming languages to build it.",
  "github_repo_link": "https://github.com/example/empty-repo",
  "module_id": "core-development",
  "schema_version": "1.0"
}
```

### Expected Score Breakdown:
- **Title Analysis**: ~2/20 points
  - No technical keywords
  - Very short and vague (2 words)
  - Poor alignment with description
- **Description Analysis**: ~8/40 points
  - Very low content depth (25 words)
  - No structure or organization
  - No technical terms
  - Extremely vague requirements
- **Repository Analysis**: ~15/40 points
  - Minimal or empty repository
  - No documentation
  - Poor file organization
  - No clear architecture

**Total Expected Score**: ~25/100 ❌ **FAIL**

---

## 🔬 Detailed Scoring Factors

### Title Analysis (20 points)
**High Score Factors:**
- Technical keywords: API, database, authentication, framework names
- Optimal length: 8-15 words
- Clear technology mentions
- Strong alignment with description content

**Low Score Factors:**
- Generic words: "project", "system", "website"
- Too short (< 4 words) or too long (> 20 words)
- No technical terms
- Misalignment with description

### Description Analysis (40 points)
**High Score Factors:**
- Word count: 200-500 words
- Clear structure: headers, lists, sections
- Technical terms: frameworks, tools, methodologies
- Step-by-step implementation details
- Architecture descriptions

**Low Score Factors:**
- Word count: < 50 words
- No structure or organization
- Vague language: "some features", "it works"
- No technical specifications
- Missing implementation details

### Repository Analysis (40 points)
**High Score Factors:**
- Well-organized directory structure
- Multiple programming languages
- Comprehensive README (> 1000 characters)
- Clear architectural layers (controllers, services, models)
- Documentation files and comments

**Low Score Factors:**
- Empty or minimal repositories
- Single file projects
- No README or very short README
- No clear organization
- Missing documentation

---

## 🎯 Quick Score Optimization Tips

### To Achieve PASS (80+):
1. **Title**: Include 3-4 technical keywords, 8-12 words total
2. **Description**: 300+ words with clear sections and technical details
3. **Repository**: Multi-layered architecture with comprehensive documentation

### To Achieve BORDERLINE (50-79):
1. **Title**: Include 1-2 technical keywords, 4-8 words
2. **Description**: 100-200 words with basic structure
3. **Repository**: Basic organization with some documentation

### To Avoid FAIL (< 50):
1. **Title**: Avoid generic terms, include at least one technical keyword
2. **Description**: Write at least 50 words with some technical details
3. **Repository**: Ensure repository exists and has basic file structure

---

## 🧪 Registry Validation Requirements

All test cases must include valid registry parameters:
- **module_id**: Must be one of: `core-development`, `advanced-features`, `system-integration`, `performance-optimization`, `security-implementation`
- **schema_version**: Must be `1.0` (current supported version)

**Invalid registry parameters will result in rejection before evaluation begins.**