const API_BASE = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private token: string | null = localStorage.getItem('token');

  setToken(token: string | null) {
    this.token = token;
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }

  getToken() {
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('No autorizado');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new Error(err.detail || `Error ${res.status}`);
    }
    if (res.status === 204) return {} as T;
    return res.json();
  }

  // Auth
  async login(username: string, password: string) {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    if (!res.ok) throw new Error('Credenciales inválidas');
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(username: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async getMe() {
    return this.request<{ id: number; username: string; email: string }>('/auth/me');
  }

  // Portfolio
  async getPortfolios() {
    return this.request<Portfolio[]>('/portfolio/');
  }

  async createPortfolio(name: string) {
    return this.request<Portfolio>('/portfolio/', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async importYahoo(symbols: string[], portfolioName: string) {
    return this.request<Portfolio>('/portfolio/import-yahoo', {
      method: 'POST',
      body: JSON.stringify({ symbols, portfolio_name: portfolioName }),
    });
  }

  async addHolding(portfolioId: number, data: { symbol: string; quantity: number; avg_cost: number }) {
    return this.request(`/portfolio/${portfolioId}/holdings`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteHolding(holdingId: number) {
    return this.request(`/portfolio/holdings/${holdingId}`, { method: 'DELETE' });
  }

  // Analysis
  async getQuote(symbol: string) {
    return this.request<Quote>(`/analysis/quote/${symbol}`);
  }

  async getTechnical(symbol: string) {
    return this.request<TechnicalAnalysis>(`/analysis/technical/${symbol}`);
  }

  async getPatterns(symbol: string) {
    return this.request<PatternAnalysis>(`/analysis/patterns/${symbol}`);
  }

  async getValuation(symbol: string) {
    return this.request<Valuation>(`/analysis/valuation/${symbol}`);
  }

  async getPortfolioAnalysis(portfolioId: number) {
    return this.request<PortfolioAnalysis>(`/analysis/portfolio/${portfolioId}`);
  }

  // Trading
  async getAlerts() {
    return this.request<Alert[]>('/trading/alerts');
  }

  async createAlert(data: { symbol: string; alert_type: string; threshold?: number; message?: string }) {
    return this.request<Alert>('/trading/alerts', { method: 'POST', body: JSON.stringify(data) });
  }

  async deleteAlert(id: number) {
    return this.request(`/trading/alerts/${id}`, { method: 'DELETE' });
  }

  async getStopLosses() {
    return this.request<StopLoss[]>('/trading/stop-loss');
  }

  async createStopLoss(data: { symbol: string; quantity: number; trigger_price: number; trailing_percent?: number }) {
    return this.request<StopLoss>('/trading/stop-loss', { method: 'POST', body: JSON.stringify(data) });
  }

  async deleteStopLoss(id: number) {
    return this.request(`/trading/stop-loss/${id}`, { method: 'DELETE' });
  }

  async placeOrder(data: { symbol: string; side: string; quantity: number; order_type?: string; limit_price?: number }) {
    return this.request<Order>('/trading/orders', { method: 'POST', body: JSON.stringify(data) });
  }

  async getOrders() {
    return this.request<Order[]>('/trading/orders');
  }

  async getNotifications() {
    return this.request<Notification[]>('/trading/notifications');
  }

  async getAccount() {
    return this.request<AccountStatus>('/trading/account');
  }

  async checkAlerts() {
    return this.request('/trading/alerts/check', { method: 'POST' });
  }
}

export const api = new ApiClient();

// Types
export interface Portfolio {
  id: number;
  name: string;
  yahoo_portfolio_id?: string;
  created_at: string;
  holdings: Holding[];
  total_value?: number;
  total_gain_loss?: number;
  total_gain_loss_pct?: number;
}

export interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  avg_cost: number;
  currency: string;
  notes?: string;
  current_price?: number;
  market_value?: number;
  gain_loss?: number;
  gain_loss_pct?: number;
  isosteric_value?: number;
  intrinsic_value?: number;
  valuation_rating?: string;
}

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  currency: string;
  timestamp: string;
}

export interface TechnicalAnalysis {
  symbol: string;
  rsi?: number;
  macd: number;
  macd_signal: number;
  sma_20: number;
  sma_50: number;
  sma_200?: number;
  bollinger_upper: number;
  bollinger_lower: number;
  fibonacci_levels: Record<string, number>;
  support_levels: number[];
  resistance_levels: number[];
  trend: string;
  signals: string[];
}

export interface PatternAnalysis {
  symbol: string;
  patterns: Array<{ type: string; strength: string; level?: string; price?: number; neural_confidence?: number }>;
  fibonacci_retracements: Record<string, number>;
  neural_confidence: number;
  neural_accuracy?: number;
  prediction_direction: string;
  prediction_confidence: number;
}

export interface Valuation {
  symbol: string;
  current_price: number;
  intrinsic_value: number;
  isosteric_value: number;
  currency: string;
  pe_ratio?: number;
  pb_ratio?: number;
  peg_ratio?: number;
  dividend_yield?: number;
  fair_value_range: { low: number; mid: number; high: number };
  rating: string;
  rating_score: number;
  metrics: Record<string, unknown>;
}

export interface PortfolioAnalysis {
  portfolio_id: number;
  holdings_analysis: Array<{
    symbol: string;
    trend: string;
    rsi?: number;
    signals: string[];
    patterns: unknown[];
    prediction: string;
    confidence: number;
  }>;
  sector_allocation: Record<string, number>;
  risk_score: number;
  diversification_score: number;
  correlation_matrix: Record<string, number>;
  recommendations: string[];
}

export interface Alert {
  id: number;
  symbol: string;
  alert_type: string;
  threshold?: number;
  message?: string;
  is_active: boolean;
  triggered: boolean;
  created_at: string;
}

export interface StopLoss {
  id: number;
  symbol: string;
  quantity: number;
  trigger_price: number;
  trailing_percent?: number;
  is_active: boolean;
  triggered: boolean;
  created_at: string;
}

export interface Order {
  id: number;
  symbol: string;
  side: string;
  quantity: number;
  order_type: string;
  limit_price?: number;
  status: string;
  external_id?: string;
  created_at: string;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface AccountStatus {
  configured: boolean;
  mode: string;
  buying_power?: number;
  cash?: number;
  portfolio_value?: number;
  message?: string;
}
