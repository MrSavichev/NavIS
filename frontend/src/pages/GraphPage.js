import React, { useEffect, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { graphApi, systemsApi } from "../api/client";

const NODE_COLORS = {
  system:    "#1a1a2e",
  service:   "#1565c0",
  interface: "#6a1b9a",
  method:    "#2e7d32",
};

const STYLESHEET = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "font-size": 11,
      "text-valign": "bottom",
      "text-halign": "center",
      "background-color": (ele) => NODE_COLORS[ele.data("type")] || "#607d8b",
      color: "#333",
      width: 36,
      height: 36,
      "text-margin-y": 4,
    },
  },
  {
    selector: "node[type='system']",
    style: { width: 52, height: 52, "font-size": 13, "font-weight": "bold" },
  },
  {
    selector: "edge",
    style: {
      width: 1.5,
      "line-color": "#b0bec5",
      "target-arrow-color": "#b0bec5",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(kind)",
      "font-size": 9,
      color: "#90a4ae",
    },
  },
];

export default function GraphPage() {
  const [elements, setElements] = useState([]);
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState("");
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    systemsApi.list().then((r) => setSystems(r.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { depth };
    if (selectedSystem) params.system_id = selectedSystem;
    graphApi.get(params).then((r) => {
      const { nodes, edges } = r.data;
      const cyNodes = nodes.map((n) => ({ data: { id: n.id, label: n.label, type: n.type } }));
      const cyEdges = edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, kind: e.kind } }));
      setElements([...cyNodes, ...cyEdges]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [selectedSystem, depth]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <h1 className="page-title" style={{ margin: 0 }}>Граф зависимостей</h1>
        <select className="search-bar" style={{ margin: 0, width: 220 }} value={selectedSystem} onChange={(e) => setSelectedSystem(e.target.value)}>
          <option value="">Все ИС</option>
          {systems.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select className="search-bar" style={{ margin: 0, width: 140 }} value={depth} onChange={(e) => setDepth(Number(e.target.value))}>
          <option value={1}>Глубина: 1</option>
          <option value={2}>Глубина: 2</option>
          <option value={3}>Глубина: 3</option>
        </select>
        <div style={{ display: "flex", gap: 8, fontSize: 13 }}>
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <span key={type} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 12, height: 12, borderRadius: "50%", background: color, display: "inline-block" }} />
              {type}
            </span>
          ))}
        </div>
      </div>

      {loading && <div className="loading">Загрузка графа...</div>}
      {!loading && elements.length === 0 && (
        <div className="card card-meta" style={{ textAlign: "center", padding: 40 }}>
          Нет данных. Добавьте ИС и сервисы в каталоге.
        </div>
      )}
      {!loading && elements.length > 0 && (
        <div className="graph-container">
          <CytoscapeComponent
            elements={elements}
            stylesheet={STYLESHEET}
            layout={{ name: "breadthfirst", directed: true, padding: 40, spacingFactor: 1.5 }}
            style={{ width: "100%", height: "100%" }}
            cy={(cy) => {
              cy.on("tap", "node", (e) => {
                const node = e.target;
                console.log("Node:", node.data());
              });
            }}
          />
        </div>
      )}
    </div>
  );
}
