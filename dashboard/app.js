'use strict';

/* Cluefolio Studio OS — local dashboard
   Everything is rendered from /content/dashboard.json. No build step. */

const DATA_URL = '/content/dashboard.json';
const IG_LIMIT = 2200;
const FB_LIMIT = 2252;

const COPY = new Map();
let copySeq = 0;
let searchTimer = null;
let toastTimer = null;

const state = {
  data: null,
  filter: 'all',
  assetFilter: 'all',
  postTab: 'instagram',
  seoTab: 'onpage',
  galleryIndex: 0,
  postKey: null,
  lastHash: null,
};

const view = document.getElementById('view');
const searchInput = document.getElementById('global-search');
const toastEl = document.getElementById('toast');
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxCap = document.getElementById('lightbox-cap');

const GATE_LABELS = {
  G1_greenlight: 'G1 Greenlight',
  G2_factual_lock: 'G2 Factual lock',
  G3_rights_clearance: 'G3 Rights',
  G4_story_approval: 'G4 Story',
  G5_clearance: 'G5 Standards',
  G6_qa_signoff: 'G6 QA',
};

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
  'August', 'September', 'October', 'November', 'December'];

/* ---------- helpers ---------- */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function esc(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]));
}

function num(value) {
  return Number(value || 0).toLocaleString('en-US');
}

function icon(name) {
  return `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
}

function humanize(key) {
  return String(key).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function imgUrl(post, file) {
  return `/content/${encodeURIComponent(post.slug)}/images/${encodeURIComponent(file)}`;
}

function postBy(param) {
  if (!state.data) return null;
  return state.data.posts.find((p) => p.number === param || p.slug === param) || null;
}

function allImages() {
  const rows = [];
  state.data.posts.forEach((post) => {
    post.images.forEach((img) => rows.push({ post, img }));
  });
  return rows;
}

function statusBadge(post) {
  return `<span class="badge ${post.status}"><span class="dot"></span>${esc(post.status_label)}</span>`;
}

function copyBtn(text, label = 'Copy') {
  const id = `copy-${++copySeq}`;
  COPY.set(id, text);
  return `<button type="button" class="copy-btn" data-copy="${id}">${icon('copy')}${esc(label)}</button>`;
}

function tagCloud(items, cls = '') {
  return `<div class="tag-cloud">${items.map((t) => `<span class="tag ${cls}">${esc(t)}</span>`).join('')}</div>`;
}

function field(label, value, opts = {}) {
  if (value == null || value === '') return '';
  const body = opts.html ? value : esc(value);
  return `<div class="field">
    <div class="k"><span>${esc(label)}</span>${opts.copy ? copyBtn(String(value), 'Copy') : ''}</div>
    <div class="v ${opts.cls || ''}">${body}</div>
  </div>`;
}

function charLine(length, limit, note = '') {
  const ok = length <= limit;
  return `<div class="charline"><span class="${ok ? 'ok' : 'warn'}">${num(length)} / ${num(limit)} characters</span><span>${esc(note)}</span></div>`;
}

function kpi(label, value, hint, suffix = '') {
  return `<div class="kpi"><div class="label">${esc(label)}</div><div class="value">${esc(value)}${suffix ? `<small>${esc(suffix)}</small>` : ''}</div><div class="hint">${esc(hint)}</div></div>`;
}

function emptyState(title, body) {
  return `<div class="empty"><h2>${esc(title)}</h2><p>${esc(body)}</p></div>`;
}

function monthLabel(key) {
  const [year, month] = key.split('-');
  return `${MONTHS[Number(month) - 1] || month} ${year}`;
}

function dayOf(date) {
  return String(Number(date.slice(8, 10)));
}

function shortWeekday(date) {
  const d = new Date(`${date}T12:00:00`);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('en-US', { weekday: 'short' });
}

function postCard(post) {
  return `<a class="post-card" href="#/post/${esc(post.number)}">
    <div class="cover">
      <img src="${imgUrl(post, post.cover)}" alt="${esc(post.captions.alt_text)}" loading="lazy">
      <div class="top"><span class="num">${esc(post.number)}</span>${statusBadge(post)}</div>
    </div>
    <div class="body">
      <span class="badge cat">${esc(post.category)}</span>
      <h3>${esc(post.title)}</h3>
      <p class="angle">${esc(post.angle)}</p>
      <div class="foot"><span>${esc(post.display_date)} · ${post.image_count} image${post.image_count === 1 ? '' : 's'}</span><span class="score">${post.viral_readiness.total}/40</span></div>
    </div>
  </a>`;
}

function titleCell(post) {
  return `<a href="#/post/${esc(post.number)}" class="title-cell" style="display:block">${esc(post.title)}<br><span class="small mono">${esc(post.number)}</span></a>`;
}

function chk(value, min, max) {
  const len = String(value).length;
  const ok = len >= min && len <= max;
  return `<span class="${ok ? 'ok' : 'warn'}">${len}</span>`;
}

/* ---------- data ---------- */

async function loadData(force = false) {
  const res = await fetch(`${DATA_URL}${force ? `?t=${Date.now()}` : ''}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  state.data = await res.json();
  const meta = state.data.meta;
  const count = document.getElementById('nav-post-count');
  const sidebarPosts = document.getElementById('sidebar-posts');
  const sidebarImages = document.getElementById('sidebar-images');
  if (count) count.textContent = meta.total_posts;
  if (sidebarPosts) sidebarPosts.textContent = `${meta.total_posts} posts`;
  if (sidebarImages) sidebarImages.textContent = `${meta.total_images} images`;
}

/* ---------- routing ---------- */

function parseRoute() {
  const raw = location.hash.replace(/^#\/?/, '');
  const [pathPart, qs = ''] = raw.split('?');
  const parts = pathPart.split('/').filter(Boolean);
  return {
    name: parts[0] || 'overview',
    param: parts[1] ? decodeURIComponent(parts[1]) : null,
    query: new URLSearchParams(qs),
  };
}

const NAV_MAP = {
  overview: 'overview', posts: 'posts', post: 'posts', search: 'posts',
  calendar: 'calendar', pipeline: 'pipeline', seo: 'seo', assets: 'assets', playbook: 'playbook',
};

const CRUMBS = {
  overview: 'Overview', posts: 'Posts', post: 'Post package', search: 'Search',
  calendar: 'Calendar', pipeline: 'Pipeline', seo: 'SEO & SMM', assets: 'Assets', playbook: 'Playbook',
};

const TITLES = {
  overview: 'Overview', posts: 'Posts', post: 'Post package', search: 'Search',
  calendar: 'Calendar', pipeline: 'Pipeline', seo: 'SEO & SMM', assets: 'Assets', playbook: 'Playbook',
};

function render() {
  if (!state.data) return;
  const route = parseRoute();
  const navKey = NAV_MAP[route.name] || 'overview';

  $$('.nav a').forEach((a) => a.classList.toggle('active', a.dataset.nav === navKey));
  const crumb = document.getElementById('crumb-page');
  if (crumb) crumb.textContent = CRUMBS[route.name] || 'Overview';

  view.innerHTML = viewFor(route);

  const post = route.name === 'post' ? postBy(route.param) : null;
  document.title = post
    ? `${post.number} · ${post.title} — Cluefolio Studio`
    : `${TITLES[route.name] || 'Overview'} — Cluefolio Studio OS`;

  const q = route.name === 'search' ? (route.query.get('q') || '') : '';
  if (document.activeElement !== searchInput && searchInput.value !== q) {
    searchInput.value = q;
  }

  if (state.lastHash !== location.hash) {
    window.scrollTo(0, 0);
    state.lastHash = location.hash;
  }
}

function viewFor(route) {
  switch (route.name) {
    case 'overview': return viewOverview();
    case 'posts': return viewPosts();
    case 'post': return viewPost(route.param);
    case 'calendar': return viewCalendar();
    case 'pipeline': return viewPipeline();
    case 'seo': return viewSeo();
    case 'assets': return viewAssets();
    case 'playbook': return viewPlaybook();
    case 'search': return viewSearch(route.query.get('q') || '');
    default: return emptyState('Page not found', 'Use the navigation to pick a section.');
  }
}

/* ---------- overview ---------- */

function viewOverview() {
  const d = state.data;
  const m = d.meta;
  const next = d.posts.find((p) => p.number === m.next_post)
    || d.posts.find((p) => p.status === 'ready')
    || d.posts[0];

  const igTags = d.posts.reduce((n, p) => n + p.ig_tags, 0);
  const fbTags = d.posts.reduce((n, p) => n + p.fb_tags, 0);
  const aiImages = allImages().filter((row) => row.img.ai).length;

  const phaseDefs = [
    { label: 'Research & fact-check', test: (i) => i <= 3 },
    { label: 'Visuals & render', test: (i) => i >= 4 && i <= 6 },
    { label: 'Story & copy', test: (i) => i >= 7 && i <= 8 },
    { label: 'Standards & QA', test: (i) => i >= 9 && i <= 10 },
    { label: 'Ready to publish', test: (i) => i >= 11 },
  ];
  const phases = phaseDefs.map((def) => ({
    label: def.label,
    count: d.posts.filter((p) => def.test(p.pipeline.stage_index)).length,
  }));
  const maxPhase = Math.max(...phases.map((p) => p.count), 1);

  return `
  <section class="hero-banner">
    <div class="eyebrow">Season One · Local command center · Generated ${esc(m.generated)}</div>
    <h1>Eleven stories. Every claim traceable.</h1>
    <p class="lede">${esc(m.season)}. ${esc(m.cadence)}</p>
    <div class="actions">
      <a class="btn accent" href="#/post/${esc(next.number)}">Open Post ${esc(next.number)} ${icon('arrow')}</a>
      <a class="btn ghost" href="#/calendar">${icon('calendar')} Content calendar</a>
      <a class="btn ghost" href="#/seo">${icon('search')} SEO &amp; SMM</a>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><strong>${num(m.total_posts)}</strong><span>Stories in season</span></div>
      <div class="hero-stat"><strong>${num(m.total_images)}</strong><span>Cleared images</span></div>
      <div class="hero-stat"><strong>${num(m.total_story_words)}</strong><span>Story words</span></div>
      <div class="hero-stat"><strong>${num(m.avg_viral_score)}</strong><span>Avg viral score</span></div>
    </div>
  </section>

  <div class="kpis">
    ${kpi('Ready to publish', num(m.ready), 'All six gates passed')}
    ${kpi('In draft', num(m.draft), 'Awaiting Gate 2 fact-check')}
    ${kpi('Hashtags mapped', num(igTags + fbTags), `${igTags} Instagram · ${fbTags} Facebook`)}
    ${kpi('AI reconstructions', num(aiImages), 'Labeled on image and caption')}
    ${kpi('Next package', `#${esc(m.next_post)}`, next.display_date)}
  </div>

  <div class="overview-grid">
    <article class="feature-card">
      <a class="feature-cover" href="#/post/${esc(next.number)}">
        <img src="${imgUrl(next, next.cover)}" alt="${esc(next.captions.alt_text)}">
      </a>
      <div class="feature-body">
        <div class="eyebrow">Next package · Post ${esc(next.number)} · ${esc(next.display_date)}</div>
        <h3>${esc(next.title)}</h3>
        <div class="feature-meta">${statusBadge(next)}<span class="badge cat">${esc(next.category)}</span><span class="badge blue">Viral ${next.viral_readiness.total}/40</span></div>
        <p class="dek">${esc(next.hook)}</p>
        <div class="actions">
          <a class="btn sm" href="#/post/${esc(next.number)}">Open package ${icon('arrow')}</a>
          <a class="btn ghost sm" href="#/calendar">See the season</a>
        </div>
      </div>
    </article>

    <div class="pipeline-mini">
      <h3>Production pipeline</h3>
      <p class="sub">Where the ${num(m.total_posts)} packages sit right now.</p>
      <div class="stage-track">
        ${phases.map((p, i) => `
          <div class="stage-row ${p.count ? 'done' : ''}">
            <span class="num">${i + 1}</span>
            <div>
              <div style="display:flex;justify-content:space-between;gap:8px;font-size:11.5px;color:var(--muted);margin-bottom:4px"><span>${esc(p.label)}</span></div>
              <div class="bar"><i style="width:${Math.max(p.count ? 4 : 0, (p.count / maxPhase) * 100)}%"></i></div>
            </div>
            <span class="cnt">${p.count}</span>
          </div>`).join('')}
      </div>
      <div class="divider"></div>
      <a class="btn ghost sm" href="#/pipeline">${icon('pipeline')} Open pipeline board</a>
    </div>
  </div>

  <div class="section-head">
    <div>
      <div class="eyebrow">The slate</div>
      <h2>Season calendar</h2>
    </div>
    <a class="btn ghost sm" href="#/posts">All posts ${icon('arrow')}</a>
  </div>
  <div class="season-strip">
    ${d.posts.map((p) => `
      <a class="season-card" href="#/post/${esc(p.number)}">
        <div class="thumb">
          <img src="${imgUrl(p, p.cover)}" alt="${esc(p.captions.alt_text)}" loading="lazy">
          ${statusBadge(p)}
        </div>
        <div class="body">
          <div class="date">${esc(p.display_date)}</div>
          <h4>${esc(p.title)}</h4>
        </div>
      </a>`).join('')}
  </div>`;
}

/* ---------- posts ---------- */

function viewPosts() {
  const d = state.data;
  const filters = [
    { id: 'all', label: 'All posts' },
    { id: 'ready', label: 'Ready' },
    { id: 'draft', label: 'Draft' },
  ];
  const list = state.filter === 'all' ? d.posts : d.posts.filter((p) => p.status === state.filter);

  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Content library</div>
      <h1>Posts</h1>
      <p class="lede">${num(d.posts.length)} packages across the season. Two are publish-ready. Nine are drafts until Gate 2 locks the facts.</p>
    </div>
    <div class="actions"><a class="btn ghost sm" href="#/calendar">${icon('calendar')} Calendar view</a></div>
  </div>

  <div class="filters">
    ${filters.map((f) => {
      const count = f.id === 'all' ? d.posts.length : d.posts.filter((p) => p.status === f.id).length;
      return `<button type="button" class="chip ${state.filter === f.id ? 'active' : ''}" data-filter data-scope="posts" data-value="${f.id}">${esc(f.label)}<span class="n">${count}</span></button>`;
    }).join('')}
    <span class="results-line">${list.length} of ${d.posts.length} posts</span>
  </div>

  ${list.length ? `<div class="post-grid">${list.map(postCard).join('')}</div>` : emptyState('Nothing here', 'No posts match this filter.')}`;
}

/* ---------- post detail ---------- */

function viewPost(param) {
  const post = postBy(param);
  if (!post) return emptyState('Post not found', 'That post number is not in the dashboard payload.');

  if (state.postKey !== post.number) {
    state.postKey = post.number;
    state.galleryIndex = 0;
    state.postTab = 'instagram';
  }

  const imgs = post.images.length
    ? post.images
    : [{ file: post.cover, alt: post.captions.alt_text, credit: '', role: 'cover', ai: false }];
  const idx = Math.min(state.galleryIndex, imgs.length - 1);
  const active = imgs[idx];
  const activeSrc = imgUrl(post, active.file);
  const story = Array.isArray(post.story)
    ? post.story
    : String(post.story || '').split(/\n\n+/).filter(Boolean);

  const tabs = [
    ['instagram', 'Instagram'],
    ['facebook', 'Facebook'],
    ['first_comment', 'First comment'],
    ['alt_text', 'Alt text'],
    ['hashtags', 'Hashtags'],
    ['keywords', 'Keywords'],
    ['seo', 'SEO'],
  ];

  return `
  <a class="back-btn" href="#/posts">${icon('arrow')} All posts</a>

  <header class="detail-head">
    <div class="title-block">
      <div class="eyebrow">Post ${esc(post.number)} · ${esc(post.display_date)} · Event ${esc(post.event_date)}</div>
      <h1>${esc(post.title)}</h1>
      <p class="sub">${esc(post.subtitle)}</p>
      <div class="detail-meta">
        ${statusBadge(post)}
        <span class="badge cat">${esc(post.category)}</span>
        <span class="badge blue">${esc(post.publishing.format)}</span>
        <span class="badge cat">Viral ${post.viral_readiness.total}/40</span>
      </div>
    </div>
  </header>

  <div class="detail-grid">
    <div class="detail-left">
      <div class="cover-large">
        <img id="cover-img" src="${activeSrc}" alt="${esc(active.alt)}" data-lightbox data-src="${activeSrc}" data-cap="${esc(`${post.title} — ${active.credit || 'Cluefolio Studio'}`)}">
      </div>
      <div class="thumbs">
        ${imgs.map((im, i) => `
          <button type="button" class="${i === idx ? 'active' : ''}" data-thumb data-index="${i}" data-thumb-src="${imgUrl(post, im.file)}" data-thumb-alt="${esc(im.alt)}" data-thumb-cap="${esc(`${post.title} — ${im.credit || 'Cluefolio Studio'}`)}" title="${esc(im.role)}: ${esc(im.credit)}">
            <img src="${imgUrl(post, im.file)}" alt="${esc(im.alt)}" loading="lazy">
          </button>`).join('')}
      </div>

      <section class="story">
        <div class="eyebrow">Full story · ${num(post.story_words)} words</div>
        <h2>The story</h2>
        ${story.map((para) => `<p>${esc(para)}</p>`).join('')}
        <p class="payoff">${esc(post.payoff)}</p>
        <p class="cta-line">${esc(post.cta)}</p>
      </section>

      <section class="meta-block">
        <h3>Sources</h3>
        <ul class="source-list">${post.sources.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>
        <div class="review-note"><strong>Editorial note.</strong> ${esc(post.review_notes)}</div>
        <div class="disclosure"><strong>Image disclosure.</strong> ${esc(post.ai_disclosure)}</div>
      </section>

      <section class="meta-block">
        <h3>Angle &amp; audience</h3>
        <div class="field-list">
          ${field('Angle', post.angle, { cls: 'big' })}
          ${field('One-line hook', post.hook)}
          ${field('Dek', post.dek)}
          ${field('Audience', post.audience)}
          ${field('Payoff', post.payoff)}
          ${field('Call to action', post.cta)}
        </div>
      </section>
    </div>

    <aside class="detail-right" style="position:static">
      <div style="display:grid;gap:16px">
        <section class="pack">
          <div class="pack-head">
            <h3>Platform pack</h3>
            <span class="small">${num(post.ig_chars)} IG · ${num(post.fb_chars)} FB</span>
          </div>
          <div class="tabs">
            ${tabs.map(([id, label]) => `<button type="button" class="tab ${state.postTab === id ? 'active' : ''}" data-tab data-scope="post" data-value="${id}">${esc(label)}</button>`).join('')}
          </div>
          <div class="pack-body">${packBody(post, state.postTab)}</div>
        </section>

        ${publishingCard(post)}
        ${gatesCard(post)}
        ${viralCard(post)}
      </div>
    </aside>
  </div>`;
}

function packBody(post, tab) {
  const caps = post.captions;

  if (tab === 'facebook') {
    return `
      <div class="copy-row"><span class="label">Facebook caption</span>${copyBtn(caps.facebook, 'Copy caption')}</div>
      <div class="caption-box tall">${esc(caps.facebook)}</div>
      ${charLine(post.fb_chars, FB_LIMIT, `${post.fb_tags} hashtags · house maximum`)}
      <p class="hint">Written natively for Facebook, not pasted from Instagram. The credit sits before the hashtags.</p>`;
  }

  if (tab === 'first_comment') {
    return `
      <div class="copy-row"><span class="label">First comment · pin this</span>${copyBtn(caps.first_comment, 'Copy comment')}</div>
      <div class="caption-box">${esc(caps.first_comment)}</div>
      <p class="hint">Post immediately after publishing and pin it. This is the public source ledger and the correction anchor.</p>`;
  }

  if (tab === 'alt_text') {
    const perImage = post.images.map((im) => `
      <div class="field">
        <div class="k"><span>${esc(im.file)} · ${esc(im.role)}</span>${copyBtn(im.alt, 'Copy')}</div>
        <div class="v">${esc(im.alt)}</div>
      </div>`).join('');
    return `
      <div class="copy-row"><span class="label">Cover alt text</span>${copyBtn(caps.alt_text, 'Copy alt')}</div>
      <div class="caption-box">${esc(caps.alt_text)}</div>
      <p class="hint">Descriptive, not a keyword dump. Paste alt text for every image in the carousel.</p>
      <div class="divider"></div>
      <div class="field-list">${perImage}</div>`;
  }

  if (tab === 'hashtags') {
    return `
      <div class="copy-row"><span class="label">Instagram · ${post.hashtags.instagram.length} tags</span>${copyBtn(post.hashtags.instagram.join(' '), 'Copy tags')}</div>
      ${tagCloud(post.hashtags.instagram)}
      <div class="copy-row" style="margin-top:16px"><span class="label">Facebook · ${post.hashtags.facebook.length} tags</span>${copyBtn(post.hashtags.facebook.join(' '), 'Copy tags')}</div>
      ${tagCloud(post.hashtags.facebook)}
      <p class="hint">Specific beats popular. Instagram 5-6 tags, Facebook 3-4, always after the credit.</p>`;
  }

  if (tab === 'keywords') {
    return `
      ${field('Primary keyword', post.keywords.primary, { cls: 'big', copy: true })}
      <div class="field">
        <div class="k"><span>Secondary keywords · ${post.keywords.secondary.length}</span>${copyBtn(post.keywords.secondary.join(', '), 'Copy')}</div>
        ${tagCloud(post.keywords.secondary, 'kw')}
      </div>
      <div class="field">
        <div class="k"><span>Long-tail queries · ${post.keywords.long_tail.length}</span>${copyBtn(post.keywords.long_tail.join('\n'), 'Copy')}</div>
        <ul class="source-list">${post.keywords.long_tail.map((k) => `<li>${esc(k)}</li>`).join('')}</ul>
      </div>
      <p class="hint">${post.keyword_count} keyword targets mapped for this post across primary, secondary, and long-tail intent.</p>`;
  }

  if (tab === 'seo') {
    return `<div class="field-list">
      ${seoField('SEO title · target 50-60', post.seo.title, 50, 60)}
      ${seoField('Meta description · target 140-160', post.seo.meta_description, 140, 160)}
      ${field('Focus keyword', post.seo.focus_keyword, { copy: true })}
      ${field('Slug', post.seo.slug, { cls: 'mono', copy: true })}
      ${field('Canonical', post.seo.canonical, { cls: 'mono', copy: true })}
      ${seoField('OG title · target 40-60', post.seo.og_title, 40, 60)}
      ${seoField('OG description · target 100-160', post.seo.og_description, 100, 160)}
      ${field('Schema type', post.seo.schema_type)}
      ${field('Image alt text', post.seo.image_alt, { copy: true })}
      ${field('Internal links', post.seo.internal_links.join('  ·  '), { cls: 'mono' })}
    </div>`;
  }

  return `
    <div class="copy-row"><span class="label">Instagram caption</span>${copyBtn(caps.instagram, 'Copy caption')}</div>
    <div class="caption-box tall">${esc(caps.instagram)}</div>
    ${charLine(post.ig_chars, IG_LIMIT, `${post.ig_tags} hashtags · ${num(post.story_words)} story words`)}
    <p class="hint">The first 125 characters are the hook, before the “more” cut. Credit sits before the hashtags.</p>`;
}

function seoField(label, value, min, max) {
  const len = String(value).length;
  const ok = len >= min && len <= max;
  return `<div class="field">
    <div class="k"><span>${esc(label)} · <span class="${ok ? 'ok' : 'warn'}" style="color:var(${ok ? '--green' : '--amber'})">${len} chars</span></span>${copyBtn(String(value), 'Copy')}</div>
    <div class="v">${esc(value)}</div>
  </div>`;
}

function publishingCard(post) {
  return `<section class="pack">
    <div class="pack-head"><h3>Publishing</h3><span class="small">${esc(post.weekday)}</span></div>
    <div class="pack-body"><div class="field-list">
      ${field('Scheduled', `${post.display_date} · ${post.publishing.best_time}`)}
      ${field('Recommended window', post.publishing.recommended_window)}
      ${field('Format', post.publishing.format)}
      ${field('Audience', post.audience)}
      ${field('First comment plan', post.publishing.first_comment)}
      ${field('Disclosure', post.publishing.disclosure)}
    </div></div>
  </section>`;
}

function gatesCard(post) {
  const gates = Object.entries(post.pipeline.gates);
  const passed = gates.filter(([, v]) => v === 'PASS').length;
  return `<section class="pack">
    <div class="pack-head"><h3>Gates</h3><span class="small">${passed}/${gates.length} passed</span></div>
    <div class="pack-body">
      <div class="progress" style="margin-bottom:14px"><i style="width:${post.pipeline.progress}%"></i></div>
      <div class="gate-grid">
        ${gates.map(([key, value]) => `<div class="gate ${value === 'PASS' ? 'pass' : 'pending'}"><span class="g-name">${esc(GATE_LABELS[key] || key)}</span><span class="g-status">${esc(value)}</span></div>`).join('')}
      </div>
      <p class="hint" style="margin-top:12px">Stage: ${esc(post.pipeline.stage)} · Next: ${esc(post.pipeline.next_action)}</p>
    </div>
  </section>`;
}

function viralCard(post) {
  const scores = Object.entries(post.viral_readiness.scores);
  return `<section class="pack">
    <div class="pack-head"><h3>Viral readiness</h3><span class="small">${post.viral_readiness.total}/40</span></div>
    <div class="pack-body">
      <div class="field-list">
        ${scores.map(([key, value]) => `<div class="field">
          <div class="k"><span>${esc(humanize(key))}</span><span>${value}/5</span></div>
          <div class="progress"><i style="width:${(value / 5) * 100}%"></i></div>
        </div>`).join('')}
      </div>
      <p class="hint" style="margin-top:12px">${esc(post.viral_readiness.note)}</p>
    </div>
  </section>`;
}

/* ---------- calendar ---------- */

function viewCalendar() {
  const cal = state.data.calendar;
  const groups = new Map();
  cal.posts.forEach((entry) => {
    const key = entry.date.slice(0, 7);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(entry);
  });

  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Publishing schedule</div>
      <h1>Content calendar</h1>
      <p class="lede">${esc(cal.cadence)}</p>
    </div>
    <div class="actions"><a class="btn ghost sm" href="#/posts">${icon('file')} Post library</a></div>
  </div>
  <div class="review-note" style="margin:0 0 26px">${esc(cal.note)}</div>

  ${Array.from(groups.entries()).map(([key, items]) => `
    <section class="month-block">
      <div class="month-head"><h2>${esc(monthLabel(key))}</h2><span>${items.length} post${items.length === 1 ? '' : 's'}</span></div>
      <div class="cal-list">
        ${items.map((entry) => {
          const post = postBy(entry.number);
          if (!post) return '';
          return `<a class="cal-row" href="#/post/${esc(entry.number)}">
            <div class="cal-date"><strong>${dayOf(entry.date)}</strong><span>${esc(shortWeekday(entry.date))}</span></div>
            <div class="cal-thumb"><img src="${imgUrl(post, post.cover)}" alt="${esc(post.captions.alt_text)}" loading="lazy"></div>
            <div class="cal-body">
              <h3>${esc(entry.title)}</h3>
              <p>${esc(entry.category)} — ${esc(entry.angle)}</p>
            </div>
            <div class="cal-meta">
              ${statusBadge(post)}
              ${post.images.some((im) => im.ai) ? '<span class="badge ai">AI cover</span>' : ''}
              <span class="badge cat">${entry.provisional_score}/40</span>
              <span class="small">${post.image_count} img</span>
            </div>
          </a>`;
        }).join('')}
      </div>
    </section>`).join('')}`;
}

/* ---------- pipeline ---------- */

function viewPipeline() {
  const d = state.data;
  const groups = new Map();
  d.posts.forEach((post) => {
    const key = post.pipeline.stage;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(post);
  });
  const ordered = Array.from(groups.entries()).sort((a, b) => a[1][0].pipeline.stage_index - b[1][0].pipeline.stage_index);

  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Production</div>
      <h1>Pipeline</h1>
      <p class="lede">Eleven packages, six gates, one human publisher. Drafts sit at the visual and copy stage until Gate 2 locks the facts.</p>
    </div>
    <div class="actions"><a class="btn ghost sm" href="#/seo">${icon('check')} SEO checklist</a></div>
  </div>

  <div class="board ${ordered.length <= 2 ? 'two' : ''}">
    ${ordered.map(([stage, posts]) => `
      <div class="column">
        <div class="column-head"><h3>${esc(stage)}</h3><span class="count">${posts.length}</span></div>
        <div class="column-body">
          ${posts.map((post) => `
            <a class="mini-card" href="#/post/${esc(post.number)}">
              <img src="${imgUrl(post, post.cover)}" alt="" loading="lazy">
              <div>
                <h4>${esc(post.title)}</h4>
                <p>${esc(post.number)} · ${post.pipeline.progress}% · ${esc(post.pipeline.next_action)}</p>
              </div>
            </a>`).join('')}
        </div>
      </div>`).join('')}
  </div>

  <div class="section-head" style="margin-top:30px">
    <div><div class="eyebrow">Gate status</div><h2>Every package, every gate</h2></div>
  </div>
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr><th>Post</th><th>Stage</th><th>Progress</th><th>G1</th><th>G2</th><th>G3</th><th>G4</th><th>G5</th><th>G6</th></tr></thead>
      <tbody>
        ${d.posts.map((post) => `<tr>
          <td class="title-cell"><a href="#/post/${esc(post.number)}">${esc(post.number)} · ${esc(post.title)}</a></td>
          <td>${esc(post.pipeline.stage)}</td>
          <td class="num">${post.pipeline.progress}%</td>
          ${Object.values(post.pipeline.gates).map((v) => `<td><span class="chip-mini ${v === 'PASS' ? 'pass' : 'pending'}">${esc(v)}</span></td>`).join('')}
        </tr>`).join('')}
      </tbody>
    </table>
  </div>

  <div class="section-head" style="margin-top:30px">
    <div><div class="eyebrow">Definitions</div><h2>Stage ownership</h2></div>
  </div>
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr><th>#</th><th>Stage</th><th>Owner</th></tr></thead>
      <tbody>
        ${d.pipeline_stages.map((s, i) => `<tr><td class="num">${i + 1}</td><td class="title-cell">${esc(s.label)}</td><td>${esc(s.owner)}</td></tr>`).join('')}
      </tbody>
    </table>
  </div>`;
}

/* ---------- SEO & SMM ---------- */

function viewSeo() {
  const d = state.data;
  const posts = d.posts;
  const titles = posts.map((p) => p.seo.title.length);
  const metas = posts.map((p) => p.seo.meta_description.length);
  const avg = (arr) => Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 10) / 10;
  const metaInRange = metas.filter((n) => n >= 140 && n <= 160).length;
  const tabs = [
    ['onpage', 'On-page SEO'],
    ['keywords', 'Keywords'],
    ['hashtags', 'Hashtags'],
    ['platforms', 'Platform rules'],
  ];

  let body = '';
  if (state.seoTab === 'keywords') {
    body = `
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Post</th><th>Primary keyword</th><th>Secondary keywords</th><th>Long-tail queries</th></tr></thead>
          <tbody>
            ${posts.map((p) => `<tr>
              <td class="title-cell"><a href="#/post/${esc(p.number)}">${esc(p.number)} · ${esc(p.title)}</a></td>
              <td><strong style="color:var(--paper)">${esc(p.keywords.primary)}</strong></td>
              <td class="truncate">${esc(p.keywords.secondary.join(' · '))}</td>
              <td class="truncate">${esc(p.keywords.long_tail.join(' · '))}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>

      <div class="section-head" style="margin-top:30px"><div><div class="eyebrow">Clusters</div><h2>Keyword clusters</h2></div></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Cluster</th><th>Keywords</th><th>Posts</th></tr></thead>
          <tbody>
            ${d.playbook.keyword_clusters.map((c) => `<tr>
              <td class="title-cell">${esc(c.cluster)}</td>
              <td>${esc(c.keywords.join(' · '))}</td>
              <td class="num">${c.keywords.length}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } else if (state.seoTab === 'hashtags') {
    body = `
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Post</th><th>Instagram · 5-6 tags</th><th>Facebook · 3-4 tags</th><th>Total</th></tr></thead>
          <tbody>
            ${posts.map((p) => `<tr>
              <td class="title-cell"><a href="#/post/${esc(p.number)}">${esc(p.number)} · ${esc(p.title)}</a></td>
              <td>${esc(p.hashtags.instagram.join(' '))}</td>
              <td>${esc(p.hashtags.facebook.join(' '))}</td>
              <td class="num">${p.hashtags.instagram.length + p.hashtags.facebook.length}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div class="playbook-grid" style="margin-top:24px">
        <div class="play-card"><div class="mini-label">Instagram</div><p>${esc(d.playbook.hashtag_strategy.instagram)}</p></div>
        <div class="play-card"><div class="mini-label">Facebook</div><p>${esc(d.playbook.hashtag_strategy.facebook)}</p></div>
        <div class="play-card wide"><div class="mini-label">The rule</div><p>${esc(d.playbook.hashtag_strategy.rule)}</p></div>
      </div>`;
  } else if (state.seoTab === 'platforms') {
    body = `
      <div class="playbook-grid">
        <div class="play-card"><div class="mini-label">Instagram</div><p>${esc(d.playbook.platform_rules.instagram)}</p></div>
        <div class="play-card"><div class="mini-label">Facebook</div><p>${esc(d.playbook.platform_rules.facebook)}</p></div>
        <div class="play-card wide"><div class="mini-label">Caption formula</div><ol>${d.playbook.caption_formula.map((x) => `<li>${esc(x)}</li>`).join('')}</ol></div>
        <div class="play-card wide"><div class="mini-label">Cadence</div><p>${esc(d.playbook.cadence)}</p></div>
        <div class="play-card wide"><div class="mini-label">AI image policy</div><p>${esc(d.playbook.ai_policy)}</p></div>
      </div>`;
  } else {
    body = `
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Post</th><th>Focus keyword</th><th>SEO title</th><th>Meta description</th><th>Slug / canonical</th><th>Alt text</th></tr></thead>
          <tbody>
            ${posts.map((p) => `<tr>
              <td class="title-cell"><a href="#/post/${esc(p.number)}">${esc(p.number)} · ${esc(p.title)}</a></td>
              <td><strong style="color:var(--paper)">${esc(p.seo.focus_keyword)}</strong></td>
              <td class="truncate">${esc(p.seo.title)}<br><span class="num">${chk(p.seo.title, 50, 60)} chars</span></td>
              <td class="truncate">${esc(p.seo.meta_description)}<br><span class="num">${chk(p.seo.meta_description, 140, 160)} chars</span></td>
              <td class="mono">/${esc(p.seo.slug)}<br><span class="small">${esc(p.seo.canonical)}</span></td>
              <td class="truncate">${esc(p.seo.image_alt)}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>

      <div class="section-head" style="margin-top:30px"><div><div class="eyebrow">Social metadata</div><h2>Open Graph &amp; schema</h2></div></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Post</th><th>OG title</th><th>OG description</th><th>Schema</th><th>Internal links</th></tr></thead>
          <tbody>
            ${posts.map((p) => `<tr>
              <td class="title-cell"><a href="#/post/${esc(p.number)}">${esc(p.number)} · ${esc(p.title)}</a></td>
              <td class="truncate">${esc(p.seo.og_title)}</td>
              <td class="truncate">${esc(p.seo.og_description)}</td>
              <td><span class="badge blue">${esc(p.seo.schema_type)}</span></td>
              <td class="mono">${esc(p.seo.internal_links.join(' · '))}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>

      <div class="play-card wide" style="margin-top:24px">
        <div class="mini-label">On-page checklist</div>
        <ol>${d.playbook.seo_checklist.map((x) => `<li>${esc(x)}</li>`).join('')}</ol>
      </div>`;
  }

  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Search + social</div>
      <h1>SEO &amp; SMM</h1>
      <p class="lede">One focus keyword per story, platform-native captions, and a hashtag set that describes the post instead of chasing volume.</p>
    </div>
    <div class="actions"><a class="btn ghost sm" href="#/playbook">${icon('book')} Full playbook</a></div>
  </div>

  <div class="kpis">
    ${kpi('SEO titles', `${avg(titles)}`, 'Avg characters · target 50-60')}
    ${kpi('Meta descriptions', `${avg(metas)}`, 'Avg characters · target 140-160')}
    ${kpi('Meta in range', `${metaInRange}/${posts.length}`, '140-160 characters')}
    ${kpi('Keyword targets', num(posts.reduce((n, p) => n + p.keyword_count, 0)), 'Primary + secondary + long-tail')}
    ${kpi('Hashtag assignments', num(posts.reduce((n, p) => n + p.ig_tags + p.fb_tags, 0)), 'Instagram and Facebook')}
  </div>

  <div class="tabs" style="display:inline-flex;border:1px solid var(--line);border-radius:10px;background:var(--surface);margin-bottom:20px">
    ${tabs.map(([id, label]) => `<button type="button" class="tab ${state.seoTab === id ? 'active' : ''}" data-tab data-scope="seo" data-value="${id}">${esc(label)}</button>`).join('')}
  </div>

  ${body}`;
}

/* ---------- assets ---------- */

function viewAssets() {
  const rows = allImages();
  const authentic = rows.filter((r) => !r.img.ai).length;
  const reconstructions = rows.filter((r) => r.img.ai).length;
  const filtered = state.assetFilter === 'all'
    ? rows
    : rows.filter((r) => (state.assetFilter === 'ai' ? r.img.ai : !r.img.ai));

  const filters = [
    ['all', 'All assets', rows.length],
    ['authentic', 'Authentic', authentic],
    ['ai', 'Reconstruction', reconstructions],
  ];

  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Visual library</div>
      <h1>Assets</h1>
      <p class="lede">${authentic} authentic archival images and ${reconstructions} labeled editorial reconstructions. Every asset has a credit and descriptive alt text.</p>
    </div>
  </div>

  <div class="filters">
    ${filters.map(([id, label, count]) => `<button type="button" class="chip ${state.assetFilter === id ? 'active' : ''}" data-filter data-scope="assets" data-value="${id}">${esc(label)}<span class="n">${count}</span></button>`).join('')}
    <span class="results-line">${filtered.length} of ${rows.length} images</span>
  </div>

  <div class="asset-grid">
    ${filtered.map(({ post, img }) => {
      const src = imgUrl(post, img.file);
      const cap = `${post.title} — ${img.credit || 'Cluefolio Studio'}`;
      return `<article class="asset-card">
        <div class="img"><img src="${src}" alt="${esc(img.alt)}" loading="lazy" data-lightbox data-src="${src}" data-cap="${esc(cap)}"></div>
        <div class="body">
          <h4>${esc(post.title)}</h4>
          <p>${esc(post.number)} · ${esc(img.role)} · ${esc(img.file)}</p>
          <p>${esc(img.credit)}</p>
          <div class="row">
            ${img.ai ? '<span class="badge ai">AI reconstruction</span>' : '<span class="badge blue">Authentic</span>'}
            <a class="small" href="#/post/${esc(post.number)}">Open post</a>
          </div>
        </div>
      </article>`;
    }).join('')}
  </div>`;
}

/* ---------- playbook ---------- */

function viewPlaybook() {
  const b = state.data.playbook;
  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Operating manual</div>
      <h1>Playbook</h1>
      <p class="lede">${esc(b.positioning)}</p>
    </div>
  </div>

  <div class="playbook-grid">
    <div class="play-card"><div class="mini-label">Cadence</div><h3>Weekly, with a holiday pause</h3><p>${esc(b.cadence)}</p></div>
    <div class="play-card"><div class="mini-label">AI policy</div><h3>Authentic first</h3><p>${esc(b.ai_policy)}</p></div>

    <div class="play-card wide"><div class="mini-label">Caption formula</div><h3>Eight beats, in order</h3><ol>${b.caption_formula.map((x) => `<li>${esc(x)}</li>`).join('')}</ol></div>

    <div class="play-card wide">
      <div class="mini-label">Hashtag strategy</div>
      <h3>Specific beats popular</h3>
      <div class="playbook-grid" style="margin-top:12px">
        <div><p><strong style="color:var(--paper)">Instagram.</strong> ${esc(b.hashtag_strategy.instagram)}</p></div>
        <div><p><strong style="color:var(--paper)">Facebook.</strong> ${esc(b.hashtag_strategy.facebook)}</p></div>
      </div>
      <p style="margin-top:12px"><strong style="color:var(--paper)">The rule.</strong> ${esc(b.hashtag_strategy.rule)}</p>
    </div>

    <div class="play-card wide">
      <div class="mini-label">Keyword clusters</div>
      <h3>Eleven clusters, one per story</h3>
      <div class="table-wrap" style="margin-top:12px;border:0">
        <table class="data-table" style="min-width:0">
          <thead><tr><th>Cluster</th><th>Keywords</th></tr></thead>
          <tbody>${b.keyword_clusters.map((c) => `<tr><td class="title-cell">${esc(c.cluster)}</td><td>${esc(c.keywords.join(' · '))}</td></tr>`).join('')}</tbody>
        </table>
      </div>
    </div>

    <div class="play-card"><div class="mini-label">SEO checklist</div><h3>Ten checks before publish</h3><ol>${b.seo_checklist.map((x) => `<li>${esc(x)}</li>`).join('')}</ol></div>
    <div class="play-card"><div class="mini-label">Publishing checklist</div><h3>Ten checks before sign-off</h3><ol>${b.publishing_checklist.map((x) => `<li>${esc(x)}</li>`).join('')}</ol></div>

    <div class="play-card wide">
      <div class="mini-label">Platform rules</div>
      <h3>Native to each feed</h3>
      <div class="playbook-grid" style="margin-top:12px">
        <div><p><strong style="color:var(--paper)">Instagram.</strong> ${esc(b.platform_rules.instagram)}</p></div>
        <div><p><strong style="color:var(--paper)">Facebook.</strong> ${esc(b.platform_rules.facebook)}</p></div>
      </div>
    </div>

    <div class="play-card"><div class="mini-label">Measurement</div><h3>What gets read</h3><ul>${b.measurement.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
    <div class="play-card"><div class="mini-label">Engagement</div><h3>How we behave</h3><ul>${b.engagement.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
  </div>`;
}

/* ---------- search ---------- */

function searchPosts(query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  return state.data.posts.filter((p) => {
    const hay = [
      p.number, p.title, p.subtitle, p.category, p.angle, p.hook, p.dek, p.audience,
      p.keywords.primary, ...p.keywords.secondary, ...p.keywords.long_tail,
      ...p.hashtags.instagram, ...p.hashtags.facebook,
      p.seo.title, p.seo.meta_description, p.seo.slug, p.seo.focus_keyword,
    ].join(' ').toLowerCase();
    return terms.every((t) => hay.includes(t));
  });
}

function viewSearch(query) {
  const q = query.trim();
  const results = searchPosts(q);
  return `
  <div class="section-head">
    <div>
      <div class="eyebrow">Search</div>
      <h1>${q ? `Results for “${esc(q)}”` : 'Search the studio'}</h1>
      <p class="lede">${q ? `${results.length} post${results.length === 1 ? '' : 's'} match your query across titles, stories, keywords, hashtags, and SEO fields.` : 'Type in the search box to find a post by title, keyword, hashtag, or claim.'}</p>
    </div>
  </div>
  ${results.length
    ? `<div class="post-grid">${results.map(postCard).join('')}</div>`
    : emptyState('No matches', 'Try a broader term, a post number, or a hashtag.')}`;
}

/* ---------- copy + lightbox ---------- */

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) { /* ignore */ }
    ta.remove();
  }
  if (btn) {
    const original = btn.innerHTML;
    btn.classList.add('done');
    btn.innerHTML = `${icon('check')}Copied`;
    setTimeout(() => {
      btn.classList.remove('done');
      btn.innerHTML = original;
    }, 1400);
  }
  toast('Copied to clipboard');
}

function toast(message) {
  toastEl.textContent = message;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 1800);
}

function openLightbox(src, caption) {
  lightboxImg.src = src;
  lightboxImg.alt = caption || '';
  lightboxCap.textContent = caption || '';
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  lightbox.classList.remove('open');
  lightboxImg.src = '';
  document.body.style.overflow = '';
}

/* ---------- events ---------- */

view.addEventListener('click', (event) => {
  const target = event.target;

  const copyEl = target.closest('[data-copy]');
  if (copyEl) {
    copyText(COPY.get(copyEl.dataset.copy) || '', copyEl);
    return;
  }

  const thumb = target.closest('[data-thumb]');
  if (thumb) {
    const cover = document.getElementById('cover-img');
    if (cover) {
      cover.src = thumb.dataset.thumbSrc;
      cover.dataset.src = thumb.dataset.thumbSrc;
      cover.dataset.cap = thumb.dataset.thumbCap;
      cover.alt = thumb.dataset.thumbAlt;
    }
    $$('.thumbs button').forEach((b) => b.classList.toggle('active', b === thumb));
    state.galleryIndex = Number(thumb.dataset.index) || 0;
    return;
  }

  const lightboxEl = target.closest('[data-lightbox]');
  if (lightboxEl) {
    openLightbox(lightboxEl.dataset.src || lightboxEl.src, lightboxEl.dataset.cap || lightboxEl.alt);
    return;
  }

  const tab = target.closest('[data-tab]');
  if (tab) {
    if (tab.dataset.scope === 'post') state.postTab = tab.dataset.value;
    if (tab.dataset.scope === 'seo') state.seoTab = tab.dataset.value;
    render();
    return;
  }

  const chip = target.closest('[data-filter]');
  if (chip) {
    if (chip.dataset.scope === 'posts') state.filter = chip.dataset.value;
    if (chip.dataset.scope === 'assets') state.assetFilter = chip.dataset.value;
    render();
  }
});

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    const q = searchInput.value.trim();
    if (q) {
      location.hash = `#/search?q=${encodeURIComponent(q)}`;
    } else if (parseRoute().name === 'search') {
      location.hash = '#/posts';
    }
  }, 180);
});

document.getElementById('menu-btn').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

$$('.nav a').forEach((a) => a.addEventListener('click', () => {
  document.getElementById('sidebar').classList.remove('open');
}));

document.getElementById('refresh-btn').addEventListener('click', async (event) => {
  const btn = event.currentTarget;
  btn.disabled = true;
  try {
    await loadData(true);
    render();
    toast('Data refreshed');
  } catch (err) {
    toast(`Refresh failed: ${err.message}`);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
lightbox.addEventListener('click', (event) => {
  if (event.target === lightbox) closeLightbox();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && lightbox.classList.contains('open')) closeLightbox();
});

window.addEventListener('hashchange', render);

/* ---------- live refresh ---------- */

// Poll the compiled payload. Re-render only when something actually changed,
// so scroll position and open panels are not disturbed every minute.
let liveSignature = null;

function signatureOf(data) {
  const meta = data?.meta || {};
  const posts = (data?.posts || []).map((p) => `${p.number}:${p.status}:${p.image_count}`);
  return JSON.stringify([meta.generated, meta.published, meta.ready, posts]);
}

setInterval(async () => {
  if (lightbox.classList.contains('open')) return;
  try {
    await loadData(true);
    const next = signatureOf(state.data);
    if (liveSignature && next !== liveSignature) render();
    liveSignature = next;
  } catch (err) {
    /* server restarted or file being rebuilt; try again next tick */
  }
}, 60000);

/* ---------- boot ---------- */

(async function boot() {
  view.innerHTML = `<div class="empty"><h2>Loading studio data</h2><p>Reading content/dashboard.json…</p></div>`;
  try {
    await loadData();
    liveSignature = signatureOf(state.data);
    if (!location.hash) location.hash = '#/overview';
    render();
  } catch (err) {
    view.innerHTML = emptyState(
      'Could not load dashboard.json',
      `Start the local server first: python dashboard/serve.py — then open http://127.0.0.1:8080/dashboard/. (${err.message})`,
    );
  }
})();
