import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

export const auth = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  login: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => api.get('/auth/me'),
};

export const portfolio = {
  list: () => api.get('/portfolio/'),
  create: (name: string) => api.post('/portfolio/', { name }),
  addHolding: (portfolioId: number, data: object) =>
    api.post(`/portfolio/${portfolioId}/holdings`, data),
  deleteHolding: (holdingId: number) => api.delete(`/portfolio/holdings/${holdingId}`),
  importYahoo: (symbols: string[], portfolioName: string) =>
    api.post('/portfolio/import/yahoo', { symbols, portfolio_name: portfolioName }),
};

export const market = {
  quote: (symbol: string) => api.get(`/market/quote/${symbol}`),
  technical: (symbol: string) => api.get(`/market/analysis/technical/${symbol}`),
  neural: (symbol: string) => api.get(`/market/analysis/neural/${symbol}`),
  valuation: (symbol: string) => api.get(`/market/valuation/${symbol}`),
  isometric: (symbols: string) => api.get(`/market/valuation/isometric?symbols=${symbols}`),
  metrics: (symbol: string) => api.get(`/market/metrics/${symbol}`),
  portfolioContrast: (symbols: string) => api.get(`/market/analysis/portfolio-contrast?symbols=${symbols}`),
  portfolioNeural: (symbols: string) => api.get(`/market/analysis/portfolio-neural?symbols=${symbols}`),
};

export const alerts = {
  list: () => api.get('/alerts'),
  create: (data: object) => api.post('/alerts', data),
  delete: (id: number) => api.delete(`/alerts/${id}`),
  check: () => api.post('/alerts/check'),
};

export const trading = {
  placeOrder: (data: object) => api.post('/trading/order', data),
  orders: () => api.get('/trading/orders'),
  account: () => api.get('/trading/account'),
  configureBroker: (data: object) => api.post('/trading/broker-config', data),
  createStopLoss: (holdingId: number, data: object) => api.post(`/stop-loss/${holdingId}`, data),
  listStopLoss: () => api.get('/stop-loss'),
};
