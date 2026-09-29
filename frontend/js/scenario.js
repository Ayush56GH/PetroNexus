/**
 * PetroNexus Scenario / What-If Analysis Controller (Section 43)
 */

document.addEventListener('DOMContentLoaded', async () => {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const well = await PetroNexusAPI.getWellDetail(activeId);
    document.getElementById('scenStartDepth').value = well.current_depth_m;
    document.getElementById('scenTargetDepth').value = well.current_depth_m + 150;
    document.getElementById('scenFormation').value = well.current_formation || 'Formation-X';
  } catch (err) {
    console.error('Failed to prefill scenario:', err);
  }

  const form = document.getElementById('scenarioForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await runScenario();
    });
  }
});

async function runScenario() {
  const activeId = PetroNexusAPI.getActiveWellId();
  const currentDepth = parseFloat(document.getElementById('scenStartDepth').value);
  const targetDepth = parseFloat(document.getElementById('scenTargetDepth').value);
  const formation = document.getElementById('scenFormation').value;
  const radius = parseFloat(document.getElementById('scenRadius').value);

  const resultsContainer = document.getElementById('scenarioResults');
  resultsContainer.style.display = 'block';

  try {
    const res = await PetroNexusAPI.runScenarioAnalysis({
      well_id: activeId,
      current_depth: currentDepth,
      target_depth: targetDepth,
      formation: formation,
      radius_km: radius
    });

    document.getElementById('scenIntervalSpan').textContent = res.scenario_interval;
    document.getElementById('scenOffsetCount').textContent = res.comparable_wells_count;
    document.getElementById('scenEventCount').textContent = res.total_historical_events;
    document.getElementById('scenDensity').textContent = `${res.event_density_per_100m} events / 100m`;

    const tableBody = document.getElementById('scenEventsTable');
    if (tableBody) {
      tableBody.innerHTML = res.events.map(ev => `
        <tr>
          <td><b style="color: #fff;">${ev.well_name}</b></td>
          <td>${ev.depth_md_m} m</td>
          <td>${ev.event_type}</td>
          <td><span class="pn-card-badge" style="background: ${ev.severity === 'HIGH' ? 'var(--pn-rose-danger)' : 'var(--pn-amber-warning)'}; color: #fff;">${ev.severity}</span></td>
          <td style="font-size: 0.8rem; color: var(--pn-text-muted);">${ev.mitigation}</td>
          <td style="font-size: 0.75rem; color: var(--pn-cyan-primary);">${ev.source}</td>
        </tr>
      `).join('') || '<tr><td colspan="6" style="text-align: center; color: var(--pn-text-dim);">No events in this scenario interval.</td></tr>';
    }

  } catch (err) {
    alert(`Scenario analysis failed: ${err.message}`);
  }
}
