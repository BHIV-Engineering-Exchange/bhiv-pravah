import { cacheGet, cacheSet, cacheDel } from '../config/redis.js';
import logger from '../config/logger.js';
import cacheInvalidationService from './cacheInvalidation.service.js';

class CacheService {
  // Generate cache key with namespace
  generateKey(namespace, identifier, userId = null) {
    const userPart = userId ? `:user:${userId}` : '';
    return `artha:${namespace}:${identifier}${userPart}`;
  }

  // Cache ledger entries with user-specific keys
  async cacheLedgerEntries(filters, pagination, userId, data) {
    const key = this.generateKey(
      'ledger:entries',
      `${JSON.stringify(filters)}:${JSON.stringify(pagination)}`,
      userId
    );
    return await cacheSet(key, data, 300); // 5 minutes
  }

  async getCachedLedgerEntries(filters, pagination, userId) {
    const key = this.generateKey(
      'ledger:entries',
      `${JSON.stringify(filters)}:${JSON.stringify(pagination)}`,
      userId
    );
    return await cacheGet(key);
  }

  // Cache account balances
  async cacheAccountBalances(filters, data) {
    const key = this.generateKey('accounts', 'balances', JSON.stringify(filters));
    return await cacheSet(key, data, 600); // 10 minutes
  }

  async getCachedAccountBalances(filters) {
    const key = this.generateKey('accounts', 'balances', JSON.stringify(filters));
    return await cacheGet(key);
  }

  // Cache ledger summary
  async cacheLedgerSummary(data) {
    const key = this.generateKey('ledger', 'summary', null);
    return await cacheSet(key, data, 300); // 5 minutes
  }

  async getCachedLedgerSummary() {
    const key = this.generateKey('ledger', 'summary', null);
    return await cacheGet(key);
  }

  // Cache invoice statistics
  async cacheInvoiceStats(dateFrom, dateTo, data) {
    const key = this.generateKey('invoices', 'stats', `${dateFrom || 'all'}:${dateTo || 'all'}`);
    return await cacheSet(key, data, 900); // 15 minutes
  }

  async getCachedInvoiceStats(dateFrom, dateTo) {
    const key = this.generateKey('invoices', 'stats', `${dateFrom || 'all'}:${dateTo || 'all'}`);
    return await cacheGet(key);
  }

  // Cache expense statistics
  async cacheExpenseStats(dateFrom, dateTo, data) {
    const key = this.generateKey('expenses', 'stats', `${dateFrom || 'all'}:${dateTo || 'all'}`);
    return await cacheSet(key, data, 900); // 15 minutes
  }

  async getCachedExpenseStats(dateFrom, dateTo) {
    const key = this.generateKey('expenses', 'stats', `${dateFrom || 'all'}:${dateTo || 'all'}`);
    return await cacheGet(key);
  }

  // Invalidate related caches when data changes
  async invalidateLedgerCaches() {
    return await cacheInvalidationService.invalidateByPattern('ledger:*');
  }

  async invalidateInvoiceCaches() {
    return await cacheInvalidationService.invalidateByPattern('invoices:*');
  }

  async invalidateExpenseCaches() {
    return await cacheInvalidationService.invalidateByPattern('expenses:*');
  }

  async invalidateAccountsCaches() {
    return await cacheInvalidationService.invalidateByPattern('accounts:*');
  }

  // Generic cache methods
  async get(key) {
    return await cacheGet(key);
  }

  async set(key, value, ttl = 3600) {
    return await cacheSet(key, value, ttl);
  }

  async delete(key) {
    return await cacheDel(key);
  }
}

export default new CacheService();