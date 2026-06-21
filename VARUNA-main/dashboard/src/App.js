import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

// --- CONFIGURATION ---
// Use frame from WebSocket instead
const CAMERA_URL = null;

// Derive backend host dynamically so frontend works when accessed from mobile/other LAN devices
const HOSTNAME = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : 'localhost';
const IS_SECURE = (typeof window !== 'undefined' && window.location && window.location.protocol === 'https:');
const WS_SCHEME = IS_SECURE ? 'wss' : 'ws';
const HTTP_SCHEME = IS_SECURE ? 'https' : 'http';
const SERVER_SOCKET_URL = `${WS_SCHEME}://${HOSTNAME}:8000/ws`;
const API_URL = `${HTTP_SCHEME}://${HOSTNAME}:8000`;
// --- DYNAMIC HOSPITAL DATABASE ---
const HOSPITALS = [
    { name: "SDM Medical College (Dharwad)", coords: [15.4246, 75.0344] },
    { name: "Dharwad District Hospital", coords: [15.4600, 75.0100] },
    { name: "KLE Hospital (Belagavi)", coords: [15.8854, 74.5034] },
    { name: "Apollo Hospital (Bangalore)", coords: [12.9716, 77.5946] },
    { name: "AIIMS (Delhi)", coords: [28.5672, 77.2100] },
    { name: "Tata Memorial (Mumbai)", coords: [19.0222, 72.8415] }
];

// --- LEAFLET ICONS ---
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const crashIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/10309/10309166.png', iconSize: [40, 40], popupAnchor: [0, -20]
});
const hospitalIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/4320/4320371.png', iconSize: [40, 40], popupAnchor: [0, -20]
});

// --- HELPER COMPONENTS ---
function MapRecenter({ location }) {
    const map = useMap();
    useEffect(() => {
        if (location) map.flyTo(location, 14, { duration: 2.5 });
    }, [location, map]);
    return null;
}

function LocationMarker({ handleMapClick }) {
    useMap().on('click', (e) => handleMapClick(e));
    return null;
}

function App() {
    // --- STATE ---
    const [alert, setAlert] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    
    // Data States
    const [cameraLocation, setCameraLocation] = useState(null); 
    const [accidentPos, setAccidentPos] = useState(null);
    const [routePolyline, setRoutePolyline] = useState([]);
    const [eta, setEta] = useState("0 mins");
    const [evidencePhoto, setEvidencePhoto] = useState(null);
    const [logs, setLogs] = useState([]);
    
    // Traffic & Logic States
    const [signals, setSignals] = useState({ north: 'red', east: 'red', south: 'red', west: 'red' });
    const [algorithmInfo, setAlgorithmInfo] = useState({ active: 'Initializing...', junction_type: '4-Way' });
    const [junctionType, setJunctionType] = useState(4); // Default 4-way
    
    // Sliders
    const [manualEast, setManualEast] = useState(10);
    const [manualSouth, setManualSouth] = useState(5);
    const [manualWest, setManualWest] = useState(8);
    const [trafficLevel, setTrafficLevel] = useState(0); 
    const [trafficColor, setTrafficColor] = useState('green');
    
    // Refs
    const sendTimeoutRef = useRef(null);
    const hasRoutedRef = useRef(false);
    const wsRef = useRef(null);
    const [liveFrame, setLiveFrame] = useState(null);

    // Audio Alert
    const speakAlert = useCallback((message) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 1.1;
            window.speechSynthesis.speak(utterance);
        }
    }, []);

    const addLog = useCallback((msg) => {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        setLogs(prev => [`> [${time}] ${msg}`, ...prev.slice(0, 15)]);
    }, []);

    // --- WEBSOCKET CONNECTION ---
    useEffect(() => {
        let stopped = false;
        
        const connect = () => {
            const ws = new WebSocket(SERVER_SOCKET_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnectionStatus("Connected");
                addLog("SYSTEM ONLINE: Linked to Smart Signal Controller.");
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setAlert(data);
                    
                    // Display live frame from backend
                    if (data.frame) {
                        setLiveFrame(data.frame);
                    }
                    
                    if (data.signals) setSignals(data.signals);
                    if (data.algorithm) setAlgorithmInfo(data.algorithm);
                    if (data.gps && !cameraLocation) {
                        setCameraLocation(data.gps);
                        addLog(`GPS LOCKED: ${data.gps[0].toFixed(4)}, ${data.gps[1].toFixed(4)}`);
                    }

                    if (data.manual) {
                        if (data.manual.east !== undefined) setManualEast(data.manual.east);
                        if (data.manual.south !== undefined) setManualSouth(data.manual.south);
                        if (data.manual.west !== undefined) setManualWest(data.manual.west);
                    }
                    
                    if (data.car_count !== undefined) {
                        const percentage = Math.min((data.car_count / 15) * 100, 100);
                        setTrafficLevel(percentage);
                        setTrafficColor(percentage < 40 ? '#00ff00' : percentage < 70 ? '#ff9900' : '#ff0000');
                    }

                    // Incident logic and evidence display
                    if (data.snapshot) {
                        let snapshotData = data.snapshot;
                        if (typeof snapshotData === 'string' && snapshotData.startsWith('data:image')) {
                            // already includes data URI prefix
                        } else if (typeof snapshotData === 'string') {
                            snapshotData = `data:image/jpeg;base64,${snapshotData}`;
                        } else {
                            snapshotData = null;
                        }

                        if (snapshotData) {
                            setEvidencePhoto(snapshotData);
                            addLog(`EVIDENCE UPDATED: ${data.title || 'Detection recorded'}`);
                        }
                    }

                    if (data.level > 0) {
                        if (data.level >= 2 && !accidentPos && !hasRoutedRef.current) {
                            const loc = data.gps || cameraLocation;
                            setAccidentPos(loc);
                            const bestHospital = findNearestHospital(loc);
                            if (bestHospital) {
                                getRoute(loc, bestHospital.coords);
                                addLog(`ROUTING: ${bestHospital.name}`);
                                speakAlert(`Critical Alert. ${data.title}. Routing to nearest hospital.`);
                            }
                            hasRoutedRef.current = true;
                        }
                    } else if (data.level === 0 && hasRoutedRef.current) {
                        // Optional: Auto-reset routing flag if system goes normal
                        // hasRoutedRef.current = false; 
                    }

                } catch (err) { console.error(err); }
            };

            ws.onclose = () => {
                if(!stopped) {
                    setConnectionStatus("Reconnecting");
                    addLog("CONNECTION LOST: Attempting reconnect...");
                    setTimeout(connect, 2000);
                }
            };
        };

        connect();
        return () => { stopped = true; if(wsRef.current) wsRef.current.close(); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [addLog]);

    // --- API CALLS ---
    const postLaneUpdate = (east, south, west) => {
        if (sendTimeoutRef.current) clearTimeout(sendTimeoutRef.current);
        sendTimeoutRef.current = setTimeout(async () => {
            try {
                await fetch(`${API_URL}/update-lanes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ east: Number(east), south: Number(south), west: Number(west) })
                });
            } catch (err) { console.error(err); }
        }, 300);
    };

    const changeJunctionType = async (type) => {
        setJunctionType(type);
        try {
            await fetch(`${API_URL}/set-junction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ junction_type: type })
            });
            addLog(`CONFIG: Switched to ${type}-Way Intersection Mode`);
        } catch (e) { addLog("ERR: Failed to switch junction type"); }
    };

    const resetSystem = async () => {
        try {
            await fetch(`${API_URL}/reset-system`, { method: 'POST' });
            setAccidentPos(null);
            setRoutePolyline([]);
            setEvidencePhoto(null);
            setAlert(null);
            hasRoutedRef.current = false;
            addLog("CMD: SYSTEM RESET EXECUTED.");
        } catch(e) { console.error(e); }
    };

    // --- HELPERS ---
    const getRoute = useCallback(async (start, end) => {
        try {
            const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${start[1]},${start[0]};${end[1]},${end[0]}?overview=full&geometries=geojson`);
            const data = await response.json();
            if (data.routes?.[0]) {
                setRoutePolyline(data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]));
                setEta(`${Math.round(data.routes[0].duration / 60)} mins`);
            }
        } catch (e) { addLog("ERR: Routing Service Unavailable"); }
    }, [addLog]);

    const findNearestHospital = (coords) => {
        if (!coords) return null;
        let nearest = null, minDist = Infinity;
        HOSPITALS.forEach(h => {
            const dist = Math.sqrt(Math.pow(h.coords[0] - coords[0], 2) + Math.pow(h.coords[1] - coords[1], 2));
            if (dist < minDist) { minDist = dist; nearest = h; }
        });
        return nearest;
    };

    const handleMapClick = (e) => {
        if (!e.latlng) return;
        const newPos = [e.latlng.lat, e.latlng.lng];
        const startPos = cameraLocation || newPos;
        setAccidentPos(newPos);
        const best = findNearestHospital(newPos);
        if(best) getRoute(startPos, best.coords);
        addLog("MANUAL TRIGGER: Simulation Started.");
    };

    // --- RENDER HELPERS ---
    const getPercent = (val) => Math.min((val / 50) * 100, 100);
    const getColor = (pct) => pct < 40 ? '#00ff00' : pct < 70 ? '#ff9900' : '#ff0000';
    const overlayClass = alert?.level > 1 ? 'detection-overlay critical' : 'detection-overlay';

    return (
        <div className="dashboard-container" style={{ backgroundColor: alert?.incident_active ? '#1a0000' : '#050505' }}>
            
            <header className="header">
                <div style={{display: 'flex', alignItems: 'center'}}>
                    <div>
                        <h1 style={{margin: 0, fontSize: '1.2rem'}}>TRAFFIC COMMAND: INDIA GRID</h1>
                        <div style={{fontSize: '0.7rem', color: '#666'}}>VARUNA</div>
                    </div>
                </div>
                <div className="badges">
                    <span className="status-badge">{connectionStatus}</span>
                    {cameraLocation && <span className="conf-badge">GPS: {cameraLocation[0].toFixed(4)}, {cameraLocation[1].toFixed(4)}</span>}
                    {accidentPos && <span className="corridor-badge">GREEN CORRIDOR</span>}
                </div>
            </header>

            {/* ALGORITHM & JUNCTION CONTROL PANEL */}
            <div style={{ backgroundColor: '#111', borderBottom: '2px solid #333', padding: '10px', display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label style={{ color: '#ccc', fontSize: '0.9rem' }}>Algorithm:</label>
                    <select onChange={(e) => { 
                        fetch(`${API_URL}/set-algorithm`, { 
                            method: 'POST', 
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ algorithm: e.target.value })
                        }).catch(err => console.error(err));
                        addLog(`Algorithm: ${e.target.value}`);
                    }} style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}>
                        <option value="adaptive">Adaptive Timing</option>
                        <option value="zone">Zone Rotation</option>
                        <option value="weighted">Weighted Priority</option>
                    </select>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label style={{ color: '#ccc', fontSize: '0.9rem' }}>Junction Type:</label>
                    <select value={junctionType} onChange={(e) => setJunctionType(Number(e.target.value))} style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}>
                        <option value={2}>2-Way (T-Junction)</option>
                        <option value={3}>3-Way (Y-Junction)</option>
                        <option value={4}>4-Way (Standard Cross)</option>
                        <option value={5}>5-Way (Star Junction)</option>
                        <option value={6}>6-Way (Complex)</option>
                    </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ccc', fontSize: '0.85rem' }}>
                    <span>Status:</span>
                    <span style={{ color: '#00ff00' }}>{algorithmInfo?.active || 'Initializing...'}</span>
                    <span style={{ color: '#ffcc00' }}>({algorithmInfo?.incident_status || 'Normal'})</span>
                </div>
            </div>

            <div className="main-content">
                
                {/* LEFT PANEL: FEED & STATS */}
                <div className="panel left-panel">
                    <div className="panel-header">Live Feed & Analytics</div>
                    <div className="video-wrapper">
                        <img src={liveFrame || "https://via.placeholder.com/640x480/000000/FFFFFF?text=WAITING+FOR+STREAM"} className="camera-feed" alt="Live Feed" />
                        {alert?.level > 0 && <div className={overlayClass}></div>}
                    </div>
                    
                    <div className="stats-box">
                        <div className="stat-row">
                            <span>NORTH</span>
                            <div className="bar-container"><div className="bar" style={{ width: `${trafficLevel}%`, background: trafficColor }}></div></div>
                            <span>{Math.round(trafficLevel)}% (AI)</span>
                        </div>
                        {/* Dynamic Rendering for other lanes */}
                        {junctionType >= 3 && (
                            <div className="stat-row">
                                <span>EAST</span>
                                <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualEast)}%`, background: getColor(getPercent(manualEast)) }}></div></div>
                                <span>{manualEast}</span>
                            </div>
                        )}
                        {junctionType >= 2 && ( // South is usually the opposite lane in 2-way
                            <div className="stat-row">
                                <span>SOUTH</span>
                                <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualSouth)}%`, background: getColor(getPercent(manualSouth)) }}></div></div>
                                <span>{manualSouth}</span>
                            </div>
                        )}
                        {junctionType >= 4 && (
                            <div className="stat-row">
                                <span>WEST</span>
                                <div className="bar-container"><div className="bar" style={{ width: `${getPercent(manualWest)}%`, background: getColor(getPercent(manualWest)) }}></div></div>
                                <span>{manualWest}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* CENTER PANEL: MAP */}
                <div className="panel center-panel">
                    <div className="panel-header">Tactical Map</div>
                    {evidencePhoto ? (
                        <div className="evidence-container">
                            <img src={evidencePhoto} alt="Evidence" className="evidence-img" />
                            <div className="evidence-tag">EVIDENCE LOCKED</div>
                            <button className="btn blue" onClick={() => setEvidencePhoto(null)} style={{width: '200px', marginTop: '10px'}}>CLOSE FILE</button>
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
                            {accidentPos && <div className="route-overlay"><h4>DISPATCHED</h4><p>ETA: {eta}</p></div>}
                        </div>
                    )}
                </div>

                {/* RIGHT PANEL: LOGIC */}
                <div className="panel right-panel">
                    <div className="panel-header">System Logic</div>
                    
                    {/* ALGORITHM VISUALIZER */}
                    <div className="alert-card" style={{ borderColor: alert?.color || '#333' }}>
                        <h2 style={{ color: alert?.color || 'white' }}>{alert?.title || "SYSTEM NORMAL"}</h2>
                        
                        {/* ALGORITHM STATUS */}
                        <div style={{fontSize: '0.75rem', marginTop: '5px', color: '#00ff00'}}>
                            BRAIN: {algorithmInfo.active?.toUpperCase()}
                        </div>
                        
                        {/* LIVE TIMER BOX */}
                        {algorithmInfo.current_green_lane && (
                            <div style={{
                                marginTop: '10px',
                                padding: '8px',
                                background: 'rgba(0, 255, 0, 0.1)',
                                border: '1px solid #00ff00',
                                borderRadius: '4px'
                            }}>
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                    <span style={{fontSize: '0.8rem', color: '#aaa'}}>
                                        GREEN LANE: {algorithmInfo.current_green_lane?.toUpperCase()}
                                    </span>
                                    <span style={{
                                        fontSize: '1.2rem', 
                                        fontWeight: 'bold', 
                                        color: algorithmInfo.time_remaining < 5 ? '#ff9900' : '#00ff00',
                                        fontFamily: 'monospace'
                                    }}>
                                        {algorithmInfo.time_remaining}s
                                    </span>
                                </div>
                                <div style={{fontSize: '0.65rem', color: '#666', marginTop: '4px'}}>
                                    {algorithmInfo.reason || 'Calculating...'}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* EMERGENCY PLAYBOOK DISPLAY */}
                    {alert?.level > 0 && (
                        <div style={{
                            margin: '10px',
                            padding: '12px',
                            background: alert.level >= 3 ? 'rgba(255, 0, 0, 0.2)' : 'rgba(255, 153, 0, 0.2)',
                            border: `2px solid ${alert.color}`,
                            borderRadius: '6px',
                            animation: 'pulse 1.5s infinite'
                        }}>
                            <div style={{fontSize: '0.7rem', color: '#888', marginBottom: '5px'}}>
                                ACTIVE PLAYBOOK
                            </div>
                            
                            
                            
                            {alert.title === 'INCIDENT ACTIVE' && algorithmInfo.incident_status === 'Fire' && (
                                <div>
                                    <div style={{fontSize: '0.9rem', fontWeight: 'bold', color: '#ff3333'}}>
                                        EVACUATION MODE (Algorithm #4)
                                    </div>
                                    <div style={{fontSize: '0.65rem', color: '#ccc', marginTop: '3px'}}>
                                        - Fire lane BLOCKED<br/>
                                        - All safe lanes GREEN (5s cycles)<br/>
                                        - Maximize evacuation throughput
                                    </div>
                                </div>
                            )}
                            
                            {alert.title === 'INCIDENT ACTIVE' && algorithmInfo.incident_status === 'Accident' && (
                                <div>
                                    <div style={{fontSize: '0.9rem', fontWeight: 'bold', color: '#ff9900'}}>
                                        DIVERSION MODE (Algorithm #2)
                                    </div>
                                    <div style={{fontSize: '0.65rem', color: '#ccc', marginTop: '3px'}}>
                                        - Blocked lane: {algorithmInfo.current_green_lane || 'NORTH'}<br/>
                                        - Opposite lane prioritized (30s green)<br/>
                                        - Prevent pile-up congestion
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="action-log">
                        {logs.map((log, i) => <div key={i} className="log-entry">{log}</div>)}
                    </div>

                    <div className="manual-controls">
                        {/* JUNCTION SELECTOR */}
                        <div style={{marginBottom: '10px', display: 'flex', gap: '5px'}}>
                            {[2, 3, 4, 5, 6].map(type => (
                                <button key={type} 
                                    onClick={() => changeJunctionType(type)}
                                    style={{
                                        flex: 1, 
                                        background: junctionType === type ? '#00ff00' : '#222',
                                        color: junctionType === type ? '#000' : '#aaa',
                                        border: 'none',
                                        borderRadius: '4px',
                                        fontSize: '0.75rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >{type}-Way</button>
                            ))}
                        </div>

                        {/* SIGNAL GRID (Dynamic) */}
                        <div className="signal-grid" style={{
                            gridTemplateColumns: `repeat(${junctionType > 4 ? 3 : 2}, 1fr)`
                        }}>
                            {/* Automatically render all signals sent by backend */}
                            {Object.entries(signals).map(([lane, color]) => (
                                <div key={lane} className="signal-row" style={{
                                    background: color === 'green' ? 'rgba(0, 255, 0, 0.1)' : '#222',
                                    border: color === 'green' ? '1px solid #00ff00' : 'none'
                                }}>
                                    <span style={{
                                        fontWeight: color === 'green' ? 'bold' : 'normal',
                                        color: color === 'green' ? '#00ff00' : '#aaa'
                                    }}>
                                        {lane.charAt(0).toUpperCase() + lane.slice(1, 3)}
                                        {color === 'green' && algorithmInfo.time_remaining && (
                                            <span style={{marginLeft: '5px', fontSize: '0.7rem'}}>
                                                ({algorithmInfo.time_remaining}s)
                                            </span>
                                        )}
                                    </span>
                                    <div className={`light ${color}`}></div>
                                </div>
                            ))}
                        </div>

                        {/* SLIDERS (Conditional) */}
                        <div style={{fontSize: '0.7rem', color: '#666', marginBottom: '5px'}}>TRAFFIC LOAD</div>
                        
                        {junctionType >= 3 && (
                            <div className="control-group">
                                <div className="control-label"><span>East</span><span>{manualEast}</span></div>
                                <input type="range" min={0} max={50} value={manualEast} onChange={(e) => { const v = Number(e.target.value); setManualEast(v); postLaneUpdate(v, manualSouth, manualWest); }} />
                            </div>
                        )}
                        {junctionType >= 2 && (
                            <div className="control-group">
                                <div className="control-label"><span>South</span><span>{manualSouth}</span></div>
                                <input type="range" min={0} max={50} value={manualSouth} onChange={(e) => { const v = Number(e.target.value); setManualSouth(v); postLaneUpdate(manualEast, v, manualWest); }} />
                            </div>
                        )}
                        {junctionType >= 4 && (
                            <div className="control-group">
                                <div className="control-label"><span>West</span><span>{manualWest}</span></div>
                                <input type="range" min={0} max={50} value={manualWest} onChange={(e) => { const v = Number(e.target.value); setManualWest(v); postLaneUpdate(manualEast, manualSouth, v); }} />
                            </div>
                        )}

                        <button onClick={() => { const simPos = cameraLocation ? { latlng: { lat: cameraLocation[0], lng: cameraLocation[1] } } : { latlng: { lat: 15.45, lng: 75.01 } }; handleMapClick(simPos); }} className="btn red">SIMULATE CRASH</button>
                        <button onClick={resetSystem} className="btn blue">RESET SYSTEM</button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
