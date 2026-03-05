/**
 * Market Insight 3.0 Dashboard Logic
 */
async function bootstrap() {
  const tickerEl = document.getElementById('main-ticker');
  const miniIndEl = document.getElementById('mini-indices');
  const aiEl = document.getElementById('ai-overview');
  const newsEl = document.getElementById('top-news-feed');
  const chartsEl = document.getElementById('charts-main');
  const syncStatus = document.getElementById('sync-status');
  const refreshBtn = document.getElementById('refresh-btn');

  refreshBtn.addEventListener('click', () => {
    refreshBtn.textContent = 'RELOADING...';
    location.reload();
  });

  try {
    const response = await fetch('data/latest_report.json');
    if (!response.ok) throw new Error('Data file missing');
    const data = await response.json();

    syncStatus.textContent = `LAST SYNC: ${data.last_updated}`;

    // 1. Ticker Logic (Endless loop)
    renderTicker(tickerEl, data.quotes);

    // 2. Mini Pulse (Left Heatmap)
    renderMiniPulse(miniIndEl, data.quotes);

    // 3. AI Intelligence (Center)
    renderAIAnalysis(aiEl, data.overview);

    // 4. News Wire (Right)
    renderNewsWire(newsEl, data.news);

    // 5. Visuals (Center Bottom)
    renderVisuals(chartsEl, data.charts);

  } catch (err) {
    syncStatus.textContent = 'SYNC ERROR';
    aiEl.innerHTML = `<div style="color: var(--accent-down); padding: 20px;">FAILED TO DECODE MARKET DATA. PLEASE RUN SYSTEM CHECK.</div>`;
  }
}

function renderTicker(el, quotes) {
  const list = Object.values(quotes);
  const content = list.map(q => {
    const cls = q.change_percent >= 0 ? 'up' : 'down';
    const sign = q.change_percent >= 0 ? '+' : '';
    return `<span class="ticker-item"><strong>${q.symbol}</strong> ${q.price.toLocaleString()} (<span class="${cls}">${sign}${q.change_percent.toFixed(2)}%</span>)</span>`;
  }).join(' ');
  // Double content for smooth loop animation
  el.innerHTML = content + ' ' + content;
}

function renderMiniPulse(el, quotes) {
  const list = Object.values(quotes).slice(0, 12);
  el.innerHTML = list.map(q => {
    const cls = q.change_percent >= 0 ? 'up' : 'down';
    const sign = q.change_percent >= 0 ? '+' : '';
    return `
            <div class="mini-card ${cls}">
                <span class="mini-symbol">${q.name || q.symbol}</span>
                <span class="mini-price">${q.price.toLocaleString(undefined, { minimumFractionDigits: 1 })}</span>
                <span class="mini-pct ${cls}">${sign}${q.change_percent.toFixed(2)}%</span>
            </div>
        `;
  }).join('');
}

function renderAIAnalysis(el, overview) {
  if (!overview) return;
  el.innerHTML = `
        <div class="animate-up" style="animation-delay: 0.4s">
            <h3 style="color:var(--accent-blue); font-size: 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">🇺🇸</span> U.S. STRATEGY SUMMARY
            </h3>
            <p style="font-size: 0.95rem; line-height: 1.7; color: #ced4da; margin-bottom: 2rem;">
                ${overview.us.replace(/\n/g, '<br>')}
            </p>
            <h3 style="color:var(--accent-blue); font-size: 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">🇯🇵</span> JAPAN STRATEGY SUMMARY
            </h3>
            <p style="font-size: 0.95rem; line-height: 1.7; color: #ced4da;">
                ${overview.jp.replace(/\n/g, '<br>')}
            </p>
        </div>
    `;
}

function renderNewsWire(el, news) {
  el.innerHTML = (news || []).slice(0, 8).map((n, i) => `
        <a href="${n.url}" target="_blank" class="news-card animate-up" style="animation-delay: ${0.5 + (i * 0.05)}s">
            <h4>${n.title}</h4>
            <p>${n.summary || ''}</p>
        </a>
    `).join('');
}

function renderVisuals(el, charts) {
  el.innerHTML = Object.entries(charts || {}).map(([name, paths], i) => {
    const relPath = paths.short ? paths.short.split(/[\\/]/).slice(-2).join('/') : '';
    const longPath = paths.long ? paths.long.split(/[\\/]/).slice(-2).join('/') : relPath;
    if (!relPath) return '';
    return `
            <div class="chart-item animate-up" style="animation-delay: ${0.6 + (i * 0.1)}s">
                <p style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.8rem; font-weight: 700;">${name.toUpperCase()}</p>
                <img src="${relPath}" class="chart-img" alt="${name}" onclick="window.open('${longPath}', '_blank')">
            </div>
        `;
  }).join('');
}

document.addEventListener('DOMContentLoaded', bootstrap);
