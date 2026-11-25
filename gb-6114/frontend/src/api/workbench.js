import { request } from "./http.js";

export const api = {
  config: () => request("/workbench"),
  login: data => request("/auth/login", {method: "POST", data}),
  cases: () => request("/cases"),
  caseDetail: (id, signal) => request(`/cases/${id}`, {signal}),
  createCase: data => request("/cases", {method: "POST", data}),
  correctCase: (id, data) => request(`/cases/${id}`, {method: "PUT", data}),
  revisions: id => request(`/cases/${id}/revisions`),
  runs: () => request("/runs"),
  run: (id, signal) => request(`/runs/${id}`, {signal}),
  enqueue: (id, data) => request(`/cases/${id}/runs`, {method: "POST", data}),
  review: id => request(`/runs/${id}/review`),
  submitReview: (id, data) => request(`/runs/${id}/review`, {method: "POST", data}),
  export: id => request(`/runs/${id}/export`, {raw: true}),
  audit: () => request("/audit", {signal: AbortSignal.timeout(5000)}),
};
