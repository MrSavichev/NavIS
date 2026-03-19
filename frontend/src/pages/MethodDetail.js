import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { methodsApi } from "../api/client";

export default function MethodDetail() {
  const { interfaceId, methodId } = useParams();
  const [method, setMethod] = useState(null);
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    methodsApi.get(interfaceId, methodId).then((r) => setMethod(r.data));
  }, [interfaceId, methodId]);

  if (!method) return <div className="loading">Загрузка...</div>;

  const tabs = ["overview", "request", "response", "sources"];
  const tabLabels = { overview: "Обзор", request: "Request", response: "Response", sources: "Источники" };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/">Каталог</Link> / метод
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          {method.http_method && (
            <span className={`badge badge-${method.http_method.toLowerCase()}`} style={{ fontSize: 14, padding: "4px 10px" }}>
              {method.http_method}
            </span>
          )}
          <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 600 }}>
            {method.path || method.name}
          </span>
        </div>
        {method.description && <div style={{ color: "#546e7a", marginBottom: 8 }}>{method.description}</div>}

        {/* Вкладки */}
        <div style={{ display: "flex", gap: 4, borderBottom: "2px solid #e0e0e0", marginBottom: 16 }}>
          {tabs.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              style={{
                padding: "8px 16px", border: "none", background: "none", cursor: "pointer",
                fontWeight: tab === t ? 600 : 400,
                borderBottom: tab === t ? "2px solid #1a1a2e" : "2px solid transparent",
                marginBottom: -2,
              }}>
              {tabLabels[t]}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div>
            <div><b>Интерфейс:</b> {interfaceId}</div>
            <div><b>Создан:</b> {new Date(method.created_at).toLocaleString("ru")}</div>
            <div><b>Обновлён:</b> {new Date(method.updated_at).toLocaleString("ru")}</div>
          </div>
        )}

        {tab === "request" && (
          <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
            {method.request_schema ? JSON.stringify(method.request_schema, null, 2) : "Схема не задана"}
          </pre>
        )}

        {tab === "response" && (
          <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
            {method.response_schema ? JSON.stringify(method.response_schema, null, 2) : "Схема не задана"}
          </pre>
        )}

        {tab === "sources" && (
          <div className="card-meta">Источники появятся после импорта из Confluence / Git</div>
        )}
      </div>
    </div>
  );
}
