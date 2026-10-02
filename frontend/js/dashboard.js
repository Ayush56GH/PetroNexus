/**
 * PetroNexus Four-Panel Drilling Command Center Logic (Section 12 & 59)
 */

let mapInstance = null;
let activeWellMarker = null;
let radiusCircle = null;
let offsetMarkers = [];
let telemetryChart = null;
let ecdChart = null;
let wsConnection = null;
let currentWellData = null;

document.addEventListener('DOMContentLoaded', async () => {
  initWellSelector();
  initMap();
  initTelemetryCharts();
  await loadActiveWellDashboard();
  initWebSocket();
  initEventListeners();
});

// 1. Well Selector Initialization
async function initWellSelector() {
  const selector = document.getElementById('activeWellSelect');
  if (!selector) return;

  try {
    const wells = await PetroNexusAPI.getWells();
    selector.innerHTML = '';
    const activeId = PetroNexusAPI.getActiveWellId();

    wells.forEach(w => {
      const opt = document.createElement('option');
      opt.value = w.id;
      opt.textContent = `${w.well_name} (${w.current_formation || 'Formation-X'} @ ${w.current_depth_m}m)`;
      if (w.id === activeId) opt.selected = true;
      selector.appendChild(opt);
    });

    selector.addEventListener('change', async (e) => {
      const newId = parseInt(e.target.value, 10);
      PetroNexusAPI.setActiveWellId(newId);
      await PetroNexusAPI.activateWell(newId);
      // Reconnect WebSocket to new well
      initWebSocket();
      await loadActiveWellDashboard();
    });
  } catch (err) {
    console.error('Failed to load wells for selector:', err);
  }
}

// 2. Leaflet Map Initialization (Panel 1: Spatial Intelligence)
function initMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer || mapInstance) return;

  // Initialize Map centered at Duliajan Basin (Upper Assam)
  mapInstance = L.map('map', {
    zoomControl: true,
    attributionControl: false
  }).setView([27.3520, 95.3180], 12);

  // High-contrast dark cartographic tiles
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
  }).addTo(mapInstance);
}

// 3. Telemetry Chart.js Initialization (Panel 2: Live Drilling Telemetry)
function initTelemetryCharts() {
  const ctxTel = document.getElementById('telemetryChart');
  if (ctxTel && !telemetryChart) {
    telemetryChart = new Chart(ctxTel, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Torque (kN.m)',
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            data: [],
            borderWidth: 2,
            yAxisID: 'yTorque',
            tension: 0.3
          },
          {
            label: 'ROP (m/hr)',
            borderColor: '#0284c7',
            backgroundColor: 'rgba(2, 132, 199, 0.1)',
            data: [],
            borderWidth: 2,
            yAxisID: 'yROP',
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        scales: {
          x: { display: false },
          yTorque: {
            type: 'linear',
            position: 'left',
            min: 10,
            max: 30,
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#f59e0b', font: { size: 10 } }
          },
          yROP: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 35,
            grid: { drawOnChartArea: false },
            ticks: { color: '#0284c7', font: { size: 10 } }
          }
        },
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
        }
      }
    });
  }

  const ctxEcd = document.getElementById('ecdChart');
  if (ctxEcd && !ecdChart) {
    ecdChart = new Chart(ctxEcd, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'ECD (SG)',
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            data: [],
            borderWidth: 2,
            tension: 0.3
          },
          {
            label: 'Mud Weight (SG)',
            borderColor: '#10b981',
            borderDash: [5, 5],
            data: [],
            borderWidth: 1.5,
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        scales: {
          x: { display: false },
          y: {
            min: 1.15,
            max: 1.45,
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8', font: { size: 10 } }
          }
        },
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
        }
      }
    });
  }
}

// 4. Load & Populate Entire Dashboard
async function loadActiveWellDashboard() {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    // 1. Fetch Well Details & Profile
    const well = await PetroNexusAPI.getWellDetail(activeId);
    currentWellData = well;

    // Update Topbar
    document.getElementById('tbWellName').textContent = well.well_name;
    document.getElementById('tbDepth').textContent = `${well.current_depth_m} m`;
    document.getElementById('tbFormation').textContent = well.current_formation || 'Formation-X';

    // 2. Fetch Completeness
    const comp = await PetroNexusAPI.getCompleteness(activeId);
    document.getElementById('tbReadiness').textContent = `${comp.readiness_score}%`;
    const readinessBar = document.getElementById('tbReadinessBar');
    if (readinessBar) readinessBar.style.width = `${comp.readiness_score}%`;

    // 3. Fetch Active Alerts Count (SIH 26121 Section 50 & 51)
    try {
      const alertCountData = await PetroNexusAPI.getActiveAlertsCount(activeId);
      const tbAlertCount = document.getElementById('tbAlertCount');
      if (tbAlertCount && alertCountData) {
        tbAlertCount.textContent = alertCountData.active_alerts_count;
      }
    } catch (e) {
      console.warn('Could not fetch active alerts count:', e);
    }

    // 4. Fetch Full Offset Analysis
    const radiusSelect = document.getElementById('searchRadiusSelect');
    const radiusKm = radiusSelect ? parseFloat(radiusSelect.value) : 15.0;
    const lookaheadSelect = document.getElementById('lookaheadSelect');
    const lookaheadM = lookaheadSelect ? parseFloat(lookaheadSelect.value) : 100.0;

    const analysis = await PetroNexusAPI.runOffsetAnalysis({
      well_id: activeId,
      radius_km: radiusKm,
      current_depth: well.current_depth_m,
      formation: well.current_formation,
      lookahead_m: lookaheadM
    });

    // 5. Update Map with active well & offsets
    updateMapLayers(well, analysis.nearby_wells, radiusKm);

    // 6. Update Subsurface Memory Column (Panel 3)
    renderSubsurfaceMemory(well, analysis.historical_events);

    // 7. Update Proactive Advisor & Alerts (Panel 4)
    renderProactiveAdvisor(analysis);

    // 8. Update Offset Memory Cards
    renderOffsetMemoryCards(analysis.comparable_wells);

  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
}

// Update Map Layers
function updateMapLayers(activeWell, nearbyWells, radiusKm) {
  if (!mapInstance) return;

  // Clear existing offset markers
  offsetMarkers.forEach(m => mapInstance.removeLayer(m));
  offsetMarkers = [];
  if (activeWellMarker) mapInstance.removeLayer(activeWellMarker);
  if (radiusCircle) mapInstance.removeLayer(radiusCircle);

  const activeLatLng = [activeWell.latitude, activeWell.longitude];
  mapInstance.panTo(activeLatLng);

  // Search Radius Circle
  radiusCircle = L.circle(activeLatLng, {
    radius: radiusKm * 1000,
    color: '#0284c7',
    fillColor: '#0284c7',
    fillOpacity: 0.06,
    weight: 1.5,
    dashArray: '4, 6'
  }).addTo(mapInstance);

  // Active Well Marker (Pulsing Cyan Icon)
  const activeIcon = L.divIcon({
    className: 'pn-active-well-marker-icon',
    html: `<div style="width: 20px; height: 20px; background: #0284c7; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 0 16px #38bdf8; animation: pulse-live 1.5s infinite;"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
  activeWellMarker = L.marker(activeLatLng, { icon: activeIcon }).addTo(mapInstance);
  activeWellMarker.bindPopup(`
    <div style="font-size: 12px; line-height: 1.5;">
      <b style="color: #38bdf8; font-size: 13px;">${activeWell.well_name}</b> (ACTIVE WELL)<br/>
      <b>Formation:</b> ${activeWell.current_formation}<br/>
      <b>Current Depth:</b> ${activeWell.current_depth_m} m MD<br/>
      <b>Target Depth:</b> ${activeWell.target_depth_m} m<br/>
      <span style="color: #10b981; font-weight: 700;">eRTMAC LIVE</span>
    </div>
  `).openPopup();

  // Offset Markers
  nearbyWells.forEach(ow => {
    const isHazard = ow.mud_losses_count > 0;
    const markerColor = isHazard ? '#ef4444' : '#10b981';

    const offsetIcon = L.divIcon({
      className: 'pn-offset-marker-icon',
      html: `<div style="width: 14px; height: 14px; background: ${markerColor}; border: 1.5px solid #fff; border-radius: 50%; box-shadow: 0 0 8px ${markerColor};"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    const m = L.marker([ow.latitude, ow.longitude], { icon: offsetIcon }).addTo(mapInstance);
    m.bindPopup(`
      <div style="font-size: 12px; line-height: 1.5;">
        <b style="color: #fff; font-size: 13px;">${ow.well_name}</b> (Offset)<br/>
        <b>Distance:</b> ${ow.distance_km} km away<br/>
        <b>Formation:</b> ${ow.current_formation}<br/>
        <b>Historical Losses:</b> <span style="color: ${isHazard ? '#ef4444' : '#10b981'}; font-weight: 700;">${ow.mud_losses_count} documented</span><br/>
        <button class="pn-btn pn-btn-sm pn-btn-primary" style="margin-top: 6px; width: 100%;" onclick="openOffsetComparisonModal(${ow.id})">Compare with Active</button>
      </div>
    `);
    offsetMarkers.push(m);
  });
}

// Render Subsurface Memory (Panel 3: Vertical Formation & Event Pins)
function renderSubsurfaceMemory(activeWell, events) {
  const container = document.getElementById('subsurfaceMemoryColumn');
  if (!container) return;

  const currentDepth = activeWell.current_depth_m;
  const formations = [
    { name: 'Alluvium & Upper Clay', top: 0, bottom: 450, color: '#334155' },
    { name: 'Dhekiajuli Formation', top: 450, bottom: 1050, color: '#1e293b' },
    { name: 'Girujan Clay Formation', top: 1050, bottom: 1700, color: '#1e293b' },
    { name: 'Tipam Sandstone', top: 1700, bottom: 2400, color: '#0f2744' },
    { name: 'Formation-X', top: 2400, bottom: 2850, color: '#163558' },
    { name: 'Barail Arenaceous Unit', top: 2850, bottom: 3250, color: '#272044' },
    { name: 'Kopili Formation', top: 3250, bottom: 3600, color: '#1a1a2e' }
  ];

  let html = '';

  formations.forEach(f => {
    const isCurrent = currentDepth >= f.top && currentDepth <= f.bottom;
    const formEvents = events.filter(e => e.depth_md_m >= f.top && e.depth_md_m <= f.bottom);

    html += `
      <div class="pn-formation-block ${isCurrent ? 'active-formation' : ''}" style="border-left-color: ${isCurrent ? '#f59e0b' : '#0284c7'};">
        <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.85rem; color: #fff;">
          <span>${f.name}</span>
          <span style="font-family: var(--pn-font-mono); font-size: 0.75rem; color: var(--pn-text-dim);">${f.top}–${f.bottom} m</span>
        </div>
    `;

    // If active bit is inside this formation, show the Bit Marker!
    if (isCurrent) {
      html += `
        <div class="pn-active-bit-marker" id="liveBitMarker">
          <span>BIT POSITION:</span>
          <span id="bitMarkerDepth">${currentDepth} m MD</span>
          <span style="margin-left: auto; font-size: 0.7rem; color: #000;">DRILLING ADVANCE</span>
        </div>
      `;
    }

    // Render historical event pins in this formation
    if (formEvents.length > 0) {
      formEvents.slice(0, 4).forEach(ev => {
        const delta = roundDec(ev.depth_md_m - currentDepth, 1);
        const deltaStr = delta > 0 ? `+${delta} m ahead` : `${Math.abs(delta)} m behind`;
        const pinColor = ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)';
        const borderColor = ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? '#ef4444' : '#f59e0b';

        html += `
          <div class="pn-event-pin" style="background: ${pinColor}; border-color: ${borderColor}; cursor: pointer;" onclick="openEvidenceModalFromEvent('${escapeHtml(ev.well_name)}', '${escapeHtml(ev.event_type)}', ${ev.depth_md_m}, '${escapeHtml(ev.source)}')">
            <span style="font-weight: 700; color: #fff;">${ev.well_name}</span>
            <span>${ev.event_type} @ ${ev.depth_md_m} m</span>
            <span style="margin-left: auto; font-family: var(--pn-font-mono); font-size: 0.72rem; color: #cbd5e1;">[${deltaStr}]</span>
          </div>
        `;
      });
    }

    html += `</div>`;
  });

  container.innerHTML = html;
}

// Render Proactive Advisor (Panel 4)
function renderProactiveAdvisor(analysis) {
  const advisorContainer = document.getElementById('proactiveAdvisorContent');
  if (!advisorContainer) return;

  const attention = analysis.historical_attention;
  const hazards = analysis.lookahead_events;

  let badgeColor = attention.attention_level === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)';

  let html = `
    <div style="background: rgba(14, 21, 38, 0.7); border: 1px solid var(--pn-border-strong); border-radius: 6px; padding: 0.85rem; margin-bottom: 0.85rem;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
        <span style="font-weight: 700; font-size: 0.9rem; color: #fff;">HISTORICAL ATTENTION LEVEL</span>
        <span class="pn-card-badge" style="background: ${badgeColor}; color: #fff;">${attention.attention_level}</span>
      </div>
      <div style="font-size: 0.82rem; color: var(--pn-text-muted); line-height: 1.45; margin-bottom: 0.6rem;">
        ${attention.rationale}
      </div>
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="openDecisionTraceModal()">
          <i class="bi bi-diagram-3"></i> View Decision Trace
        </button>
        <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="openMitigationPlaybookModal()">
          <i class="bi bi-journal-text"></i> Mitigation Playbook
        </button>
        <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="openContextPackModal()">
          <i class="bi bi-file-earmark-pdf"></i> Generate Context Pack
        </button>
      </div>
    </div>
  `;

  // Look-Ahead corridor alerts
  if (hazards.length > 0) {
    html += `<div style="font-size: 0.78rem; font-weight: 700; color: var(--pn-text-dim); text-transform: uppercase; margin-bottom: 0.5rem;">Verified Look-Ahead Hazards (+150m)</div>`;
    hazards.slice(0, 3).forEach(h => {
      html += `
        <div class="pn-alert-item severity-${h.severity}">
          <div class="pn-alert-title">
            <span>${h.event_type} (${h.corridor_zone})</span>
            <span style="font-size: 0.72rem; color: #fca5a5; font-weight: 600;">${h.offset_well_name}</span>
          </div>
          <div class="pn-alert-desc">
            ${h.description}
          </div>
          <div class="pn-alert-actions">
            <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="openEvidenceModalFromLookahead('${escapeHtml(h.offset_well_name)}', '${escapeHtml(h.event_type)}', ${h.hazard_depth_md_m}, '${escapeHtml(h.source_citation)}', '${escapeHtml(h.historical_mitigation)}')">
              Why am I seeing this?
            </button>
            <span style="font-size: 0.72rem; color: var(--pn-text-dim); margin-left: auto;">${h.source_citation}</span>
          </div>
        </div>
      `;
    });
  } else {
    html += `<div style="font-size: 0.82rem; color: var(--pn-text-dim); padding: 1rem; text-align: center;">No high-severity hazards in lookahead corridor.</div>`;
  }

  advisorContainer.innerHTML = html;
}

// Render Offset Memory Cards (Section 46)
function renderOffsetMemoryCards(comparableWells) {
  const container = document.getElementById('offsetMemoryCardsContainer');
  if (!container) return;

  let html = '';
  comparableWells.slice(0, 4).forEach(cw => {
    const card = cw.memory_card;
    const badgeColor = cw.relevance_category === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)';
    html += `
      <div style="background: var(--pn-bg-surface); border: 1px solid var(--pn-border-subtle); border-radius: 6px; padding: 0.75rem; margin-bottom: 0.6rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
          <b style="color: #fff; font-size: 0.88rem;">${card.well_name}</b>
          <span style="font-size: 0.72rem; background: ${badgeColor}; color: #fff; padding: 0.15rem 0.4rem; border-radius: 3px; font-weight: 700;">${cw.relevance_category} (${cw.overall_relevance_pct}%)</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--pn-cyan-primary); margin-bottom: 0.3rem;">
          ${card.distance_km} km away • ${card.formation}
        </div>
        <div style="font-size: 0.78rem; color: var(--pn-text-muted); line-height: 1.35; margin-bottom: 0.4rem;">
          <b>Critical Depth:</b> ${card.critical_depth_m} m | <b>Events:</b> ${card.key_events_summary}<br/>
          <b>Lesson:</b> ${card.lesson}
        </div>
        <div style="font-size: 0.72rem; color: var(--pn-text-dim); display: flex; justify-content: space-between;">
          <span>Source: ${card.source}</span>
          <a href="#" style="color: var(--pn-cyan-primary);" onclick="openSourceCitation('${escapeHtml(card.source)}')">Open Source</a>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// 5. WebSocket Connection for Simulated eRTMAC & Real Data Replay (SIH 26121 Section 27, 68, 69)
let currentStreamMode = 'SIMULATOR';

function initWebSocket() {
  if (wsConnection) {
    wsConnection.close();
  }

  const activeId = PetroNexusAPI.getActiveWellId();
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const modeSel = document.getElementById('streamModeSelect');
  currentStreamMode = modeSel ? modeSel.value : 'SIMULATOR';

  const endpoint = currentStreamMode === 'REPLAY' ? `/ws/replay/${activeId}` : `/ws/drilling/${activeId}`;
  const wsUrl = `${protocol}//${window.location.host}${endpoint}`;

  wsConnection = new WebSocket(wsUrl);

  const tbErtmac = document.getElementById('tbErtmacStatus');

  wsConnection.onopen = () => {
    console.log(`Connected to WebSocket (${currentStreamMode}) for Well ${activeId}`);
    if (tbErtmac) {
      if (currentStreamMode === 'REPLAY') {
        tbErtmac.innerHTML = '<span class="pn-live-dot" style="background:#38bdf8;"></span> REPLAY READY';
        tbErtmac.style.background = 'rgba(2, 132, 199, 0.2)';
        tbErtmac.style.color = '#38bdf8';
        tbErtmac.style.borderColor = 'rgba(2, 132, 199, 0.4)';
      } else {
        tbErtmac.innerHTML = '<span class="pn-live-dot" style="background:#f59e0b;"></span> SIM STANDBY';
        tbErtmac.style.background = 'rgba(245, 158, 11, 0.2)';
        tbErtmac.style.color = '#fbbf24';
        tbErtmac.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      }
    }
  };

  wsConnection.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleLiveTelemetryTick(data);
  };

  wsConnection.onclose = () => {
    console.log('Telemetry WebSocket closed.');
    if (tbErtmac) {
      tbErtmac.innerHTML = '<span class="pn-live-dot" style="background:#94a3b8;"></span> STANDBY';
      tbErtmac.style.background = 'rgba(100, 116, 139, 0.2)';
      tbErtmac.style.color = '#94a3b8';
    }
  };
}

// Handle Real-Time Telemetry Tick
function handleLiveTelemetryTick(data) {
  const t = data.telemetry;
  if (!t) return;

  const tbErtmac = document.getElementById('tbErtmacStatus');
  if (tbErtmac && data.is_running) {
    if (currentStreamMode === 'REPLAY') {
      tbErtmac.innerHTML = '<span class="pn-live-dot" style="background:#38bdf8;"></span> REPLAYING REAL DATA';
      tbErtmac.style.background = 'rgba(2, 132, 199, 0.25)';
      tbErtmac.style.color = '#38bdf8';
    } else {
      tbErtmac.innerHTML = '<span class="pn-live-dot" style="background:#10b981;"></span> SIMULATING eRTMAC';
      tbErtmac.style.background = 'rgba(16, 185, 129, 0.2)';
      tbErtmac.style.color = '#34d399';
    }
  }

  // Update Digital Gauges
  setGauge('gDepth', `${(t.depth || t.depth_md || 0).toFixed(1)} m`);
  setGauge('gRop', `${(t.rop || 0).toFixed(1)} m/hr`);
  setGauge('gWob', `${(t.wob || 0).toFixed(1)} t`);
  setGauge('gRpm', `${Math.round(t.rpm || 0)}`);
  setGauge('gTorque', `${(t.torque || 0).toFixed(1)} kN.m`);
  setGauge('gEcd', `${(t.ecd || 1.25).toFixed(3)} SG`);
  setGauge('gMw', `${(t.mud_weight || 1.20).toFixed(2)} SG`);
  setGauge('gSpp', `${Math.round(t.spp || 0)} psi`);
  setGauge('gFlow', `${Math.round(t.flow_rate || t.flow_in || 0)} lpm`);
  setGauge('gMse', t.mse ? `${t.mse.toFixed(1)} MPa` : 'N/A');

  // Update Topbar Depth & Bit Position in Subsurface column
  const curDepth = (t.depth || t.depth_md || 0).toFixed(1);
  const tbDepth = document.getElementById('tbDepth');
  if (tbDepth) tbDepth.textContent = `${curDepth} m`;

  const bitMarkerDepth = document.getElementById('bitMarkerDepth');
  if (bitMarkerDepth) bitMarkerDepth.textContent = `${curDepth} m MD`;

  // Update Rolling Charts
  if (telemetryChart) {
    const timeLabel = (t.timestamp || '').split(' ')[1] || (t.timestamp || '').substring(11, 19) || '';
    if (telemetryChart.data.labels.length > 20) {
      telemetryChart.data.labels.shift();
      telemetryChart.data.datasets[0].data.shift();
      telemetryChart.data.datasets[1].data.shift();
    }
    telemetryChart.data.labels.push(timeLabel);
    telemetryChart.data.datasets[0].data.push(t.torque || 0);
    telemetryChart.data.datasets[1].data.push(t.rop || 0);
    telemetryChart.update();
  }

  if (ecdChart) {
    const timeLabel = (t.timestamp || '').split(' ')[1] || (t.timestamp || '').substring(11, 19) || '';
    if (ecdChart.data.labels.length > 20) {
      ecdChart.data.labels.shift();
      ecdChart.data.datasets[0].data.shift();
      ecdChart.data.datasets[1].data.shift();
    }
    ecdChart.data.labels.push(timeLabel);
    ecdChart.data.datasets[0].data.push(t.ecd || 1.25);
    ecdChart.data.datasets[1].data.push(t.mud_weight || 1.20);
    ecdChart.update();
  }

  // Handle Real-Time Anomaly Notifications
  const anomalyContainer = document.getElementById('liveAnomalyBanner');
  if (anomalyContainer) {
    const a = data.anomalies;
    if (a && a.has_anomaly) {
      anomalyContainer.style.display = 'block';
      anomalyContainer.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; font-weight: 700; color: #fff;">
          <span>⚠ REAL-TIME DRILLING ANOMALY: ${(a.anomaly_types || []).join(', ')}</span>
          <span style="font-size: 0.72rem; background: var(--pn-rose-danger); padding: 2px 6px; border-radius: 3px;">CRITICAL</span>
        </div>
        <div style="font-size: 0.78rem; color: #fee2e2; margin-top: 3px;">
          ${(a.details || []).join(' • ')}<br/>
          <b>Action:</b> ${(a.suggested_actions || []).join(' ')}
        </div>
      `;
    } else {
      anomalyContainer.style.display = 'none';
    }
  }

  // Update simulator button UI states
  const btnStart = document.getElementById('btnStartSim');
  const btnPause = document.getElementById('btnPauseSim');
  if (btnStart && btnPause) {
    if (data.is_running) {
      btnStart.style.opacity = '0.5';
      btnPause.style.opacity = '1';
    } else {
      btnStart.style.opacity = '1';
      btnPause.style.opacity = '0.5';
    }
  }
}

function setGauge(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// Telemetry & Simulator Control Listeners
function initEventListeners() {
  const streamMode = document.getElementById('streamModeSelect');
  if (streamMode) {
    streamMode.addEventListener('change', () => {
      initWebSocket();
    });
  }

  const speedSelect = document.getElementById('replaySpeedSelect');
  if (speedSelect) {
    speedSelect.addEventListener('change', () => {
      const spd = parseFloat(speedSelect.value);
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify({ command: 'SPEED', speed: spd }));
      }
    });
  }

  const btnStart = document.getElementById('btnStartSim');
  if (btnStart) {
    btnStart.addEventListener('click', () => {
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        const spd = speedSelect ? parseFloat(speedSelect.value) : 1.0;
        wsConnection.send(JSON.stringify({ command: 'START', speed: spd }));
      }
    });
  }

  const btnPause = document.getElementById('btnPauseSim');
  if (btnPause) {
    btnPause.addEventListener('click', () => {
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send('PAUSE');
      }
    });
  }

  const btnReset = document.getElementById('btnResetSim');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send('RESET');
      }
    });
  }

  // Radius change
  const radiusSelect = document.getElementById('searchRadiusSelect');
  if (radiusSelect) {
    radiusSelect.addEventListener('change', () => loadActiveWellDashboard());
  }

  // Lookahead change
  const lookaheadSelect = document.getElementById('lookaheadSelect');
  if (lookaheadSelect) {
    lookaheadSelect.addEventListener('change', () => loadActiveWellDashboard());
  }
}

// Modal Viewers
function openEvidenceModalFromLookahead(well, eventType, depth, source, mitigation) {
  const modal = document.getElementById('globalModal');
  const title = document.getElementById('globalModalTitle');
  const body = document.getElementById('globalModalBody');
  if (!modal || !title || !body) return;

  title.textContent = `Evidence Trail: ${well} ${eventType}`;
  body.innerHTML = `
    <div style="background: var(--pn-bg-surface); padding: 1rem; border-radius: 6px; border: 1px solid var(--pn-border-subtle); margin-bottom: 1rem;">
      <h6 style="color: var(--pn-cyan-primary); margin-bottom: 0.5rem;">Why PetroNexus Flagged This Upcoming Hazard</h6>
      <p style="font-size: 0.85rem; color: var(--pn-text-main); margin-bottom: 0.5rem;">
        <b>Offset Well:</b> ${well} (Technically Comparable Development Directional Well)<br/>
        <b>Hazard Event:</b> ${eventType} at <b>${depth} m MD</b><br/>
        <b>Distance Ahead:</b> Within upcoming look-ahead corridor interval<br/>
        <b>Verified Source Citation:</b> <span style="color: #38bdf8; font-weight: 700;">${source}</span>
      </p>
      <hr style="border-color: var(--pn-border-subtle);"/>
      <h6 style="color: #fff; margin-bottom: 0.3rem;">Observed Historical Mitigation:</h6>
      <p style="font-size: 0.82rem; color: var(--pn-text-muted);">
        ${mitigation}
      </p>
    </div>
    <div style="display: flex; justify-content: flex-end; gap: 0.5rem;">
      <button class="pn-btn pn-btn-primary" onclick="openSourceCitation('${source}')">View Document Source Page</button>
      <button class="pn-btn" onclick="askAIAssistant('Tell me more about the ${eventType} in ${well} at ${depth}m and recommended prevention')">Ask AI Assistant</button>
    </div>
  `;
  modal.style.display = 'flex';
}

function openEvidenceModalFromEvent(well, eventType, depth, source) {
  openEvidenceModalFromLookahead(well, eventType, depth, source, 'Pumped LCM pill and controlled circulation flow rate until returns stabilized.');
}

function openDecisionTraceModal() {
  const modal = document.getElementById('globalModal');
  const title = document.getElementById('globalModalTitle');
  const body = document.getElementById('globalModalBody');
  if (!modal || !title || !body) return;

  title.textContent = 'PetroNexus Decision Trace: Explainable Reasoning Path';
  body.innerHTML = `
    <div style="font-size: 0.85rem; color: var(--pn-text-muted); margin-bottom: 1rem;">
      This decision trace reveals the deterministic logic step-by-step from raw telemetry to proactive alert generation:
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">1</div>
      <div>
        <b style="color: #fff;">Bit Context Ingestion</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-text-muted);">Active well OIL-DEMO-023 advancing at 2846m MD in Formation-X.</span>
      </div>
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">2</div>
      <div>
        <b style="color: #fff;">Spatial Boundary Query</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-text-muted);">Found 24 offset wells within active 15 km search radius in Duliajan Basin.</span>
      </div>
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">3</div>
      <div>
        <b style="color: #fff;">Technical Comparability Filter</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-text-muted);">Filtered to 4 technically comparable wells (OIL-DEMO-018, 021, 011, 007) based on formation, depth, trajectory, and drilling parameters.</span>
      </div>
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">4</div>
      <div>
        <b style="color: #fff;">Subsurface Memory Correlation</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-text-muted);">Found 4 historical operational events (3 Mud Losses, 1 Severe Torque Spike) in Formation-X interval.</span>
      </div>
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">5</div>
      <div>
        <b style="color: #fff;">Look-Ahead Corridor Scan</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-text-muted);">Identified that 2860m (Mud Loss in OIL-DEMO-018) is only 14m ahead of the active bit.</span>
      </div>
    </div>
    <div class="pn-trace-step">
      <div class="pn-trace-node">6</div>
      <div>
        <b style="color: #fff;">Deterministic Engineering Alert</b><br/>
        <span style="font-size: 0.8rem; color: var(--pn-rose-danger);">Generated HIGH Historical Attention Advisory with verified citations to WCR-018 Page 37.</span>
      </div>
    </div>
  `;
  modal.style.display = 'flex';
}

function openMitigationPlaybookModal() {
  const modal = document.getElementById('globalModal');
  const title = document.getElementById('globalModalTitle');
  const body = document.getElementById('globalModalBody');
  if (!modal || !title || !body) return;

  title.textContent = 'Historical Mitigation Playbook: Formation-X';
  body.innerHTML = `
    <div style="background: rgba(2, 132, 199, 0.08); border: 1px solid var(--pn-cyan-primary); border-radius: 6px; padding: 0.75rem; font-size: 0.82rem; margin-bottom: 1rem;">
      <b>Engineering Protocol:</b> Documented mitigations successfully executed by Oil India Limited in offset wells under comparable conditions.
      <i>Final decisions remain with drilling supervisors.</i>
    </div>
    <div style="margin-bottom: 1rem; border-left: 3px solid #0284c7; padding-left: 0.75rem;">
      <b style="color: #fff;">1. Loss Circulation Treatment (LCM Pill & Throttling)</b><br/>
      <span style="font-size: 0.82rem; color: var(--pn-text-muted);">
        <b>Procedure:</b> Pick bit to 2845m. Spot 30 bbl medium LCM pill (25 ppb walnut shells + 15 ppb CaCO3). Soak for 90 mins under static conditions. Resume drilling with flow throttled to 1950 LPM.<br/>
        <b>Observed Efficacy:</b> High (Circulation restored in 4.5 hrs) • <b>Citations:</b> WCR-018 Page 37, Mud Report-011 Page 15
      </span>
    </div>
    <div style="margin-bottom: 1rem; border-left: 3px solid #f59e0b; padding-left: 0.75rem;">
      <b style="color: #fff;">2. String Reciprocation & Reaming Sweep Procedure</b><br/>
      <span style="font-size: 0.82rem; color: var(--pn-text-muted);">
        <b>Procedure:</b> Pick up to casing shoe (2150m). Pump 25 bbl high-viscosity pill (45 sec funnel viscosity). Ream tight spot with 80 RPM to clear cuttings bed.<br/>
        <b>Observed Efficacy:</b> High (Overpull eliminated in 3 hrs) • <b>Citations:</b> DDR-021 Page 22
      </span>
    </div>
  `;
  modal.style.display = 'flex';
}

function openContextPackModal() {
  window.location.href = '/reports.html';
}

function openSourceCitation(sourceStr) {
  window.location.href = '/documents.html';
}

function askAIAssistant(promptText) {
  sessionStorage.setItem('petronexus_prefilled_ai_prompt', promptText);
  window.location.href = '/assistant.html';
}

function closeGlobalModal() {
  const modal = document.getElementById('globalModal');
  if (modal) modal.style.display = 'none';
}

// Helpers
function roundDec(num, dec) {
  return Number(Math.round(num + 'e' + dec) + 'e-' + dec);
}
function escapeHtml(text) {
  if (!text) return '';
  return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

window.closeGlobalModal = closeGlobalModal;
window.openEvidenceModalFromLookahead = openEvidenceModalFromLookahead;
window.openEvidenceModalFromEvent = openEvidenceModalFromEvent;
window.openDecisionTraceModal = openDecisionTraceModal;
window.openMitigationPlaybookModal = openMitigationPlaybookModal;
window.openContextPackModal = openContextPackModal;
window.openSourceCitation = openSourceCitation;
window.askAIAssistant = askAIAssistant;
