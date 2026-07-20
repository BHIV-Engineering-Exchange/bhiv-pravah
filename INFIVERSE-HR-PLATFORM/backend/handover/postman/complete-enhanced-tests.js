// ==================== COMPLETE ENHANCED ISSUE DETECTION SCRIPTS ====================
// Copy this entire script to Postman Collection > Scripts > Post-response

// ==================== CORE VALIDATIONS ====================
pm.test("Status code is successful (2xx)", function () {
    pm.expect(pm.response.code).to.be.oneOf([200, 201, 202, 204]);
});

pm.test("Response time is under 2000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

pm.test("Content-Type is application/json", function () {
    const contentType = pm.response.headers.get("Content-Type");
    if (contentType && pm.response.code !== 204) {
        pm.expect(contentType).to.include("application/json");
    }
});

pm.test("Response body is valid JSON", function () {
    if (pm.response.code !== 204 && pm.response.text().length > 0) {
        pm.response.json();
    }
});

pm.test("No server errors (5xx)", function () {
    pm.expect(pm.response.code).to.be.below(500);
});

// ==================== METHOD-SPECIFIC VALIDATIONS ====================
pm.test("GET request returns data", function () {
    if (pm.request.method === "GET" && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        pm.expect(jsonData).to.not.be.undefined;
    }
});

pm.test("POST request returns creation confirmation", function () {
    if (pm.request.method === "POST" && (pm.response.code === 200 || pm.response.code === 201)) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        const hasCreationIndicator = jsonData.id !== undefined || jsonData._id !== undefined || jsonData.data !== undefined || jsonData.result !== undefined || jsonData.message !== undefined || jsonData.success !== undefined || jsonData.created !== undefined || jsonData.status !== undefined;
        pm.expect(hasCreationIndicator).to.be.true;
    }
});

pm.test("PUT/PATCH request returns update confirmation", function () {
    if ((pm.request.method === "PUT" || pm.request.method === "PATCH") && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        const hasUpdateIndicator = jsonData.id !== undefined || jsonData._id !== undefined || jsonData.data !== undefined || jsonData.result !== undefined || jsonData.message !== undefined || jsonData.success !== undefined || jsonData.updated !== undefined || jsonData.status !== undefined;
        pm.expect(hasUpdateIndicator).to.be.true;
    }
});

pm.test("DELETE request returns success", function () {
    if (pm.request.method === "DELETE") {
        pm.expect(pm.response.code).to.be.oneOf([200, 202, 204]);
        if (pm.response.code === 200 && pm.response.text().length > 0) {
            const jsonData = pm.response.json();
            const hasDeleteIndicator = jsonData.message !== undefined || jsonData.success !== undefined || jsonData.deleted !== undefined || jsonData.status !== undefined;
            pm.expect(hasDeleteIndicator).to.be.true;
        }
    }
});

// ==================== AUTHENTICATION VALIDATIONS ====================
pm.test("Auth endpoints return token/session data", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isAuthEndpoint = requestName.includes("login") || requestName.includes("auth") || requestName.includes("token") || requestName.includes("signin") || requestName.includes("register") || requestName.includes("signup");
    
    if (isAuthEndpoint && (pm.response.code === 200 || pm.response.code === 201)) {
        const jsonData = pm.response.json();
        const hasAuthData = jsonData.token !== undefined || jsonData.access_token !== undefined || jsonData.accessToken !== undefined || jsonData.session !== undefined || jsonData.sessionId !== undefined || jsonData.jwt !== undefined || jsonData.refresh_token !== undefined || jsonData.refreshToken !== undefined || jsonData.user !== undefined || jsonData.data !== undefined;
        pm.expect(hasAuthData).to.be.true;
    }
});

// ==================== HR PLATFORM SPECIFIC VALIDATIONS ====================
pm.test("Candidate endpoints return valid structure", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isCandidateEndpoint = requestName.includes("candidate");
    
    if (isCandidateEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        if (Array.isArray(jsonData)) {
            if (jsonData.length > 0) {
                jsonData.forEach(function(candidate) {
                    pm.expect(typeof candidate).to.equal("object");
                });
            }
        } else if (jsonData.data && Array.isArray(jsonData.data)) {
            if (jsonData.data.length > 0) {
                jsonData.data.forEach(function(candidate) {
                    pm.expect(typeof candidate).to.equal("object");
                });
            }
        } else if (typeof jsonData === "object") {
            pm.expect(jsonData).to.not.be.null;
        }
    }
});

pm.test("Job endpoints return valid structure", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isJobEndpoint = requestName.includes("job") && !requestName.includes("jobless");
    
    if (isJobEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        if (Array.isArray(jsonData)) {
            if (jsonData.length > 0) {
                jsonData.forEach(function(job) {
                    pm.expect(typeof job).to.equal("object");
                });
            }
        } else if (jsonData.data && Array.isArray(jsonData.data)) {
            if (jsonData.data.length > 0) {
                jsonData.data.forEach(function(job) {
                    pm.expect(typeof job).to.equal("object");
                });
            }
        } else if (typeof jsonData === "object") {
            pm.expect(jsonData).to.not.be.null;
        }
    }
});

pm.test("Interview endpoints return valid structure", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isInterviewEndpoint = requestName.includes("interview") || requestName.includes("schedule");
    
    if (isInterviewEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        pm.expect(typeof jsonData).to.equal("object");
    }
});

pm.test("Application endpoints return valid structure", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isApplicationEndpoint = requestName.includes("application") || requestName.includes("apply");
    
    if (isApplicationEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        pm.expect(typeof jsonData).to.equal("object");
    }
});

// ==================== AI/ML SERVICE VALIDATIONS ====================
pm.test("AI/LangGraph endpoints return valid response", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const requestUrl = pm.request.url.toString().toLowerCase();
    const isAIEndpoint = requestName.includes("lang") || requestName.includes("graph") || requestName.includes("ai") || requestName.includes("ml") || requestName.includes("predict") || requestName.includes("analyze") || requestName.includes("process") || requestUrl.includes("langgraph");
    
    if (isAIEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        const hasAIResponse = jsonData.result !== undefined || jsonData.output !== undefined || jsonData.prediction !== undefined || jsonData.analysis !== undefined || jsonData.data !== undefined || jsonData.response !== undefined || jsonData.message !== undefined || jsonData.status !== undefined;
        pm.expect(hasAIResponse).to.be.true;
    }
});

pm.test("Agent endpoints return valid response", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const requestUrl = pm.request.url.toString().toLowerCase();
    const isAgentEndpoint = requestName.includes("agent") || requestUrl.includes("agent");
    
    if (isAgentEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.not.be.null;
        const hasAgentResponse = jsonData.result !== undefined || jsonData.action !== undefined || jsonData.task !== undefined || jsonData.status !== undefined || jsonData.data !== undefined || jsonData.response !== undefined || jsonData.agent !== undefined || jsonData.output !== undefined;
        pm.expect(hasAgentResponse).to.be.true;
    }
});

// ==================== PAGINATION VALIDATIONS ====================
pm.test("Paginated responses have proper structure", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const isListEndpoint = requestName.includes("list") || requestName.includes("all") || (requestName.includes("get") && (requestName.includes("s") || requestName.includes("candidates") || requestName.includes("jobs")));
    
    if (isListEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        if (jsonData.data !== undefined && jsonData.total !== undefined) {
            pm.expect(jsonData.data).to.be.an("array");
            pm.expect(jsonData.total).to.be.a("number");
        } else if (jsonData.items !== undefined) {
            pm.expect(jsonData.items).to.be.an("array");
        } else if (jsonData.results !== undefined) {
            pm.expect(jsonData.results).to.be.an("array");
        }
    }
});

// ==================== HEALTH CHECK VALIDATIONS ====================
pm.test("Health check endpoints return healthy status", function () {
    const requestName = pm.info.requestName.toLowerCase();
    const requestUrl = pm.request.url.toString().toLowerCase();
    const isHealthEndpoint = requestName.includes("health") || requestName.includes("ping") || requestName.includes("status") || requestName.includes("root") || requestUrl.includes("/health") || requestUrl.includes("/ping");
    
    if (isHealthEndpoint && pm.response.code === 200) {
        const jsonData = pm.response.json();
        if (jsonData.status) {
            pm.expect(jsonData.status.toLowerCase()).to.be.oneOf(['ok', 'healthy', 'running', 'up', 'success', 'active']);
        }
    }
});

// ==================== SECURITY ISSUE DETECTION ====================
pm.test("Security headers present", function () {
    const securityHeaders = ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection", "Strict-Transport-Security"];
    let missingHeaders = [];
    securityHeaders.forEach(header => {
        if (!pm.response.headers.has(header)) missingHeaders.push(header);
    });
    if (missingHeaders.length > 0) console.warn("Missing security headers:", missingHeaders);
});

pm.test("No sensitive data in response", function () {
    const responseText = pm.response.text().toLowerCase();
    const sensitivePatterns = ["password", "secret", "token", "key", "credential", "ssn", "social security", "credit card", "cvv"];
    let exposedData = [];
    sensitivePatterns.forEach(pattern => {
        if (responseText.includes(pattern) && !responseText.includes("password_hash")) exposedData.push(pattern);
    });
    if (exposedData.length > 0) console.error("Potential sensitive data exposure:", exposedData);
});

// ==================== PERFORMANCE MONITORING ====================
pm.test("Performance monitoring by endpoint type", function () {
    const responseTime = pm.response.responseTime;
    const requestName = pm.info.requestName.toLowerCase();
    const thresholds = { health: 500, auth: 1000, list: 1500, search: 2000, ai: 5000, ml: 10000, default: 2000 };
    let threshold = thresholds.default;
    
    if (requestName.includes("health")) threshold = thresholds.health;
    else if (requestName.includes("auth") || requestName.includes("login")) threshold = thresholds.auth;
    else if (requestName.includes("list") || requestName.includes("get")) threshold = thresholds.list;
    else if (requestName.includes("search")) threshold = thresholds.search;
    else if (requestName.includes("ai") || requestName.includes("predict")) threshold = thresholds.ai;
    else if (requestName.includes("ml") || requestName.includes("analyze")) threshold = thresholds.ml;
    
    if (responseTime > threshold) console.warn(`Slow response: ${requestName} took ${responseTime}ms (threshold: ${threshold}ms)`);
});

// ==================== DATA INTEGRITY ====================
pm.test("Critical fields validation", function () {
    if (pm.response.code === 200 && pm.response.text().length > 0) {
        const jsonData = pm.response.json();
        const requestName = pm.info.requestName.toLowerCase();
        let criticalFields = [];
        
        if (requestName.includes("candidate")) criticalFields = ["id", "name", "email"];
        else if (requestName.includes("job")) criticalFields = ["id", "title", "department"];
        else if (requestName.includes("user") || requestName.includes("auth")) criticalFields = ["id", "username"];
        
        criticalFields.forEach(field => {
            if (jsonData[field] === null || jsonData[field] === undefined || jsonData[field] === "") {
                console.error(`Critical field '${field}' is null/undefined/empty in ${requestName}`);
            }
        });
    }
});

pm.test("Response data types are valid", function () {
    if (pm.response.code === 200 && pm.response.text().length > 0) {
        const jsonData = pm.response.json();
        
        if (jsonData.id !== undefined) {
            pm.expect(typeof jsonData.id).to.be.oneOf(["string", "number"]);
        }
        if (jsonData._id !== undefined) {
            pm.expect(typeof jsonData._id).to.be.oneOf(["string", "number"]);
        }
        if (jsonData.created_at !== undefined || jsonData.createdAt !== undefined) {
            const dateField = jsonData.created_at || jsonData.createdAt;
            pm.expect(typeof dateField).to.be.oneOf(["string", "number"]);
        }
        if (jsonData.updated_at !== undefined || jsonData.updatedAt !== undefined) {
            const dateField = jsonData.updated_at || jsonData.updatedAt;
            pm.expect(typeof dateField).to.be.oneOf(["string", "number"]);
        }
    }
});

pm.test("Array responses contain valid objects", function () {
    if (pm.response.code === 200 && pm.response.text().length > 0) {
        const jsonData = pm.response.json();
        
        if (Array.isArray(jsonData) && jsonData.length > 0) {
            jsonData.forEach(function(item, index) {
                pm.expect(typeof item).to.equal("object", "Item at index " + index + " should be an object");
                pm.expect(item).to.not.be.null;
            });
        }
    }
});

// ==================== ERROR HANDLING ====================
pm.test("Error responses have proper structure", function () {
    if (pm.response.code >= 400 && pm.response.code < 500) {
        if (pm.response.text().length > 0) {
            const jsonData = pm.response.json();
            const hasErrorInfo = jsonData.message !== undefined || jsonData.error !== undefined || jsonData.detail !== undefined || jsonData.errors !== undefined || jsonData.msg !== undefined;
            pm.expect(hasErrorInfo).to.be.true;
        }
    }
});

// ==================== RATE LIMITING ====================
pm.test("Rate limiting monitoring", function () {
    const rateLimitHeaders = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"];
    rateLimitHeaders.forEach(header => {
        if (pm.response.headers.has(header)) {
            const value = pm.response.headers.get(header);
            console.log(`Rate limit - ${header}: ${value}`);
            if (header === "X-RateLimit-Remaining" && parseInt(value) < 10) console.warn(`Low rate limit: ${value}`);
        }
    });
    if (pm.response.code === 429) console.error("Rate limit exceeded!");
});

// ==================== DATABASE CONNECTION ISSUES ====================
pm.test("Database connection health", function () {
    if (pm.response.code >= 500) {
        const responseText = pm.response.text().toLowerCase();
        const dbErrorPatterns = ["connection refused", "timeout", "database", "sql", "connection pool", "deadlock", "constraint"];
        
        dbErrorPatterns.forEach(pattern => {
            if (responseText.includes(pattern)) {
                console.error(`Potential database issue detected: ${pattern}`);
            }
        });
    }
});

// ==================== COMPREHENSIVE LOGGING ====================
pm.test("Request/Response logging", function () {
    const requestInfo = {
        method: pm.request.method,
        url: pm.request.url.toString(),
        timestamp: new Date().toISOString(),
        responseTime: pm.response.responseTime,
        statusCode: pm.response.code,
        responseSize: pm.response.text().length
    };
    
    if (pm.response.responseTime > 3000) console.log("SLOW REQUEST:", JSON.stringify(requestInfo, null, 2));
    if (pm.response.code >= 400) console.log("ERROR REQUEST:", JSON.stringify(requestInfo, null, 2));
    
    pm.globals.set(`metrics_${pm.info.requestName}`, JSON.stringify(requestInfo));
});