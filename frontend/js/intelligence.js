/**
 * PetroNexus Offset Intelligence & Look-Ahead Controller (Sections 15, 16, 17, 44, 49)
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadIntelligenceData();

  const radiusSelect = document.getElementById('intelRadius');
  const lookaheadSelect = document.getElementById('intelLookahead');

  if (radiusSelect) radiusSelect.addEventListener('change', () => loadIntelligenceData());
  if (lookaheadSelect) lookaheadSelect.addEventListener('change', () => loadIntelligenceData());
});

async function loadIntelligenceData() {
  const activeId = PetroNexusAPI.getActiveWellId();
  const radius = parseFloat(document.getElementById('intelRadius')?.value || '15.0');
  const lookahead = parseFloat(document.getElementById('intelLookahead')?.value || '100.0');

  try {
    const well = await PetroNexusAPI.getWellDetail(activeId);
    document.getElementById('intelWellHeader').textContent = `${well.well_name} (${well.current_formation} @ ${well.current_depth_m} m)`;

    const analysis = await PetroNexusAPI.runOffsetAnalysis({
      well_id: activeId,
      radius_km: radius,
      current_depth: well.current_depth_m,
      formation: well.current_formation,
      lookahead_m: lookahead
    });

    renderComparableWells(analysis.comparable_wells);
    renderLookaheadCorridor(analysis.lookahead_events, well.current_depth_m);
    renderMemoryGaps(analysis.memory_gaps);
    renderDataConflicts(analysis.data_conflicts);
    renderMitigationPlaybook(analysis.mitigation_playbook);

  } catch (err) {
    console.error('Failed to load intelligence data:', err);
  }
}

function renderComparableWells(comparable) {
  const container = document.getElementById('comparableWellsTableBody');
  if (!container) return;

  container.innerHTML = comparable.map(c => `
    <tr>
      <td><b style="color: #fff;">${c.well_name}</b></td>
      <td>${c.distance_km} km</td>
      <td>
        <div style="display: flex; align-items: center; gap: 6px;">
          <div style="flex: 1; height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden;">
            <div style="width: ${c.formation_match_pct}%; height: 100%; background: #0284c7;"></div>
          </div>
          <span style="font-size: 0.75rem;">${c.formation_match_pct}%</span>
        </div>
      </td>
      <td>${c.depth_match_pct}%</td>
      <td>
        <span class="pn-card-badge" style="background: ${c.relevance_category === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)'}; color: #fff;">
          ${c.relevance_category} (${c.overall_relevance_pct}%)
        </span>
      </td>
      <td style="font-size: 0.8rem; color: var(--pn-text-muted);">
        ${c.why_comparable.slice(0, 2).join(' • ')}
      </td>
    </tr>
  `).join('');
}

function renderLookaheadCorridor(hazards, currentDepth) {
  const container = document.getElementById('lookaheadList');
  if (!container) return;

  if (!hazards.length) {
    container.innerHTML = '<div style="color: var(--pn-text-dim); padding: 1rem;">No offset hazards in active corridor window.</div>';
    return;
  }

  container.innerHTML = hazards.map(h => `
    <div class="pn-alert-item severity-${h.severity}">
      <div class="pn-alert-title">
        <span>${h.event_type} (${h.corridor_zone})</span>
        <span style="color: #38bdf8; font-size: 0.78rem;">${h.offset_well_name} @ ${h.hazard_depth_md_m} m</span>
      </div>
      <div class="pn-alert-desc">
        ${h.description}
      </div>
      <div style="font-size: 0.75rem; color: #fde68a; margin-bottom: 0.4rem;">
        <b>Observed Historical Mitigation:</b> ${h.historical_mitigation}
      </div>
      <div style="font-size: 0.72rem; color: var(--pn-text-dim);">
        Source: ${h.source_citation}
      </div>
    </div>
  `).join('');
}

function renderMemoryGaps(gaps) {
  const container = document.getElementById('memoryGapsList');
  if (!container) return;

  container.innerHTML = gaps.map(g => `
    <div style="background: var(--pn-bg-surface); border-left: 3px solid var(--pn-amber-warning); padding: 0.75rem; border-radius: 0 4px 4px 0; margin-bottom: 0.6rem;">
      <b style="color: #fff; font-size: 0.85rem;">[!] ${g.title}</b>
      <div style="font-size: 0.8rem; color: var(--pn-text-muted); margin: 0.25rem 0;">
        ${g.description}
      </div>
      <div style="font-size: 0.75rem; color: #fde68a;">
        <b>Recommendation:</b> ${g.recommendation}
      </div>
    </div>
  `).join('');
}

function renderDataConflicts(conflicts) {
  const container = document.getElementById('dataConflictsList');
  if (!container) return;

  container.innerHTML = conflicts.map(cf => `
    <div style="background: var(--pn-bg-surface); border-left: 3px solid var(--pn-cyan-primary); padding: 0.75rem; border-radius: 0 4px 4px 0; margin-bottom: 0.6rem;">
      <div style="display: flex; justify-content: space-between;">
        <b style="color: #fff; font-size: 0.85rem;">${cf.parameter} (${cf.well_name})</b>
        <span style="color: var(--pn-rose-danger); font-size: 0.75rem; font-weight: 700;">${cf.delta}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--pn-text-muted); margin: 0.3rem 0;">
        <b>Source 1:</b> ${cf.source_1} -> ${cf.value_1}<br/>
        <b>Source 2:</b> ${cf.source_2} -> ${cf.value_2}
      </div>
      <div style="font-size: 0.75rem; color: #38bdf8;">
        <b>Explanation:</b> ${cf.recommendation}
      </div>
    </div>
  `).join('');
}

function renderMitigationPlaybook(playbook) {
  const container = document.getElementById('playbookContainer');
  if (!container) return;

  container.innerHTML = playbook.map(p => `
    <div style="background: var(--pn-bg-surface-elevated); border: 1px solid var(--pn-border-subtle); border-radius: 6px; padding: 0.85rem; margin-bottom: 0.75rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
        <b style="color: #fff; font-size: 0.9rem;">${p.title}</b>
        <span style="font-size: 0.72rem; background: var(--pn-cyan-glow); color: var(--pn-cyan-primary); padding: 2px 6px; border-radius: 3px;">${p.action_category}</span>
      </div>
      <div style="font-size: 0.82rem; color: var(--pn-text-muted); line-height: 1.45; margin-bottom: 0.5rem;">
        ${p.procedure}
      </div>
      <div style="font-size: 0.75rem; color: var(--pn-emerald-success); display: flex; justify-content: space-between;">
        <span><b>Efficacy:</b> ${p.observed_efficacy}</span>
        <span style="color: var(--pn-text-dim);">Evidence: ${p.evidence_sources.join(', ')}</span>
      </div>
    </div>
  `).join('');
}
