import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { methodsApi, interfacesDirectApi } from "../api/client";

export default function MethodDetail() {
  const { interfaceId, methodId } = useParams();
  const [method, setMethod] = useState(null);
  const [iface, setIface] = useState(null);
  const [sources, setSources] = useState([]);
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    methodsApi.get(interfaceId, methodId).then((r) => setMethod(r.data));
    interfacesDirectApi.get(interfaceId).then((r) => setIface(r.data));
    methodsApi.sources(methodId).then((r) => setSources(r.data));
  }, [interfaceId, methodId]);

  if (!method) return <div className="loading">Загрузка...</div>;

  const tabs = ["overview", "request", "response", "sources"];
  const tabLabels = { overview: "Обзор", request: "Request", response: "Response", sources: `Источники${sources.length ? ` (${sources.length})` : ""}` };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/">Каталог</Link>
        {iface && <> / <Link to={`/systems`}>{iface.name}</Link></>}
        {" / "}{method.path || method.name}
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
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div><b>Интерфейс:</b> {iface ? `${iface.name}${iface.version ? ` v${iface.version}` : ""}` : interfaceId}</div>
            {iface?.spec_ref && (
              <div><b>Спецификация:</b> <a href={iface.spec_ref} target="_blank" rel="noreferrer" style={{ color: "#2563eb" }}>{iface.spec_ref}</a></div>
            )}
            <div><b>Операция:</b> {method.name}</div>
            <div><b>Создан:</b> {new Date(method.created_at).toLocaleString("ru")}</div>
            <div><b>Обновлён:</b> {new Date(method.updated_at).toLocaleString("ru")}</div>
          </div>
        )}

        {tab === "request" && (
          <div>
            {method.request_schema ? (
              <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
                {JSON.stringify(method.request_schema, null, 2)}
              </pre>
            ) : (
              <div style={{ color: "#90a4ae", fontStyle: "italic" }}>
                Request body не предусмотрен — метод {method.http_method} обычно передаёт параметры в URL
              </div>
            )}
          </div>
        )}

        {tab === "response" && (
          <div>
            {method.response_schema ? (
              <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
                {JSON.stringify(method.response_schema, null, 2)}
              </pre>
            ) : (
              <div style={{ color: "#90a4ae", fontStyle: "italic" }}>Схема ответа не задана</div>
            )}
          </div>
        )}

        {tab === "sources" && (
          <div>
            {sources.length === 0 ? (
              <div style={{ color: "#90a4ae", fontStyle: "italic" }}>Источники не найдены</div>
            ) : (
              sources.map((s) => (
                <div key={s.id} style={{
                  borderLeft: "3px solid #2563eb", paddingLeft: 12, marginBottom: 12
                }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{
                      background: "#dbeafe", color: "#1e40af", borderRadius: 4,
                      padding: "1px 7px", fontSize: 12, fontWeight: 600
                    }}>{s.type.toUpperCase()}</span>
                    <a href={s.ref} target="_blank" rel="noreferrer"
                      style={{ color: "#2563eb", fontFamily: "monospace", fontSize: 13, wordBreak: "break-all" }}>
                      {s.ref}
                    </a>
                  </div>
                  <div style={{ color: "#94a3b8", fontSize: 12, marginTop: 4 }}>
                    Собран: {new Date(s.collected_at).toLocaleString("ru")}
                    {s.hash && <span style={{ marginLeft: 12, fontFamily: "monospace" }}>#{s.hash.slice(0, 8)}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
