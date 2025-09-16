// frontend/src/pages/ETest.jsx
import React, { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function ETest() {
  const [jsonPath, setJsonPath] = useState("/etestnew/SPECS/usr/aquq/etest_app/output.json");
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState({}); // deviceName -> boolean
  const [mods, setMods] = useState([]); // [{name, devices:[]}]
  const [filter, setFilter] = useState("");

  const selectedList = useMemo(() => Object.keys(selected).filter(k => selected[k]), [selected]);
  const filteredMods = useMemo(() => {
    const f = filter.trim().toLowerCase();
    if (!f) return mods;
    return mods.filter(m => m.name.toLowerCase().includes(f));
  }, [mods, filter]);

  async function fetchDevices() {
    setLoading(true);
    setError("");
    try {
      const url = new URL(`${API_BASE}/api/etest/devices`);
      if (jsonPath) url.searchParams.set("json_path", jsonPath);
      const res = await fetch(url.toString());
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Failed to load devices");
      setDevices(data.devices || []);
      // Clear previous selections/result when path changes
      setSelected({});
      setMods([]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchMods() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/etest/device-mods`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ devices: selectedList, json_path: jsonPath })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Failed to load mods");
      setMods(data.mods || []);
    } catch (e) {
      setError(e.message);
      setMods([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // initial load on mount
    fetchDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleAll(on) {
    const next = {};
    devices.forEach(d => { next[d.name] = !!on; });
    setSelected(next);
  }

  function downloadCSV() {
    if (!mods.length) return;
    const lines = ["mod,devices"];
    mods.forEach(m => {
      const devs = (m.devices || []).join(";");
      // quote if needed
      const mod = /[,\s"]/.test(m.name) ? `"${m.name.replace(/"/g, '""')}"` : m.name;
      const devq = devs.includes(",") ? `"${devs.replace(/"/g, '""')}"` : devs;
      lines.push(`${mod},${devq}`);
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "etest_mods.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{ padding: 16, maxWidth: 1200, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>eTest Program Generator</h1>
      <p style={{ marginTop: -8, color: "#666" }}>
        Load devices from the JSON, select some, then aggregate and view all related <code>mod</code>s.
      </p>

      <section style={{ marginTop: 16 }}>
        <label style={{ fontWeight: 600 }}>JSON path on server (NFS): </label>
        <input
          value={jsonPath}
          onChange={e => setJsonPath(e.target.value)}
          style={{ width: "100%", maxWidth: 800, padding: 8, marginTop: 4 }}
          placeholder="/etestnew/SPECS/usr/aquq/etest_app/output.json"
        />
        <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={fetchDevices} disabled={loading}>Reload devices</button>
          <button onClick={() => toggleAll(true)} disabled={!devices.length}>Select all</button>
          <button onClick={() => toggleAll(false)} disabled={!devices.length}>Clear</button>
        </div>
        {error ? <div style={{ color: "crimson", marginTop: 8 }}>Error: {error}</div> : null}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Step 1 — Devices</h2>
        {loading && <div>Loading…</div>}
        {!loading && !devices.length && <div>No devices loaded.</div>}
        {!!devices.length && (
          <div style={{ maxHeight: 280, overflow: "auto", border: "1px solid #ddd" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #eee" }}>Select</th>
                  <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #eee" }}>Device</th>
                  <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #eee" }}>PRB</th>
                </tr>
              </thead>
              <tbody>
                {devices.map(d => (
                  <tr key={d.name}>
                    <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5" }}>
                      <input
                        type="checkbox"
                        checked={!!selected[d.name]}
                        onChange={(e) => setSelected(prev => ({ ...prev, [d.name]: e.target.checked }))}
                      />
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5", fontFamily: "monospace" }}>{d.name}</td>
                    <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5" }}>{d.prb ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <button onClick={fetchMods} disabled={!selectedList.length || loading}>
            OK — Aggregate Mods ({selectedList.length} device{selectedList.length===1?"":"s"})
          </button>
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Step 2 — Mods (unique)</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Filter mods…"
            style={{ padding: 8, minWidth: 240 }}
          />
          <button onClick={downloadCSV} disabled={!mods.length}>Download CSV</button>
        </div>
        <div style={{ marginTop: 8 }}>
          {loading && <div>Working…</div>}
          {!loading && !mods.length && <div>No mods to show yet. Select devices and click OK.</div>}
          {!!mods.length && (
            <div style={{ maxHeight: 380, overflow: "auto", border: "1px solid #ddd" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #eee" }}>Mod</th>
                    <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #eee" }}>Devices that contain it</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMods.map(m => (
                    <tr key={m.name}>
                      <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5", fontFamily: "monospace" }}>{m.name}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5" }}>
                        {(m.devices || []).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
