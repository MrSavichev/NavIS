import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { systemsApi, servicesApi, interfacesApi, methodsApi } from "../api/client";

// ─── Модальное окно ────────────────────────────────────────────────────────────

function Modal({ title, onClose, children }) {
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
    }} onClick={onClose}>
      <div style={{
        background: "#1e293b", border: "1px solid #334155", borderRadius: 12,
        padding: 24, width: "100%", maxWidth: 480, maxHeight: "90vh", overflowY: "auto",
      }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, color: "#f1f5f9" }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#94a3b8", fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Редактирование системы ────────────────────────────────────────────────────

function EditSystemModal({ system, onSave, onClose }) {
  const [form, setForm] = useState({
    name: system.name,
    description: system.description || "",
    owner: system.owner || "",
    tags: (system.tags || []).join(", "),
    environments: (system.environments || []).join(", "),
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSave = async () => {
    setSaving(true);
    const payload = {
      ...form,
      tags: form.tags ? form.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
      environments: form.environments ? form.environments.split(",").map((e) => e.trim()).filter(Boolean) : [],
    };
    try {
      const r = await systemsApi.update(system.id, payload);
      onSave(r.data);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="Редактировать систему" onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {[
          { key: "name", label: "Название *", placeholder: "My System" },
          { key: "description", label: "Описание", placeholder: "" },
          { key: "owner", label: "Владелец", placeholder: "team-name" },
          { key: "tags", label: "Теги (через запятую)", placeholder: "billing, payments" },
          { key: "environments", label: "Окружения (через запятую)", placeholder: "prod, staging" },
        ].map(({ key, label, placeholder }) => (
          <label key={key} style={labelStyle}>
            {label}
            <input value={form[key]} onChange={set(key)} placeholder={placeholder} style={inputStyle} />
          </label>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button onClick={handleSave} disabled={saving || !form.name} style={btnStyle("#16a34a")}>
            {saving ? "Сохранение..." : "Сохранить"}
          </button>
          <button onClick={onClose} style={btnStyle("#334155")}>Отмена</button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Метод в дереве ────────────────────────────────────────────────────────────

function MethodRow({ interfaceId, serviceSystemId, method, onDeleted }) {
  const [confirming, setConfirming] = useState(false);

  const handleDelete = async (e) => {
    e.preventDefault();
    if (!confirming) { setConfirming(true); return; }
    await methodsApi.delete(interfaceId, method.id);
    onDeleted(method.id);
  };

  return (
    <div style={{ display: "flex", alignItems: "center", paddingLeft: 32 }} className="tree-item-header">
      <Link to={`/methods/${interfaceId}/${method.id}`}
        style={{ textDecoration: "none", color: "inherit", display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
        <span className={`badge badge-${(method.http_method || "").toLowerCase()}`}>{method.http_method || "–"}</span>
        <span style={{ fontFamily: "monospace", fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {method.path || method.name}
        </span>
        {method.description && (
          <span className="card-meta" style={{ marginLeft: "auto", flexShrink: 0 }}>
            {method.description.slice(0, 50)}
          </span>
        )}
      </Link>
      <button onClick={handleDelete}
        style={{ ...iconBtn, color: confirming ? "#ef4444" : "#475569", marginLeft: 8 }}
        title={confirming ? "Нажмите ещё раз для подтверждения" : "Удалить метод"}>
        {confirming ? "удалить?" : "×"}
      </button>
    </div>
  );
}

// ─── Интерфейс в дереве ────────────────────────────────────────────────────────

function InterfaceBlock({ iface, systemId, onDeleted }) {
  const [methods, setMethods] = useState([]);
  const [open, setOpen] = useState(true);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    methodsApi.list(iface.id).then((r) => setMethods(r.data));
  }, [iface.id]);

  const handleDeleteIface = async (e) => {
    e.stopPropagation();
    if (!confirming) { setConfirming(true); return; }
    await interfacesApi.delete(iface.service_id, iface.id);
    onDeleted(iface.id);
  };

  return (
    <div className="tree-item" style={{ marginLeft: 16 }}>
      <div className="tree-item-header" onClick={() => { setConfirming(false); setOpen(!open); }}>
        <span>{open ? "▾" : "▸"}</span>
        <span className={`badge badge-${iface.type}`}>{iface.type.toUpperCase()}</span>
        <span style={{ fontWeight: 500 }}>{iface.name}</span>
        {iface.version && <span className="card-meta">v{iface.version}</span>}
        <span className="card-meta" style={{ marginLeft: "auto" }}>{methods.length} методов</span>
        <button onClick={handleDeleteIface}
          style={{ ...iconBtn, color: confirming ? "#ef4444" : "#475569" }}
          title={confirming ? "Нажмите ещё раз" : "Удалить интерфейс"}>
          {confirming ? "удалить?" : "×"}
        </button>
      </div>
      {open && (
        <div className="tree-item-body" style={{ padding: 0 }}>
          {methods.map((m) => (
            <MethodRow key={m.id} interfaceId={iface.id} method={m}
              onDeleted={(id) => setMethods((ms) => ms.filter((x) => x.id !== id))} />
          ))}
          {methods.length === 0 && <div style={{ padding: "8px 32px", color: "#90a4ae", fontSize: 13 }}>Нет методов</div>}
        </div>
      )}
    </div>
  );
}

// ─── Сервис в дереве ───────────────────────────────────────────────────────────

function ServiceBlock({ systemId, service, onDeleted }) {
  const [interfaces, setInterfaces] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(service.name);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const load = () => {
    if (!open) interfacesApi.list(service.id).then((r) => setInterfaces(r.data));
    setOpen(!open);
  };

  const handleRename = async (e) => {
    if (e.key === "Escape") { setEditing(false); setName(service.name); return; }
    if (e.key !== "Enter") return;
    await servicesApi.update(systemId, service.id, { name });
    setEditing(false);
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!confirmingDelete) { setConfirmingDelete(true); return; }
    await servicesApi.delete(systemId, service.id);
    onDeleted(service.id);
  };

  return (
    <div className="tree-item">
      <div className="tree-item-header" onClick={() => { if (!editing) load(); }}>
        <span>{open ? "▾" : "▸"}</span>
        {editing ? (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={handleRename}
            onBlur={() => { setEditing(false); setName(service.name); }}
            autoFocus
            onClick={(e) => e.stopPropagation()}
            style={{ ...inputStyle, padding: "2px 8px", fontSize: 14, width: 220 }}
          />
        ) : (
          <span style={{ fontWeight: 500 }}>{name}</span>
        )}
        {service.description && !editing && <span className="card-meta">{service.description}</span>}
        <div style={{ marginLeft: "auto", display: "flex", gap: 4 }} onClick={(e) => e.stopPropagation()}>
          <button onClick={() => setEditing(true)} style={iconBtn} title="Переименовать">✎</button>
          <button onClick={handleDelete}
            style={{ ...iconBtn, color: confirmingDelete ? "#ef4444" : "#475569" }}
            title={confirmingDelete ? "Нажмите ещё раз" : "Удалить сервис"}>
            {confirmingDelete ? "удалить?" : "×"}
          </button>
        </div>
      </div>
      {open && (
        <div className="tree-item-body">
          {interfaces.map((iface) => (
            <InterfaceBlock key={iface.id} iface={iface} systemId={systemId}
              onDeleted={(id) => setInterfaces((is) => is.filter((x) => x.id !== id))} />
          ))}
          {interfaces.length === 0 && <div style={{ color: "#90a4ae", fontSize: 13 }}>Нет интерфейсов</div>}
        </div>
      )}
    </div>
  );
}

// ─── Страница системы ──────────────────────────────────────────────────────────

export default function SystemDetail() {
  const { systemId } = useParams();
  const navigate = useNavigate();
  const [system, setSystem] = useState(null);
  const [services, setServices] = useState([]);
  const [showEdit, setShowEdit] = useState(false);

  useEffect(() => {
    systemsApi.get(systemId).then((r) => setSystem(r.data));
    servicesApi.list(systemId).then((r) => setServices(r.data));
  }, [systemId]);

  const handleDelete = async () => {
    if (!window.confirm(`Удалить систему "${system.name}" со всеми сервисами и методами?`)) return;
    await systemsApi.delete(system.id);
    navigate("/");
  };

  if (!system) return <div className="loading">Загрузка...</div>;

  return (
    <div>
      {showEdit && (
        <EditSystemModal system={system} onSave={(updated) => setSystem(updated)} onClose={() => setShowEdit(false)} />
      )}

      <div className="breadcrumb"><Link to="/">Каталог</Link> / {system.name}</div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="card-title">{system.name}</div>
            {system.description && <div style={{ marginBottom: 8 }}>{system.description}</div>}
            {system.owner && <div className="card-meta">👤 {system.owner}</div>}
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              {system.tags.map((t) => <span key={t} className="badge" style={{ background: "#e8eaf6", color: "#3949ab" }}>{t}</span>)}
              {system.environments.map((e) => <span key={e} className="badge" style={{ background: "#e8f5e9", color: "#2e7d32" }}>{e}</span>)}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", flexShrink: 0 }}>
            <button onClick={() => setShowEdit(true)} style={btnStyle("#334155")}>✎ Редактировать</button>
            <Link to={`/systems/${systemId}/sources`} style={{ ...btnStyle("#1e40af"), textDecoration: "none" }}>
              ⚡ Источники
            </Link>
            <button onClick={handleDelete} style={btnStyle("#7f1d1d")}>Удалить</button>
          </div>
        </div>
      </div>

      <h2 style={{ marginBottom: 12, fontSize: 18 }}>Сервисы ({services.length})</h2>
      {services.map((svc) => (
        <ServiceBlock key={svc.id} systemId={systemId} service={svc}
          onDeleted={(id) => setServices((s) => s.filter((x) => x.id !== id))} />
      ))}
      {services.length === 0 && <div className="card card-meta">Сервисы не добавлены</div>}
    </div>
  );
}

// ─── Стили ─────────────────────────────────────────────────────────────────────

function btnStyle(bg) {
  return {
    background: bg, color: "#fff", border: "none", borderRadius: 6,
    padding: "7px 14px", cursor: "pointer", fontSize: 13, fontWeight: 500,
  };
}

const iconBtn = {
  background: "none", border: "none", cursor: "pointer",
  fontSize: 16, padding: "0 4px", color: "#475569",
};

const labelStyle = {
  display: "flex", flexDirection: "column", gap: 4, fontSize: 13, color: "#94a3b8",
};

const inputStyle = {
  background: "#0f172a", border: "1px solid #334155", borderRadius: 6,
  color: "#f1f5f9", padding: "8px 10px", fontSize: 14, outline: "none",
};
