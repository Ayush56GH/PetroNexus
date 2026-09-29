/**
 * PetroNexus Alert Center Controller (Section 30)
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadAlerts();
});

async function loadAlerts() {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const alerts = await PetroNexusAPI.getAlerts(activeId);
    renderAlerts(alerts);
  } catch (err) {
    console.error('Failed to load alerts:', err);
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsContainer');
  if (!container) return;

  if (!alerts.length) {
    container.innerHTML = '<div style="color: var(--pn-text-dim); padding: 2rem; text-align: center;">No active operational alerts for this well.</div>';
    return;
  }

  container.innerHTML = alerts.map(a => {
    const isAck = a.status === 'ACKNOWLEDGED';
    return `
      <div class="pn-card" style="border-left: 4px solid ${a.severity === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)'}; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-weight: 700; color: #fff; font-size: 0.95rem;">${a.title}</span>
          <div>
            <span class="pn-card-badge" style="background: ${a.severity === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)'}; color: #fff; margin-right: 0.5rem;">${a.severity}</span>
            <span class="pn-card-badge" style="background: ${isAck ? 'var(--pn-emerald-success)' : 'var(--pn-border-strong)'}; color: #fff;">${a.status}</span>
          </div>
        </div>
        <div style="font-size: 0.85rem; color: var(--pn-text-main); margin-bottom: 0.6rem; line-height: 1.45;">
          ${a.message}
        </div>
        <div style="font-size: 0.78rem; color: var(--pn-text-dim); margin-bottom: 0.75rem;">
          Depth: ${a.current_depth_m} m • Formation: ${a.formation_name} • Triggered: ${a.created_at}
          ${isAck ? ` • Acknowledged by: <b style="color: var(--pn-emerald-success);">${a.acknowledged_by}</b>` : ''}
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="viewAlertEvidence(${a.id})">
            View Evidence Trail
          </button>
          ${!isAck ? `
            <button class="pn-btn pn-btn-sm pn-btn-success" onclick="acknowledgeAlert(${a.id})">
              Acknowledge Alert
            </button>
          ` : ''}
          <button class="pn-btn pn-btn-sm" onclick="askAIAssistant('Why did PetroNexus generate alert: ${escapeHtml(a.title)}?')">
            Ask PetroNexus AI
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function acknowledgeAlert(alertId) {
  try {
    await PetroNexusAPI.acknowledgeAlert(alertId);
    await loadAlerts();
  } catch (err) {
    alert(`Failed to acknowledge: ${err.message}`);
  }
}

async function viewAlertEvidence(alertId) {
  try {
    const res = await PetroNexusAPI.getAlertEvidence(alertId);
    const modal = document.getElementById('globalModal');
    const title = document.getElementById('globalModalTitle');
    const body = document.getElementById('globalModalBody');
    if (!modal || !title || !body) return;

    title.textContent = `Alert Evidence Trail: ${res.title}`;
    body.innerHTML = `
      <div style="font-size: 0.85rem; color: var(--pn-text-muted); margin-bottom: 1rem;">
        This alert is deterministically grounded in verified offset well records within the active formation interval:
      </div>
      ${res.evidence_trail.map(ev => `
        <div style="background: var(--pn-bg-surface); border: 1px solid var(--pn-border-subtle); padding: 0.85rem; border-radius: 6px; margin-bottom: 0.75rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <b style="color: #fff; font-size: 0.9rem;">${ev.offset_well} (${ev.distance_km} km away)</b>
            <span style="color: var(--pn-cyan-primary); font-weight: 700; font-size: 0.8rem;">Correlation: ${Math.round(ev.correlation_factor * 100)}%</span>
          </div>
          <div style="font-size: 0.82rem; color: #fca5a5; margin-bottom: 0.4rem;">
            • ${ev.event_type} @ ${ev.event_depth_m} m MD (${ev.delta_depth_m > 0 ? `+${ev.delta_depth_m}m ahead` : `${Math.abs(ev.delta_depth_m)}m behind`})
          </div>
          <div style="font-size: 0.8rem; color: var(--pn-text-main); margin-bottom: 0.5rem; line-height: 1.4;">
            ${ev.narrative}
          </div>
          <div style="font-size: 0.75rem; color: var(--pn-text-dim); display: flex; justify-content: space-between;">
            <span>Document: <b style="color: #38bdf8;">${ev.document_citation}, ${ev.page_citation}</b></span>
            <a href="/documents.html" style="color: var(--pn-cyan-primary);">Open Source Page</a>
          </div>
        </div>
      `).join('')}
    `;
    modal.style.display = 'flex';
  } catch (err) {
    alert(`Failed to load evidence: ${err.message}`);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

window.acknowledgeAlert = acknowledgeAlert;
window.viewAlertEvidence = viewAlertEvidence;
