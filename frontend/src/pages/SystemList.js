import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { systemsApi, searchApi } from "../api/client";

export default function SystemList() {
  const [systems, setSystems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    systemsApi.list().then((r) => {
      setSystems(r.data);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (query.length < 2) { setSearchResults(null); return; }
    const t = setTimeout(() => {
      searchApi.search(query).then((r) => setSearchResults(r.data));
    }, 300);
    return () => clearTimeout(t);
  }, [query]);

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", owner: "", tags: "", environments: "" });

  const handleCreate = async () => {
    const payload = {
      ...form,
      tags: form.tags ? form.tags.split(",").map(t => t.trim()).filter(Boolean) : [],
      environments: form.environments ? form.environments.split(",").map(e => e.trim()).filter(Boolean) : [],
    };
    const r = await systemsApi.create(payload);
    setSystems([...systems, { ...r.data, service_count: 0 }]);
    setForm({ name: "", description: "", owner: "", tags: "", environments: "" });
    setShowCreate(false);
  };

  if (loading) return <div className="loading">Загрузка...</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 className="page-title">Информационные системы</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Добавить ИС</button>
      </div>

      <input
        className="search-bar"
        placeholder="Поиск по ИС, сервисам, методам..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {searchResults && (
        <div className="card">
          <div className="card-title">Результаты поиска</div>
          {searchResults.length === 0 && <div className="card-meta">Ничего не найдено</div>}
          {searchResults.map((r) => (
            <div key={r.id} className="tree-item-header"
              style={{ borderBottom: "1px solid var(--border)", cursor: r.url ? "pointer" : "default" }}
              onClick={() => r.url && navigate(r.url)}>
              <span className={`badge badge-${r.type}`}>{r.type}</span>
              <span style={{ fontWeight: 500 }}>{r.label}</span>
              {r.path && <span className="card-meta">{r.path}</span>}
              {r.url && <span className="card-meta" style={{ marginLeft: "auto" }}>→</span>}
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="card">
          <div className="card-title">Новая ИС</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 400 }}>
            <input className="search-bar" style={{ margin: 0 }} placeholder="Название *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input className="search-bar" style={{ margin: 0 }} placeholder="Описание" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <input className="search-bar" style={{ margin: 0 }} placeholder="Владелец / команда" value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
            <input className="search-bar" style={{ margin: 0 }} placeholder="Теги (через запятую): billing, payments" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
            <input className="search-bar" style={{ margin: 0 }} placeholder="Окружения (через запятую): prod, staging, dev" value={form.environments} onChange={(e) => setForm({ ...form, environments: e.target.value })} />
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-primary" onClick={handleCreate} disabled={!form.name}>Создать</button>
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Отмена</button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {systems.map((sys) => (
          <div key={sys.id} className="card" style={{ cursor: "pointer" }} onClick={() => navigate(`/systems/${sys.id}`)}>
            <div className="card-title">{sys.name}</div>
            {sys.owner && <div className="card-meta">👤 {sys.owner}</div>}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              {sys.tags.map((t) => <span key={t} className="badge badge-tag">{t}</span>)}
            </div>
            <div style={{ marginTop: 12, fontSize: 13, color: "var(--text-muted)" }}>
              {sys.service_count} сервис{sys.service_count !== 1 ? "ов" : ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
