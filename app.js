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
    // Add cache-buster to ensure the latest data is always fetched
    const dataPath = `./data/latest_report.json?v=${new Date().getTime()}`;
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
    // Apply the color class to the entire ticker item content
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

  // Truncate to approx 200 chars
  const usShort = usFull.length > 200 ? usFull.substring(0, 200) + '...' : usFull;
  const jpShort = jpFull.length > 200 ? jpFull.substring(0, 200) + '...' : jpFull;

  el.innerHTML = `
        <div class="animate-up" style="animation-delay: 0.4s">
            <h3 style="color:var(--accent-blue); font-size: 0.8rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                U.S. STRATEGY SUMMARY
            </h3>
            <div class="overview-content" style="margin-bottom: 0.5rem;">
                ${usShort.replace(/\n/g, '<br>')}
                ${usFull.length > 200 ? `<button class="read-more-btn" onclick="openAIModal('US')">READ FULL ANALYSIS ↘</button>` : ''}
            </div>
            <h3 style="color:var(--accent-blue); font-size: 0.8rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
                JAPAN STRATEGY SUMMARY
            </h3>
            <div class="overview-content">
                ${jpShort.replace(/\n/g, '<br>')}
                ${jpFull.length > 200 ? `<button class="read-more-btn" onclick="openAIModal('JP')">READ FULL ANALYSIS ↘</button>` : ''}
            </div>
        </div>
    `;
}

window.openAIModal = function (market) {
  const title = market === 'US' ? 'U.S. Market Strategy (Full Detail)' : 'Japan Market Strategy (Full Detail)';
  const body = market === 'US' ? currentAIData.us : currentAIData.jp;

  document.getElementById('ai-modal-title').textContent = title;
  document.getElementById('ai-modal-body').innerHTML = body.replace(/\n/g, '<br>');
  document.getElementById('ai-modal').classList.add('active');
};

window.closeAIModal = function () {
  document.getElementById('ai-modal').classList.remove('active');
};

function renderNewsWire(el, news) {
  if (!news) return;
  // Mix categories to avoid displaying only one type at the top
  const shuffled = [...news].sort(() => Math.random() - 0.5);
  currentNewsData = shuffled;

  el.innerHTML = currentNewsData.slice(0, 15).map((n, i) => `
        <div class="news-card animate-up" style="animation-delay: ${0.5 + (i * 0.05)}s" onclick="openNewsModal(${i})">
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 0.6rem; color: var(--text-secondary); margin-bottom: 2px; font-weight: 700;">
                <span style="color:var(--accent-blue);">${(n.category || 'GENERAL').toUpperCase()}</span> | ${n.source || 'Unknown Source'}
              </div>
              <h4 style="white-space: normal; line-height: 1.4;">${n.headline}</h4>
            </div>
            <span style="color: var(--accent-blue); font-size: 0.7rem; flex-shrink:0; margin-left: 10px;">DETAIL ↗</span>
        </div>
    `).join('');
}

window.openNewsModal = function (index) {
  const n = currentNewsData[index];
  if (!n) return;

  let url = n.url || '';
  if (url && !url.startsWith('http')) {
    url = 'https://' + url;
  }

  document.getElementById('modal-source').textContent = (n.category || 'GENERAL') + ' | SOURCE: ' + (n.source || 'UNKNOWN');
  document.getElementById('modal-title').textContent = n.headline;
  document.getElementById('modal-body').textContent = n.summary || '詳細情報はありません。';

  const linkEl = document.getElementById('modal-link');
  if (url) {
    linkEl.href = url;
    linkEl.style.display = 'inline-block';
    console.log('Set link href to:', url);
  } else {
    linkEl.style.display = 'none';
  }

  document.getElementById('news-modal').classList.add('active');
};

window.closeNewsModal = function () {
  document.getElementById('news-modal').classList.remove('active');
};

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
