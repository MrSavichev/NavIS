import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import SystemList from "./pages/SystemList";
import SystemDetail from "./pages/SystemDetail";
import MethodDetail from "./pages/MethodDetail";
import GraphPage from "./pages/GraphPage";
import SourcesPage from "./pages/SourcesPage";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <Link to="/" className="logo">NavIS</Link>
          <span className="logo-sub">Навигатор Информационных Систем</span>
          <nav>
            <Link to="/">Каталог</Link>
            <Link to="/graph">Граф</Link>
          </nav>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<SystemList />} />
            <Route path="/systems/:systemId" element={<SystemDetail />} />
            <Route path="/methods/:interfaceId/:methodId" element={<MethodDetail />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/systems/:systemId/sources" element={<SourcesPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
