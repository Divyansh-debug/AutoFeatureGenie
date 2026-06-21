/* ═══════════════════════════════════════════════════════════════
   AutoFeatureGenie — Main Application JavaScript
   Communicates with the FastAPI backend at localhost:8000
═══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000';

/* ─── State ───────────────────────────────────────────────────── */
const state = {
  selectedFile: null,
  uploadedFilename: null,
  edaData: null,
  csvRows: [],         // preview rows
  csvHeaders: [],
  suggestions: null,
  distChart: null,
  missingChart: null,
  historyChart: null,
};

/* ─── DOM refs ───────────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);

/* ─── Init ────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  hljs.highlightAll();
  checkBackendStatus();
  setInterval(checkBackendStatus, 15000);
  setupNav();
  setupDropZone();
  setupFileInput();
  setupUploadBtn();
  setupDistColSelect();
  setupColSearch();
  setupGenerateBtn();
  setupHistoryRefresh();
  setupModal();
  $('clear-file-btn').addEventListener('click', clearFile);
});

/* ═══════════════════════════════════════════════════════════════
   Navigation
═══════════════════════════════════════════════════════════════ */
function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      switchSection(item.dataset.section);
    });
  });
}

function switchSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  $(`section-${name}`).classList.add('active');
  $(`nav-${name}`).classList.add('active');

  if (name === 'history') loadHistory();
}

/* ═══════════════════════════════════════════════════════════════
   Backend Status
═══════════════════════════════════════════════════════════════ */
async function checkBackendStatus() {
  const dot = $('status-dot');
  const txt = $('status-text');
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(4000) });
    if (r.ok) {
      const d = await r.json();
      dot.className = 'status-dot online';
      txt.textContent = `v${d.version || '?'} · online`;
    } else {
      throw new Error('bad');
    }
  } catch {
    dot.className = 'status-dot offline';
    txt.textContent = 'Backend offline';
  }
}

/* ═══════════════════════════════════════════════════════════════
   Drop Zone & File Input
═══════════════════════════════════════════════════════════════ */
function setupDropZone() {
  const dz = $('drop-zone');
  dz.addEventListener('click', () => $('file-input').click());
  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('dragover');
    const f = e.dataTransfer.files[0];
    if (f) selectFile(f);
  });
}

function setupFileInput() {
  $('file-input').addEventListener('change', (e) => {
    const f = e.target.files[0];
    if (f) selectFile(f);
  });
}

function selectFile(f) {
  if (!f.name.endsWith('.csv')) { toast('Only CSV files are supported.', 'error'); return; }
  if (f.size > 100 * 1024 * 1024) { toast('File too large (max 100 MB).', 'error'); return; }
  state.selectedFile = f;
  $('file-name-display').textContent = f.name;
  $('file-size-display').textContent = formatBytes(f.size);
  $('drop-zone').classList.add('hidden');
  $('file-ready').classList.remove('hidden');
}

function clearFile() {
  state.selectedFile = null;
  $('file-input').value = '';
  $('drop-zone').classList.remove('hidden');
  $('file-ready').classList.add('hidden');
  $('progress-wrap').classList.add('hidden');
}

/* ═══════════════════════════════════════════════════════════════
   Upload & EDA
═══════════════════════════════════════════════════════════════ */
function setupUploadBtn() {
  $('upload-btn').addEventListener('click', uploadFile);
}

async function uploadFile() {
  if (!state.selectedFile) return;
  const btn = $('upload-btn');
  btn.disabled = true;

  // Show progress
  const pw = $('progress-wrap');
  const pf = $('progress-fill');
  const pl = $('progress-label');
  pw.classList.remove('hidden');
  setProgress(pf, pl, 10, 'Connecting to backend…');

  const fd = new FormData();
  fd.append('file', state.selectedFile);

  try {
    setProgress(pf, pl, 30, 'Uploading file…');
    const r = await fetch(`${API}/upload/`, { method: 'POST', body: fd });
    setProgress(pf, pl, 70, 'Analysing data…');

    if (!r.ok) {
      const e = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(e.detail || `HTTP ${r.status}`);
    }

    const data = await r.json();
    setProgress(pf, pl, 100, 'Done!');

    // Parse CSV preview
    await parseCsvPreview(state.selectedFile);

    state.uploadedFilename = data.filename;
    state.edaData = data.eda_summary;

    setTimeout(() => {
      pw.classList.add('hidden');
      renderEDA(data);
      $('generate-btn').disabled = false;
      $('no-dataset-notice').classList.add('hidden');
      toast(`✅ Uploaded "${data.filename}" — ${data.rows.toLocaleString()} rows`, 'success');
    }, 400);

  } catch (err) {
    pw.classList.add('hidden');
    toast(`Upload failed: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

function setProgress(bar, label, pct, text) {
  bar.style.width = `${pct}%`;
  label.textContent = text;
}

/* Parse CSV rows from the File object for preview */
async function parseCsvPreview(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const lines = e.target.result.split('\n').filter(l => l.trim());
      const parse = (line) => line.split(',').map(c => c.trim().replace(/^"|"$/g, ''));
      state.csvHeaders = parse(lines[0] || '');
      state.csvRows = lines.slice(1, 11).map(parse);
      resolve();
    };
    reader.readAsText(file);
  });
}

/* ─── Render EDA Dashboard ────────────────────────────────────── */
function renderEDA(data) {
  const eda = data.eda_summary;
  const dash = $('eda-dashboard');
  dash.classList.remove('hidden');

  $('eda-title').textContent = data.filename;
  $('eda-badge').textContent = `${eda.shape[0].toLocaleString()} rows × ${eda.shape[1]} cols`;

  // KPIs
  const missing = Object.values(eda.column_info).reduce((s, c) => s + c.missing_values, 0);
  const target = eda.likely_target_column || '—';
  renderKPIs([
    { val: eda.shape[0].toLocaleString(), label: 'Rows',          icon: '📊' },
    { val: eda.shape[1],                  label: 'Columns',        icon: '🗂️' },
    { val: missing,                        label: 'Missing Cells',  icon: '⚠️' },
    { val: target,                         label: 'Target Column',  icon: '🎯' },
  ]);

  // Populate dist-col select
  const numericCols = Object.entries(eda.column_info)
    .filter(([, info]) => info.mean !== undefined)
    .map(([col]) => col);

  const sel = $('dist-col-select');
  sel.innerHTML = numericCols.map(c => `<option value="${c}">${c}</option>`).join('');

  renderDistChart(eda, numericCols[0]);
  renderMissingChart(eda);
  renderStatsTable(eda);
  renderPreviewTable();

  // Auto-fill target col in features section
  if (eda.likely_target_column) {
    $('target-col-input').value = eda.likely_target_column;
  }
}

function renderKPIs(items) {
  $('kpi-row').innerHTML = items.map(({ val, label, icon }) => `
    <div class="kpi-card">
      <div class="kpi-icon">${icon}</div>
      <div class="kpi-val">${val}</div>
      <div class="kpi-label">${label}</div>
    </div>
  `).join('');
}

/* ─── Distribution Chart ──────────────────────────────────────── */
function setupDistColSelect() {
  $('dist-col-select').addEventListener('change', (e) => {
    if (state.edaData) renderDistChart(state.edaData, e.target.value);
  });
}

function renderDistChart(eda, colName) {
  if (!colName) return;
  const info = eda.column_info[colName];
  if (!info || info.mean === undefined) return;

  // Generate approximate normal distribution bins using mean/std
  const { mean, std, min, max } = info;
  const bins = 20;
  const step = (max - min) / bins;
  const labels = Array.from({ length: bins }, (_, i) => (min + i * step).toFixed(2));
  // Gaussian approximation for shape
  const data = labels.map(x => {
    const z = (parseFloat(x) - mean) / (std || 1);
    return Math.round(100 * Math.exp(-.5 * z * z));
  });

  const ctx = $('dist-chart').getContext('2d');
  if (state.distChart) state.distChart.destroy();
  state.distChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: colName,
        data,
        backgroundColor: 'rgba(124,58,237,.6)',
        borderColor: 'rgba(124,58,237,1)',
        borderWidth: 1,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#64748b', maxTicksLimit: 6, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
      },
    },
  });
}

/* ─── Missing Values Chart ────────────────────────────────────── */
function renderMissingChart(eda) {
  const entries = Object.entries(eda.column_info)
    .filter(([, info]) => info.missing_values > 0)
    .sort((a, b) => b[1].missing_values - a[1].missing_values)
    .slice(0, 10);

  const ctx = $('missing-chart').getContext('2d');
  if (state.missingChart) state.missingChart.destroy();

  if (!entries.length) {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.fillStyle = '#6ee7b7';
    ctx.font = '14px Inter';
    ctx.textAlign = 'center';
    ctx.fillText('🎉 No missing values!', ctx.canvas.width / 2, ctx.canvas.height / 2);
    return;
  }

  state.missingChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: entries.map(([c]) => c),
      datasets: [{
        label: 'Missing',
        data: entries.map(([, i]) => i.missing_values),
        backgroundColor: 'rgba(239,68,68,.6)',
        borderColor: 'rgba(239,68,68,1)',
        borderWidth: 1, borderRadius: 3,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
      },
    },
  });
}

/* ─── Column Stats Table ──────────────────────────────────────── */
function renderStatsTable(eda) {
  const tbody = $('stats-tbody');
  const rows = Object.entries(eda.column_info);

  function typeClass(dtype) {
    if (dtype.includes('int')) return 'type-int64';
    if (dtype.includes('float')) return 'type-float64';
    if (dtype === 'bool') return 'type-bool';
    return 'type-object';
  }

  const makeRows = (entries) => entries.map(([col, info]) => `
    <tr>
      <td>${escHtml(col)}</td>
      <td><span class="type-badge ${typeClass(info.dtype)}">${info.dtype}</span></td>
      <td>${info.missing_values}</td>
      <td>${info.unique_values.toLocaleString()}</td>
      <td>${info.mean !== undefined ? info.mean.toFixed(3) : '—'}</td>
      <td>${info.std  !== undefined ? info.std.toFixed(3)  : '—'}</td>
      <td>${info.min  !== undefined ? info.min.toFixed(3)  : '—'}</td>
      <td>${info.max  !== undefined ? info.max.toFixed(3)  : '—'}</td>
    </tr>
  `).join('');

  tbody.innerHTML = makeRows(rows);

  // Search
  $('col-search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    tbody.innerHTML = makeRows(rows.filter(([c]) => c.toLowerCase().includes(q)));
  });
}

function setupColSearch() {
  // Listener added in renderStatsTable
}

/* ─── Data Preview Table ──────────────────────────────────────── */
function renderPreviewTable() {
  if (!state.csvHeaders.length) return;
  $('preview-badge').textContent = `first ${state.csvRows.length} rows`;

  const wrap = $('preview-table-wrap');
  const ths = state.csvHeaders.map(h => `<th>${escHtml(h)}</th>`).join('');
  const trs = state.csvRows.map(row =>
    `<tr>${row.map(c => `<td>${escHtml(c)}</td>`).join('')}</tr>`
  ).join('');

  wrap.innerHTML = `
    <table class="stats-table">
      <thead><tr>${ths}</tr></thead>
      <tbody>${trs}</tbody>
    </table>`;
}

/* ═══════════════════════════════════════════════════════════════
   Feature Suggestions
═══════════════════════════════════════════════════════════════ */
function setupGenerateBtn() {
  $('generate-btn').addEventListener('click', generateFeatures);
}

async function generateFeatures() {
  if (!state.uploadedFilename) {
    toast('Upload a dataset first.', 'error');
    return;
  }

  const domain = $('domain-select').value;
  const btn = $('generate-btn');
  btn.disabled = true;
  $('feature-spinner').classList.remove('hidden');
  $('features-list').classList.add('hidden');
  $('features-list').innerHTML = '';

  try {
    const r = await fetch(
      `${API}/feature-suggestions/?filename=${encodeURIComponent(state.uploadedFilename)}&domain=${domain}`,
      { signal: AbortSignal.timeout(180000) }
    );

    if (!r.ok) {
      const e = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(e.detail || `HTTP ${r.status}`);
    }

    const data = await r.json();
    state.suggestions = data.suggestions;

    const pt = data.processing_time ? `${data.processing_time.toFixed(1)}s` : '';
    toast(`✨ ${data.suggestions.length} features generated ${pt ? 'in ' + pt : ''}`, 'success');

    renderFeatures(data.suggestions);
  } catch (err) {
    toast(`Generation failed: ${err.message}`, 'error');
  } finally {
    $('feature-spinner').classList.add('hidden');
    btn.disabled = false;
  }
}

function renderFeatures(suggestions) {
  const list = $('features-list');
  list.classList.remove('hidden');

  // Check for error
  if (suggestions.length && suggestions[0].error) {
    list.innerHTML = `
      <div class="no-dataset-notice">
        <div class="notice-icon">❌</div>
        <p>${escHtml(suggestions[0].error)}</p>
        ${suggestions[0].details ? `<pre class="mono" style="text-align:left;max-width:600px;overflow:auto;">${escHtml(suggestions[0].details)}</pre>` : ''}
      </div>`;
    return;
  }

  list.innerHTML = suggestions.map((s, i) => buildFeatureCard(s, i)).join('');

  // Activate accordion
  list.querySelectorAll('.feature-card-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.closest('.feature-card');
      card.classList.toggle('open');
      // syntax highlight on open
      card.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
    });
  });

  // Open first card
  const first = list.querySelector('.feature-card');
  if (first) {
    first.classList.add('open');
    first.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
  }

  // Copy buttons
  list.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const code = btn.dataset.code;
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'Copy Code'; btn.classList.remove('copied'); }, 2000);
      });
    });
  });

  // Validate buttons
  list.querySelectorAll('.validate-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      validateFeature(btn.dataset.code);
    });
  });
}

function buildFeatureCard(s, i) {
  const complexity = (s.complexity || 'medium').toLowerCase();
  const code = s.code_snippet || '# No code provided';
  const codeEsc = escHtml(code);

  return `
    <div class="feature-card">
      <div class="feature-card-header">
        <div class="feature-num">${i + 1}</div>
        <div style="flex:1; min-width:0;">
          <div class="feature-col-name">${escHtml(s.column || 'Feature')}</div>
          <div class="feature-idea-preview">${escHtml((s.idea || '').substring(0, 80))}${(s.idea || '').length > 80 ? '…' : ''}</div>
        </div>
        <div class="feature-meta">
          <span class="complexity-badge complexity-${complexity}">${complexity}</span>
          <svg class="feature-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
        </div>
      </div>
      <div class="feature-body">
        <div class="feature-details-grid">
          <div class="feature-detail">
            <span class="detail-label">💡 Idea</span>
            <span class="detail-value">${escHtml(s.idea || '—')}</span>
          </div>
          <div class="feature-detail">
            <span class="detail-label">📌 Reason</span>
            <span class="detail-value">${escHtml(s.reason || '—')}</span>
          </div>
        </div>
        ${s.expected_impact ? `<div class="impact-chip">📈 ${escHtml(s.expected_impact)}</div>` : ''}
        <div class="code-block-wrap">
          <div class="code-block-label">
            <span>🐍 Python Code</span>
          </div>
          <pre><code class="language-python">${codeEsc}</code></pre>
        </div>
        <div class="feature-actions">
          <button class="btn btn-outline btn-sm copy-btn" data-code="${escAttr(code)}">Copy Code</button>
          <button class="btn btn-outline btn-sm validate-btn" data-code="${escAttr(code)}" 
            ${state.uploadedFilename ? '' : 'disabled'}>
            🧪 Validate Feature
          </button>
        </div>
      </div>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   Auto-Validator
═══════════════════════════════════════════════════════════════ */
async function validateFeature(codeSnippet) {
  const targetCol = $('target-col-input').value.trim();
  if (!targetCol) {
    toast('Enter a target column name first.', 'error');
    return;
  }
  if (!state.uploadedFilename) {
    toast('Upload a dataset first.', 'error');
    return;
  }

  const modal = $('validator-modal');
  const body  = $('modal-body');
  modal.classList.remove('hidden');
  body.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;gap:16px;padding:20px;">
      <div class="spinner"></div>
      <p class="text-muted">Running baseline model → applying feature → scoring…</p>
    </div>`;

  try {
    const url = `${API}/validate-feature/?filename=${encodeURIComponent(state.uploadedFilename)}&target_col=${encodeURIComponent(targetCol)}`;
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: codeSnippet,
      signal: AbortSignal.timeout(120000),
    });

    const result = await r.json();

    if (result.status === 'success') {
      const imp = result.improvement;
      const sign = imp >= 0 ? '+' : '';
      const valClass = imp >= 0 ? 'val-pos' : 'val-neg';
      const metric = result.metric || 'score';
      const task = result.task || '';

      body.innerHTML = `
        <div class="validator-grid">
          <div class="validator-stat">
            <div class="validator-stat-val val-neutral">${result.baseline_score.toFixed(4)}</div>
            <div class="validator-stat-label">Baseline ${metric}</div>
          </div>
          <div class="validator-stat">
            <div class="validator-stat-val val-neutral">${result.augmented_score.toFixed(4)}</div>
            <div class="validator-stat-label">Augmented ${metric}</div>
          </div>
          <div class="validator-stat">
            <div class="validator-stat-val ${valClass}">${sign}${imp.toFixed(4)}</div>
            <div class="validator-stat-label">Improvement Δ</div>
          </div>
        </div>
        <p class="text-muted" style="font-size:12.5px;">
          Task: <strong>${task}</strong> · 3-fold cross-validation · Gradient Boosting baseline
        </p>
        <p style="margin-top:10px;font-size:13px;color:${imp >= 0 ? 'var(--green)' : 'var(--red)'}">
          ${imp >= 0
            ? '✅ This feature appears to improve model performance!'
            : '⚠️ This feature did not improve performance on this dataset.'}
        </p>`;
    } else {
      body.innerHTML = `
        <div class="notice-icon" style="font-size:32px;text-align:center;margin-bottom:12px;">❌</div>
        <p style="color:var(--red);margin-bottom:8px;">${escHtml(result.error || 'Validation failed')}</p>
        ${result.traceback ? `<pre class="mono" style="overflow:auto;max-height:200px;font-size:11px;">${escHtml(result.traceback)}</pre>` : ''}`;
    }
  } catch (err) {
    body.innerHTML = `<p style="color:var(--red);">Request failed: ${escHtml(err.message)}</p>`;
  }
}

function setupModal() {
  $('modal-close').addEventListener('click', () => $('validator-modal').classList.add('hidden'));
  $('validator-modal').addEventListener('click', (e) => {
    if (e.target === $('validator-modal')) $('validator-modal').classList.add('hidden');
  });
}

/* ═══════════════════════════════════════════════════════════════
   History
═══════════════════════════════════════════════════════════════ */
function setupHistoryRefresh() {
  $('refresh-history-btn').addEventListener('click', loadHistory);
}

async function loadHistory() {
  $('history-spinner').classList.remove('hidden');
  $('history-empty').classList.add('hidden');
  $('history-table-card').classList.add('hidden');
  $('history-chart-card').classList.add('hidden');

  try {
    const r = await fetch(`${API}/history/?limit=50`);
    const data = await r.json();
    const items = data.history || [];

    $('history-spinner').classList.add('hidden');

    if (!items.length) {
      $('history-empty').classList.remove('hidden');
      return;
    }

    $('history-count-badge').textContent = `${items.length} suggestions`;
    $('history-table-card').classList.remove('hidden');

    const tbody = $('history-tbody');
    tbody.innerHTML = items.map((h, i) => {
      const imp = h.improvement_score;
      let impHtml;
      if (imp === null || imp === undefined) impHtml = '<span class="improvement-na">—</span>';
      else if (imp >= 0) impHtml = `<span class="improvement-pos">+${imp.toFixed(4)}</span>`;
      else impHtml = `<span class="improvement-neg">${imp.toFixed(4)}</span>`;

      const date = h.created_at ? h.created_at.substring(0, 16).replace('T', ' ') : '—';

      return `<tr>
        <td>${i + 1}</td>
        <td>${escHtml(h.dataset)}</td>
        <td><strong>${escHtml(h.column_name)}</strong></td>
        <td style="max-width:260px;white-space:normal;line-height:1.4;">${escHtml((h.idea || '').substring(0, 80))}${(h.idea || '').length > 80 ? '…' : ''}</td>
        <td>${impHtml}</td>
        <td class="mono">${date}</td>
      </tr>`;
    }).join('');

    // Chart for scored items
    const scored = items.filter(h => h.improvement_score !== null && h.improvement_score !== undefined);
    if (scored.length) {
      $('history-chart-card').classList.remove('hidden');
      renderHistoryChart(scored);
    }

  } catch (err) {
    $('history-spinner').classList.add('hidden');
    toast(`History load failed: ${err.message}`, 'error');
  }
}

function renderHistoryChart(items) {
  const sorted = [...items].sort((a, b) => a.improvement_score - b.improvement_score);
  const ctx = $('history-chart').getContext('2d');
  if (state.historyChart) state.historyChart.destroy();

  state.historyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(h => h.column_name),
      datasets: [{
        label: 'Improvement Score',
        data: sorted.map(h => h.improvement_score),
        backgroundColor: sorted.map(h =>
          h.improvement_score >= 0 ? 'rgba(16,185,129,.65)' : 'rgba(239,68,68,.65)'
        ),
        borderColor: sorted.map(h =>
          h.improvement_score >= 0 ? 'rgba(16,185,129,1)' : 'rgba(239,68,68,1)'
        ),
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Δ ${ctx.raw >= 0 ? '+' : ''}${ctx.raw.toFixed(4)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
      },
    },
  });
}

/* ═══════════════════════════════════════════════════════════════
   Toast Notifications
═══════════════════════════════════════════════════════════════ */
function toast(message, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span><span>${escHtml(message)}</span>`;
  $('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

/* ═══════════════════════════════════════════════════════════════
   Utilities
═══════════════════════════════════════════════════════════════ */
function escHtml(str) {
  if (!str && str !== 0) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escAttr(str) {
  return escHtml(str).replace(/\n/g, '&#10;').replace(/\r/g, '');
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}
