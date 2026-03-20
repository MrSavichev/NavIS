import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { methodsApi, interfacesDirectApi, servicesDirectApi } from "../api/client";

function EditMethodModal({ method, interfaceId, onSave, onClose }) {
  const [form, setForm] = useState({
    name: method.name || "",
    description: method.description || "",
    path: method.path || "",
    http_method: method.http_method || "",
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSave = async () => {
    setSaving(true);
    try {
      const r = await methodsApi.update(interfaceId, method.id, form);
      onSave(r.data);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}>
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 12, padding: 24, width: "100%", maxWidth: 480 }}
        onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
          <h3 style={{ margin: 0, color: "#f1f5f9" }}>Редактировать метод</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#94a3b8", fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { key: "name", label: "Название операции" },
            { key: "http_method", label: "HTTP метод (GET, POST...)" },
            { key: "path", label: "Путь (/api/v1/resource)" },
            { key: "description", label: "Описание" },
          ].map(({ key, label }) => (
            <label key={key} style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13, color: "#94a3b8" }}>
              {label}
              <input value={form[key]} onChange={set(key)}
                style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#f1f5f9", padding: "8px 10px", fontSize: 14, outline: "none" }} />
            </label>
          ))}
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button onClick={handleSave} disabled={saving}
              style={{ background: "#16a34a", color: "#fff", border: "none", borderRadius: 6, padding: "7px 14px", cursor: "pointer", fontSize: 13 }}>
              {saving ? "Сохранение..." : "Сохранить"}
            </button>
            <button onClick={onClose}
              style={{ background: "#334155", color: "#fff", border: "none", borderRadius: 6, padding: "7px 14px", cursor: "pointer", fontSize: 13 }}>
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MethodDetail() {
  const { interfaceId, methodId } = useParams();
  const navigate = useNavigate();
  const [method, setMethod] = useState(null);
  const [iface, setIface] = useState(null);
  const [service, setService] = useState(null);
  const [sources, setSources] = useState([]);
  const [tab, setTab] = useState("overview");
  const [deleting, setDeleting] = useState(false);
  const [showEdit, setShowEdit] = useState(false);

  useEffect(() => {
    methodsApi.get(interfaceId, methodId).then((r) => setMethod(r.data));
    interfacesDirectApi.get(interfaceId).then((r) => {
      setIface(r.data);
      servicesDirectApi.get(r.data.service_id).then((sr) => setService(sr.data));
    });
    methodsApi.sources(methodId).then((r) => setSources(r.data));
  }, [interfaceId, methodId]);

  const handleDelete = async () => {
    if (!window.confirm(`Удалить метод ${method.path || method.name}?`)) return;
    setDeleting(true);
    try {
      await methodsApi.delete(interfaceId, methodId);
      navigate(service ? `/systems/${service.system_id}` : "/");
    } catch {
      setDeleting(false);
    }
  };

  if (!method) return <div className="loading">Загрузка...</div>;

  if (showEdit) return (
    <EditMethodModal method={method} interfaceId={interfaceId}
      onSave={(updated) => setMethod(updated)} onClose={() => setShowEdit(false)} />
  );

  const tabs = ["overview", "request", "response", "sources"];
  const tabLabels = {
    overview: "Обзор",
    request: "Request",
    response: "Response",
    sources: `Источники${sources.length ? ` (${sources.length})` : ""}`,
  };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/">Каталог</Link>
        {service && <> / <Link to={`/systems/${service.system_id}`}>{service.name}</Link></>}
        {iface && <> / {iface.name}{iface.version ? ` v${iface.version}` : ""}</>}
        {" / "}<span style={{ color: "#94a3b8" }}>{method.path || method.name}</span>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            {method.http_method && (
              <span className={`badge badge-${method.http_method.toLowerCase()}`} style={{ fontSize: 14, padding: "4px 10px" }}>
                {method.http_method}
              </span>
            )}
            <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 600 }}>
              {method.path || method.name}
            </span>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <button onClick={() => setShowEdit(true)}
              style={{ background: "#334155", color: "#fff", border: "none", borderRadius: 6, padding: "6px 12px", cursor: "pointer", fontSize: 13 }}>
              ✎ Редактировать
            </button>
            <button onClick={handleDelete} disabled={deleting}
              style={{ background: "#7f1d1d", color: "#fff", border: "none", borderRadius: 6, padding: "6px 12px", cursor: "pointer", fontSize: 13, whiteSpace: "nowrap" }}>
              {deleting ? "Удаление..." : "Удалить"}
            </button>
          </div>
        </div>

        {method.description && <div style={{ color: "#546e7a", margin: "8px 0" }}>{method.description}</div>}

        {/* Вкладки */}
        <div style={{ display: "flex", gap: 4, borderBottom: "2px solid var(--border)", marginBottom: 16, marginTop: 8, overflowX: "auto" }}>
          {tabs.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              style={{
                padding: "8px 16px", border: "none", background: "none", cursor: "pointer",
                fontWeight: tab === t ? 600 : 400, whiteSpace: "nowrap", color: "var(--text)",
                borderBottom: tab === t ? "2px solid var(--text)" : "2px solid transparent",
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
              <div><b>Спецификация:</b>{" "}
                <a href={iface.spec_ref} target="_blank" rel="noreferrer" style={{ color: "#2563eb", wordBreak: "break-all" }}>
                  {iface.spec_ref}
                </a>
              </div>
            )}
            <div><b>Операция:</b> {method.name}</div>
            <div><b>Создан:</b> {new Date(method.created_at).toLocaleString("ru")}</div>
            <div><b>Обновлён:</b> {new Date(method.updated_at).toLocaleString("ru")}</div>
          </div>
        )}

        {tab === "request" && (
          method.request_schema ? (
            <pre style={{ padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
              {JSON.stringify(method.request_schema, null, 2)}
            </pre>
          ) : (
            <div style={{ color: "#90a4ae", fontStyle: "italic" }}>
              Request body не предусмотрен{method.http_method === "GET" ? " — GET передаёт параметры в URL" : ""}
            </div>
          )
        )}

        {tab === "response" && (
          method.response_schema ? (
            <pre style={{ padding: 16, borderRadius: 6, overflow: "auto", fontSize: 13 }}>
              {JSON.stringify(method.response_schema, null, 2)}
            </pre>
          ) : (
            <div style={{ color: "#90a4ae", fontStyle: "italic" }}>Схема ответа не задана</div>
          )
        )}

        {tab === "sources" && (
          sources.length === 0 ? (
            <div style={{ color: "#90a4ae", fontStyle: "italic" }}>Источники не найдены</div>
          ) : (
            sources.map((s) => (
              <div key={s.id} style={{ borderLeft: "3px solid #2563eb", paddingLeft: 12, marginBottom: 12 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <span style={{ background: "#dbeafe", color: "#1e40af", borderRadius: 4, padding: "1px 7px", fontSize: 12, fontWeight: 600 }}>
                    {s.type.toUpperCase()}
                  </span>
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
          )
        )}
      </div>
    </div>
  );
}
