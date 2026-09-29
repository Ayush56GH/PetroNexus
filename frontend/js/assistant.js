/**
 * PetroNexus AI Drilling Assistant Controller (Sections 31, 32, 33, 34, 35)
 */

document.addEventListener('DOMContentLoaded', async () => {
  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const well = await PetroNexusAPI.getWellDetail(activeId);
    document.getElementById('aiWellHeader').textContent = `${well.well_name} • ${well.current_formation} @ ${well.current_depth_m} m MD`;
  } catch (err) {
    console.error('Failed to load active well:', err);
  }

  initChatForm();

  // Check if there is a prefilled prompt from dashboard
  const prefilled = sessionStorage.getItem('petronexus_prefilled_ai_prompt');
  if (prefilled) {
    sessionStorage.removeItem('petronexus_prefilled_ai_prompt');
    const input = document.getElementById('aiQueryInput');
    if (input) {
      input.value = prefilled;
      sendAIQuery(prefilled);
    }
  }
});

function initChatForm() {
  const form = document.getElementById('aiChatForm');
  const input = document.getElementById('aiQueryInput');

  if (form && input) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;
      input.value = '';
      sendAIQuery(q);
    });
  }

  // Quick prompt chips
  document.querySelectorAll('.pn-prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) sendAIQuery(prompt);
    });
  });
}

async function sendAIQuery(queryText) {
  const messagesContainer = document.getElementById('chatMessagesContainer');
  if (!messagesContainer) return;

  // Append user message
  appendUserMessage(queryText);

  // Append Loading placeholder
  const loadingId = 'aiLoading_' + Date.now();
  appendLoadingPlaceholder(loadingId);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const activeId = PetroNexusAPI.getActiveWellId();
  try {
    const res = await PetroNexusAPI.queryAI(queryText, activeId);
    removeElement(loadingId);
    appendAIResponse(res);
  } catch (err) {
    removeElement(loadingId);
    appendErrorMessage(err.message || 'Error communicating with PetroNexus Assistant.');
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendUserMessage(text) {
  const container = document.getElementById('chatMessagesContainer');
  const div = document.createElement('div');
  div.style.cssText = 'display: flex; justify-content: flex-end; margin-bottom: 1rem;';
  div.innerHTML = `
    <div style="background: var(--pn-cyan-primary); color: #fff; padding: 0.75rem 1rem; border-radius: 8px 8px 0 8px; max-width: 80%; font-size: 0.88rem; line-height: 1.45;">
      ${escapeHtml(text)}
    </div>
  `;
  container.appendChild(div);
}

function appendLoadingPlaceholder(id) {
  const container = document.getElementById('chatMessagesContainer');
  const div = document.createElement('div');
  div.id = id;
  div.style.cssText = 'display: flex; justify-content: flex-start; margin-bottom: 1rem;';
  div.innerHTML = `
    <div style="background: var(--pn-bg-surface-elevated); border: 1px solid var(--pn-border-subtle); padding: 0.75rem 1rem; border-radius: 8px 8px 8px 0; color: var(--pn-text-muted); font-size: 0.85rem; display: flex; align-items: center; gap: 8px;">
      <span class="spinner-border spinner-border-sm text-info" role="status"></span>
      Retrieving offset well memory & documents...
    </div>
  `;
  container.appendChild(div);
}

function appendAIResponse(res) {
  const container = document.getElementById('chatMessagesContainer');
  const div = document.createElement('div');
  div.style.cssText = 'display: flex; justify-content: flex-start; margin-bottom: 1.25rem;';

  // Format markdown headers into styled blocks
  let formatted = escapeHtml(res.response)
    .replace(/### (.*?)\n/g, '<h6 style="color: #38bdf8; font-size: 0.88rem; font-weight: 800; margin-top: 0.75rem; margin-bottom: 0.35rem; text-transform: uppercase;">$1</h6>')
    .replace(/\*\*(.*?)\*\*/g, '<b style="color: #fff;">$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');

  // Source badges
  let sourcesHtml = '';
  if (res.sources && res.sources.length) {
    sourcesHtml = `
      <div style="margin-top: 0.85rem; padding-top: 0.6rem; border-top: 1px solid var(--pn-border-subtle); display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
        <span style="font-size: 0.72rem; color: var(--pn-text-dim); font-weight: 700;">VERIFIED CITATIONS:</span>
        ${res.sources.map(s => `<span style="font-size: 0.72rem; background: rgba(2, 132, 199, 0.15); color: #38bdf8; border: 1px solid rgba(2, 132, 199, 0.3); padding: 2px 6px; border-radius: 3px;">${s}</span>`).join('')}
      </div>
    `;
  }

  div.innerHTML = `
    <div style="background: var(--pn-bg-card); border: 1px solid var(--pn-border-strong); padding: 1rem 1.25rem; border-radius: 8px 8px 8px 0; max-width: 85%; font-size: 0.85rem; line-height: 1.55; color: var(--pn-text-main); box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
      <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 0.5rem;">
        <span class="pn-brand-logo" style="width: 20px; height: 20px; font-size: 11px;">PN</span>
        <b style="color: #fff; font-size: 0.85rem;">PetroNexus Assistant</b>
        <span style="font-size: 0.7rem; color: var(--pn-emerald-success); margin-left: auto;">Grounded RAG Mode</span>
      </div>
      <div>${formatted}</div>
      ${sourcesHtml}
    </div>
  `;
  container.appendChild(div);
}

function appendErrorMessage(msg) {
  const container = document.getElementById('chatMessagesContainer');
  const div = document.createElement('div');
  div.style.cssText = 'display: flex; justify-content: flex-start; margin-bottom: 1rem;';
  div.innerHTML = `
    <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--pn-rose-danger); padding: 0.75rem 1rem; border-radius: 8px; color: #fca5a5; font-size: 0.85rem;">
      <b>Error:</b> ${escapeHtml(msg)}
    </div>
  `;
  container.appendChild(div);
}

function removeElement(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function escapeHtml(text) {
  if (!text) return '';
  return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
