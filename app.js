const STORAGE_KEY = 'uiv-deep-reads-read';
const DATA_URL = 'data/articles.json';

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? url : '#';
  } catch {
    return '#';
  }
}

let allArticles = [];
let activeSectors = new Set();
let activeTypes = new Set();
let unreadOnly = false;

function getReadIds() {
  try {
    return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'));
  } catch {
    return new Set();
  }
}

function markRead(id) {
  const ids = getReadIds();
  ids.add(id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

function getVisibleArticles() {
  const readIds = getReadIds();
  return allArticles.filter(a => {
    if (unreadOnly && readIds.has(a.id)) return false;
    if (activeSectors.size > 0 && !a.sectors.some(s => activeSectors.has(s))) return false;
    if (activeTypes.size > 0 && !activeTypes.has(a.source_type)) return false;
    return true;
  });
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function renderCard(article, isRead) {
  const card = document.createElement('article');
  card.className = `card${isRead ? ' read' : ''}`;
  card.dataset.id = article.id;

  const sectorTags = article.sectors
    .map(s => `<span class="tag">${esc(s)}</span>`)
    .join('');

  const url = safeUrl(article.url);

  card.innerHTML = `
    <div class="card-meta">
      ${sectorTags}
      <span class="source">${esc(article.source_name)}</span>
      <span class="dot">·</span>
      <span class="read-time">${esc(article.estimated_read_minutes)} min</span>
      <span class="dot">·</span>
      <span class="date">${esc(formatDate(article.published_at))}</span>
    </div>
    <h2 class="card-title">
      <a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(article.title)}</a>
    </h2>
    <p class="excerpt">${esc(article.excerpt)}</p>
    ${article.signal ? `<p class="signal"><strong>VC Signal:</strong> ${esc(article.signal)}</p>` : ''}
    <div class="card-actions">
      <a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="btn-read">
        Open article ↗
      </a>
      ${isRead
        ? '<span class="read-label">Read ✓</span>'
        : `<button class="btn-mark-read" data-id="${esc(article.id)}">Mark as read ✓</button>`
      }
    </div>
  `;
  return card;
}

function render() {
  const container = document.getElementById('articles');
  const empty = document.getElementById('empty-state');
  const readIds = getReadIds();
  const visible = getVisibleArticles();

  container.innerHTML = '';

  if (visible.length === 0) {
    empty.hidden = false;
    return;
  }

  empty.hidden = true;
  visible.forEach(a => container.appendChild(renderCard(a, readIds.has(a.id))));

  container.querySelectorAll('.btn-mark-read').forEach(btn => {
    btn.addEventListener('click', () => {
      markRead(btn.dataset.id);
      render();
    });
  });
}

function buildFilters() {
  const presentSectors = [...new Set(allArticles.flatMap(a => a.sectors))].sort();
  const presentTypes = [...new Set(allArticles.map(a => a.source_type))].sort();

  const sectorContainer = document.getElementById('sector-filters');
  presentSectors.forEach(sector => {
    const pill = document.createElement('button');
    pill.className = 'pill';
    pill.textContent = sector;
    pill.addEventListener('click', () => {
      activeSectors.has(sector) ? activeSectors.delete(sector) : activeSectors.add(sector);
      pill.classList.toggle('active');
      render();
    });
    sectorContainer.appendChild(pill);
  });

  const typeContainer = document.getElementById('type-filters');
  presentTypes.forEach(type => {
    const pill = document.createElement('button');
    pill.className = 'pill';
    pill.textContent = type;
    pill.addEventListener('click', () => {
      activeTypes.has(type) ? activeTypes.delete(type) : activeTypes.add(type);
      pill.classList.toggle('active');
      render();
    });
    typeContainer.appendChild(pill);
  });

  document.getElementById('unread-only').addEventListener('change', e => {
    unreadOnly = e.target.checked;
    render();
  });
}

async function init() {
  try {
    const resp = await fetch(DATA_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    allArticles = data.articles || [];
    buildFilters();
    render();
  } catch (err) {
    document.getElementById('articles').innerHTML =
      `<p class="empty-state">Could not load articles. Run the collector first.</p>`;
  }
}

init();
