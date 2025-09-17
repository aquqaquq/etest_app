import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "";

// Simple case-insensitive contains check for all search tokens
function matchesQuery(str, query) {
  if (!query) return true;
  const tokens = query
    .split(/\s+/)
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);
  const s = (str || "").toLowerCase();
  return tokens.every((t) => s.includes(t));
}

// Simple, scalable SVG wafer map component
function WaferMapSVG({ dies, onToggle, selected = new Set(), waferDiameterPx = 720, waferFlat }) {
  if (!dies || dies.length === 0) return <div className="text-gray-700">No wafer map available.</div>;

  // Bounds and normalization
  const minX = Math.min(...dies.map(d => d.x));
  const maxX = Math.max(...dies.map(d => d.x));
  const minY = Math.min(...dies.map(d => d.y));
  const maxY = Math.max(...dies.map(d => d.y));
  const cols = Math.max(1, maxX - minX + 1);
  const rows = Math.max(1, maxY - minY + 1);

  const normalized = dies.map(d => ({
    ...d,
    gx: d.x - minX,
    gy: (maxY - d.y), // invert so larger y appears lower (top-origin for drawing)
    key: `${d.x},${d.y}`,
  }));

  // Fixed-size wafer circle, axes placed outside
  const marginPx = { left: 72, top: 72, right: 40, bottom: 64 };
  const svgWidth = waferDiameterPx + marginPx.left + marginPx.right;
  const svgHeight = waferDiameterPx + marginPx.top + marginPx.bottom;
  const centerX = marginPx.left + waferDiameterPx / 2;
  const centerY = marginPx.top + waferDiameterPx / 2;
  const waferRadius = waferDiameterPx / 2;

  // Compute anisotropic unit sizes (unitX, unitY) so all die rectangles fit inside the circle,
  // maximizing width while fitting the vertical extent nicely.
  const circlePaddingPx = 4; // clearance from circle stroke
  const R = waferRadius - circlePaddingPx;
  // Precompute A,B per die: distance (in grid units) from wafer center to farthest rectangle corner
  const AB = normalized.map(d => {
    const cx = Math.abs((d.gx + 0.5) - cols / 2);
    const cy = Math.abs((d.gy + 0.5) - rows / 2);
    return { A: cx + 0.5, B: cy + 0.5 };
  });
  const Amax = AB.reduce((m, v) => Math.max(m, v.A), 0);
  const Bmax = AB.reduce((m, v) => Math.max(m, v.B), 0);
  // Handle degenerate cases (single row/column)
  let unitX, unitY;
  if (Amax === 0 && Bmax === 0) {
    unitX = unitY = R; // single die
  } else if (Amax === 0) {
    unitY = R / Bmax;
    unitX = unitY; // square dies when only vertical extent exists
  } else if (Bmax === 0) {
    unitX = R / Amax;
    unitY = unitX; // square dies when only horizontal extent exists
  } else {
    // Balance X/Y by normalizing to their maxima and scaling by r so that
    // max_i sqrt((A/Amax)^2 + (B/Bmax)^2) == r and (A*unitX)^2 + (B*unitY)^2 <= R^2
    let r = 0;
    for (const { A, B } of AB) {
      const val = Math.sqrt((A / Amax) ** 2 + (B / Bmax) ** 2);
      r = Math.max(r, val);
    }
    r = Math.max(r, 1); // guard
    unitX = R / (r * Amax);
    unitY = R / (r * Bmax);
  }

  // Grid boundaries in pixels relative to wafer center
  const leftPx = centerX - (cols / 2) * unitX;
  const topPx = centerY - (rows / 2) * unitY;
  const rightPx = leftPx + cols * unitX;
  const bottomPx = topPx + rows * unitY;

  // Styling helpers
  const axisTextStyle = { fontSize: 12, fill: '#334155', userSelect: 'none' };
  const coordTextStyle = { fontSize: Math.max(10, Math.floor(Math.min(unitX, unitY) * 0.5)), fill: 'white', pointerEvents: 'none' };

  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
  <svg width={svgWidth} height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`} shapeRendering="geometricPrecision">
        {/* Notch as a masked + clipped wedge: oversize the wedge slightly and clip to circle to avoid any gap */}
        {(() => {
          if (waferFlat?.angleDeg == null) {
            return (
              <circle cx={centerX} cy={centerY} r={waferRadius} fill="none" stroke="#9ca3af" strokeWidth={2} />
            );
          }
          const theta = (Math.PI / 180) * waferFlat.angleDeg;
          const nx = Math.cos(theta);
          const ny = Math.sin(theta);
          const tx = -ny;
          const ty = nx;
          const baseHalf = (waferFlat.sizePx ?? 40) / 2; // interpret as chord half-length on the circle
          const apexInset = 14;
          const baseOutset = 4; // outward offset for mask to fully cover stroke
          const apexX = centerX + (waferRadius - apexInset) * nx;
          const apexY = centerY + (waferRadius - apexInset) * ny;
          // Map chord half-length to angular half-width on circle
          const clamped = Math.min(waferRadius, Math.max(0, baseHalf));
          const phi = Math.asin(clamped / waferRadius); // radians
          // Endpoints on the circle (exact) and a tiny outward-overshoot for wedge fill (to be clipped to circle)
          const ex1 = centerX + waferRadius * Math.cos(theta + phi);
          const ey1 = centerY + waferRadius * Math.sin(theta + phi);
          const ex2 = centerX + waferRadius * Math.cos(theta - phi);
          const ey2 = centerY + waferRadius * Math.sin(theta - phi);
          const overshoot = 1.5; // px outward to guarantee overlap; will be clipped to circle
          const ex1o = centerX + (waferRadius + overshoot) * Math.cos(theta + phi);
          const ey1o = centerY + (waferRadius + overshoot) * Math.sin(theta + phi);
          const ex2o = centerX + (waferRadius + overshoot) * Math.cos(theta - phi);
          const ey2o = centerY + (waferRadius + overshoot) * Math.sin(theta - phi);
          // Mask base points slightly outside along local radial directions to hide arc stroke
          const mx1 = centerX + (waferRadius + baseOutset) * Math.cos(theta + phi);
          const my1 = centerY + (waferRadius + baseOutset) * Math.sin(theta + phi);
          const mx2 = centerX + (waferRadius + baseOutset) * Math.cos(theta - phi);
          const my2 = centerY + (waferRadius + baseOutset) * Math.sin(theta - phi);
          const pts = `${apexX},${apexY} ${mx1},${my1} ${mx2},${my2}`;
          const maskId = `wafer-notch-mask`;
          const clipId = `wafer-circle-clip`;
          return (
            <>
              <defs>
                <mask id={maskId} maskUnits="userSpaceOnUse">
                  {/* show all by default */}
                  <rect x="0" y="0" width={svgWidth} height={svgHeight} fill="white" />
                  {/* hide stroke within wedge */}
                  <polygon points={pts} fill="black" />
                </mask>
                {/* Clip to the circle interior so the oversized wedge can't protrude */}
                <clipPath id={clipId} clipPathUnits="userSpaceOnUse">
                  <circle cx={centerX} cy={centerY} r={waferRadius} />
                </clipPath>
              </defs>
              {/* Filled wedge first, slightly oversized and clipped to circle to remove any seams */}
              <polygon
                points={`${apexX},${apexY} ${ex1o},${ey1o} ${ex2o},${ey2o}`}
                fill="#9ca3af"
                stroke="#9ca3af"
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
                clipPath={`url(#${clipId})`}
              />
              {/* Circle stroke drawn last with mask so it sits cleanly on top around the wedge sides */}
              <circle cx={centerX} cy={centerY} r={waferRadius} fill="none" stroke="#9ca3af" strokeWidth={2} mask={`url(#${maskId})`} />
            </>
          );
        })()}

        {/* Grid backdrop clipped visually by the circle (we compute unit size so dies fit) */}
        <g stroke="#d1d5db" strokeWidth={1}>
          {Array.from({ length: cols + 1 }, (_, i) => (
            <line key={`v-${i}`} x1={leftPx + i * unitX} y1={topPx} x2={leftPx + i * unitX} y2={bottomPx} />
          ))}
          {Array.from({ length: rows + 1 }, (_, j) => (
            <line key={`h-${j}`} x1={leftPx} y1={topPx + j * unitY} x2={rightPx} y2={topPx + j * unitY} />
          ))}
        </g>

        {/* Axis labels (original coordinates) placed outside the wafer circle */}
        <g>
          {/* X labels above the circle */}
          {Array.from({ length: cols }, (_, i) => (
            <text
              key={`xt-${i}`}
              x={leftPx + (i + 0.5) * unitX}
              y={centerY - waferRadius - 10}
              textAnchor="middle"
              style={axisTextStyle}
            >
              {minX + i}
            </text>
          ))}
          {/* Y labels left of the circle; value corresponds to original y row */}
          {Array.from({ length: rows }, (_, j) => {
            const label = minY + (rows - 1 - j); // original y value for row j
            return (
              <text
                key={`yl-${j}`}
                x={centerX - waferRadius - 12}
                y={topPx + (j + 0.65) * unitY}
                textAnchor="end"
                style={axisTextStyle}
              >
                {label}
              </text>
            );
          })}
        </g>

        {/* Dies (all fit within the wafer circle) */}
        <g>
          {normalized.map(die => {
            const x = leftPx + die.gx * unitX;
            const y = topPx + die.gy * unitY;
            const selectedNow = selected.has(die.key);
            return (
              <g key={die.key} onClick={() => onToggle?.(die)} style={{ cursor: 'pointer' }}>
                <rect
                  x={x + 1}
                  y={y + 1}
                  width={Math.max(2, unitX - 2)}
                  height={Math.max(2, unitY - 2)}
                  rx={Math.max(2, Math.min(unitX, unitY) * 0.12)}
                  ry={Math.max(2, Math.min(unitX, unitY) * 0.12)}
                  fill={selectedNow ? '#2563eb' : '#60a5fa'}
                  stroke="#1f2937"
                  strokeWidth={0.8}
                />
                <title>{`(${die.x}, ${die.y})`}</title>
                <text x={x + unitX / 2} y={y + unitY / 2 + Math.max(8, Math.min(unitX, unitY) * 0.18)} textAnchor="middle" style={coordTextStyle}>
                  {die.x},{die.y}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

export default function EtestProgramGenerator() {
  const [loading, setLoading] = useState(true);
  const [devices, setDevices] = useState([]);
  const [query, setQuery] = useState("");
  const [selectedDevice, setSelectedDevice] = useState("");
  const [mods, setMods] = useState([]);
  const [error, setError] = useState("");
  const [currentDevice, setCurrentDevice] = useState("");
  const [selectedDies, setSelectedDies] = useState(new Set());
  const [skywaterInitial, setSkywaterInitial] = useState("");
  const hasSelection = !!selectedDevice;

  // Load device list (already filtered by backend to non-empty mods)
  useEffect(() => {
    async function loadDevices() {
      try {
        setLoading(true);
        setError("");
        const res = await fetch(`${API_BASE}/api/etest/json`);
        if (!res.ok) throw new Error(`Failed to load devices: ${res.status}`);
        const data = await res.json();
        setDevices(data.devices || []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    loadDevices();
  }, []);

  const filteredDevices = useMemo(() => {
    return devices.filter((d) => matchesQuery(d, query));
  }, [devices, query]);

  async function handleOk(dev) {
    if (!dev) return;
    try {
      setError("");
      setMods([]);
      const res = await fetch(
        `${API_BASE}/api/etest/device-mods`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ devices: [dev] })
        }
      );
      if (!res.ok) throw new Error(`Failed to load device data: ${res.status}`);
      const data = await res.json();
      console.log("Fetched Mods:", data.mods); // Debugging log for mods data
      console.log("Fetched Wafers:", data.wafers); // Debugging log for wafers data
      setMods(Array.isArray(data.mods) ? data.mods : []);
      const parsedWafers = (data.wafers[dev] || []).map(coord => {
        const [x, y] = coord.split(',').map(Number);
        return { x, y };
      });
      // Determine wafer flat angle from metadata (prefer flatLocation letters)
      const meta = (data.waferMeta && data.waferMeta[dev]) || {};
      const loc = (meta.flatLocation || '').toUpperCase();
      // Convention (SVG y-down): 0° right, 90° bottom, 180° left, 270° top
      const locMap = { 'R': 0, 'B': 90, 'L': 180, 'T': 270 };
      let angleDeg = locMap[loc];
      // If no location provided, fall back to numeric angle if available.
      // The JSON uses 0=T, 90=R, 180=B, 270=L. Convert to SVG angles (0=R,90=B,180=L,270=T).
      if (angleDeg == null && typeof meta.flatAngle_deg === 'number') {
        const a = Number(meta.flatAngle_deg);
        if (Number.isFinite(a)) {
          angleDeg = (a + 270) % 360; // rotate by -90° to map top→270, right→0, bottom→90, left→180
        }
      }
      const waferFlat = angleDeg != null ? { angleDeg, sizePx: 100 } : undefined;
      setCurrentDevice({ name: dev, waf: parsedWafers, waferFlat }); // include wafer flat for drawing
  setSelectedDies(new Set()); // reset selection on load
      console.log("Updated Current Device:", { name: dev, waf: parsedWafers }); // Debugging log for currentDevice state
    } catch (e) {
      setError(e.message);
    }
  }

  function handleDeviceChange(e) {
    setSelectedDevice(e.target.value);
  }

  function handleModsOkClick(devKey) {
    // Refresh the selected device's data without clobbering currentDevice shape
    if (devKey) {
      handleOk(devKey);
    }
  }

  function clearModsSelection() {
    setMods([]);
    setCurrentDevice("");
    setSelectedDies(new Set());
  }

  function handleSubmit() {
    const dies = Array.from(selectedDies);
    const payload = {
      device: selectedDevice || currentDevice?.name,
      skywaterInitial,
      dies,
    };
    // Placeholder: wire to backend when endpoint is defined
    console.log("Submit payload:", payload);
    if (!skywaterInitial) {
      alert("Please enter Skywater initial before submitting.");
      return;
    }
    alert(`Submitting ${dies.length} dies for ${payload.device} by ${skywaterInitial}`);
  }

  const devKey = selectedDevice || (filteredDevices.length === 1 ? filteredDevices[0] : "");

  return (
    <div className="col">
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Etest Program Generator</h1>

      {error && <div style={{ color: '#b91c1c' }}>{error}</div>}

      {loading ? (
        <div>Loading device list…</div>
      ) : (
        <>
          {/* Filter card */}
          <div className="card">
            <div className="card-header">Filter devices</div>
            <div className="card-body">
              <div className="row" style={{ alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="Type to filter… (e.g., 5CC9 8000)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="input grow"
                />
                <button
                  onClick={() => { setQuery(""); setSelectedDevice(""); setMods([]); setCurrentDevice(""); setSelectedDies(new Set()); }}
                  className="btn"
                >
                  Clear
                </button>
              </div>
              <div className="mt-2" style={{ fontSize: 12, color: '#64748b' }}>
                Showing {filteredDevices.length} of {devices.length}
              </div>
            </div>
          </div>

          {/* Device + Mods cards */}
          <div className="row">
            <div className="card grow">
              <div className="card-header">Device</div>
              <div className="card-body">
                <div style={{ maxHeight: '20rem', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 8, padding: 8 }}>
                  {filteredDevices.map((key) => {
                    const isChecked = selectedDevice === key;
                    return (
                      <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 4px', borderBottom: '1px solid var(--border)' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {
                            const newSelection = isChecked ? "" : key;
                            setSelectedDevice(newSelection);
                            if (newSelection) {
                              handleOk(newSelection);
                            } else {
                              setMods([]);
                              setCurrentDevice("");
                              setSelectedDies(new Set());
                            }
                          }}
                        />
                        <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 13 }}>{key}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {hasSelection && (
              <div className="card grow">
                <div className="card-header">Mods</div>
                <div className="card-body">
                  {mods.length === 0 ? (
                    <div style={{ color: '#334155' }}>No mods.</div>
                  ) : (
                    <div style={{ maxHeight: '20rem', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 8, padding: 8 }}>
                      {mods.map((m, index) => (
                        <div key={m.name + index} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 4px', borderBottom: '1px solid var(--border)' }}>
                          <input type="checkbox" onChange={() => {}} />
                          <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 13 }}>
                            {m.name} (x: {m.x ?? ''}, y: {m.y ?? ''})
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Wafer Map + Submit */}
          {hasSelection && (
            <div className="row" style={{ alignItems: 'stretch' }}>
              {/* Wafer */}
              <div className="card grow">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Wafer Map</span>
                  {(() => {
                    const totalDies = currentDevice?.waf?.length || 0;
                    const allSelected = totalDies > 0 && selectedDies.size === totalDies;
                    const noneSelected = selectedDies.size === 0;
                    return (
                      <div className="row" style={{ alignItems: 'center' }}>
                        <div style={{ fontSize: 12, color: '#64748b' }}>Selected: {selectedDies.size}/{totalDies}</div>
                        <button
                          type="button"
                          className="btn primary"
                          disabled={allSelected || totalDies === 0}
                          onClick={() => {
                            if (!currentDevice?.waf) return;
                            setSelectedDies(new Set(currentDevice.waf.map(d => `${d.x},${d.y}`)));
                          }}
                        >
                          Select All
                        </button>
                        <button
                          type="button"
                          className="btn"
                          disabled={noneSelected}
                          onClick={() => setSelectedDies(new Set())}
                        >
                          Unselect All
                        </button>
                      </div>
                    );
                  })()}
                </div>
                <div className="card-body">
                  {currentDevice && currentDevice.waf && currentDevice.waf.length > 0 ? (
                    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: 8 }}>
                      <WaferMapSVG
                        dies={currentDevice.waf}
                        selected={selectedDies}
                        onToggle={(die) => {
                          setSelectedDies(prev => {
                            const next = new Set(prev);
                            const key = `${die.x},${die.y}`;
                            if (next.has(key)) next.delete(key); else next.add(key);
                            return next;
                          });
                        }}
                        waferDiameterPx={820}
                        waferFlat={currentDevice.waferFlat}
                        // Pass waferFlat metadata here when available, e.g., { angleDeg: 270, sizePx: 100 }
                      />
                    </div>
                  ) : (
                    <div style={{ color: '#334155' }}>No wafer map available.</div>
                  )}
                </div>
              </div>

              {/* Submit */}
              <div className="card" style={{ width: '32%' }}>
                <div className="card-header">Submit</div>
                <div className="card-body">
                  <label className="mb-2" style={{ fontSize: 12, color: '#334155' }}>Skywater initial</label>
                  <input
                    type="text"
                    value={skywaterInitial}
                    onChange={(e) => setSkywaterInitial(e.target.value)}
                    placeholder="Enter initials"
                    className="input mt-2"
                  />
                  <button
                    type="button"
                    onClick={handleSubmit}
                    className="btn success mt-3"
                    style={{ width: '100%', paddingTop: 14, paddingBottom: 14, fontSize: 18 }}
                    title="Submit selected dies"
                  >
                    Submit
                  </button>
                  <div className="mt-3" style={{ fontSize: 12, color: '#64748b' }}>Selected dies: {selectedDies.size}</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
