/**
 * PetroNexus Reports & Engineering Context Pack Controller (Sections 50 & 68)
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadPreIntervalBrief();

  const btnGenPack = document.getElementById('btnGenerateContextPack');
  if (btnGenPack) {
    btnGenPack.addEventListener('click', async () => {
      await generateContextPack();
    });
  }
});

async function loadPreIntervalBrief() {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const brief = await PetroNexusAPI.getPreIntervalBrief(activeId);
    document.getElementById('pibWellName').textContent = brief.well_name;
    document.getElementById('pibDepth').textContent = `${brief.current_depth_m} m MD`;
    document.getElementById('pibInterval').textContent = brief.upcoming_interval_m;
    document.getElementById('pibFormation').textContent = brief.upcoming_formation;
    document.getElementById('pibOffsetCount').textContent = brief.offset_wells_count;
    document.getElementById('pibEventCount').textContent = brief.historical_events_count;

    const compWell = brief.most_comparable_well;
    document.getElementById('pibComparableWell').innerHTML = `
      <b style="color: #fff;">${compWell.well_name}</b> (${compWell.distance_km} km away)<br/>
      <span style="color: #fca5a5;">${compWell.historical_event}</span><br/>
      <span style="font-size: 0.8rem; color: #fde68a;"><b>Documented Action:</b> ${compWell.recommended_action}</span>
    `;

    const mitList = document.getElementById('pibMitigationsList');
    if (mitList) {
      mitList.innerHTML = brief.documented_mitigations.map(m => `<li>${m}</li>`).join('');
    }

    const srcList = document.getElementById('pibSourcesList');
    if (srcList) {
      srcList.innerHTML = brief.evidence_sources.map(s => `<span class="pn-card-badge" style="background: rgba(2, 132, 199, 0.2); color: #38bdf8;">${s}</span>`).join(' ');
    }

  } catch (err) {
    console.error('Failed to load pre-interval brief:', err);
  }
}

async function generateContextPack() {
  const activeId = PetroNexusAPI.getActiveWellId();
  const btn = document.getElementById('btnGenerateContextPack');
  const spinner = document.getElementById('packSpinner');
  const resultDiv = document.getElementById('packResultContainer');

  try {
    if (btn) btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';

    const res = await PetroNexusAPI.generateContextPack(activeId);

    if (resultDiv) {
      resultDiv.style.display = 'block';
      document.getElementById('packGenTime').textContent = res.generated_at;
      document.getElementById('packPdfLink').href = res.pdf_download_url;
      document.getElementById('packJsonPreview').textContent = JSON.stringify(res, null, 2);
    }

  } catch (err) {
    alert(`Failed to generate Context Pack: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
  }
}
