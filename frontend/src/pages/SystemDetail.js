import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { systemsApi, servicesApi, interfacesApi, methodsApi } from "../api/client";

function MethodBadge({ method }) {
  return <span className={`badge badge-${(method || "").toLowerCase()}`}>{method || "–"}</span>;
}

function MethodRow({ interfaceId, method }) {
  return (
    <Link to={`/methods/${interfaceId}/${method.id}`} style={{ textDecoration: "none", color: "inherit" }}>
      <div className="tree-item-header" style={{ paddingLeft: 32 }}>
        <MethodBadge method={method.http_method} />
        <span style={{ fontFamily: "monospace", fontSize: 13 }}>{method.path || method.name}</span>
        {method.description && <span className="card-meta" style={{ marginLeft: "auto" }}>{method.description.slice(0, 60)}</span>}
      </div>
    </Link>
  );
}

function InterfaceBlock({ iface }) {
  const [methods, setMethods] = useState([]);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    methodsApi.list(iface.id).then((r) => setMethods(r.data));
  }, [iface.id]);

  return (
    <div className="tree-item" style={{ marginLeft: 16 }}>
      <div className="tree-item-header" onClick={() => setOpen(!open)}>
        <span>{open ? "▾" : "▸"}</span>
        <span className={`badge badge-${iface.type}`}>{iface.type.toUpperCase()}</span>
        <span style={{ fontWeight: 500 }}>{iface.name}</span>
        {iface.version && <span className="card-meta">v{iface.version}</span>}
        <span className="card-meta" style={{ marginLeft: "auto" }}>{methods.length} методов</span>
      </div>
      {open && (
        <div className="tree-item-body" style={{ padding: 0 }}>
          {methods.map((m) => <MethodRow key={m.id} interfaceId={iface.id} method={m} />)}
          {methods.length === 0 && <div style={{ padding: "8px 32px", color: "#90a4ae", fontSize: 13 }}>Нет методов</div>}
        </div>
      )}
    </div>
  );
}

function ServiceBlock({ systemId, service }) {
  const [interfaces, setInterfaces] = useState([]);
  const [open, setOpen] = useState(false);

  const load = () => {
    if (!open) interfacesApi.list(service.id).then((r) => setInterfaces(r.data));
    setOpen(!open);
  };

  return (
    <div className="tree-item">
      <div className="tree-item-header" onClick={load}>
        <span>{open ? "▾" : "▸"}</span>
        <span style={{ fontWeight: 500 }}>{service.name}</span>
        {service.description && <span className="card-meta">{service.description}</span>}
      </div>
      {open && (
        <div className="tree-item-body">
          {interfaces.map((iface) => <InterfaceBlock key={iface.id} iface={iface} />)}
          {interfaces.length === 0 && <div style={{ color: "#90a4ae", fontSize: 13 }}>Нет интерфейсов</div>}
        </div>
      )}
    </div>
  );
}

export default function SystemDetail() {
  const { systemId } = useParams();
  const [system, setSystem] = useState(null);
  const [services, setServices] = useState([]);

  useEffect(() => {
    systemsApi.get(systemId).then((r) => setSystem(r.data));
    servicesApi.list(systemId).then((r) => setServices(r.data));
  }, [systemId]);

  if (!system) return <div className="loading">Загрузка...</div>;

  return (
    <div>
      <div className="breadcrumb"><Link to="/">Каталог</Link> / {system.name}</div>
      <div className="card">
        <div className="card-title">{system.name}</div>
        {system.description && <div style={{ marginBottom: 8 }}>{system.description}</div>}
        {system.owner && <div className="card-meta">👤 {system.owner}</div>}
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          {system.tags.map((t) => <span key={t} className="badge" style={{ background: "#e8eaf6", color: "#3949ab" }}>{t}</span>)}
          {system.environments.map((e) => <span key={e} className="badge" style={{ background: "#e8f5e9", color: "#2e7d32" }}>{e}</span>)}
        </div>
      </div>

      <h2 style={{ marginBottom: 12, fontSize: 18 }}>Сервисы ({services.length})</h2>
      {services.map((svc) => (
        <ServiceBlock key={svc.id} systemId={systemId} service={svc} />
      ))}
      {services.length === 0 && <div className="card card-meta">Сервисы не добавлены</div>}
    </div>
  );
}
