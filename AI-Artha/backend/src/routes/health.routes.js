import express from 'express';
import mongoose from 'mongoose';
import { getRedisClient } from '../config/redis.js';
import logger from '../config/logger.js';
import healthService from '../services/health.service.js';
import performanceService from '../services/performance.service.js';
import observabilityService from '../services/observability.service.js';

const router = express.Router();

// Basic health check
router.get('/health', (req, res) => {
  res.json({
    success: true,
    message: 'ARTHA API is running',
    timestamp: new Date().toISOString(),
    version: '0.1.0',
    uptime: process.uptime(),
  });
});

// Detailed health check
router.get('/health/detailed', async (req, res) => {
  try {
    const health = await healthService.getSystemHealth();
    const statusCode = health.status === 'healthy' ? 200 : 503;
    
    res.status(statusCode).json({
      success: health.status === 'healthy',
      message: `ARTHA API is ${health.status}`,
      data: health,
    });
  } catch (error) {
    logger.error('Detailed health check error:', error);
    res.status(503).json({
      success: false,
      message: 'Health check failed',
      error: error.message,
    });
  }
});

// Readiness probe (for Kubernetes)
router.get('/ready', async (req, res) => {
  try {
    // Check if database is ready
    if (mongoose.connection.readyState !== 1) {
      return res.status(503).json({
        success: false,
        message: 'Database not ready',
      });
    }

    res.json({
      success: true,
      message: 'Service is ready',
    });
  } catch (error) {
    logger.error('Readiness check error:', error);
    res.status(503).json({
      success: false,
      message: 'Service not ready',
    });
  }
});

// Liveness probe (for Kubernetes)
router.get('/live', (req, res) => {
  res.json({
    success: true,
    message: 'Service is alive',
  });
});

// Performance metrics endpoint (public, limited info)
router.get('/metrics', (req, res) => {
  try {
    const metrics = performanceService.getMetrics();
    
    // Return limited public metrics
    res.json({
      success: true,
      data: {
        uptime: metrics.uptime,
        memory: metrics.memory.current,
        requests: {
          total: metrics.requests.total,
          errorPercentage: metrics.requests.errorPercentage,
        },
        responseTime: {
          avg: metrics.responseTime.avg,
        },
      },
    });
  } catch (error) {
    logger.error('Metrics endpoint error:', error);
    res.status(500).json({
      success: false,
      message: 'Metrics unavailable',
    });
  }
});

// System status endpoint
router.get('/status', async (req, res) => {
  try {
    const dbState = mongoose.connection.readyState;
    const redisClient = getRedisClient();
    
    let redisStatus = 'disabled';
    if (redisClient) {
      try {
        const ping = await redisClient.ping();
        redisStatus = ping === 'PONG' ? 'connected' : 'error';
      } catch {
        redisStatus = 'error';
      }
    }
    
    const status = {
      database: dbState === 1 ? 'connected' : 'disconnected',
      redis: redisStatus,
      uptime: Math.floor(process.uptime()),
      environment: process.env.NODE_ENV,
      version: '0.1.0',
    };
    
    const isHealthy = status.database === 'connected';
    
    res.status(isHealthy ? 200 : 503).json({
      success: isHealthy,
      data: status,
    });
  } catch (error) {
    logger.error('Status endpoint error:', error);
    res.status(503).json({
      success: false,
      message: 'Status check failed',
    });
  }
});

// Comprehensive observability health check
router.get('/observability', async (req, res) => {
  try {
    const health = await observabilityService.getSystemHealth();
    res.status(health.status === 'healthy' ? 200 : 503).json({
      success: health.status === 'healthy',
      data: health,
    });
  } catch (error) {
    logger.error('Observability health check error:', error);
    res.status(503).json({ success: false, message: 'Observability check failed' });
  }
});

// Prometheus-compatible metrics
router.get('/prometheus', (req, res) => {
  try {
    const metrics = observabilityService.getMetrics();
    let output = '';
    for (const [key, value] of Object.entries(metrics)) {
      output += `# TYPE artha_${key} gauge\nartha_${key} ${value}\n`;
    }
    res.set('Content-Type', 'text/plain');
    res.send(output);
  } catch (error) {
    res.status(500).send('# Error generating metrics\n');
  }
});

// Runtime dashboard data
router.get('/dashboard', async (req, res) => {
  try {
    const data = await observabilityService.getDashboardData();
    res.json({ success: true, data });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Dashboard data unavailable' });
  }
});

export default router;