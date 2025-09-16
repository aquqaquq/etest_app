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

export default function EtestProgramGenerator() {
  const [loading, setLoading] = useState(true);
  const [devices, setDevices] = useState([]);
  const [query, setQuery] = useState("");
  const [selectedDevice, setSelectedDevice] = useState("");
  const [mods, setMods] = useState([]);
  const [error, setError] = useState("");
  const [currentDevice, setCurrentDevice] = useState("");

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
        `${API_BASE}/api/etest/mods?device=${encodeURIComponent(dev)}`
      );
      if (!res.ok) throw new Error(`Failed to load mods: ${res.status}`);
      const data = await res.json();
      setMods(Array.isArray(data.mods) ? data.mods : []);
      setCurrentDevice(dev); // Update currentDevice state
    } catch (e) {
      setError(e.message);
    }
  }

  function handleDeviceChange(e) {
    setSelectedDevice(e.target.value);
  }

  function handleModsOkClick(devKey) {
    setCurrentDevice(devKey);
  }

  function clearModsSelection() {
    setMods([]);
    setCurrentDevice("");
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
            <div className="flex-1" style={{ width: '48%' }}>  {/* Devices section with explicit width */}
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

              <div className="flex gap-2 mt-2">  {/* OK and Clear buttons */}
                <button
                  type="button"
                  onClick={() => handleModsOkClick(devKey)}
                  className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700"
                >
                  OK
                </button>
                <button
                  type="button"
                  onClick={clearModsSelection}
                  className="border rounded-lg px-3 py-2 hover:bg-gray-50"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="flex-1" style={{ width: '48%' }}>  {/* Mods section with explicit width */}
              {/* Mods section */}
              <h2 className="text-lg mb-2">Mods</h2>  {/* Keep h2 */}
              {mods.length === 0 ? (
                <div className="text-gray-700">No mods.</div>
              ) : (
                <div className="border rounded-lg h-40 overflow-auto p-2 bg-white">
                  <div className="flex flex-col" style={{ maxHeight: '20rem', overflowY: 'auto' }}>
                    {mods.map((m) => (
                      <div key={m} className="flex items-center gap-2 px-2 py-1 border-b">
                        <input
                          type="checkbox"
                          onChange={() => {}}
                        />
                        <span className="font-mono text-sm">{m}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
