/**
 * PetroNexus Centralized API Client & State Manager
 */

const API_BASE = '/api';

const PetroNexusAPI = {
  // Token & Well Storage
  getToken() {
    return localStorage.getItem('petronexus_token') || '';
  },
  setToken(token) {
    localStorage.setItem('petronexus_token', token);
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem('petronexus_user') || '{}');
    } catch {
      return {};
    }
  },
  setUser(user) {
    localStorage.setItem('petronexus_user', JSON.stringify(user));
  },
  getActiveWellId() {
    return parseInt(localStorage.getItem('petronexus_active_well_id') || '23', 10);
  },
  setActiveWellId(id) {
    localStorage.setItem('petronexus_active_well_id', id.toString());
  },
  logout() {
    localStorage.removeItem('petronexus_token');
    localStorage.removeItem('petronexus_user');
    window.location.href = '/login.html';
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    options.headers = headers;
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, options);
      if (response.status === 401) {
        // If on a protected page, redirect to login
        if (!window.location.pathname.includes('login') && !window.location.pathname.includes('register') && window.location.pathname !== '/') {
          // Allow automatic demo login if in demo environment
          console.warn('Unauthorized. Session expired.');
        }
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'API Error' }));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Request to ${endpoint} failed:`, err);
      throw err;
    }
  },

  // Auth
  login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },
  register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },
  getMe() {
    return this.request('/auth/me');
  },

  // Wells
  getWells(status) {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return this.request(`/wells${q}`);
  },
  getWellDetail(id) {
    return this.request(`/wells/${id}`);
  },
  getNearbyWells(id, radiusKm = 15.0) {
    return this.request(`/wells/${id}/nearby?radius_km=${radiusKm}`);
  },
  getWellFormations(id) {
    return this.request(`/wells/${id}/formations`);
  },
  getWellEvents(id) {
    return this.request(`/wells/${id}/events`);
  },
  getWellParameters(id) {
    return this.request(`/wells/${id}/parameters`);
  },
  getWellTrajectories(id) {
    return this.request(`/wells/${id}/trajectories`);
  },
  activateWell(id) {
    return this.request(`/wells/${id}/activate`, { method: 'POST' });
  },

  // Current Well Ingestion
  uploadCurrentWellFile(formData) {
    return this.request('/current-well/upload', {
      method: 'POST',
      body: formData
    });
  },
  getCurrentWellProfile(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/current-well/profile${q}`);
  },
  getCompleteness(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/current-well/completeness${q}`);
  },
  getMissingData(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/current-well/missing-data${q}`);
  },
  demoIngest(demoType = 'pdf', wellId = 23) {
    return this.request('/current-well/demo-ingest', {
      method: 'POST',
      body: JSON.stringify({ demo_type: demoType, well_id: wellId })
    });
  },

  // Intelligence
  runOffsetAnalysis(payload) {
    return this.request('/intelligence/offset-analysis', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  runLookAheadScan(payload) {
    return this.request('/intelligence/look-ahead', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  runScenarioAnalysis(payload) {
    return this.request('/intelligence/scenario', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  compareWells(wellIds) {
    return this.request('/intelligence/compare', {
      method: 'POST',
      body: JSON.stringify({ well_ids: wellIds })
    });
  },

  // Alerts
  getAlerts(wellId, status) {
    let q = [];
    if (wellId) q.push(`well_id=${wellId}`);
    if (status) q.push(`status=${status}`);
    const qs = q.length ? `?${q.join('&')}` : '';
    return this.request(`/alerts${qs}`);
  },
  acknowledgeAlert(alertId, acknowledgedBy = 'Drilling Engineer') {
    return this.request(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: acknowledgedBy })
    });
  },
  getAlertEvidence(alertId) {
    return this.request(`/alerts/${alertId}/evidence`);
  },

  // Documents
  getDocuments(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/documents${q}`);
  },
  getDocumentDetail(id) {
    return this.request(`/documents/${id}`);
  },
  getDocumentPage(id, pageNum) {
    return this.request(`/documents/${id}/pages/${pageNum}`);
  },
  uploadDocument(formData) {
    return this.request('/documents/upload', {
      method: 'POST',
      body: formData
    });
  },

  // AI Assistant
  queryAI(query, wellId, depth, conversationId) {
    const payload = { query, well_id: wellId };
    if (depth !== undefined && depth !== null) payload.current_depth = depth;
    if (conversationId) payload.conversation_id = conversationId;
    return this.request('/ai/query', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Reports
  generateContextPack(wellId) {
    return this.request('/reports/context-pack', {
      method: 'POST',
      body: JSON.stringify({ well_id: wellId, include_ai_synthesis: true, export_format: 'pdf' })
    });
  },
  getPreIntervalBrief(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/reports/pre-interval-brief${q}`);
  },

  // Data Quality & Audit
  getDataQuality(wellId) {
    const q = wellId ? `?well_id=${wellId}` : '';
    return this.request(`/data-quality${q}`);
  },
  getAuditLogs(action) {
    const q = action ? `?action=${action}` : '';
    return this.request(`/audit-logs${q}`);
  }
};

window.PetroNexusAPI = PetroNexusAPI;
