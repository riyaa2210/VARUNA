import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

// --- CONFIGURATION ---
// ⚠️ UPDATE WITH YOUR IP ADDRESS
const CAMERA_URL = "http://10.149.88.192:8080/video"; 
const SERVER_SOCKET_URL = "ws://localhost:8000/ws"; 

// --- GEOLOCATION CONFIG (DHARWAD) ---
const HOSPITAL_POS = [15.4246, 75.0344]; // SDM College of Medical Sciences
const DEFAULT_CENTER = [15.4589, 75.0078]; // Dharwad City Center

// --- LEAFLET ICON FIXES ---
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Map Icons
const crashIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/10309/10309166.png', // Alert Icon
    iconSize: [40, 40],
    popupAnchor: [0, -20]
});

const hospitalIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/4320/4320371.png', // Hospital Icon
    iconSize: [40, 40],
    popupAnchor: [0, -20]
});

// --- HELPER COMPONENTS ---
function LocationMarker({ handleMapClick }) {
    useMap().on('click', (e) => {
        handleMapClick(e);
    });
    return null;
}

function App() {
    // State Management
    const [alert, setAlert] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnected 🔴");
    const [accidentPos, setAccidentPos] = useState(null);
    const [routePolyline, setRoutePolyline] = useState([]);
    const [eta, setEta] = useState("0 mins");
    const [evidencePhoto, setEvidencePhoto] = useState(null);
    const [logs, setLogs] = useState([]);
    
    // Traffic Stats State
    const [trafficLevel, setTrafficLevel] = useState(0); // 0 to 100%
    const [trafficColor, setTrafficColor] = useState('green');

    // Refs for preventing duplicate routes
    const hasRoutedRef = useRef(false);

    // --- LOGGING SYSTEM ---
    const addLog = (msg) => {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        setLogs(prev => [`[${time}] ${msg}`, ...prev.slice(0, 7)]);
    };

    // --- WEBSOCKET CONNECTION ---
    useEffect(() => {
        let ws = new WebSocket(SERVER_SOCKET_URL);
        
        ws.onopen = () => {
            setConnectionStatus("Connected 🟢");
            addLog("SYSTEM ONLINE: Connected to AI Brain.");
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setAlert(data);
                
                // 1. Update Traffic Visualization (Real-time from Backend)
                if (data.car_count !== undefined) {
                    // Assume 20 cars = 100% congestion for this junction
                    const percentage = Math.min((data.car_count / 20) * 100, 100);
                    setTrafficLevel(percentage);
                    
                    if (percentage < 30) setTrafficColor('#4caf50'); // Green
                    else if (percentage < 60) setTrafficColor('#ff9800'); // Orange
                    else setTrafficColor('#f44336'); // Red
                }

                // 2. Handle Incident Logic
                if (data.level > 0) {
                    // Snapshot Evidence Handling
                    if (data.snapshot) {
                        setEvidencePhoto(data.snapshot);
                        addLog(`📸 EVIDENCE LOCKED: ${data.title}`);
                    }

                    // Auto-Routing Trigger (Level 2/3)
                    if (data.level >= 2 && !accidentPos && !hasRoutedRef.current) {
                        const simulatedCrash = [15.45, 75.01]; // Demo Location
                        setAccidentPos(simulatedCrash);
                        getRoute(simulatedCrash, HOSPITAL_POS);
                        addLog(`🚨 CRITICAL ALERT: Green Corridor Activated.`);
                        hasRoutedRef.current = true;
                    }
                }
            } catch (err) {
                console.error("Data Parsing Error:", err);
            }
        };

        ws.onclose = () => {
            setConnectionStatus("Disconnected 🔴");
            // Optional: Auto-reconnect logic could go here
        };

        return () => ws.close();
    }, [accidentPos]);

    // --- OSRM ROUTING SERVICE ---
    const getRoute = async (start, end) => {
        // OSRM uses Lon,Lat format
        const url = `https://router.project-osrm.org/route/v1/driving/${start[1]},${start[0]};${end[1]},${end[0]}?overview=full&geometries=geojson`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.routes && data.routes.length > 0) {
                const coords = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
                setRoutePolyline(coords);
                const durationMins = Math.round(data.routes[0].duration / 60);
                setEta(`${durationMins} mins`);
            }
        } catch (error) {
            console.error("Routing Service Error:", error);
            addLog("⚠️ Routing Service Unavailable (Network Error)");
        }
    };

    // --- MANUAL CONTROLS ---
    const handleMapClick = (e) => {
        if (!e.latlng) return;
        const newPos = [e.latlng.lat, e.latlng.lng];
        setAccidentPos(newPos);
        getRoute(newPos, HOSPITAL_POS);
        addLog("📍 Manual Incident Marker Placed.");
    };

    const resetSystem = () => {
        setAccidentPos(null);
        setRoutePolyline([]);
        setEvidencePhoto(null);
        setAlert(null);
        setTrafficLevel(0);
        hasRoutedRef.current = false;
        addLog("🔄 System Reset. Scanning...");
    };

    // --- RENDER ---
    return (
        <div className="dashboard-container" style={{ backgroundColor: alert?.level > 1 ? '#1a0000' : '#050505' }}>
            
            {/* HEADER */}
            <header className="header">
                <div style={{display: 'flex', alignItems: 'center'}}>
                    <span style={{fontSize: '1.5rem', marginRight: '10px'}}>🛡️</span>
                    <div>
                        <h1 style={{margin: 0, fontSize: '1.2rem'}}>DHARWAD SMART TRAFFIC COMMAND</h1>
                        <div style={{fontSize: '0.7rem', color: '#666'}}>TEAM CODING_NEXUS | SIH 2025</div>
                    </div>
                </div>
                <div className="badges">
                    <span className="status-badge">{connectionStatus}</span>
                    {alert?.confidence && <span className="conf-badge">AI CONFIDENCE: {alert.confidence}</span>}
                    {accidentPos && <span className="corridor-badge">🟢 GREEN CORRIDOR ACTIVE</span>}
                </div>
            </header>

            <div className="main-content">
                
                {/* LEFT PANEL: LIVE MONITORING */}
                <div className="panel left-panel">
                    <div className="panel-header">📍 Live Junction Feed</div>
                    <div className="video-wrapper">
                        <img 
                            src={CAMERA_URL} 
                            className="camera-feed" 
                            alt="Live Feed" 
                            onError={(e) => {
                                e.target.onerror = null; 
                                e.target.src = "https://via.placeholder.com/640x480/000000/FFFFFF?text=WAITING+FOR+CAMERA...";
                            }} 
                        />
                        {alert?.level > 0 && <div className="detection-overlay" style={{borderColor: alert.color}}></div>}
                    </div>
                    
                    {/* DYNAMIC TRAFFIC STATS */}
                    <div className="stats-box">
                        <h3>🚦 Traffic Density Analysis</h3>
                        
                        <div className="stat-row">
                            <span>North Lane:</span>
                            <div className="bar-container">
                                <div 
                                    className="bar" 
                                    role="progressbar"
                                    aria-label="North Lane congestion"
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    aria-valuenow={Math.round(trafficLevel)}
                                    style={{ width: `${trafficLevel}%`, background: trafficColor }}
                                >
                                    <span className="sr-only">{Math.round(trafficLevel)} percent</span>
                                </div>
                            </div>
                            <span style={{width: '40px', textAlign: 'right'}}>{Math.round(trafficLevel)}%</span>
                        </div>

                        <div className="stat-row">
                            <span>East Lane:</span>
                            <div className="bar-container">
                                <div 
                                    className="bar" 
                                    role="progressbar"
                                    aria-label="East Lane congestion"
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    aria-valuenow={15}
                                    style={{width: '15%', background: '#4caf50'}}
                                >
                                    <span className="sr-only">15 percent</span>
                                </div>
                            </div>
                            <span style={{width: '40px', textAlign: 'right'}}>15%</span>
                        </div>
                        
                        <div className="stat-desc">
                            {trafficLevel > 60 
                                ? "High Congestion Detected. Action: Extending Green Signal." 
                                : "Traffic Flow Normal. Standard Signal Timing."}
                        </div>
                    </div>
                </div>

                {/* CENTER PANEL: MAP & EVIDENCE */}
                <div className="panel center-panel">
                    <div className="panel-header">🗺️ Tactical Operations Map</div>
                    
                    {evidencePhoto ? (
                        <div className="evidence-container">
                            <img 
                                src={`data:image/jpeg;base64,${evidencePhoto}`} 
                                alt="Evidence" 
                                className="evidence-img" 
                            />
                            <div className="evidence-tag">
                                📸 EVIDENCE LOCKER: CRASH RECORDED
                            </div>
                            <button className="btn blue" onClick={() => setEvidencePhoto(null)} style={{marginTop: '20px', width: '200px'}}>
                                Return to Map
                            </button>
                        </div>
                    ) : (
                        <div className="map-wrapper">
                            <MapContainer center={DEFAULT_CENTER} zoom={14} style={{ height: "100%", width: "100%" }}>
                                <TileLayer
                                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                    attribution='&copy; CartoDB'
                                />
                                <LocationMarker handleMapClick={handleMapClick} />
                                
                                {/* Hospital Marker */}
                                <Marker position={HOSPITAL_POS} icon={hospitalIcon}>
                                    <Popup>SDM Hospital (Trauma Center)</Popup>
                                </Marker>

                                {/* Accident Marker */}
                                {accidentPos && (
                                    <Marker position={accidentPos} icon={crashIcon}>
                                        <Popup>INCIDENT DETECTED</Popup>
                                    </Marker>
                                )}

                                {/* Route Line */}
                                {routePolyline.length > 0 && (
                                    <Polyline positions={routePolyline} color="#00ff00" weight={6} opacity={0.8} dashArray="10, 10" />
                                )}
                            </MapContainer>
                            
                            {accidentPos && (
                                <div className="route-overlay">
                                    <h4>🚑 Ambulance Dispatched</h4>
                                    <p><strong>Destination:</strong> SDM Hospital</p>
                                    <p><strong>ETA:</strong> {eta} (Green Corridor Active)</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* RIGHT PANEL: LOGS & CONTROLS */}
                <div className="panel right-panel">
                    <div className="panel-header">⚠️ Incident Log</div>
                    
                    {/* Alert Banner */}
                    <div 
                        className="alert-card" 
                        style={{ borderColor: alert?.color || '#333' }}
                        role="status"
                        aria-live={alert?.level > 1 ? "assertive" : "polite"}
                        aria-atomic="true"
                    >
                        <h2 style={{ color: alert?.color || 'white' }}>
                            {alert?.title || "SYSTEM NORMAL"}
                        </h2>
                        <p>{alert?.message || "Scanning Traffic..."}</p>
                    </div>
                    
                    {/* Logs */}
                    <div className="action-log" role="log" aria-live="polite" aria-atomic="false">
                        {logs.map((log, i) => (
                            <div key={i} className="log-entry">{log}</div>
                        ))}
                        {logs.length === 0 && <div style={{textAlign: 'center', color: '#555', marginTop: '20px'}}>No recent logs...</div>}
                    </div>

                    {/* Controls */}
                    <div className="manual-controls">
                        <p style={{fontSize: '0.8rem', color: '#888'}}>COMMAND CENTER CONTROLS</p>
                        <button 
                            onClick={() => {
                                const simulatedPos = { latlng: { lat: 15.45, lng: 75.01 } };
                                handleMapClick(simulatedPos);
                            }} 
                            className="btn red"
                        >
                            TRIGGER SIMULATION
                        </button>
                        <button onClick={resetSystem} className="btn blue">
                            RESET SYSTEM
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}

export default App;