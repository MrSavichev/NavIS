import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
});

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
};

export const interfacesApi = {
  list: (serviceId) => api.get(`/services/${serviceId}/interfaces/`),
  create: (serviceId, data) => api.post(`/services/${serviceId}/interfaces/`, data),
};

export const methodsApi = {
  list: (interfaceId) => api.get(`/interfaces/${interfaceId}/methods/`),
  get: (interfaceId, id) => api.get(`/interfaces/${interfaceId}/methods/${id}`),
};

export const graphApi = {
  get: (params) => api.get("/graph/", { params }),
};

export const searchApi = {
  search: (q) => api.get("/search/", { params: { q } }),
};
