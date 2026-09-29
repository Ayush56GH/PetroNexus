/**
 * PetroNexus Current Well Intelligence Ingestion Controller (Sections 3, 4, 5, 8, 9)
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadCurrentWellProfile();
  initUploadForm();
});

async function loadCurrentWellProfile() {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const profile = await PetroNexusAPI.getCurrentWellProfile(activeId);
    renderWellProfile(profile);
    renderCompleteness(profile.completeness);
  } catch (err) {
    console.error('Failed to load active well profile:', err);
  }
}

function renderWellProfile(p) {
  document.getElementById('profWellName').textContent = p.well_name;
  document.getElementById('profField').textContent = p.field;
  document.getElementById('profOperator').textContent = p.operator;
  document.getElementById('profCoords').textContent = `${p.latitude}, ${p.longitude}`;
  document.getElementById('profDepth').textContent = `${p.current_depth_m} m MD`;
  document.getElementById('profFormation').textContent = p.current_formation;
  document.getElementById('profStatus').textContent = p.status;
  document.getElementById('profType').textContent = p.well_type;

  const t = p.latest_telemetry || {};
  document.getElementById('profRop').textContent = `${t.rop} m/hr`;
  document.getElementById('profWob').textContent = `${t.wob} t`;
  document.getElementById('profRpm').textContent = `${t.rpm}`;
  document.getElementById('profTorque').textContent = `${t.torque} kN.m`;
  document.getElementById('profEcd').textContent = `${t.ecd} SG`;
  document.getElementById('profMw').textContent = `${t.mud_weight} SG`;
  document.getElementById('profSpp').textContent = `${t.spp} psi`;
  document.getElementById('profFlow').textContent = `${t.flow_rate} LPM`;

  // Render Upload History
  const historyList = document.getElementById('uploadSessionHistory');
  if (historyList && p.upload_sessions) {
    historyList.innerHTML = p.upload_sessions.map(s => `
      <div style="background: var(--pn-bg-surface); padding: 0.6rem; border-radius: 4px; margin-bottom: 0.4rem; display: flex; justify-content: space-between; font-size: 0.8rem;">
        <span><b>${s.file_name}</b> (${s.file_type})</span>
        <span style="color: var(--pn-emerald-success);">${s.created_at}</span>
      </div>
    `).join('') || '<div style="color: var(--pn-text-dim);">No previous upload sessions recorded.</div>';
  }
}

function renderCompleteness(c) {
  if (!c) return;
  document.getElementById('readinessScoreVal').textContent = `${c.readiness_score}%`;
  document.getElementById('readinessMeterFill').style.width = `${c.readiness_score}%`;

  // Breakdown grid
  const breakdownContainer = document.getElementById('readinessBreakdownGrid');
  if (breakdownContainer && c.readiness_breakdown) {
    let html = '';
    for (const [dim, info] of Object.entries(c.readiness_breakdown)) {
      const isOk = info.status === '✓';
      const isWarn = info.status === '⚠';
      const color = isOk ? 'var(--pn-emerald-success)' : (isWarn ? 'var(--pn-amber-warning)' : 'var(--pn-rose-danger)');
      html += `
        <div style="background: var(--pn-bg-surface); border: 1px solid var(--pn-border-subtle); border-radius: 4px; padding: 0.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem;">
          <span>${dim}</span>
          <span style="color: ${color}; font-weight: 800; font-family: var(--pn-font-mono);">${info.status}</span>
        </div>
      `;
    }
    breakdownContainer.innerHTML = html;
  }

  // Critical Missing
  const critList = document.getElementById('criticalMissingList');
  if (critList) {
    critList.innerHTML = c.critical_missing.length ? c.critical_missing.map(m => `
      <div style="color: #fca5a5; font-size: 0.82rem; margin-bottom: 0.25rem;">• ${m}</div>
    `).join('') : '<div style="color: var(--pn-emerald-success); font-size: 0.82rem;">✓ All critical operational parameters populated.</div>';
  }

  // Recommended Missing
  const recList = document.getElementById('recommendedMissingList');
  if (recList) {
    recList.innerHTML = c.recommended_missing.length ? c.recommended_missing.map(m => `
      <div style="color: #fde68a; font-size: 0.82rem; margin-bottom: 0.25rem;">• ${m}</div>
    `).join('') : '<div style="color: var(--pn-emerald-success); font-size: 0.82rem;">✓ All recommended parameters available.</div>';
  }

  // Next Best Data Actions
  const actionList = document.getElementById('nextBestActionsList');
  if (actionList) {
    actionList.innerHTML = c.next_best_actions.map((a, i) => `
      <div style="background: var(--pn-bg-surface-elevated); border-left: 3px solid var(--pn-cyan-primary); padding: 0.5rem 0.75rem; margin-bottom: 0.4rem; font-size: 0.82rem; color: #fff;">
        <b>Action ${i + 1}:</b> ${a}
      </div>
    `).join('');
  }
}

function initUploadForm() {
  const form = document.getElementById('wellUploadForm');
  const fileInput = document.getElementById('wellFileInput');
  const uploadAlert = document.getElementById('uploadAlert');
  const uploadSpinner = document.getElementById('uploadSpinner');

  if (form && fileInput) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files.length) {
        alert('Please select a file to upload.');
        return;
      }

      const activeId = PetroNexusAPI.getActiveWellId();
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('well_id', activeId);

      try {
        if (uploadSpinner) uploadSpinner.style.display = 'inline-block';
        if (uploadAlert) uploadAlert.style.display = 'none';

        const result = await PetroNexusAPI.uploadCurrentWellFile(formData);

        if (uploadAlert) {
          uploadAlert.className = 'alert alert-success';
          uploadAlert.innerHTML = `<b>Success:</b> ${result.message}`;
          uploadAlert.style.display = 'block';
        }

        // Refresh profile and completeness
        await loadCurrentWellProfile();

      } catch (err) {
        if (uploadAlert) {
          uploadAlert.className = 'alert alert-danger';
          uploadAlert.textContent = `Upload failed: ${err.message}`;
          uploadAlert.style.display = 'block';
        }
      } finally {
        if (uploadSpinner) uploadSpinner.style.display = 'none';
      }
    });
  }

  // Quick demo sample file pickers
  const demoButtons = [
    { id: 'btnQuickPdf', type: 'pdf', label: 'Well Report PDF' },
    { id: 'btnQuickCsv', type: 'csv', label: 'Telemetry CSV' },
    { id: 'btnQuickSurvey', type: 'survey', label: 'Directional Survey' },
    { id: 'btnQuickLas', type: 'las', label: 'LAS Well-Log' }
  ];

  demoButtons.forEach(btnInfo => {
    const el = document.getElementById(btnInfo.id);
    if (el) {
      el.addEventListener('click', async () => {
        const activeId = PetroNexusAPI.getActiveWellId();
        const uploadAlert = document.getElementById('uploadAlert');
        const uploadSpinner = document.getElementById('uploadSpinner');
        try {
          if (uploadSpinner) uploadSpinner.style.display = 'inline-block';
          if (uploadAlert) {
            uploadAlert.className = 'alert alert-info';
            uploadAlert.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processing ${btnInfo.label}...`;
            uploadAlert.style.display = 'block';
          }
          const res = await PetroNexusAPI.demoIngest(btnInfo.type, activeId);
          if (uploadAlert) {
            uploadAlert.className = 'alert alert-success';
            uploadAlert.innerHTML = `<b>Ingested:</b> ${res.message} (Readiness: <b>${res.completeness.readiness_score}%</b>)`;
          }
          await loadCurrentWellProfile();
        } catch (err) {
          if (uploadAlert) {
            uploadAlert.className = 'alert alert-danger';
            uploadAlert.textContent = `Demo ingest failed: ${err.message}`;
          }
        } finally {
          if (uploadSpinner) uploadSpinner.style.display = 'none';
        }
      });
    }
  });
}
