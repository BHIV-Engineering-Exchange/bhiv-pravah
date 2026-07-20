const { auditLogger } = require('../services/complianceAuditLogger');

// API Key authentication for compliance endpoints
const verifyComplianceApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const validKey = process.env.COMPLIANCE_API_KEY || 'uniguru-dev-key-2025';

  if (!apiKey || apiKey !== validKey) {
    // Log unauthorized access attempt
    auditLogger.logEvent(
      req.headers['x-user-id'] || 'anonymous',
      'unauthorized_access',
      'compliance_api',
      {
        ip_address: req.ip,
        user_agent: req.get('User-Agent'),
        attempted_endpoint: req.originalUrl,
        provided_key: apiKey ? 'provided' : 'missing'
      },
      'failure'
    ).catch(console.error);

    return res.status(401).json({ 
      error: 'Invalid or missing API key',
      message: 'X-API-Key header is required for compliance endpoints'
    });
  }

  // Add user info to request for logging
  req.complianceUser = {
    id: req.headers['x-user-id'] || 'system',
    ipAddress: req.ip,
    userAgent: req.get('User-Agent')
  };

  next();
};

// Middleware to log all compliance API access
const logComplianceAccess = (req, res, next) => {
  const startTime = Date.now();
  
  // Override res.json to log response
  const originalJson = res.json;
  res.json = function(data) {
    const duration = Date.now() - startTime;
    
    // Log the API access
    auditLogger.logAccess(
      req.complianceUser?.id || 'system',
      `api_${req.method.toLowerCase()}`,
      req.originalUrl,
      res.statusCode < 400 ? 'success' : 'failure',
      'compliance_api_access',
      'compliance_monitoring',
      req.originalUrl,
      req.complianceUser?.ipAddress,
      req.complianceUser?.userAgent,
      {
        method: req.method,
        status_code: res.statusCode,
        duration_ms: duration,
        request_size: req.get('content-length') || 0,
        response_size: JSON.stringify(data).length
      }
    ).catch(console.error);

    return originalJson.call(this, data);
  };

  next();
};

module.exports = {
  verifyComplianceApiKey,
  logComplianceAccess
};