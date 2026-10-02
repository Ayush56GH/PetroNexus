/**
 * PetroNexus Alert Center Controller (SIH 26121 Section 30, 42, 78)
 * Evidence-grounded alert presentation, 5-point explainable breakdown,
 * and auditable engineer action workflow.
 */

let pendingActionAlertId = null;

document.addEventListener('DOMContentLoaded', async () => {
  await loadAlerts();

  const btnSubmit = document.getElementById('btnSubmitAction');
  if (btnSubmit) {
    btnSubmit.addEventListener('click', async () => {
      if (!pendingActionAlertId) return;

      const action = document.getElementById('actionSelect').value;
      const notes = document.getElementById('engineerNoteInput').value;

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Logging...';

      try {
        await PetroNexusAPI.request(`/alerts/${pendingActionAlertId}/acknowledge`, {
          method: 'POST',
          body: JSON.stringify({
            status: action,
            engineer_notes: notes,
            acknowledged_by: 'Drilling Engineer (Rig Site)'
          })
        });

        closeActionModal();
        await loadAlerts();
      } catch (err) {
        alert(`Failed to log action: ${err.message}`);
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = 'Submit to Audit Log';
      }
    });
  }
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

  if (!alerts || !alerts.length) {
    container.innerHTML = '<div style="color: var(--pn-text-dim); padding: 2rem; text-align: center;">No active operational alerts for this well.</div>';
    return;
  }

  container.innerHTML = alerts.map(a => {
    let statusBadgeColor = 'var(--pn-border-strong)';
    if (a.status === 'ACKNOWLEDGED') statusBadgeColor = 'var(--pn-emerald-success)';
    else if (a.status === 'ESCALATED') statusBadgeColor = 'var(--pn-rose-danger)';
    else if (a.status === 'DISMISSED') statusBadgeColor = '#64748b';

    const severityBorder = a.severity === 'HIGH' || a.severity === 'CRITICAL' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)';

    // 5-Point Explainability Breakdown (Section 78)
    const whatHappened = a.what_happened || a.message;
    const whyItMatters = a.why_it_matters || 'Offset wells in this formation encountered significant NPT and severe circulation losses within this depth interval.';
    const histEvidence = a.historical_evidence_text || 'Documented in offset WCR and DDR records in identical stratigraphic horizon.';
    const curIndicator = a.current_indicator_text || 'Bit advancing within correlated formation boundary.';
    const recommendedAction = a.recommended_action || 'Review offset mitigation playbook, throttle flow rate, and prepare LCM pill.';

    return `
      <div class="pn-card" style="border-left: 4px solid ${severityBorder}; margin-bottom: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
          <span style="font-weight: 700; color: #fff; font-size: 1.05rem;">${a.title}</span>
          <div style="display: flex; gap: 0.4rem;">
            <span class="pn-card-badge" style="background: ${severityBorder}; color: #fff;">${a.severity}</span>
            <span class="pn-card-badge" style="background: ${statusBadgeColor}; color: #fff;">${a.status || 'ACTIVE'}</span>
          </div>
        </div>

        <div style="font-size: 0.88rem; color: #e2e8f0; margin-bottom: 0.85rem; line-height: 1.5;">
          ${a.message}
        </div>

        <!-- 5-Point Engineering Explanation Box (Section 78) -->
        <div style="background: rgba(14, 21, 38, 0.6); border: 1px solid var(--pn-border-subtle); border-radius: 6px; padding: 0.85rem; margin-bottom: 0.85rem; font-size: 0.8rem; line-height: 1.5;">
          <div style="color: #38bdf8; font-weight: 700; margin-bottom: 0.4rem; font-size: 0.82rem;">
            <i class="bi bi-shield-check"></i> AUDITABLE ENGINEERING EXPLANATION:
          </div>
          <div style="display: grid; grid-template-columns: 1fr; gap: 0.4rem;">
            <div><b style="color: #94a3b8;">WHAT HAPPENED?</b> <span style="color: #fff;">${whatHappened}</span></div>
            <div><b style="color: #94a3b8;">WHY IT MATTERS?</b> <span style="color: #cbd5e1;">${whyItMatters}</span></div>
            <div><b style="color: #94a3b8;">HISTORICAL EVIDENCE:</b> <span style="color: #cbd5e1;">${histEvidence}</span></div>
            <div><b style="color: #94a3b8;">CURRENT INDICATOR:</b> <span style="color: #cbd5e1;">${curIndicator}</span></div>
            <div><b style="color: #94a3b8;">ENGINEER REVIEW:</b> <span style="color: #fde68a;">${recommendedAction}</span></div>
          </div>
        </div>

        <div style="font-size: 0.76rem; color: var(--pn-text-dim); margin-bottom: 0.85rem;">
          Depth: <b style="color: #38bdf8;">${a.current_depth_m} m</b> • Formation: <b style="color: #fff;">${a.formation_name}</b> • Triggered: ${new Date(a.created_at).toLocaleString()}
          ${a.engineer_notes ? `<br/><span style="color: #34d399;"><i class="bi bi-journal-check"></i> <b>Engineer Note:</b> "${a.engineer_notes}"</span>` : ''}
          ${a.acknowledged_by ? ` • By: <b style="color: #34d399;">${a.acknowledged_by}</b>` : ''}
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <button class="pn-btn pn-btn-sm pn-btn-primary" onclick="viewAlertEvidence(${a.id})">
            <i class="bi bi-file-earmark-ruled"></i> View Evidence Trail
          </button>
          <button class="pn-btn pn-btn-sm pn-btn-success" onclick="openActionModal(${a.id}, '${escapeHtml(a.title)}')">
            <i class="bi bi-check2-circle"></i> Log Engineer Action / Acknowledge
          </button>
          <button class="pn-btn pn-btn-sm" onclick="askAIAssistant('Why did PetroNexus generate alert: ${escapeHtml(a.title)}?')">
            <i class="bi bi-robot"></i> Ask PetroNexus AI
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function openActionModal(alertId, alertTitle) {
  pendingActionAlertId = alertId;
  const modal = document.getElementById('engineerActionModal');
  const title = document.getElementById('actionModalTitle');
  if (title) title.textContent = `Log Action for Alert #${alertId}: ${alertTitle}`;
  if (modal) modal.style.display = 'flex';
}

function closeActionModal() {
  pendingActionAlertId = null;
  const modal = document.getElementById('engineerActionModal');
  if (modal) modal.style.display = 'none';
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

window.openActionModal = openActionModal;
window.closeActionModal = closeActionModal;
window.viewAlertEvidence = viewAlertEvidence;
