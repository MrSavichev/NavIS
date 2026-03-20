import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { systemsApi, servicesApi, searchApi, edgesApi } from "../api/client";

const KINDS = ["calls", "depends", "uses", "consumes", "publishes", "extends", "serves"];

const SOURCE_BADGE = {
  manual: { label: "ручной", color: "#0284c7" },
  confluence: { label: "confluence", color: "#7c3aed" },
  auto: { label: "авто", color: "#475569" },
};

function Badge({ source }) {
  const s = SOURCE_BADGE[source] || { label: source, color: "#475569" };
  return (
    <span style={{
      fontSize: 11, padding: "2px 7px", borderRadius: 10,
      background: s.color + "33", color: s.color, border: `1px solid ${s.color}55`,
    }}>{s.label}</span>
  );
}

export default function MappingPage() {
  const { systemId } = useParams();
  const [system, setSystem] = useState(null);
  const [services, setServices] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);

  // Форма
  const [fromId, setFromId] = useState("");
  const [fromType, setFromType] = useState("service");
  const [kind, setKind] = useState("calls");
  const [toSearch, setToSearch] = useState("");
  const [toResults, setToResults] = useState([]);
  const [toSelected, setToSelected] = useState(null); // { id, type, label }
  const [externalName, setExternalName] = useState("");
  const [toMode, setToMode] = useState("search"); // "search" | "external"
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sysR, svcR, edgeR] = await Promise.all([
        systemsApi.get(systemId),
        servicesApi.list(systemId),
        edgesApi.listForSystem(systemId),
      ]);
      setSystem(sysR.data);
      setServices(svcR.data);
      setEdges(edgeR.data);
      if (svcR.data.length > 0 && !fromId) {
        setFromId(svcR.data[0].id);
      }
    } finally {
      setLoading(false);
    }
  }, [systemId]);

  useEffect(() => { load(); }, [load]);

  // Поиск TO через search API
  useEffect(() => {
    if (toMode !== "search" || toSearch.trim().length < 2) {
      setToResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const r = await searchApi.search(toSearch.trim());
        setToResults(r.data.results || []);
      } catch {
        setToResults([]);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [toSearch, toMode]);

  const handleCreate = async () => {
    setError(null);
    let toId, toType;
    if (toMode === "search") {
      if (!toSelected) { setError("Выберите целевой объект из поиска"); return; }
      toId = toSelected.id;
      toType = toSelected.type;
    } else {
      if (!externalName.trim()) { setError("Введите название внешнего сервиса"); return; }
      toId = `ext:${externalName.trim()}`;
      toType = "external";
    }
    if (!fromId) { setError("Выберите источник (FROM)"); return; }

    setSaving(true);
    try {
      await edgesApi.create({ from_id: fromId, from_type: fromType, to_id: toId, to_type: toType, kind });
      setToSelected(null);
      setToSearch("");
      setExternalName("");
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (edgeId) => {
    if (!window.confirm("Удалить связь?")) return;
    await edgesApi.delete(edgeId);
    await load();
  };

  if (loading) return <div style={{ padding: 32, color: "#94a3b8" }}>Загрузка...</div>;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px" }}>
      {/* Хлебные крошки */}
      <div style={{ fontSize: 13, color: "#64748b", marginBottom: 16 }}>
        <Link to="/" style={{ color: "#64748b" }}>Каталог</Link>
        {" / "}
        <Link to={`/systems/${systemId}`} style={{ color: "#64748b" }}>{system?.name}</Link>
        {" / Маппинг зависимостей"}
      </div>

      <h2 style={{ margin: "0 0 24px", color: "#f1f5f9" }}>
        Маппинг зависимостей — {system?.name}
      </h2>

      {/* ─── Форма создания ───────────────────────────────────────────────── */}
      <div style={{
        background: "#1e293b", border: "1px solid #334155", borderRadius: 12,
        padding: 20, marginBottom: 32,
      }}>
        <h3 style={{ margin: "0 0 16px", color: "#f1f5f9", fontSize: 15 }}>Добавить связь</h3>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
          {/* FROM */}
          <div style={{ flex: "1 1 200px" }}>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>FROM (сервис)</label>
            <select
              value={fromId}
              onChange={(e) => setFromId(e.target.value)}
              style={inputStyle}
            >
              {services.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          {/* KIND */}
          <div style={{ flex: "0 1 160px" }}>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>Тип связи</label>
            <select value={kind} onChange={(e) => setKind(e.target.value)} style={inputStyle}>
              {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>

          {/* TO mode toggle */}
          <div style={{ flex: "1 1 280px" }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
              <label style={{ fontSize: 12, color: "#94a3b8" }}>TO</label>
              <button
                onClick={() => { setToMode("search"); setToSelected(null); setExternalName(""); }}
                style={{ ...toggleStyle, background: toMode === "search" ? "#1d4ed8" : "transparent" }}
              >из каталога</button>
              <button
                onClick={() => { setToMode("external"); setToSelected(null); setToSearch(""); }}
                style={{ ...toggleStyle, background: toMode === "external" ? "#92400e" : "transparent" }}
              >внешний</button>
            </div>

            {toMode === "search" ? (
              <div style={{ position: "relative" }}>
                <input
                  value={toSelected ? toSelected.label : toSearch}
                  onChange={(e) => { setToSearch(e.target.value); setToSelected(null); }}
                  placeholder="Поиск сервиса, интерфейса, метода..."
                  style={inputStyle}
                />
                {toResults.length > 0 && !toSelected && (
                  <div style={{
                    position: "absolute", top: "100%", left: 0, right: 0, zIndex: 100,
                    background: "#0f172a", border: "1px solid #334155", borderRadius: 8,
                    maxHeight: 200, overflowY: "auto",
                  }}>
                    {toResults.map((r) => (
                      <div
                        key={r.id}
                        onClick={() => { setToSelected(r); setToSearch(""); setToResults([]); }}
                        style={{
                          padding: "8px 12px", cursor: "pointer", borderBottom: "1px solid #1e293b",
                          color: "#e2e8f0", fontSize: 13,
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "#1e293b"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        <span style={{ color: "#64748b", marginRight: 6, fontSize: 11 }}>[{r.type}]</span>
                        {r.label}
                        {r.description && <span style={{ color: "#64748b", marginLeft: 8, fontSize: 11 }}>{r.description.slice(0, 40)}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <input
                value={externalName}
                onChange={(e) => setExternalName(e.target.value)}
                placeholder="Название внешнего сервиса"
                style={inputStyle}
              />
            )}
          </div>

          {/* Кнопка */}
          <button
            onClick={handleCreate}
            disabled={saving}
            style={{
              flex: "0 0 auto", padding: "8px 20px", borderRadius: 8,
              background: "#1d4ed8", color: "#fff", border: "none",
              cursor: saving ? "not-allowed" : "pointer", opacity: saving ? 0.7 : 1,
              height: 36, alignSelf: "flex-end",
            }}
          >
            {saving ? "..." : "+ Добавить"}
          </button>
        </div>

        {error && <div style={{ marginTop: 10, color: "#f87171", fontSize: 13 }}>{error}</div>}
      </div>

      {/* ─── Список рёбер ─────────────────────────────────────────────────── */}
      <h3 style={{ color: "#f1f5f9", margin: "0 0 12px", fontSize: 15 }}>
        Связи ({edges.length})
      </h3>

      {edges.length === 0 ? (
        <div style={{ color: "#64748b", fontSize: 14 }}>Связи не найдены</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {edges.map((e) => (
            <div key={e.id} style={{
              display: "flex", alignItems: "center", gap: 12,
              background: "#1e293b", border: "1px solid #334155", borderRadius: 10,
              padding: "10px 14px",
            }}>
              <span style={{ color: "#e2e8f0", fontSize: 14, flex: 1 }}>
                <span style={{ color: "#93c5fd" }}>{e.from_label || e.from_id}</span>
                <span style={{ color: "#475569", margin: "0 8px" }}>—{e.kind}→</span>
                <span style={{ color: e.to_type === "external" ? "#fbbf24" : "#86efac" }}>
                  {e.to_label || e.to_id}
                </span>
              </span>
              <span style={{ color: "#64748b", fontSize: 11 }}>[{e.from_type}→{e.to_type}]</span>
              <Badge source={e.source} />
              {e.source === "manual" && (
                <button
                  onClick={() => handleDelete(e.id)}
                  style={{
                    background: "none", border: "1px solid #475569", borderRadius: 6,
                    color: "#94a3b8", cursor: "pointer", padding: "2px 10px", fontSize: 12,
                  }}
                >Удалить</button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const inputStyle = {
  width: "100%", padding: "7px 10px", borderRadius: 8,
  background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0",
  fontSize: 14, boxSizing: "border-box",
};

const toggleStyle = {
  fontSize: 11, padding: "2px 8px", borderRadius: 10,
  border: "1px solid #334155", color: "#e2e8f0", cursor: "pointer",
};
