// Estado global do frontend.
const state = {
  sessionId: null,
  processId: null,
  processes: [],
};

const els = {
  health: document.getElementById('health-badge'),
  processSelect: document.getElementById('process-select'),
  processInfo: document.getElementById('process-info'),
  documentsList: document.getElementById('documents-list'),
  chatWindow: document.getElementById('chat-window'),
  chatForm: document.getElementById('chat-form'),
  chatInput: document.getElementById('chat-input'),
  historyList: document.getElementById('history-list'),
  refreshHistory: document.getElementById('refresh-history'),
  suggestions: document.querySelectorAll('.suggestion'),
};

async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`Erro ${res.status} em ${path}`);
  return res.json();
}

async function checkHealth() {
  try {
    const data = await api('GET', '/api/health');
    els.health.textContent = `online — modo ${data.llm_mode}`;
    els.health.classList.remove('error');
  } catch (e) {
    els.health.textContent = 'offline';
    els.health.classList.add('error');
  }
}

async function loadProcesses() {
  try {
    state.processes = await api('GET', '/api/processes');
    els.processSelect.innerHTML = '';

    const blank = document.createElement('option');
    blank.value = '';
    blank.textContent = '— nenhum (atendimento anônimo)';
    els.processSelect.appendChild(blank);

    state.processes.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.customer_name} — ${p.visa_type} / ${p.destination_country}`;
      els.processSelect.appendChild(opt);
    });

    if (state.processes.length > 0) {
      els.processSelect.value = state.processes[0].id;
      selectProcess(state.processes[0].id);
    }
  } catch (e) {
    console.error(e);
  }
}

function renderProcess(p) {
  if (!p) {
    els.processInfo.innerHTML = '<p class="hint">Nenhum processo selecionado.</p>';
    els.documentsList.innerHTML = '';
    return;
  }
  const statusClass = p.status.replace(/[^a-z_]/g, '');
  els.processInfo.innerHTML = `
    <div class="row"><span class="label">Cliente</span><span>${p.customer_name}</span></div>
    <div class="row"><span class="label">Tipo de visto</span><span>${p.visa_type}</span></div>
    <div class="row"><span class="label">Destino</span><span>${p.destination_country}</span></div>
    <div class="row"><span class="label">Status</span><span class="status-pill ${statusClass}">${p.status.replace('_', ' ')}</span></div>
    <div class="row"><span class="label">Atualizado em</span><span>${formatDate(p.updated_at)}</span></div>
    <div class="row"><span class="label">ID</span><span style="font-size:11px;">${p.id}</span></div>
  `;
  els.documentsList.innerHTML = p.documents.map((d) => `
    <li>
      <span>${d.name}</span>
      <span class="doc-status ${d.status}">${d.status}</span>
    </li>
  `).join('');
}

function selectProcess(id) {
  state.processId = id || null;
  // Encerra a sessão de chat anterior para vincular ao novo processo.
  state.sessionId = null;
  const proc = state.processes.find((p) => p.id === id) || null;
  renderProcess(proc);
  loadHistory();
}

function appendMessage(role, text, meta) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  if (meta) {
    const m = document.createElement('div');
    m.className = 'meta';
    m.textContent = meta;
    bubble.appendChild(m);
  }
  els.chatWindow.appendChild(div);
  els.chatWindow.scrollTop = els.chatWindow.scrollHeight;
}

async function sendMessage(message) {
  appendMessage('user', message);
  try {
    const payload = { message };
    if (state.sessionId) payload.session_id = state.sessionId;
    if (state.processId) payload.process_id = state.processId;

    const resp = await api('POST', '/api/chat', payload);
    state.sessionId = resp.session_id;

    const meta = `intenção: ${resp.intent} (${(resp.confidence * 100).toFixed(0)}%)` +
      (resp.blocked_by_governance ? ' • bloqueada pela governança' : '');
    appendMessage('bot', resp.response);
    const lastBubble = els.chatWindow.querySelector('.msg.bot:last-child .bubble');
    const m = document.createElement('div');
    m.className = 'meta';
    m.textContent = meta;
    lastBubble.appendChild(m);

    loadHistory();
  } catch (e) {
    appendMessage('bot', `Erro ao processar: ${e.message}`);
  }
}

async function loadHistory() {
  try {
    const url = state.processId
      ? `/api/history?process_id=${state.processId}&limit=30`
      : `/api/history?limit=30`;
    const data = await api('GET', url);
    if (!data.length) {
      els.historyList.innerHTML = '<li class="hint">Sem interações registradas ainda.</li>';
      return;
    }
    els.historyList.innerHTML = data.map((i) => {
      const ents = i.entities && Object.keys(i.entities).length
        ? Object.entries(i.entities).map(([k, v]) => `${k}=${Array.isArray(v) ? v.join('/') : v}`).join(', ')
        : 'sem entidades';
      const blocked = i.blocked_by_governance ? '<span class="tag blocked">governança</span>' : '';
      return `
        <li>
          <div class="h-question">▶ ${escapeHtml(i.user_message)}</div>
          <div class="h-answer">${escapeHtml(i.bot_response).slice(0, 200)}${i.bot_response.length > 200 ? '…' : ''}</div>
          <div class="h-meta">
            <span class="tag">${i.intent || '?'}</span>
            <span class="tag">conf ${i.intent_confidence != null ? (i.intent_confidence * 100).toFixed(0) + '%' : '-'}</span>
            <span class="tag">${ents}</span>
            ${blocked}
            <span class="tag">${formatDate(i.created_at)}</span>
          </div>
        </li>
      `;
    }).join('');
  } catch (e) {
    console.error(e);
  }
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString('pt-BR');
  } catch {
    return iso;
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Eventos
els.chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const value = els.chatInput.value.trim();
  if (!value) return;
  els.chatInput.value = '';
  sendMessage(value);
});

els.processSelect.addEventListener('change', (e) => selectProcess(e.target.value));
els.refreshHistory.addEventListener('click', loadHistory);
els.suggestions.forEach((btn) => {
  btn.addEventListener('click', () => sendMessage(btn.textContent));
});

// Boot
checkHealth();
loadProcesses();
