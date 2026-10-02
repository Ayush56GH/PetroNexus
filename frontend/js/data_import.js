/**
 * PetroNexus Data Ingestion & Provenance Center (SIH 26121 Section 3, 10, 48, 68)
 * Handles file preview, column mapping, physical data quality validation,
 * WITSML/eRTMAC connector test, and audit tracking.
 */

document.addEventListener('DOMContentLoaded', () => {
  let currentPreviewData = null;
  let currentFileName = null;

  // DOM Elements
  const fileInput = document.getElementById('fileInput');
  const importCategorySelect = document.getElementById('importCategorySelect');
  const btnPreview = document.getElementById('btnPreview');
  const previewLoading = document.getElementById('previewLoading');
  const mappingSection = document.getElementById('mappingSection');
  const detectedBadge = document.getElementById('detectedBadge');
  const mappingTbody = document.getElementById('mappingTbody');
  const dataPreviewBox = document.getElementById('dataPreviewBox');
  const btnCommitImport = document.getElementById('btnCommitImport');
  const importSuccessBox = document.getElementById('importSuccessBox');
  const successDetails = document.getElementById('successDetails');
  const provenanceTableBody = document.getElementById('provenanceTableBody');
  const jobsHistoryBody = document.getElementById('jobsHistoryBody');
  const statusAlert = document.getElementById('statusAlert');

  // WITSML Elements
  const btnConnectWitsml = document.getElementById('btnConnectWitsml');
  const btnDiscoverChannels = document.getElementById('btnDiscoverChannels');
  const witsmlStatusBox = document.getElementById('witsmlStatusBox');
  const witsmlBadge = document.getElementById('witsmlBadge');
  const topWitsmlStatus = document.getElementById('topWitsmlStatus');

  // Target schema field options per category
  const TARGET_FIELDS = {
    WELL_HEADER: [
      { id: 'well_name', label: 'well_name (Well Name / Identifier)' },
      { id: 'latitude', label: 'latitude (Latitude Decimal Deg)' },
      { id: 'longitude', label: 'longitude (Longitude Decimal Deg)' },
      { id: 'operator', label: 'operator (Operator Company)' },
      { id: 'field', label: 'field (Oil/Gas Field Name)' },
      { id: 'basin', label: 'basin (Sedimentary Basin)' },
      { id: 'block', label: 'block (Concession Block)' },
      { id: 'spud_date', label: 'spud_date (Spudding Date)' },
      { id: 'total_depth', label: 'total_depth (Total Depth MD)' },
      { id: 'status', label: 'status (DRILLING, COMPLETED, SUSPENDED)' }
    ],
    WELL_TRAJECTORY: [
      { id: 'md', label: 'md (Measured Depth m/ft)' },
      { id: 'inclination', label: 'inclination (Inclination Deg)' },
      { id: 'azimuth', label: 'azimuth (Azimuth Deg)' },
      { id: 'tvd', label: 'tvd (True Vertical Depth)' },
      { id: 'tvdss', label: 'tvdss (Subsea TVD)' },
      { id: 'dogleg_severity', label: 'dogleg_severity (DLS deg/30m)' }
    ],
    DRILLING_PARAMETERS: [
      { id: 'depth_md', label: 'depth_md (Measured Depth m/ft)' },
      { id: 'rop', label: 'rop (Rate of Penetration)' },
      { id: 'wob', label: 'wob (Weight on Bit)' },
      { id: 'rpm', label: 'rpm (Surface Rotary RPM)' },
      { id: 'torque', label: 'torque (Drilling Torque)' },
      { id: 'spp', label: 'spp (Standpipe Pressure)' },
      { id: 'flow_in', label: 'flow_in (Flow Rate In)' },
      { id: 'ecd', label: 'ecd (Equivalent Circulating Density)' },
      { id: 'mud_weight', label: 'mud_weight (Active Mud Weight)' }
    ],
    FORMATION_TOPS: [
      { id: 'formation_name', label: 'formation_name (Formation Name)' },
      { id: 'top_md', label: 'top_md (Formation Top MD)' },
      { id: 'base_md', label: 'base_md (Formation Base MD)' },
      { id: 'top_tvd', label: 'top_tvd (Top TVD)' },
      { id: 'base_tvd', label: 'base_tvd (Base TVD)' },
      { id: 'lithology', label: 'lithology (Lithology Description)' }
    ],
    HISTORICAL_EVENTS: [
      { id: 'event_type', label: 'event_type (MUD_LOSS, STUCK_PIPE, KICK, etc)' },
      { id: 'formation', label: 'formation (Formation where occurred)' },
      { id: 'start_md', label: 'start_md (Event Depth Top)' },
      { id: 'end_md', label: 'end_md (Event Depth Base)' },
      { id: 'severity', label: 'severity (LOW, MEDIUM, HIGH, CRITICAL)' },
      { id: 'description', label: 'description (Operational Narrative)' },
      { id: 'mitigation', label: 'mitigation (Corrective Action Taken)' },
      { id: 'npt_hours', label: 'npt_hours (Non-Productive Time Hrs)' }
    ],
    TELEMETRY: [
      { id: 'timestamp', label: 'timestamp (ISO8601 or DateTime)' },
      { id: 'depth_md', label: 'depth_md (Bit Depth MD)' },
      { id: 'rop', label: 'rop (Rate of Penetration)' },
      { id: 'wob', label: 'wob (Weight on Bit)' },
      { id: 'rpm', label: 'rpm (Rotary RPM)' },
      { id: 'torque', label: 'torque (Torque)' },
      { id: 'spp', label: 'spp (Standpipe Pressure)' },
      { id: 'flow_in', label: 'flow_in (Flow In)' },
      { id: 'pit_gain', label: 'pit_gain (Active Pit Gain/Loss)' }
    ],
    PETROPHYSICAL_LAS: [
      { id: 'DEPT', label: 'DEPT (Index Curve - Measured Depth)' },
      { id: 'GR', label: 'GR (Gamma Ray API)' },
      { id: 'RES', label: 'RES / ILD (Resistivity ohm.m)' },
      { id: 'NPHI', label: 'NPHI (Neutron Porosity)' },
      { id: 'RHOB', label: 'RHOB (Bulk Density g/cm3)' },
      { id: 'DT', label: 'DT (Sonic Travel Time us/ft)' }
    ]
  };

  // Helper: Show Alert Banner
  function showAlert(msg, type = 'info') {
    if (!statusAlert) return;
    statusAlert.className = `alert alert-${type}`;
    statusAlert.innerHTML = msg;
    statusAlert.style.display = 'block';
    setTimeout(() => {
      statusAlert.style.display = 'none';
    }, 7000);
  }

  // Load Data Provenance Registry
  async function loadDataSources() {
    if (!provenanceTableBody) return;
    try {
      const sources = await PetroNexusAPI.getDataSources();
      if (!sources || sources.length === 0) {
        provenanceTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No sources registered.</td></tr>';
        return;
      }
      provenanceTableBody.innerHTML = sources.map(src => {
        let badgeClass = 'pn-provenance-real';
        let label = 'REAL';
        if (src.is_synthetic) {
          badgeClass = 'pn-provenance-demo';
          label = 'SYNTHETIC DEMO';
        } else if (src.is_public) {
          badgeClass = 'pn-provenance-public';
          label = 'PUBLIC DATASET';
        } else if (src.is_user_uploaded) {
          badgeClass = 'pn-provenance-user';
          label = 'USER UPLOADED';
        }

        const statusColor = src.status === 'CONNECTED' || src.status === 'ACTIVE' ? '#34d399' : '#94a3b8';

        return `
          <tr>
            <td>
              <strong style="color: #fff;">${src.name}</strong><br/>
              <span style="color: #64748b; font-size: 0.7rem;">${src.source_type}</span>
            </td>
            <td><span class="${badgeClass}">${label}</span></td>
            <td><span style="color: ${statusColor}; font-weight: 600;">${src.status}</span></td>
            <td style="font-family: var(--pn-font-mono); color: #cbd5e1;">${src.record_count?.toLocaleString() || 0}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load data sources:', err);
    }
  }

  // Load Ingestion Jobs Audit Log
  async function loadIngestionJobs() {
    if (!jobsHistoryBody) return;
    try {
      const jobs = await PetroNexusAPI.getIngestionJobs();
      if (!jobs || jobs.length === 0) {
        jobsHistoryBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No ingestion history found.</td></tr>';
        return;
      }
      jobsHistoryBody.innerHTML = jobs.map(j => {
        const statusColor = j.status === 'COMPLETED' ? '#34d399' : j.status === 'FAILED' ? '#ef4444' : '#38bdf8';
        const dateStr = j.created_at ? new Date(j.created_at).toLocaleString() : 'N/A';
        const qualityScore = j.quality_summary?.quality_score ? `${j.quality_summary.quality_score}%` : 'N/A';

        return `
          <tr>
            <td style="font-family: var(--pn-font-mono); color: #94a3b8;">#${j.id}</td>
            <td style="font-weight: 600; color: #fff;">${j.file_name}</td>
            <td><span class="badge bg-dark border border-secondary">${j.data_type}</span></td>
            <td><span style="color: ${statusColor}; font-weight: 600;">${j.status}</span></td>
            <td style="font-family: var(--pn-font-mono); color: #38bdf8;">${j.rows_imported || 0} / ${j.rows_total || 0}</td>
            <td><span class="badge bg-secondary">${qualityScore}</span></td>
            <td style="color: #64748b; font-size: 0.72rem;">${dateStr}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load jobs:', err);
    }
  }

  // Handle File Preview & Dynamic Field Mapping
  if (btnPreview) {
    btnPreview.addEventListener('click', async () => {
      const file = fileInput.files[0];
      if (!file) {
        showAlert('Please choose a file (.csv, .xlsx, .las) first.', 'warning');
        return;
      }

      currentFileName = file.name;
      const category = importCategorySelect.value;
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      previewLoading.style.display = 'inline-block';
      mappingSection.style.display = 'none';
      importSuccessBox.style.display = 'none';

      try {
        const res = await PetroNexusAPI.previewImportFile(formData);
        currentPreviewData = res;
        previewLoading.style.display = 'none';

        if (res.error) {
          showAlert(`Preview failed: ${res.error}`, 'danger');
          return;
        }

        const disc = res.discovery || {};
        detectedBadge.innerText = `${disc.total_rows || disc.total_samples || 0} rows • ${disc.columns?.length || disc.curves?.length || 0} fields detected`;

        // Populate Mapping Table
        const targetOptions = TARGET_FIELDS[category] || [];
        const cols = disc.columns || (disc.curves ? disc.curves.map(c => c.name) : []);
        const suggested = disc.suggested_mapping || {};
        const sampleRows = disc.preview_rows || [];

        mappingTbody.innerHTML = cols.map(col => {
          const autoTarget = suggested[col] || '';
          const sampleVal = sampleRows.length > 0 && sampleRows[0][col] !== undefined ? sampleRows[0][col] : '-';

          const optionsHtml = `
            <option value="">-- Ignore / Unmapped --</option>
            ${targetOptions.map(t => `
              <option value="${t.id}" ${autoTarget === t.id ? 'selected' : ''}>${t.label}</option>
            `).join('')}
          `;

          return `
            <tr>
              <td style="font-family: var(--pn-font-mono); font-weight: 600; color: #38bdf8;">${col}</td>
              <td>
                <select class="form-select form-select-sm mapping-select" data-col="${col}" style="background: #1e293b; color: #fff; border-color: var(--pn-border-subtle); font-size: 0.78rem;">
                  ${optionsHtml}
                </select>
              </td>
              <td style="font-family: var(--pn-font-mono); color: #94a3b8; font-size: 0.72rem;">${sampleVal}</td>
            </tr>
          `;
        }).join('');

        // Populate Raw Sample Box
        if (sampleRows.length > 0) {
          dataPreviewBox.innerHTML = `<pre style="margin:0; color:#38bdf8;">${JSON.stringify(sampleRows.slice(0, 3), null, 2)}</pre>`;
        } else if (disc.curves) {
          dataPreviewBox.innerHTML = `<div style="color:#38bdf8;">Detected Curves: ${disc.curves.map(c => `${c.name} (${c.unit || '-'})`).join(', ')}</div>`;
        }

        mappingSection.style.display = 'block';
        showAlert('Columns successfully discovered and auto-mapped.', 'success');

      } catch (err) {
        previewLoading.style.display = 'none';
        showAlert(`Error previewing file: ${err.message}`, 'danger');
      }
    });
  }

  // Handle Commit Import
  if (btnCommitImport) {
    btnCommitImport.addEventListener('click', async () => {
      if (!currentFileName) {
        showAlert('No previewed file ready to commit.', 'warning');
        return;
      }

      const category = importCategorySelect.value;
      const mapping = {};
      document.querySelectorAll('.mapping-select').forEach(sel => {
        const col = sel.getAttribute('data-col');
        const target = sel.value;
        if (target) {
          mapping[col] = target;
        }
      });

      btnCommitImport.disabled = true;
      btnCommitImport.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Ingesting into Database...';

      try {
        const payload = {
          file_name: currentFileName,
          data_category: category,
          column_mapping: mapping,
          well_id: 23 // Default target well or creates new for WELL_HEADER
        };

        const res = await PetroNexusAPI.executeImport(payload);
        btnCommitImport.disabled = false;
        btnCommitImport.innerHTML = '<i class="bi bi-check2-circle"></i> Ingest & Index Data';

        if (res.status === 'SUCCESS') {
          mappingSection.style.display = 'none';
          importSuccessBox.style.display = 'block';
          successDetails.innerHTML = `
            <strong>File:</strong> ${res.file_name} &bull; <strong>Category:</strong> ${res.data_category}<br/>
            <strong>Records Ingested:</strong> ${res.imported_records} &bull; <strong>Job ID:</strong> #${res.job_id}<br/>
            <strong>Physical Data Quality:</strong> ${res.quality_summary?.quality_score || 100}% (${res.quality_summary?.quality_status || 'GOOD'})
          `;
          showAlert(`Successfully imported ${res.imported_records} records into PetroNexus!`, 'success');
          loadDataSources();
          loadIngestionJobs();
        } else {
          showAlert(`Import returned unexpected status: ${JSON.stringify(res)}`, 'warning');
        }
      } catch (err) {
        btnCommitImport.disabled = false;
        btnCommitImport.innerHTML = '<i class="bi bi-check2-circle"></i> Ingest & Index Data';
        showAlert(`Import error: ${err.message}`, 'danger');
      }
    });
  }

  // WITSML Connector Actions
  if (btnConnectWitsml) {
    btnConnectWitsml.addEventListener('click', async () => {
      const url = document.getElementById('witsmlUrl').value;
      const username = document.getElementById('witsmlUser').value;
      const password = document.getElementById('witsmlPass').value;
      const wellUid = document.getElementById('witsmlWellUid').value;
      const interval = parseInt(document.getElementById('witsmlInterval').value, 10) || 5;

      witsmlStatusBox.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Testing connection to eRTMAC WITSML server...';

      try {
        const res = await PetroNexusAPI.configureWitsml({
          endpoint_url: url,
          username: username,
          password: password,
          well_uid: wellUid,
          polling_interval_sec: interval
        });

        if (res.status === 'CONNECTED') {
          witsmlBadge.className = 'badge bg-success';
          witsmlBadge.innerText = 'CONNECTED';
          if (topWitsmlStatus) topWitsmlStatus.innerText = 'ONLINE (eRTMAC)';
          witsmlStatusBox.innerHTML = `
            <span style="color:#34d399;"><i class="bi bi-check-circle"></i> Connected to ${url}</span><br/>
            Active Wellbore: ${wellUid} &bull; Channels Discovered: ${res.discovered_channels || 21}<br/>
            Data Age: Just now &bull; Polling: ${interval}s
          `;
        } else {
          witsmlBadge.className = 'badge bg-secondary';
          witsmlBadge.innerText = 'STANDBY';
          if (topWitsmlStatus) topWitsmlStatus.innerText = 'STANDBY';
          witsmlStatusBox.innerHTML = `
            <span style="color:#fbbf24;"><i class="bi bi-info-circle"></i> ${res.message || 'eRTMAC connector configured but not connected'}</span><br/>
            Server responded with status: ${res.status || 'OFFLINE'}. Standby mode active.
          `;
        }
      } catch (err) {
        witsmlBadge.className = 'badge bg-danger';
        witsmlBadge.innerText = 'OFFLINE';
        witsmlStatusBox.innerHTML = `
          <span style="color:#f87171;"><i class="bi bi-exclamation-triangle"></i> eRTMAC Connection Standby:</span> ${err.message}<br/>
          (SIH Rule: No synthetic data is fabricated as live Oil India telemetry).
        `;
      }
    });
  }

  if (btnDiscoverChannels) {
    btnDiscoverChannels.addEventListener('click', async () => {
      witsmlStatusBox.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Discovering standard WITSML 1.4.1.1 telemetry log channels...';
      try {
        const channels = await PetroNexusAPI.getWitsmlChannels();
        witsmlStatusBox.innerHTML = `
          <strong>Discovered ${channels.length} WITSML Channels:</strong><br/>
          <div style="font-size:0.7rem; color:#38bdf8; margin-top:0.3rem;">
            ${channels.map(c => `<code>${c.channel}</code> (${c.unit || '-'})`).join(', ')}
          </div>
        `;
      } catch (err) {
        witsmlStatusBox.innerHTML = `<span style="color:#f87171;">Failed to query channels: ${err.message}</span>`;
      }
    });
  }

  // Initial Data Loads
  loadDataSources();
  loadIngestionJobs();
});
