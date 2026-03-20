import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    if (status === 500) {
      console.error("[NavIS] Server error:", detail || error.message);
    } else if (status === 404) {
      console.warn("[NavIS] Not found:", error.config?.url);
    } else if (!error.response) {
      console.error("[NavIS] Network error — backend unavailable");
    }
    return Promise.reject(error);
  }
);

export const systemsApi = {
  list: () => api.get("/systems/"),
  get: (id) => api.get(`/systems/${id}`),
  create: (data) => api.post("/systems/", data),
  update: (id, data) => api.patch(`/systems/${id}`, data),
  delete: (id) => api.delete(`/systems/${id}`),
};

export const servicesApi = {
  list: (systemId) => api.get(`/systems/${systemId}/services/`),
  get: (systemId, id) => api.get(`/systems/${systemId}/services/${id}`),
  create: (systemId, data) => api.post(`/systems/${systemId}/services/`, data),
  update: (systemId, id, data) => api.patch(`/systems/${systemId}/services/${id}`, data),
  delete: (systemId, id) => api.delete(`/systems/${systemId}/services/${id}`),
};

export const interfacesApi = {
  list: (serviceId) => api.get(`/services/${serviceId}/interfaces/`),
  create: (serviceId, data) => api.post(`/services/${serviceId}/interfaces/`, data),
  update: (serviceId, id, data) => api.patch(`/services/${serviceId}/interfaces/${id}`, data),
  delete: (serviceId, id) => api.delete(`/services/${serviceId}/interfaces/${id}`),
};

export const methodsApi = {
  list: (interfaceId) => api.get(`/interfaces/${interfaceId}/methods/`),
  get: (interfaceId, id) => api.get(`/interfaces/${interfaceId}/methods/${id}`),
  create: (interfaceId, data) => api.post(`/interfaces/${interfaceId}/methods/`, data),
  update: (interfaceId, id, data) => api.patch(`/interfaces/${interfaceId}/methods/${id}`, data),
  delete: (interfaceId, id) => api.delete(`/interfaces/${interfaceId}/methods/${id}`),
  sources: (methodId) => api.get(`/methods/${methodId}/sources`),
};

export const interfacesDirectApi = {
  get: (interfaceId) => api.get(`/interfaces/${interfaceId}`),
};

export const servicesDirectApi = {
  get: (serviceId) => api.get(`/services/${serviceId}`),
};

export const graphApi = {
  get: (params) => api.get("/graph/", { params }),
};

export const searchApi = {
  search: (q) => api.get("/search/", { params: { q } }),
};

export const ingestApi = {
  listSources: (systemId) => api.get(`/systems/${systemId}/sources/`),
  createSource: (systemId, data) => api.post(`/systems/${systemId}/sources/`, data),
  deleteSource: (systemId, sourceId) => api.delete(`/systems/${systemId}/sources/${sourceId}`),
  runSource: (systemId, sourceId) => api.post(`/systems/${systemId}/sources/${sourceId}/run`),
  listJobs: (sourceId) => api.get("/ingest/jobs", { params: { source_id: sourceId } }),
  getJob: (jobId) => api.get(`/ingest/jobs/${jobId}`),
};
