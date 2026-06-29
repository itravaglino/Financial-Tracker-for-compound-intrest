const API_BASE = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }

  async request(path, options = {}) {
    const headers = { ...options.headers };
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Error en la solicitud');
    return data;
  }

  login(username, password) {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    return this.request('/auth/login', { method: 'POST', body: form, headers: {} });
  }

  register(username, email, password) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  getMe() { return this.request('/auth/me'); }

  getPortfolios() { return this.request('/portfolio/'); }
  createPortfolio(name) {
    return this.request('/portfolio/', { method: 'POST', body: JSON.stringify({ name }) });
  }
  addHolding(portfolioId, data) {
    return this.request(`/portfolio/${portfolioId}/holdings`, {
      method: 'POST', body: JSON.stringify(data),
    });
  }
  importYahoo(portfolioId, symbols) {
    return this.request('/portfolio/import-yahoo', {
      method: 'POST', body: JSON.stringify({ portfolio_id: portfolioId, symbols }),
    });
  }
  analyzePortfolio(portfolioId) {
    return this.request(`/portfolio/${portfolioId}/analysis`);
  }

  getQuote(symbol) { return this.request(`/market/quote/${symbol}`); }
  getIsometric(symbol) { return this.request(`/market/isometric/${symbol}`); }
  getValuation(symbol) { return this.request(`/market/valuation/${symbol}`); }
  getTechnical(symbol) { return this.request(`/market/technical/${symbol}`); }
  compare(symbols) { return this.request(`/market/compare?symbols=${symbols.join(',')}`); }

  createAlert(data) {
    return this.request('/portfolio/alerts', { method: 'POST', body: JSON.stringify(data) });
  }
  getAlerts() { return this.request('/portfolio/alerts/list'); }
  deleteAlert(id) { return this.request(`/portfolio/alerts/${id}`, { method: 'DELETE' }); }

  createStopLoss(data) {
    return this.request('/trading/stop-loss', { method: 'POST', body: JSON.stringify(data) });
  }
  getStopLosses() { return this.request('/trading/stop-loss'); }
  deleteStopLoss(id) { return this.request(`/trading/stop-loss/${id}`, { method: 'DELETE' }); }

  placeOrder(data) {
    return this.request('/trading/orders', { method: 'POST', body: JSON.stringify(data) });
  }
  getOrders() { return this.request('/trading/orders'); }
  getAccount() { return this.request('/trading/account'); }
  checkAlerts() { return this.request('/trading/check-alerts', { method: 'POST' }); }
}

export const api = new ApiClient();
