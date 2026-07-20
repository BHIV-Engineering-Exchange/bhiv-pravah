// Backend response types (exact match to backend)
export interface DataStatus {
  data_source: 'REALTIME_YAHOO_FINANCE' | 'CACHED_YAHOO_FINANCE' | 'FALLBACK_PROVIDER' | 'INVALID';
  data_freshness_seconds: number;
  market_context: 'NORMAL' | 'HIGH_VOLATILITY' | 'EVENT_WINDOW' | 'MARKET_CLOSED';
}

export interface PredictionItem {
  symbol: string;
  action?: string;
  predicted_return?: number;
  current_price?: number;
  predicted_price?: number;
  model_agreement?: string;
  signal_strength?: number;
  trust_gate_active?: boolean;
  trust_gate_reason?: string;
  data_status?: DataStatus;
  error?: string;
  reason?: string;
  market_intelligence?: {
    plain_language_summary?: string;
    directional_bias?: 'bullish' | 'bearish' | 'neutral';
    decision_support?: string;
    low_probability_trade_filter?: boolean;
    not_a_sell_signal?: boolean;
    strength_building?: string[];
    weakness_forming?: string[];
    risk_increasing?: string[];
    market_context?: {
      market_context?: string;
      regime?: string;
      trend_strength?: string;
      atr_percent?: number | null;
      adx?: number;
    };
    evolving_patterns?: {
      momentum_shift?: string;
      breakout_state?: string;
      breakout_quality?: string;
      continuation_vs_exhaustion?: string;
      exhaustion_risk?: string;
      evolving_patterns?: string[];
    };
    confirmation_layer?: {
      confidence?: number;
      models_align?: boolean;
      price_agreement?: boolean;
    };
  };
  timestamp?: string;
  confidence?: number;
  individual_predictions?: Record<string, any>;
  unavailable?: boolean;
  // UI-specific and extended backend properties
  ensemble_details?: {
    models_align: boolean;
    price_agreement: boolean;
  };
  isUserAdded?: boolean;
  _dataIntegrity?: {
    shouldDisplay: boolean;
    status: string;
    confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
  };
  _marketDataValidation?: {
    isValid: boolean;
    reason?: string;
  };
  horizon?: string;
}

// Analyze Response Type Definition
export interface AnalyzeResponse {
  symbol: string;
  predictions: PredictionItem[];
  metadata?: {
    consensus?: string;
    average_confidence?: number;
    horizons?: string[];
    [key: string]: unknown;
  };
  error?: string;
}

// Portfolio Holding Type Definition
export interface Holding {
  symbol: string;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  value: number;
}
