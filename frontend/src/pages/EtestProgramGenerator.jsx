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
function WaferMapSVG({ dies, onToggle, selected = new Set(), waferDiameterPx = 720 }) {
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
  const marginPx = { left: 80, top: 80, right: 24, bottom: 48 };
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
  const axisTextStyle = { fontSize: 14, fill: '#333', userSelect: 'none' };
  const coordTextStyle = { fontSize: Math.max(10, Math.floor(Math.min(unitX, unitY) * 0.5)), fill: 'white', pointerEvents: 'none' };

  return (
    <div className="w-full flex justify-center">
      <svg width={svgWidth} height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
        {/* Background */}
        <rect x={0} y={0} width={svgWidth} height={svgHeight} fill="#f3f4f6" />

        {/* Wafer outline circle (fixed size) */}
        <circle cx={centerX} cy={centerY} r={waferRadius} fill="none" stroke="#9ca3af" strokeWidth={2} />

        {/* Grid backdrop clipped visually by the circle (we compute unit size so dies fit) */}
        <g stroke="#d1d5db" strokeWidth={1}>
          {Array.from({ length: cols + 1 }, (_, i) => (
            <line key={`v-${i}`} x1={leftPx + i * unitX} y1={topPx} x2={leftPx + i * unitX} y2={bottomPx} />
          ))}
          {Array.from({ length: rows + 1 }, (_, j) => (
            <line key={`h-${j}`} x1={leftPx} y1={topPx + j * unitY} x2={rightPx} y2={topPx + j * unitY} />
          ))}
        </g>

        {/* Axis labels (original coordinates): X along top, Y along left with bottom as minY */}
        <g>
          {Array.from({ length: cols }, (_, i) => (
            <text key={`xt-${i}`} x={leftPx + (i + 0.5) * unitX} y={topPx - 16} textAnchor="middle" style={axisTextStyle}>{minX + i}</text>
          ))}
          {Array.from({ length: rows }, (_, j) => {
            const label = minY + (rows - 1 - j);
            return (
              <text key={`yl-${j}`} x={leftPx - 18} y={topPx + (j + 0.7) * unitY} textAnchor="middle" style={axisTextStyle}>{label}</text>
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
  setCurrentDevice({ name: dev, waf: parsedWafers }); // Update currentDevice state with parsed wafers
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
    <div className="flex flex-col gap-6 p-6 bg-gray-100 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Etest Program Generator</h1>

      {error && <div className="text-red-600">{error}</div>}

      {loading ? (
        <div>Loading device list…</div>
      ) : (
        <>
          {/* Search + selection row */}
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:gap-4">
            <div className="flex flex-row items-center gap-2">  {/* Adjust layout to align input and Clear button */}
              <h2 className="text-lg mb-2">Filter devices</h2>  {/* Change label to h2 */}
              <input
                type="text"
                placeholder="Type to filter… (e.g., 5CC9 8000)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 border rounded p-2"
              />
              <button
                onClick={() => { setQuery(""); setSelectedDevice(""); setMods([]); }}
                className="border rounded px-3 py-2 ml-2"  /* Ensure Clear button is aligned */
              >
                Clear
              </button>
            </div>
            <div className="text-xs text-gray-600 mt-1">
              Showing {filteredDevices.length} of {devices.length}
            </div>
          </div>

          <div className="flex flex-row gap-4 w-full" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>  {/* Ensure proper alignment */}
            <div className="flex-1" style={{ width: hasSelection ? '48%' : '100%' }}>  {/* Devices section width adapts to selection */}
              {/* Devices section */}
              <h2 className="text-lg mb-2">Device</h2>  {/* Change to h2 */}
              <div className="border rounded-lg h-40 overflow-auto p-2 bg-white">
                <div className="flex flex-col" style={{ maxHeight: '20rem', overflowY: 'auto' }}>
                  {filteredDevices.map((key) => {
                    const isChecked = selectedDevice === key;
                    return (
                      <div key={key} className="flex items-center gap-2 border-b py-2">
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
                            }
                          }}
                        />
                        <span className="font-mono text-sm">{key}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Removed device section Clear/OK per request */}
            </div>

            {hasSelection && (
              <div className="flex-1" style={{ width: '48%' }}>  {/* Mods section with explicit width */}
                {/* Mods section */}
                <h2 className="text-lg mb-2">Mods</h2>  {/* Keep h2 */}
                {mods.length === 0 ? (
                  <div className="text-gray-700">No mods.</div>
                ) : (
                  <div className="border rounded-lg h-40 overflow-auto p-2 bg-white">
                    <div className="flex flex-col" style={{ maxHeight: '20rem', overflowY: 'auto' }}>
                      {mods.map((m, index) => (
                        <div key={m.name + index} className="flex items-center gap-2 px-2 py-1 border-b">
                          <input
                            type="checkbox"
                            onChange={() => {}}
                          />
                          <span className="font-mono text-sm">
                            {m.name} (x: {m.x ?? ''}, y: {m.y ?? ''})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Wafer Map + Submit panel below */}
          {hasSelection && (
            <div className="w-full flex gap-4 items-start mt-4">
              <div className="flex-1" style={{ width: '70%' }}>  {/* Wafer map section */}
                <h2 className="text-lg mb-2">Wafer Map</h2>
                {/* Buttons on top */}
                <div className="flex gap-2 mb-2">  {/* Select/Unselect buttons */}
                  <button
                    type="button"
                    onClick={() => {
                      if (!currentDevice?.waf) return;
                      setSelectedDies(new Set(currentDevice.waf.map(d => `${d.x},${d.y}`)));
                    }}
                    className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700"
                  >
                    Select All
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedDies(new Set())}
                    className="border rounded-lg px-3 py-2 hover:bg-gray-50"
                  >
                    Unselect All
                  </button>
                </div>
                {currentDevice && currentDevice.waf && currentDevice.waf.length > 0 ? (
                  <div className="border rounded-lg bg-white p-2">
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
                    />
                  </div>
                ) : (
                  <div className="text-gray-700">No wafer map available.</div>
                )}
              </div>
              {/* Right-side actions: Skywater initial + big Submit */}
              <div className="border rounded-lg bg-white p-4" style={{ width: '30%' }}>
                <label className="block text-sm font-medium text-gray-700 mb-1">Skywater initial</label>
                <input
                  type="text"
                  value={skywaterInitial}
                  onChange={(e) => setSkywaterInitial(e.target.value)}
                  placeholder="Enter initials"
                  className="w-full border rounded p-2 mb-4"
                />
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="w-full text-xl bg-green-600 text-white rounded-lg px-6 py-4 hover:bg-green-700"
                  title="Submit selected dies"
                >
                  Submit
                </button>
                <div className="mt-3 text-sm text-gray-600">Selected dies: {selectedDies.size}</div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
