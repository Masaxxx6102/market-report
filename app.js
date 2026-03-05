/**
 * Market Insight 3.0 Dashboard Logic
 */
async function bootstrap() {
  const tickerEl = document.getElementById('main-ticker');
  const syncStatus = document.getElementById('sync-status');
  const refreshBtn = document.getElementById('refresh-btn');

  refreshBtn.addEventListener('click', () => {
    refreshBtn.textContent = 'RELOADING...';
    location.reload();
  });

  try {
    const dataPath = `./data/latest_report.json?v=${new Date().getTime()}`;
    const response = await fetch(dataPath);
    if (!response.ok) throw new Error(`Data file missing`);
    const data = await response.json();

    syncStatus.textContent = `LAST SYNC: ${data.last_updated}`;

    // Header Countdown Logic
    const updateCountdown = () => {
      const now = new Date();
      const mins = now.getMinutes();
      const nextMark = Math.ceil((mins + 1) / 15) * 15;
      const diff = nextMark - mins;
      const footer = document.getElementById('sync-footer');
      if (footer) {
        footer.textContent = `NEXT UPDATE: ~${diff} MIN`;
      }
    };
    updateCountdown();
    setInterval(updateCountdown, 60000);

    renderTicker(tickerEl, data.quotes);
    renderUSPulse(document.getElementById('us-indices'), data.quotes);
    renderJPPulse(document.getElementById('jp-indices'), data.quotes);
    renderAIAnalysis(document.getElementById('ai-overview'), data.overview);
    renderNewsWire(document.getElementById('top-news-feed'), data.news);
    renderVisuals(document.getElementById('charts-main'), data.charts);

  } catch (err) {
    console.error('Bootstrap error:', err);
    syncStatus.textContent = 'SYNC ERROR';
  }
}

function renderTicker(el, quotes) {
  if (!el || !quotes) return;
  const list = Object.values(quotes).filter(q => q && q.symbol);
  const content = list.map(q => {
    const chgPct = Number(q.changesPercentage ?? q.change_percent ?? 0);
    const price = Number(q.price ?? 0);
    const cls = chgPct >= 0 ? 'up' : 'down';
    const sign = chgPct >= 0 ? '+' : '';
    return `<span class="ticker-item"><strong>${q.symbol}</strong> <span class="${cls}">${price.toLocaleString()}</span> (<span class="${cls}">${sign}${chgPct.toFixed(2)}%</span>)</span>`;
  }).join(' ');
  el.innerHTML = content + ' ' + content;
}

function renderUSPulse(el, quotes) {
  if (!el || !quotes) return;
  const usQuotes = Object.entries(quotes).filter(([sym]) => sym.indexOf('.') === -1 && !sym.startsWith('^'));
  renderCompactPulse(el, usQuotes);
}

function renderJPPulse(el, quotes) {
  if (!el || !quotes) return;
  const jpQuotes = Object.entries(quotes).filter(([sym]) => sym.endsWith('.T'));
  renderCompactPulse(el, jpQuotes);
}

function renderCompactPulse(el, filteredQuotes) {
  if (!el) return;
  el.innerHTML = filteredQuotes.slice(0, 20).map(([symbol, q], i) => {
    const chgPct = parseFloat(q.changesPercentage || q.change_percent || 0);
    const upDownClass = chgPct >= 0 ? 'up' : 'down';
    const price = parseFloat(q.price || 0);
    let displayName = q.name || symbol;
    if (displayName.length > 15) displayName = displayName.substring(0, 13) + '..';

    return `
            <div class="mini-card ${upDownClass} animate-up" style="animation-delay: ${0.2 + (i * 0.02)}s">
                <span class="mini-symbol" title="${symbol}">${displayName}</span>
                <div class="mini-price-group">
                    <span class="mini-price">${price.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</span>
                    <span class="mini-pct">${chgPct >= 0 ? '+' : ''}${chgPct.toFixed(2)}%</span>
                </div>
            </div>
        `;
  }).join('');
}

let currentNewsData = [];
let currentAIData = { us: '', jp: '' };

function renderAIAnalysis(el, overview) {
  if (!overview) return;
  const usFull = (overview.us_overview || overview.us || '');
  const jpFull = (overview.jp_overview || overview.jp || '');
  currentAIData = { us: usFull, jp: jpFull };
  const usShort = usFull.length > 200 ? usFull.substring(0, 200) + '...' : usFull;
  const jpShort = jpFull.length > 200 ? jpFull.substring(0, 200) + '...' : jpFull;

  el.innerHTML = `
        <div class="animate-up" style="animation-delay: 0.4s">
            <h3 style="color:var(--accent-blue); font-size: 0.8rem; margin-bottom: 0.5rem;">U.S. STRATEGY SUMMARY</h3>
            <div class="overview-content" style="margin-bottom: 1.5rem;">
                ${usShort.replace(/\n/g, '<br>')}
                ${usFull.length > 200 ? `<button class="read-more-btn" onclick="openAIModal('US')">READ FULL ANALYSIS ↘</button>` : ''}
            </div>
            <h3 style="color:var(--accent-blue); font-size: 0.8rem; margin-bottom: 0.5rem;">JAPAN STRATEGY SUMMARY</h3>
            <div class="overview-content">
                ${jpShort.replace(/\n/g, '<br>')}
                ${jpFull.length > 200 ? `<button class="read-more-btn" onclick="openAIModal('JP')">READ FULL ANALYSIS ↘</button>` : ''}
            </div>
        </div>
    `;
}

window.openAIModal = function (market) {
  const body = market === 'US' ? currentAIData.us : currentAIData.jp;
  document.getElementById('ai-modal-title').textContent = market + ' Market Strategy';
  document.getElementById('ai-modal-body').innerHTML = body.replace(/\n/g, '<br>');
  document.getElementById('ai-modal').classList.add('active');
};

window.closeAIModal = function () { document.getElementById('ai-modal').classList.remove('active'); };

function renderNewsWire(el, news) {
  if (!news) return;
  currentNewsData = [...news].sort(() => Math.random() - 0.5);
  el.innerHTML = currentNewsData.slice(0, 15).map((n, i) => `
        <div class="news-card animate-up" style="animation-delay: ${0.5 + (i * 0.05)}s" onclick="openNewsModal(${i})">
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 0.6rem; color: var(--text-secondary); margin-bottom: 2px;">
                <span style="color:var(--accent-blue);">${(n.category || 'GENERAL').toUpperCase()}</span> | ${n.source || 'Unknown'}
              </div>
              <h4 style="white-space: normal; line-height: 1.4;">${n.headline}</h4>
            </div>
            <span style="color: var(--accent-blue); font-size: 0.7rem; margin-left:10px;">DETAIL ↗</span>
        </div>
    `).join('');
}

window.openNewsModal = function (index) {
  const n = currentNewsData[index];
  if (!n) return;
  document.getElementById('modal-title').textContent = n.headline;
  document.getElementById('modal-body').textContent = n.summary || 'No detail available.';
  const linkEl = document.getElementById('modal-link');
  linkEl.href = n.url || '#';
  linkEl.style.display = n.url ? 'inline-block' : 'none';
  document.getElementById('news-modal').classList.add('active');
};

window.closeNewsModal = function () { document.getElementById('news-modal').classList.remove('active'); };

function renderVisuals(el, charts) {
  if (!el || !charts) return;
  const ts = new Date().getTime();
  let html = '';
  Object.entries(charts).forEach(([name, paths], i) => {
    const s = paths.short ? paths.short.split(/[\\/]/).slice(-2).join('/') : '';
    const l = paths.long ? paths.long.split(/[\\/]/).slice(-2).join('/') : '';
    if (s) html += `<div class="chart-item"><p style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.5rem;">${name} (1Y)</p><img src="${s}?v=${ts}" class="chart-img" onclick="window.open('${s}?v=${ts}', '_blank')"></div>`;
    if (l) html += `<div class="chart-item"><p style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.5rem;">${name} (LT)</p><img src="${l}?v=${ts}" class="chart-img" onclick="window.open('${l}?v=${ts}', '_blank')"></div>`;
  });
  el.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', bootstrap);
