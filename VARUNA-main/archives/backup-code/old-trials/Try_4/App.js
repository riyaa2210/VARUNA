// App.js: The main dashboard component for the Traffic Command Center.
// This is the heart of the frontend, connecting to the AI backend and displaying all the data.

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; // Don't forget Leaflet's CSS
import L from 'leaflet';
import './App.css'; // Our custom styles

// --- App Configuration ---
const CAMERA_URL = "http://192.168.0.9:8080/video"; // The MJPEG stream from the phone
const SERVER_SOCKET_URL = "ws://localhost:8000/ws"; // The WebSocket connection to our Python backend

// A hardcoded list of hospitals for routing. A real app would get this from a database.
const HOSPITALS = [
    { name: "SDM Medical College (Dharwad)", coords: [15.4246, 75.0344] },
    { name: "Dharwad District Hospital", coords: [15.4600, 75.0100] },
    { name: "KLE Hospital (Belagavi)", coords: [15.8854, 74.5034] },
    // Adding a few major ones for broader context on the map
    { name: "Apollo Hospital (Bangalore)", coords: [12.9716, 77.5946] },
    { name: "AIIMS (Delhi)", coords: [28.5672, 77.2100] },
    { name: "Tata Memorial (Mumbai)", coords: [19.0222, 72.8415] }
];

// This is a common fix for a bug where Leaflet icons don't show up correctly in React.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons to make incidents and hospitals stand out on the map.
const crashIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/10309/10309166.png', iconSize: [40, 40], popupAnchor: [0, -20]
});
const hospitalIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/4320/4320371.png', iconSize: [40, 40], popupAnchor: [0, -20]
});

// A small helper component to make the map fly to a new location.
function MapRecenter({ location }) {
    const map = useMap();
    useEffect(() => {
        if (location) map.flyTo(location, 14, { duration: 2.5 }); // Smoothly pan to the location
    }, [location, map]);
    return null; // It doesn't render anything, just controls the map.
}

// Helper to handle clicks on the map for manual incident simulation.
function LocationMarker({ handleMapClick }) {
    const map = useMap();
    useEffect(() => {
        map.on('click', handleMapClick); // Listen for map clicks
        return () => map.off('click', handleMapClick); // Clean up the listener
    }, [map, handleMapClick]);
    return null;
}


function App() {
    // --- STATE MANAGEMENT ---
    // `useState` holds all the data that changes and causes the UI to re-render.
    const [alert, setAlert] = useState(null); // The full alert object from the backend
    const [connectionStatus, setConnectionStatus] = useState("Disconnected 🔴"); // The WebSocket connection status for the UI
    const [cameraLocation, setCameraLocation] = useState(null); // The live GPS coordinates of the camera
    const [accidentPos, setAccidentPos] = useState(null); // Where the incident happened
    const [routePolyline, setRoutePolyline] = useState([]); // The green corridor route line on the map
    const [eta, setEta] = useState("0 mins"); // Ambulance ETA
    const [evidencePhoto, setEvidencePhoto] = useState(null); // The snapshot of the incident
    const [logs, setLogs] = useState([]); // Messages for the terminal log

    // State for the traffic simulation and display
    const [signals, setSignals] = useState({ north: 'red', east: 'red', south: 'red', west: 'red' });
    const [manualEast, setManualEast] = useState(10);
    const [manualSouth, setManualSouth] = useState(5);
    const [manualWest, setManualWest] = useState(8);
    const [trafficLevel, setTrafficLevel] = useState(0); // AI-detected traffic percentage
    const [trafficColor, setTrafficColor] = useState('#00ff00');

    // `useRef` holds values that we need to keep between renders but that DON'T cause a re-render.
    const sendTimeoutRef = useRef(null); // Used to "debounce" API calls from the sliders
    const hasRoutedRef = useRef(false); // A flag to stop us from re-routing for the same incident
    const wsRef = useRef(null); // Holds the actual WebSocket object

    // These refs are needed to get the latest state inside the WebSocket `onmessage` handler,
    // which otherwise would only have the state from when it was first created (a "stale closure").
    const cameraLocationRef = useRef(cameraLocation);
    const accidentPosRef = useRef(accidentPos);
    const evidenceRef = useRef(evidencePhoto);
    useEffect(() => { cameraLocationRef.current = cameraLocation; }, [cameraLocation]);
    useEffect(() => { accidentPosRef.current = accidentPos; }, [accidentPos]);
    useEffect(() => { evidenceRef.current = evidencePhoto; }, [evidencePhoto]);

    // A function to add a new message to the log, wrapped in `useCallback` for performance.
    const addLog = useCallback((msg) => {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        setLogs(prev => [`[${time}] ${msg}`, ...prev]); // Add to the top of the list
    }, []);

    // This `useEffect` is the core of the app. It runs once and manages the WebSocket connection.
    useEffect(() => {
        let stopped = false; // A flag to prevent reconnecting when we're leaving the page
        let backoff = 1000; // The starting delay for reconnection attempts

        const connect = () => {
            const ws = new WebSocket(SERVER_SOCKET_URL);
            wsRef.current = ws; // Save the WebSocket instance

            ws.onopen = () => {
                setConnectionStatus('Connected');
                addLog('SYSTEM INIT: WebSocket connected');
                backoff = 1000; // Reset reconnect timer on success
            };

            // This function is called every time the backend sends us data.
            ws.onmessage = (ev) => {
                const data = JSON.parse(ev.data);
                setAlert(data); // Update the main alert state with the new data
                if (data.signals) setSignals(data.signals); // Update traffic lights

                // Update the camera's GPS location, but only if it's moved a bit
                if (data.gps) {
                    const prev = cameraLocationRef.current;
                    const hasMoved = !prev || Math.hypot(prev[0] - data.gps[0], prev[1] - data.gps[1]) > 0.0002;
                    if (hasMoved) {
                        setCameraLocation(data.gps);
                        addLog(`GPS: ${data.gps[0].toFixed(4)}, ${data.gps[1].toFixed(4)}`);
                    }
                }
                
                // Update the manual traffic numbers if they come from the backend
                if (data.manual) {
                    setManualEast(Number(data.manual.east));
                    setManualSouth(Number(data.manual.south));
                    setManualWest(Number(data.manual.west));
                }

                // Update the AI-detected traffic bar
                if (data.car_count !== undefined) {
                    const pct = Math.min((data.car_count / 15) * 100, 100);
                    setTrafficLevel(pct);
                    // Change the color of the bar based on how heavy the traffic is
                    setTrafficColor(pct < 40 ? '#00ff00' : pct < 70 ? '#ff9900' : '#ff0000');
                }

                // If an incident is happening...
                if (data.level > 0) {
                    // If we get a photo and we haven't already saved one, save it.
                    if (data.snapshot && !evidenceRef.current) {
                        setEvidencePhoto(data.snapshot);
                        addLog(`EVIDENCE CAPTURED: ${data.title}`);
                    }
                    // If it's a serious incident and we haven't already planned a route...
                    if (data.level >= 2 && !accidentPosRef.current && !hasRoutedRef.current) {
                        const loc = data.gps || cameraLocationRef.current;
                        if (loc) {
                            setAccidentPos(loc); // Mark the accident location
                            const bestHospital = findNearestHospital(loc); // Find the closest hospital
                            if (bestHospital) {
                                getRoute(loc, bestHospital.coords); // Get the route for the green corridor
                                addLog(`ROUTING: ${bestHospital.name}`);
                            }
                            hasRoutedRef.current = true; // Mark that we have routed for this incident
                        }
                    }
                }
            };

            // This handles what happens when the connection drops.
            ws.onclose = () => {
                setConnectionStatus('Disconnected');
                if (!stopped) {
                    addLog(`WebSocket closed - reconnecting in ${Math.round(backoff / 1000)}s`);
                    // Try to reconnect after a delay, and increase the delay for next time (exponential backoff)
                    setTimeout(() => {
                        backoff = Math.min(backoff * 1.8, 20000); // Wait longer each time, up to 20s
                        if (!stopped) connect();
                    }, backoff);
                }
            };
            ws.onerror = (e) => { ws.close(); }; // If there's an error, just close the connection to trigger `onclose`
        };

        connect(); // Call the connect function to start the process

        // This is the cleanup function. It runs when the component is removed from the page.
        return () => {
            stopped = true;
            if (wsRef.current) wsRef.current.close();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [addLog]);

    // A "debounced" function to send traffic slider updates.
    // This prevents sending an API call for every tiny movement of the slider.
    const postLaneUpdate = (east, south, west) => {
        clearTimeout(sendTimeoutRef.current); // Clear any pending timeout
        // Set a new timeout to send the data after 300ms of no changes
        sendTimeoutRef.current = setTimeout(() => {
            fetch('http://localhost:8000/update-lanes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ east: Number(east), south: Number(south), west: Number(west) })
            }).catch(err => console.error(err));
        }, 300);
    };

    // Calls the OSRM routing API to get a route between two points.
    const getRoute = useCallback(async (start, end) => {
        try {
            // OSRM wants coordinates as longitude,latitude
            const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${start[1]},${start[0]};${end[1]},${end[0]}?overview=full&geometries=geojson`);
            const data = await response.json();
            if (data.routes?.[0]) {
                // Leaflet wants coordinates as latitude,longitude, so we have to flip them back.
                setRoutePolyline(data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]));
                setEta(`${Math.round(data.routes[0].duration / 60)} mins`);
            }
        } catch (e) {
            addLog("ERR: Routing Service Failed");
        }
    }, [addLog]);

    // A simple function to find the nearest hospital from our list using basic geometry.
    const findNearestHospital = (coords) => {
        if (!coords) return null;
        let nearest = null;
        let minDist = Infinity;
        HOSPITALS.forEach(h => {
            const dist = Math.hypot(h.coords[0] - coords[0], h.coords[1] - coords[1]);
            if (dist < minDist) {
                minDist = dist;
                nearest = h;
            }
        });
        return nearest;
    };

    // This is called when the user clicks the map, used for the "Simulate Crash" demo feature.
    const handleMapClick = (e) => {
        if (!e.latlng) return;
        const newPos = [e.latlng.lat, e.latlng.lng];
        setAccidentPos(newPos); // Manually set the accident position
        const best = findNearestHospital(newPos);
        if (best) getRoute(newPos, best.coords); // And find a route
        addLog("MANUAL TRIGGER: Simulation Started.");
    };

    // Resets the system state both on the frontend and by calling the backend.
    const resetSystem = () => {
        fetch('http://localhost:8000/reset-system', { method: 'POST' }).catch(e => console.error(e));
        // Reset the frontend state right away for a snappy feel.
        setAccidentPos(null);
        setRoutePolyline([]);
        setEvidencePhoto(null);
        setAlert(null);
        hasRoutedRef.current = false;
        addLog("CMD: SYSTEM RESET EXECUTED.");
    };
    
    // --- Render Helpers ---
    const getPercent = (val) => Math.min((val / 50) * 100, 100);
    const getColor = (pct) => pct < 40 ? '#00ff00' : pct < 70 ? '#ff9900' : '#ff0000';
    const overlayClass = `detection-overlay ${alert?.title === 'AMBULANCE DETECTED' ? 'ambulance' : alert?.level > 1 ? 'critical' : ''}`;

    return (
        // The background of the whole dashboard turns dark red during a serious alert.
        <div className="dashboard-container" style={{ backgroundColor: alert?.incident_active ? '#1a0000' : '#050505' }}>
            <header className="header">
                <div className="header-title">
                    <span role="img" aria-label="shield" style={{fontSize: '1.5rem', marginRight: '10px'}}>🛡️</span>
                    <div>
                        <h1>TRAFFIC COMMAND: INDIA GRID</h1>
                        <div className="subtitle">TEAM CODING_NEXUS | SIH 2025</div>
                    </div>
                </div>
                <div className="badges">
                    <span className="status-badge">{connectionStatus}</span>
                    {cameraLocation && <span className="conf-badge">GPS: {cameraLocation[0].toFixed(4)}, {cameraLocation[1].toFixed(4)}</span>}
                    {accidentPos && <span className="corridor-badge">🟢 GREEN CORRIDOR</span>}
                </div>
            </header>

            <div className="main-content">
                {/* === LEFT PANEL: Live Feed & Traffic Bars === */}
                <div className="panel left-panel">
                    <div className="panel-header">Live Feed & Analytics</div>
                    <div className="video-wrapper">
                        <img src={CAMERA_URL} className="camera-feed" alt="Live Feed" onError={(e) => { e.target.src = "https://via.placeholder.com/640x480/000000/FFFFFF?text=NO+SIGNAL"; }} />
                        {/* The flashing red overlay appears during an incident */}
                        {alert?.incident_active && <div className={overlayClass}></div>}
                    </div>
                    
                    <div className="stats-box">
                        {/* Each of these rows represents a traffic lane */}
                        <div className="stat-row">
                            <span>NORTH</span>
                            <div className="bar-container"><div className="bar" style={{ width: `${trafficLevel}%`, background: trafficColor }}></div></div>
                            <span>{Math.round(trafficLevel)}% (AI)</span>
                        </div>
                        <div className="stat-row">
                            <span>EAST</span>
                            <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualEast)}%`, background: getColor(getPercent(manualEast)) }}></div></div>
                            <span>{manualEast} (Man)</span>
                        </div>
                        <div className="stat-row">
                            <span>SOUTH</span>
                            <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualSouth)}%`, background: getColor(getPercent(manualSouth)) }}></div></div>
                            <span>{manualSouth} (Man)</span>
                        </div>
                        <div className="stat-row">
                            <span>WEST</span>
                            <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualWest)}%`, background: getColor(getPercent(manualWest)) }}></div></div>
                            <span>{manualWest} (Man)</span>
                        </div>
                    </div>
                </div>

                {/* === CENTER PANEL: Map or Evidence Photo === */}
                <div className="panel center-panel">
                    <div className="panel-header">Tactical Map</div>
                    {/* This is a conditional render. If there's an evidence photo, show it. Otherwise, show the map. */}
                    {evidencePhoto ? (
                        <div className="evidence-container">
                            <img src={`data:image/jpeg;base64,${evidencePhoto}`} alt="Evidence" className="evidence-img" />
                            <div className="evidence-tag">EVIDENCE LOCKED</div>
                            <button className="btn blue" onClick={() => setEvidencePhoto(null)}>CLOSE FILE</button>
                        </div>
                    ) : (
                        <div className="map-wrapper">
                            <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: "100%", width: "100%" }}>
                                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution='&copy; CartoDB' />
                                <MapRecenter location={cameraLocation} />
                                <LocationMarker handleMapClick={handleMapClick} />
                                {HOSPITALS.map((h, i) => <Marker key={i} position={h.coords} icon={hospitalIcon}><Popup>{h.name}</Popup></Marker>)}
                                {cameraLocation && <Marker position={cameraLocation}><Popup>Active Cam</Popup></Marker>}
                                {accidentPos && <Marker position={accidentPos} icon={crashIcon}><Popup>INCIDENT</Popup></Marker>}
                                {routePolyline.length > 0 && <Polyline positions={routePolyline} color="#00ff00" weight={5} dashArray="10, 10" />}
                            </MapContainer>
                            {accidentPos && <div className="route-overlay"><h4>🚑 DISPATCHED</h4><p>ETA: {eta}</p></div>}
                        </div>
                    )}
                </div>

                {/* === RIGHT PANEL: Logs and Controls === */}
                <div className="panel right-panel">
                    <div className="panel-header">System Log</div>
                    <div className="alert-card" style={{ borderColor: alert?.color || '#333' }}>
                        <h2 style={{ color: alert?.color || 'white' }}>{alert?.title || "SYSTEM NORMAL"}</h2>
                        <p>{alert?.message || "Scanning Sector..."}</p>
                    </div>
                    
                    <div className="action-log">
                        {logs.slice(0, 10).map((log, i) => <div key={i} className="log-entry">{log}</div>)}
                    </div>

                    <div className="manual-controls">
                        <div className="subtitle">Traffic Simulation</div>
                        <div className="control-group">
                            <div className="control-label"><span>East Lane</span><span>{manualEast}</span></div>
                            <input aria-label="East lane traffic" type="range" min={0} max={50} value={manualEast} onChange={(e) => { const v = e.target.value; setManualEast(v); postLaneUpdate(v, manualSouth, manualWest); }} />
                        </div>
                        <div className="control-group">
                            <div className="control-label"><span>South Lane</span><span>{manualSouth}</span></div>
                            <input aria-label="South lane traffic" type="range" min={0} max={50} value={manualSouth} onChange={(e) => { const v = e.target.value; setManualSouth(v); postLaneUpdate(manualEast, v, manualWest); }} />
                        </div>
                        <div className="control-group">
                            <div className="control-label"><span>West Lane</span><span>{manualWest}</span></div>
                            <input aria-label="West lane traffic" type="range" min={0} max={50} value={manualWest} onChange={(e) => { const v = e.target.value; setManualWest(v); postLaneUpdate(manualEast, manualSouth, v); }} />
                        </div>

                        <div className="signal-grid">
                            <div className="signal-row"><span>N</span><div className={`light ${signals.north}`}></div></div>
                            <div className="signal-row"><span>E</span><div className={`light ${signals.east}`}></div></div>
                            <div className="signal-row"><span>S</span><div className={`light ${signals.south}`}></div></div>
                            <div className="signal-row"><span>W</span><div className={`light ${signals.west}`}></div></div>
                        </div>

                        <button onClick={() => { const simPos = cameraLocation ? { latlng: { lat: cameraLocation[0], lng: cameraLocation[1] } } : { latlng: { lat: 15.45, lng: 75.01 } }; handleMapClick(simPos); }} className="btn red">SIMULATE CRASH</button>
                        <button onClick={resetSystem} className="btn blue">RESET SYSTEM</button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
