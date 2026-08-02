/**
 * AnalyticsTab.js — Feature 1: Analytics Dashboard
 *
 * Fetches data from /analytics and renders:
 *  - Summary stat cards (total detections, confirmed incidents, confirmation rate)
 *  - Bar chart: incidents by hour of day
 *  - Bar chart: incidents last 7 days
 *  - Recent incidents log table
 *
 * Uses recharts for all charts (no CDN, no extra setup).
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = {
    green: '#00ff00',
    red: '#ff3333',
    orange: '#ff9900',
    cyan: '#00e5ff',
    bg: '#111',
    panel: '#1a1a1a',
    border: '#333',
    text: '#ccc',
    dimText: '#666',
};

// Reusable stat card
function StatCard({ label, value, color, subtitle }) {
    return (
        <div style={{
            background: COLORS.panel,
            border: `1px solid ${color || COLORS.border}`,
            borderRadius: 6,
            padding: '16px 20px',
            minWidth: 150,
            flex: 1,
            boxShadow: color ? `0 0 12px ${color}33` : 'none',
        }}>
            <div style={{ fontSize: '0.7rem', color: COLORS.dimText, textTransform: 'uppercase', letterSpacing: 1 }}>
                {label}
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: color || COLORS.green, margin: '4px 0' }}>
                {value ?? '—'}
            </div>
            {subtitle && <div style={{ fontSize: '0.7rem', color: COLORS.dimText }}>{subtitle}</div>}
        </div>
    );
}

// Custom tooltip for charts
function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
        <div style={{
            background: '#0d0d0d',
            border: `1px solid ${COLORS.green}`,
            padding: '8px 12px',
            borderRadius: 4,
            fontSize: '0.75rem',
            color: COLORS.green
        }}>
            <div>{label}</div>
            <div>Count: <strong>{payload[0].value}</strong></div>
        </div>
    );
}

export default function AnalyticsTab({ apiUrl }) {
    const [data, setData] = useState(null);
    const [anprData, setAnprData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastRefresh, setLastRefresh] = useState(null);

    const fetchAnalytics = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            // Fetch analytics and ANPR log in parallel
            const [analyticsRes, anprRes] = await Promise.all([
                fetch(`${apiUrl}/analytics`),
                fetch(`${apiUrl}/anpr-log?limit=20`),
            ]);
            if (!analyticsRes.ok) throw new Error(`HTTP ${analyticsRes.status}`);
            const json = await analyticsRes.json();
            setData(json);
            if (anprRes.ok) {
                const anprJson = await anprRes.json();
                setAnprData(anprJson);
            }
            setLastRefresh(new Date().toLocaleTimeString());
        } catch (e) {
            setError(`Failed to load analytics: ${e.message}`);
        } finally {
            setLoading(false);
        }
    }, [apiUrl]);

    // Initial load + auto-refresh every 30 seconds
    useEffect(() => {
        fetchAnalytics();
        const interval = setInterval(fetchAnalytics, 30000);
        return () => clearInterval(interval);
    }, [fetchAnalytics]);

    // Transform by_hour object → array for recharts
    const hourData = data
        ? Array.from({ length: 24 }, (_, i) => ({
            hour: `${String(i).padStart(2, '0')}:00`,
            count: data.by_hour?.[String(i)] || 0,
        }))
        : [];

    // Transform by_day object → array
    const dayData = data
        ? Object.entries(data.by_day || {}).map(([day, count]) => ({
            day: day.slice(5), // MM-DD
            count,
        }))
        : [];

    // Pie chart data
    const pieData = data ? [
        { name: 'Accidents', value: data.confirmed_accidents || 0 },
        { name: 'Fires', value: data.confirmed_fires || 0 },
        {
            name: 'False Positives',
            value: Math.max(0, (data.total_detections || 0) - (data.total_confirmed || 0))
        },
    ].filter(d => d.value > 0) : [];

    const PIE_COLORS = [COLORS.orange, COLORS.red, COLORS.dimText];

    return (
        <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px',
            background: '#050505',
            fontFamily: "'Courier New', monospace",
            color: '#fff',
        }}>
            {/* Header row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                    <h2 style={{ margin: 0, color: COLORS.green, fontSize: '1rem', textTransform: 'uppercase', letterSpacing: 2 }}>
                        Analytics — Incident Intelligence
                    </h2>
                    {lastRefresh && (
                        <div style={{ fontSize: '0.65rem', color: COLORS.dimText, marginTop: 2 }}>
                            Last refreshed: {lastRefresh} · Auto-refreshes every 30s
                        </div>
                    )}
                </div>
                <button
                    onClick={fetchAnalytics}
                    disabled={loading}
                    style={{
                        background: 'transparent',
                        border: `1px solid ${COLORS.green}`,
                        color: COLORS.green,
                        padding: '6px 14px',
                        borderRadius: 4,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: '0.75rem',
                        opacity: loading ? 0.5 : 1,
                    }}
                >
                    {loading ? 'Loading...' : '↻ Refresh'}
                </button>
            </div>

            {/* Error state */}
            {error && (
                <div style={{
                    background: 'rgba(255,51,51,0.1)',
                    border: '1px solid #ff3333',
                    borderRadius: 6,
                    padding: '12px 16px',
                    color: '#ff3333',
                    fontSize: '0.8rem',
                    marginBottom: 16,
                }}>
                    {error}
                    <div style={{ fontSize: '0.7rem', color: COLORS.dimText, marginTop: 4 }}>
                        Make sure the backend is running and evidence_archive/ exists.
                    </div>
                </div>
            )}

            {/* Skeleton while loading */}
            {loading && !data && (
                <div style={{ textAlign: 'center', color: COLORS.dimText, padding: 40, fontSize: '0.85rem' }}>
                    Loading analytics data...
                </div>
            )}

            {data && (
                <>
                    {/* ── STAT CARDS ── */}
                    <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                        <StatCard
                            label="Total Detections"
                            value={data.total_detections}
                            color={COLORS.cyan}
                            subtitle="All frames with any detection"
                        />
                        <StatCard
                            label="Confirmed Accidents"
                            value={data.confirmed_accidents}
                            color={COLORS.orange}
                            subtitle="Saved in evidence_archive/severe"
                        />
                        <StatCard
                            label="Confirmed Fires"
                            value={data.confirmed_fires}
                            color={COLORS.red}
                            subtitle="Saved in evidence_archive/fire"
                        />
                        <StatCard
                            label="Confirmation Rate"
                            value={`${data.confirmation_rate}%`}
                            color={data.confirmation_rate > 20 ? COLORS.red : COLORS.green}
                            subtitle="Confirmed / Total detections"
                        />
                    </div>

                    {/* ── CHARTS ROW ── */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>

                        {/* Incidents by Hour */}
                        <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 16 }}>
                            <div style={{ fontSize: '0.75rem', color: COLORS.green, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
                                Detections by Hour of Day
                            </div>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={hourData} margin={{ top: 0, right: 8, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fontSize: 9, fill: COLORS.dimText }}
                                        interval={2}
                                    />
                                    <YAxis tick={{ fontSize: 10, fill: COLORS.dimText }} allowDecimals={false} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Bar dataKey="count" fill={COLORS.green} radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Incidents last 7 days */}
                        <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 16 }}>
                            <div style={{ fontSize: '0.75rem', color: COLORS.green, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
                                Detections — Last 7 Days
                            </div>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={dayData} margin={{ top: 0, right: 8, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: COLORS.dimText }} />
                                    <YAxis tick={{ fontSize: 10, fill: COLORS.dimText }} allowDecimals={false} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Bar dataKey="count" fill={COLORS.cyan} radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* ── PIE + RECENT INCIDENTS ROW ── */}
                    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16, marginBottom: 20 }}>

                        {/* Incident breakdown pie */}
                        <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 16 }}>
                            <div style={{ fontSize: '0.75rem', color: COLORS.green, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
                                Incident Breakdown
                            </div>
                            {pieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={180}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={45}
                                            outerRadius={75}
                                            paddingAngle={3}
                                            dataKey="value"
                                        >
                                            {pieData.map((_, index) => (
                                                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ background: '#0d0d0d', border: '1px solid #333', fontSize: '0.75rem' }}
                                            itemStyle={{ color: COLORS.green }}
                                        />
                                        <Legend
                                            iconSize={10}
                                            wrapperStyle={{ fontSize: '0.7rem', color: COLORS.text }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ textAlign: 'center', color: COLORS.dimText, fontSize: '0.75rem', padding: 40 }}>
                                    No confirmed incidents yet.
                                    <br />Run the system to collect data.
                                </div>
                            )}
                        </div>

                        {/* Recent incidents table */}
                        <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: 16 }}>
                            <div style={{ fontSize: '0.75rem', color: COLORS.green, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
                                Recent Confirmed Incidents
                            </div>
                            {data.recent_incidents?.length > 0 ? (
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                                    <thead>
                                        <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                                            {['#', 'Type', 'Date', 'Time', 'Evidence File'].map(h => (
                                                <th key={h} style={{
                                                    textAlign: 'left',
                                                    padding: '6px 10px',
                                                    color: COLORS.dimText,
                                                    fontWeight: 'normal',
                                                    textTransform: 'uppercase',
                                                    fontSize: '0.65rem',
                                                    letterSpacing: 1,
                                                }}>
                                                    {h}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.recent_incidents.map((inc, i) => (
                                            <tr
                                                key={i}
                                                style={{
                                                    borderBottom: `1px solid #1a1a1a`,
                                                    background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                                                }}
                                            >
                                                <td style={{ padding: '7px 10px', color: COLORS.dimText }}>{i + 1}</td>
                                                <td style={{ padding: '7px 10px' }}>
                                                    <span style={{
                                                        padding: '2px 8px',
                                                        borderRadius: 3,
                                                        fontSize: '0.65rem',
                                                        fontWeight: 'bold',
                                                        background: inc.type === 'Fire' ? 'rgba(255,51,51,0.2)' : 'rgba(255,153,0,0.2)',
                                                        color: inc.type === 'Fire' ? COLORS.red : COLORS.orange,
                                                        border: `1px solid ${inc.type === 'Fire' ? COLORS.red : COLORS.orange}`,
                                                    }}>
                                                        {inc.type.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '7px 10px', color: COLORS.text }}>{inc.date}</td>
                                                <td style={{ padding: '7px 10px', color: COLORS.text }}>{inc.time}</td>
                                                <td style={{ padding: '7px 10px', color: COLORS.dimText, fontSize: '0.65rem', fontFamily: 'monospace' }}>
                                                    {inc.file}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div style={{ color: COLORS.dimText, fontSize: '0.75rem', padding: 20 }}>
                                    No confirmed incidents in evidence archive yet.
                                </div>
                            )}
                        </div>
                    </div>
                    {/* ── ANPR PANEL ── */}
                    <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.cyan}22`, borderRadius: 6, padding: 16 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                            <div style={{ fontSize: '0.75rem', color: COLORS.cyan, textTransform: 'uppercase', letterSpacing: 1 }}>
                                ANPR — License Plate Log
                            </div>
                            {/* ANPR status pill */}
                            <span style={{
                                padding: '2px 10px',
                                borderRadius: 10,
                                fontSize: '0.65rem',
                                fontWeight: 'bold',
                                background: data.anpr_enabled ? 'rgba(0,229,255,0.15)' : 'rgba(100,100,100,0.2)',
                                color: data.anpr_enabled ? COLORS.cyan : COLORS.dimText,
                                border: `1px solid ${data.anpr_enabled ? COLORS.cyan : '#444'}`,
                            }}>
                                {data.anpr_enabled ? 'ACTIVE' : 'INACTIVE — run: pip install easyocr'}
                            </span>
                        </div>

                        {/* ANPR summary stats */}
                        {data.anpr && (
                            <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
                                <StatCard label="Total Plate Reads" value={data.anpr.total_reads} color={COLORS.cyan} />
                                <StatCard label="Unique Plates" value={data.anpr.unique_plates} color={COLORS.green} />
                                <StatCard label="Incident-linked" value={data.anpr.incident_plates} color={COLORS.orange}
                                    subtitle="Plates seen during incidents" />
                            </div>
                        )}

                        {/* Top plates */}
                        {data.anpr?.top_plates?.length > 0 && (
                            <div style={{ marginBottom: 14 }}>
                                <div style={{ fontSize: '0.65rem', color: COLORS.dimText, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                                    Most Seen Plates
                                </div>
                                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                    {data.anpr.top_plates.map((p, i) => (
                                        <div key={i} style={{
                                            background: '#0d0d0d',
                                            border: `1px solid ${COLORS.cyan}44`,
                                            borderRadius: 4,
                                            padding: '4px 12px',
                                            fontSize: '0.75rem',
                                            fontFamily: 'monospace',
                                            color: COLORS.cyan,
                                        }}>
                                            {p.plate} <span style={{ color: COLORS.dimText }}>×{p.count}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recent plate reads table */}
                        {anprData?.plates?.length > 0 ? (
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                                        {['Plate', 'Confidence', 'Incident', 'Timestamp'].map(h => (
                                            <th key={h} style={{
                                                textAlign: 'left', padding: '5px 10px',
                                                color: COLORS.dimText, fontWeight: 'normal',
                                                textTransform: 'uppercase', fontSize: '0.62rem', letterSpacing: 1,
                                            }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {anprData.plates.map((p, i) => (
                                        <tr key={i} style={{
                                            borderBottom: '1px solid #1a1a1a',
                                            background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                                        }}>
                                            <td style={{ padding: '6px 10px', fontFamily: 'monospace', color: COLORS.cyan, fontWeight: 'bold' }}>
                                                {p.plate_text}
                                            </td>
                                            <td style={{ padding: '6px 10px', color: p.confidence > 0.7 ? COLORS.green : COLORS.orange }}>
                                                {(p.confidence * 100).toFixed(0)}%
                                            </td>
                                            <td style={{ padding: '6px 10px' }}>
                                                {p.incident_type !== 'None' ? (
                                                    <span style={{
                                                        padding: '1px 7px', borderRadius: 3, fontSize: '0.62rem', fontWeight: 'bold',
                                                        background: 'rgba(255,51,51,0.2)', color: COLORS.red, border: `1px solid ${COLORS.red}`,
                                                    }}>{p.incident_type}</span>
                                                ) : (
                                                    <span style={{ color: COLORS.dimText }}>—</span>
                                                )}
                                            </td>
                                            <td style={{ padding: '6px 10px', color: COLORS.dimText, fontSize: '0.65rem' }}>
                                                {p.timestamp}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div style={{ color: COLORS.dimText, fontSize: '0.75rem', padding: '10px 0' }}>
                                {data.anpr_enabled
                                    ? 'No plates logged yet. Run the live feed to start collecting.'
                                    : 'Install EasyOCR to enable plate detection.'}
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
