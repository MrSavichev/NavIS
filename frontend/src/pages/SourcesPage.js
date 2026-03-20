import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { ingestApi, systemsApi } from "../api/client";

const STATUS_COLOR = {
  pending: "#6b7280",
  running: "#2563eb",
  done: "#16a34a",
  error: "#dc2626",
};

function JobRow({ job, onRefresh }) {
  const [expanded, setExpanded] = useState(false);
  const color = STATUS_COLOR[job.status] || "#6b7280";

  return (
    <div style={{ borderLeft: `3px solid ${color}`, paddingLeft: 10, marginBottom: 8 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <span style={{ color, fontWeight: 600, minWidth: 70 }}>{job.status}</span>
        <span style={{ color: "#9ca3af", fontSize: 13 }}>
          {new Date(job.created_at).toLocaleString("ru-RU")}
        </span>
        {job.status === "done" && (
          <span style={{ fontSize: 13 }}>
            {job.files_found} файлов, {job.methods_created} методов
          </span>
        )}
        {job.error && (
          <span style={{ color: "#dc2626", fontSize: 13 }}>{job.error}</span>
        )}
        {job.status === "running" && (
          <button onClick={onRefresh} style={btnSmStyle}>↻ Обновить</button>
        )}
        {job.log && (
          <button onClick={() => setExpanded(!expanded)} style={btnSmStyle}>
            {expanded ? "Скрыть лог" : "Лог"}
          </button>
        )}
      </div>
      {expanded && job.log && (
        <pre style={{
          background: "#0f172a", color: "#e2e8f0", padding: 10, borderRadius: 6,
          fontSize: 12, marginTop: 6, overflowX: "auto", maxHeight: 300, overflowY: "auto"
        }}>
          {job.log}
        </pre>
      )}
    </div>
  );
}

function SourceCard({ source, systemId, onDelete }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const r = await ingestApi.listJobs(source.id);
      setJobs(r.data);
    } finally {
      setLoading(false);
    }
  }, [source.id]);

  // Автополлинг пока есть running джоб
  useEffect(() => {
    const hasRunning = jobs.some((j) => j.status === "running" || j.status === "pending");
    if (!hasRunning) return;
    const timer = setInterval(loadJobs, 3000);
    return () => clearInterval(timer);
  }, [jobs, loadJobs]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await ingestApi.runSource(systemId, source.id);
      await loadJobs();
      setExpanded(true);
    } catch (e) {
      alert("Ошибка запуска: " + (e.response?.data?.detail || e.message));
    } finally {
      setRunning(false);
    }
  };

  const handleExpand = async () => {
    if (!expanded && jobs.length === 0) await loadJobs();
    setExpanded(!expanded);
  };

  const lastJob = jobs[0];
  const lastStatus = lastJob?.status;
  const statusColor = STATUS_COLOR[lastStatus] || "#374151";

  return (
    <div style={{
      background: "#1e293b", border: "1px solid #334155",
      borderRadius: 10, padding: 16, marginBottom: 14, color: "#e2e8f0",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>{source.name}</div>
          <div style={{ color: "#94a3b8", fontSize: 13, marginTop: 2 }}>
            <span style={{
              background: "#0f172a", padding: "1px 7px", borderRadius: 4,
              marginRight: 6, fontSize: 12
            }}>{source.provider || "github"}</span>
            {source.repo_url}
            {source.branch && <span style={{ color: "#64748b" }}> @ {source.branch}</span>}
            {source.path_filter && <span style={{ color: "#64748b" }}> [{source.path_filter}]</span>}
          </div>
          {lastStatus && (
            <div style={{ marginTop: 4, fontSize: 12, color: statusColor }}>
              Последний запуск: {lastStatus}
              {lastJob?.finished_at && ` (${new Date(lastJob.finished_at).toLocaleString("ru-RU")})`}
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
          <button onClick={handleRun} disabled={running} style={btnStyle("#2563eb")}>
            {running ? "Запуск..." : "▶ Запустить"}
          </button>
          <button onClick={handleExpand} style={btnStyle("#334155")}>
            {expanded ? "Скрыть" : "История"}
          </button>
          <button onClick={() => onDelete(source.id)} style={btnStyle("#7f1d1d")}>✕</button>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: 12 }}>
          {loading ? (
            <div style={{ color: "#64748b", fontSize: 13 }}>Загрузка...</div>
          ) : jobs.length === 0 ? (
            <div style={{ color: "#64748b", fontSize: 13 }}>Запусков не было</div>
          ) : (
            jobs.map((j) => <JobRow key={j.id} job={j} onRefresh={loadJobs} />)
          )}
        </div>
      )}
    </div>
  );
}

const EMPTY_FORM = {
  name: "", type: "git", repo_url: "", branch: "main",
  path_filter: "", token: "", provider: "github",
  confluence_url: "", space_key: "",
};

export default function SourcesPage() {
  const { systemId } = useParams();
  const [system, setSystem] = useState(null);
  const [sources, setSources] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    systemsApi.get(systemId).then((r) => setSystem(r.data));
    loadSources();
  }, [systemId]);

  const loadSources = async () => {
    const r = await ingestApi.listSources(systemId);
    setSources(r.data);
  };

  const handleCreate = async () => {
    const isGit = form.type === "git";
    const isConfluence = form.type === "confluence";
    if (!form.name) return;
    if (isGit && !form.repo_url) return;
    if (isConfluence && (!form.confluence_url || !form.space_key || !form.token)) return;
    setSaving(true);
    try {
      await ingestApi.createSource(systemId, form);
      setForm(EMPTY_FORM);
      setShowForm(false);
      await loadSources();
    } catch (e) {
      alert("Ошибка: " + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (sourceId) => {
    if (!window.confirm("Удалить источник?")) return;
    await ingestApi.deleteSource(systemId, sourceId);
    setSources((s) => s.filter((x) => x.id !== sourceId));
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <div style={{ padding: "24px 32px", maxWidth: 860, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 10 }}>
        <div>
          <div style={{ color: "#64748b", fontSize: 13 }}>
            <a href="/" style={{ color: "#64748b" }}>Системы</a>
            {" / "}
            <a href={`/systems/${systemId}`} style={{ color: "#64748b" }}>
              {system?.name || "..."}
            </a>
          </div>
          <h2 style={{ margin: "4px 0 0" }}>Источники данных</h2>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={btnStyle("#2563eb")}>
          {showForm ? "Отмена" : "+ Добавить источник"}
        </button>
      </div>

      {showForm && (
        <div style={{
          background: "#1e293b", border: "1px solid #3b82f6", borderRadius: 10,
          padding: 20, marginBottom: 24
        }}>
          <h3 style={{ margin: "0 0 16px", color: "#f1f5f9" }}>Новый источник</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
            <label style={labelStyle}>
              Название *
              <input value={form.name} onChange={set("name")} style={inputStyle} placeholder="My Service API" />
            </label>
            <label style={labelStyle}>
              Тип источника
              <select value={form.type} onChange={set("type")} style={inputStyle}>
                <option value="git">Git репозиторий</option>
                <option value="confluence">Confluence (draw.io)</option>
              </select>
            </label>

            {form.type === "git" && (<>
              <label style={labelStyle}>
                Провайдер
                <select value={form.provider} onChange={set("provider")} style={inputStyle}>
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                  <option value="bitbucket">Bitbucket Server</option>
                </select>
              </label>
              <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
                URL репозитория *
                <input value={form.repo_url} onChange={set("repo_url")} style={inputStyle}
                  placeholder={
                    form.provider === "bitbucket"
                      ? "https://bitbucket.company.com/projects/KEY/repos/my-repo"
                      : form.provider === "gitlab"
                      ? "https://gitlab.company.com/org/repo"
                      : "https://github.com/org/repo"
                  } />
              </label>
              <label style={labelStyle}>
                Ветка
                <input value={form.branch} onChange={set("branch")} style={inputStyle} placeholder="main" />
              </label>
              <label style={labelStyle}>
                Фильтр путей (glob)
                <input value={form.path_filter} onChange={set("path_filter")} style={inputStyle}
                  placeholder="api/**/*.yaml" />
              </label>
              <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
                Токен доступа (опционально)
                <input value={form.token} onChange={set("token")} style={inputStyle}
                  type="password" placeholder="ghp_..." />
              </label>
            </>)}

            {form.type === "confluence" && (<>
              <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
                URL Confluence *
                <input value={form.confluence_url} onChange={set("confluence_url")} style={inputStyle}
                  placeholder="https://confluence.company.com" />
              </label>
              <label style={labelStyle}>
                Space Key *
                <input value={form.space_key} onChange={set("space_key")} style={inputStyle}
                  placeholder="MYSPACE" />
              </label>
              <label style={labelStyle}>
                Фильтр страниц (title, опционально)
                <input value={form.path_filter} onChange={set("path_filter")} style={inputStyle}
                  placeholder="Схема сервисов" />
              </label>
              <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
                Basic Auth (username:password) *
                <input value={form.token} onChange={set("token")} style={inputStyle}
                  type="password" placeholder="admin:mypassword" />
              </label>
            </>)}
          </div>
          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button onClick={handleCreate} disabled={saving || !form.name || (form.type === "git" && !form.repo_url) || (form.type === "confluence" && (!form.confluence_url || !form.space_key || !form.token))}
              style={btnStyle("#16a34a")}>
              {saving ? "Сохранение..." : "Создать"}
            </button>
            <button onClick={() => setShowForm(false)} style={btnStyle("#334155")}>Отмена</button>
          </div>
        </div>
      )}

      {sources.length > 0 && (
        <div style={{ fontSize: 13, color: "#64748b", marginBottom: 12, borderTop: "1px solid #334155", paddingTop: 12 }}>
          Источники ({sources.length})
        </div>
      )}

      {sources.length === 0 ? (
        <div style={{ color: "#64748b", textAlign: "center", padding: 48 }}>
          Нет источников. Добавьте Git-репозиторий для автоматического сбора API.
        </div>
      ) : (
        sources.map((s) => (
          <SourceCard key={s.id} source={s} systemId={systemId} onDelete={handleDelete} />
        ))
      )}
    </div>
  );
}

function btnStyle(bg) {
  return {
    background: bg, color: "#fff", border: "none", borderRadius: 6,
    padding: "7px 14px", cursor: "pointer", fontSize: 13, fontWeight: 500,
  };
}

const btnSmStyle = {
  background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 4,
  padding: "2px 8px", cursor: "pointer", fontSize: 12,
};

const labelStyle = {
  display: "flex", flexDirection: "column", gap: 4, fontSize: 13, color: "#94a3b8",
};

const inputStyle = {
  background: "#0f172a", border: "1px solid #334155", borderRadius: 6,
  color: "#f1f5f9", padding: "8px 10px", fontSize: 14, outline: "none",
};
