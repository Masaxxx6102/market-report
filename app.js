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
    const dataPath = './data/latest_report.json';
    console.log(`Attempting to fetch data from: ${dataPath}`);

    const response = await fetch(dataPath);
    if (!response.ok) {
      console.error('Fetch failed:', response.status, response.statusText);
      throw new Error(`Data file missing (HTTP ${response.status}). Please ensure Daily Market Report Automation has run successfully and committed the data.`);
    }
    const data = await response.json();

    syncStatus.textContent = `LAST SYNC: ${data.last_updated}`;

    // 1. Ticker Logic (Endless loop)
    renderTicker(tickerEl, data.quotes);

    // 2. Mini Pulse (Left Heatmap)
    renderUSPulse(document.getElementById('us-indices'), data.quotes);
    renderJPPulse(document.getElementById('jp-indices'), data.quotes);

    // 3. AI Intelligence (Center)
    renderAIAnalysis(document.getElementById('ai-overview'), data.overview);

    // 4. News Wire (Right)
    renderNewsWire(document.getElementById('top-news-feed'), data.news);

    // 5. Visuals (Center Bottom)
    renderVisuals(document.getElementById('charts-main'), data.charts);

  } catch (err) {
    console.error('Bootstrap error:', err);
    syncStatus.textContent = 'SYNC ERROR';
    const aiEl = document.getElementById('ai-overview'); // Re-get aiEl here if needed for error display
    if (aiEl) {
      aiEl.innerHTML = `
        <div style="color: var(--accent-down); padding: 20px; border: 1px solid var(--accent-down); border-radius: 12px; background: rgba(255, 0, 85, 0.05);">
          <h3 style="margin-bottom: 10px;">❌ 同期エラー</h3>
          <p style="font-size: 0.9rem; margin-bottom: 15px;">データの取得に失敗しました。以下の詳細情報を教えていただけますか？</p>
          <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; font-family: monospace; font-size: 0.8rem; overflow-x: auto;">
            <strong>Error:</strong> ${err.message}<br>
            <strong>URL:</strong> ${window.location.href}<br>
            <strong>Data Path:</strong> ./data/latest_report.json
          </div>
          <p style="font-size: 0.8rem; margin-top: 15px; color: var(--text-secondary);">
            ※GitHubの [Actions] > [Daily Market Report Automation] が一度も成功していない、またはファイルの保存に失敗している可能性があります。
          </p>
        </div>
      `;
    }
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
    return `<span class="ticker-item"><strong>${q.symbol}</strong> ${price.toLocaleString()} (<span class="${cls}">${sign}${chgPct.toFixed(2)}%</span>)</span>`;
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
    const displayName = q.name || symbol;

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

function renderAIAnalysis(el, overview) {
  if (!overview) return;
  const usText = (overview.us_overview || overview.us || '').replace(/\n/g, '<br>');
  const jpText = (overview.jp_overview || overview.jp || '').replace(/\n/g, '<br>');
  el.innerHTML = `
        <div class="animate-up" style="animation-delay: 0.4s">
            <h3 style="color:var(--accent-blue); font-size: 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">🇺🇸</span> U.S. STRATEGY SUMMARY
            </h3>
            <p style="font-size: 0.95rem; line-height: 1.7; color: #ced4da; margin-bottom: 2rem;">
                ${usText}
            </p>
            <h3 style="color:var(--accent-blue); font-size: 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">🇯🇵</span> JAPAN STRATEGY SUMMARY
            </h3>
            <p style="font-size: 0.95rem; line-height: 1.7; color: #ced4da;">
                ${jpText}
            </p>
        </div>
    `;
}

function renderNewsWire(el, news) {
  el.innerHTML = (news || []).slice(0, 8).map((n, i) => `
        <a href="${n.url}" target="_blank" class="news-card animate-up" style="animation-delay: ${0.5 + (i * 0.05)}s">
            <h4>${n.headline}</h4>
            <p>${n.summary || ''}</p>
        </a>
    `).join('');
}

function renderVisuals(el, charts) {
  if (!el || !charts) return;

  const ts = new Date().getTime();
  let html = '';
  Object.entries(charts).forEach(([name, paths], i) => {
    const shortPath = paths.short ? paths.short.split(/[\\/]/).slice(-2).join('/') : '';
    const longPath = paths.long ? paths.long.split(/[\\/]/).slice(-2).join('/') : '';

    // Add Short Chart
    if (shortPath) {
      const url = `${shortPath}?v=${ts}`;
      html += `
        <div class="chart-item animate-up" style="animation-delay: ${0.6 + (i * 0.1)}s">
            <p style="font-size: 0.7rem; color: var(--text-secondary); margin-bottom: 0.5rem; font-weight: 700;">${name.toUpperCase()} (1 YEAR / WEEKLY)</p>
            <img src="${url}" class="chart-img" alt="${name} short" onclick="window.open('${url}', '_blank')">
        </div>
      `;
    }

    // Add Long Chart
    if (longPath) {
      const url = `${longPath}?v=${ts}`;
      html += `
        <div class="chart-item animate-up" style="animation-delay: ${0.65 + (i * 0.1)}s">
            <p style="font-size: 0.7rem; color: var(--text-secondary); margin-bottom: 0.5rem; font-weight: 700;">${name.toUpperCase()} (LONG TERM / MONTHLY)</p>
            <img src="${url}" class="chart-img" alt="${name} long" onclick="window.open('${url}', '_blank')">
        </div>
      `;
    }
  });
  el.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', bootstrap);
