import mongoose from 'mongoose';
import logger from '../config/logger.js';

class DatabaseService {
  /**
   * Get database statistics
   */
  async getDatabaseStats() {
    try {
      const db = mongoose.connection.db;
      const stats = await db.stats();
      
      return {
        collections: stats.collections,
        dataSize: Math.round(stats.dataSize / 1024 / 1024), // MB
        storageSize: Math.round(stats.storageSize / 1024 / 1024), // MB
        indexSize: Math.round(stats.indexSize / 1024 / 1024), // MB
        objects: stats.objects,
        avgObjSize: Math.round(stats.avgObjSize),
        indexes: stats.indexes,
      };
    } catch (error) {
      logger.error('Get database stats error:', error);
      throw error;
    }
  }

  /**
   * Get collection statistics
   */
  async getCollectionStats() {
    try {
      const db = mongoose.connection.db;
      const collections = await db.listCollections().toArray();
      const stats = [];

      for (const collection of collections) {
        try {
          const collStats = await db.collection(collection.name).stats();
          stats.push({
            name: collection.name,
            count: collStats.count,
            size: Math.round(collStats.size / 1024), // KB
            avgObjSize: Math.round(collStats.avgObjSize || 0),
            storageSize: Math.round(collStats.storageSize / 1024), // KB
            totalIndexSize: Math.round(collStats.totalIndexSize / 1024), // KB
            indexCount: collStats.nindexes,
          });
        } catch (error) {
          logger.warn(`Could not get stats for collection ${collection.name}:`, error.message);
        }
      }

      return stats.sort((a, b) => b.size - a.size);
    } catch (error) {
      logger.error('Get collection stats error:', error);
      throw error;
    }
  }

  /**
   * Get index information for all collections
   */
  async getIndexInfo() {
    try {
      const db = mongoose.connection.db;
      const collections = await db.listCollections().toArray();
      const indexInfo = {};

      for (const collection of collections) {
        try {
          const indexes = await db.collection(collection.name).indexes();
          indexInfo[collection.name] = indexes.map(index => ({
            name: index.name,
            keys: index.key,
            unique: index.unique || false,
            sparse: index.sparse || false,
            background: index.background || false,
            size: index.size || 0,
          }));
        } catch (error) {
          logger.warn(`Could not get indexes for collection ${collection.name}:`, error.message);
        }
      }

      return indexInfo;
    } catch (error) {
      logger.error('Get index info error:', error);
      throw error;
    }
  }

  /**
   * Analyze slow operations (requires profiling to be enabled)
   */
  async getSlowOperations(limit = 10) {
    try {
      const db = mongoose.connection.db;
      
      // Check if profiling is enabled
      const profilingStatus = await db.command({ profile: -1 });
      
      if (profilingStatus.was === 0) {
        return {
          message: 'Database profiling is not enabled. Enable with db.setProfilingLevel(1) to track slow operations.',
          operations: [],
        };
      }

      // Get slow operations from system.profile collection
      const slowOps = await db.collection('system.profile')
        .find({ ts: { $gte: new Date(Date.now() - 24 * 60 * 60 * 1000) } }) // Last 24 hours
        .sort({ ts: -1 })
        .limit(limit)
        .toArray();

      return {
        message: `Found ${slowOps.length} operations in the last 24 hours`,
        operations: slowOps.map(op => ({
          timestamp: op.ts,
          operation: op.op,
          namespace: op.ns,
          duration: op.millis,
          command: op.command,
        })),
      };
    } catch (error) {
      logger.error('Get slow operations error:', error);
      return {
        message: 'Could not retrieve slow operations',
        operations: [],
        error: error.message,
      };
    }
  }

  /**
   * Get connection information
   */
  async getConnectionInfo() {
    try {
      const db = mongoose.connection.db;
      const serverStatus = await db.command({ serverStatus: 1 });
      
      return {
        host: serverStatus.host,
        version: serverStatus.version,
        uptime: serverStatus.uptime,
        connections: {
          current: serverStatus.connections.current,
          available: serverStatus.connections.available,
          totalCreated: serverStatus.connections.totalCreated,
        },
        network: {
          bytesIn: Math.round(serverStatus.network.bytesIn / 1024 / 1024), // MB
          bytesOut: Math.round(serverStatus.network.bytesOut / 1024 / 1024), // MB
          numRequests: serverStatus.network.numRequests,
        },
        opcounters: serverStatus.opcounters,
      };
    } catch (error) {
      logger.error('Get connection info error:', error);
      throw error;
    }
  }

  /**
   * Suggest optimizations based on database analysis
   */
  async suggestOptimizations() {
    try {
      const suggestions = [];
      
      // Analyze collection sizes
      const collectionStats = await this.getCollectionStats();
      const largeCollections = collectionStats.filter(col => col.size > 10 * 1024); // > 10MB
      
      if (largeCollections.length > 0) {
        suggestions.push({
          type: 'performance',
          priority: 'medium',
          message: `Large collections detected: ${largeCollections.map(c => c.name).join(', ')}. Consider archiving old data.`,
        });
      }

      // Analyze index usage
      const indexInfo = await this.getIndexInfo();
      let totalIndexes = 0;
      const unusedIndexes = 0;

      Object.values(indexInfo).forEach(indexes => {
        totalIndexes += indexes.length;
        // Note: Detecting unused indexes requires additional MongoDB commands
        // This is a simplified check
      });

      if (totalIndexes > 50) {
        suggestions.push({
          type: 'performance',
          priority: 'low',
          message: `High number of indexes (${totalIndexes}). Review and remove unused indexes.`,
        });
      }

      // Check database size
      const dbStats = await this.getDatabaseStats();
      if (dbStats.dataSize > 1000) { // > 1GB
        suggestions.push({
          type: 'storage',
          priority: 'medium',
          message: `Database size is ${dbStats.dataSize}MB. Consider implementing data archiving strategy.`,
        });
      }

      if (suggestions.length === 0) {
        suggestions.push({
          type: 'info',
          priority: 'low',
          message: 'Database appears to be well optimized. Continue monitoring performance.',
        });
      }

      return suggestions;
    } catch (error) {
      logger.error('Suggest optimizations error:', error);
      throw error;
    }
  }

  /**
   * Create all indexes for better performance
   */
  async createAllIndexes() {
    try {
      const models = mongoose.models;
      const results = [];

      for (const [modelName, model] of Object.entries(models)) {
        try {
          await model.createIndexes();
          results.push({
            model: modelName,
            status: 'success',
            message: 'Indexes created successfully',
          });
        } catch (error) {
          results.push({
            model: modelName,
            status: 'error',
            message: error.message,
          });
        }
      }

      return results;
    } catch (error) {
      logger.error('Create all indexes error:', error);
      throw error;
    }
  }
}

export default new DatabaseService();