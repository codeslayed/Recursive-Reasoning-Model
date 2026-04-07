import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export const api = {
  createSession: async (query, maxDepth = 3, model = "gpt-4o-mini") => {
    const response = await axios.post(`${API_BASE}/sessions`, {
      query,
      max_depth: maxDepth,
      model,
    });
    return response.data;
  },

  getSessions: async () => {
    const response = await axios.get(`${API_BASE}/sessions`);
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await axios.get(`${API_BASE}/sessions/${sessionId}`);
    return response.data;
  },

  connectWebSocket: (sessionId) => {
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    return new WebSocket(`${wsUrl}/api/ws/${sessionId}`);
  },
};
