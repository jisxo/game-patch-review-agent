DASHBOARD_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Game Update Reaction Analyzer</title>
  <style>
    :root { color-scheme: dark; --bg:#10131a; --panel:#191e29; --line:#2a3344;
      --text:#edf2f7; --muted:#9aa7b8; --accent:#67e8b5; --warn:#f6c76a; }
    * { box-sizing: border-box; }
    body { margin:0; font:15px/1.55 system-ui,sans-serif; background:var(--bg); color:var(--text); }
    main { max-width:1180px; margin:auto; padding:40px 20px 72px; }
    h1 { margin:0 0 8px; font-size:clamp(28px,4vw,40px); letter-spacing:-.04em;
      overflow-wrap:anywhere; }
    h2 { margin:0 0 16px; font-size:19px; }
    p { color:var(--muted); }
    .toolbar,.grid,.stats { display:grid; gap:14px; }
    .toolbar { grid-template-columns:1fr auto auto; margin:28px 0; }
    .toolbar > * { min-width:0; }
    select,button { border:1px solid var(--line); border-radius:10px; padding:12px 14px;
      background:var(--panel); color:var(--text); font:inherit; }
    select { width:100%; }
    button { cursor:pointer; background:var(--accent); color:#092219; border:0; font-weight:700; }
    button.secondary { background:#263044; color:var(--text); }
    .grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .stats { grid-template-columns:repeat(3,minmax(0,1fr)); margin-bottom:14px; }
    .panel,.stat { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:20px; }
    .stat strong { display:block; margin-top:5px; font-size:26px; color:var(--accent); }
    ul { margin:0; padding-left:20px; }
    li { margin:9px 0; }
    code { color:var(--accent); font-size:12px; overflow-wrap:anywhere; }
    .full { grid-column:1/-1; }
    .warning { color:var(--warn); }
    #status { min-height:24px; }
    @media(max-width:760px) { .toolbar,.grid,.stats { grid-template-columns:1fr; } }
  </style>
</head>
<body><main>
  <h1>Game Update Reaction Analyzer</h1>
  <p>Steam 한국어 리뷰의 패치 전후 변화를 관측하고 공개 패치 문서 근거를 함께 확인합니다.</p>
  <div class="toolbar">
    <select id="patch"><option>패치 목록 불러오는 중…</option></select>
    <button id="report">분석 리포트</button>
    <button id="coverage" class="secondary">Coverage</button>
  </div>
  <p id="status"></p>
  <section id="content" hidden>
    <div class="stats">
      <div class="stat">Before 리뷰<strong id="before-count">-</strong></div>
      <div class="stat">After 리뷰<strong id="after-count">-</strong></div>
      <div class="stat">추천 비율 변화<strong id="ratio-change">-</strong></div>
    </div>
    <div class="grid">
      <article class="panel"><h2>Observed changes</h2><ul id="observed"></ul></article>
      <article class="panel"><h2>Related public evidence</h2><ul id="evidence"></ul></article>
      <article class="panel full"><h2>Needs verification</h2><ul id="verify"></ul></article>
      <article class="panel full"><h2>Limitations</h2><ul id="limits"></ul></article>
    </div>
  </section>
  <section id="coverage-content" class="panel" hidden><h2>Patch coverage</h2><ul id="coverage-list"></ul></section>
</main>
<script>
const patch = document.querySelector('#patch');
const status = document.querySelector('#status');
const content = document.querySelector('#content');
const coverageContent = document.querySelector('#coverage-content');
const percent = value => value == null ? '-' : `${(value*100).toFixed(1)}%`;
const fill = (id, values, render) => {
  document.querySelector(id).innerHTML = values.map(render).join('');
};
async function json(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
  return response.json();
}
async function loadPatches() {
  const [values, coverage] = await Promise.all([
    json('/patches'), json('/coverage?window_days=7&min_reviews=30')
  ]);
  patch.innerHTML = values.map(item => `<option value="${item.gid}">${item.title}</option>`).join('');
  const eligible = coverage.find(item => item.eligible);
  if (eligible) patch.value = eligible.patch_gid;
  status.textContent = `${values.length}개의 패치 후보를 불러왔습니다.${eligible ? ' 가장 최근 적격 패치를 선택했습니다.' : ''}`;
}
document.querySelector('#report').onclick = async () => {
  status.textContent = '분석 중…'; content.hidden = true; coverageContent.hidden = true;
  try {
    const value = await json(`/reports/${patch.value}?method=bm25&top_k=5`, {method:'POST'});
    const before = value.analysis.before, after = value.analysis.after;
    document.querySelector('#before-count').textContent = before.count;
    document.querySelector('#after-count').textContent = after.count;
    const delta = before.positive_ratio == null || after.positive_ratio == null
      ? null : (after.positive_ratio-before.positive_ratio)*100;
    document.querySelector('#ratio-change').textContent = delta == null ? '-' : `${delta>=0?'+':''}${delta.toFixed(1)}%p`;
    fill('#observed', value.report.observed_changes,
      item => `<li>${item.text}<br><code>${item.evidence_ids.join(', ')}</code></li>`);
    fill('#evidence', value.report.related_public_evidence,
      item => `<li>${item.text}<br><code>${item.evidence_ids.join(', ')}</code></li>`);
    fill('#verify', value.report.needs_verification, item => `<li class="warning">${item}</li>`);
    fill('#limits', value.report.limitations, item => `<li>${item}</li>`);
    content.hidden = false;
    status.textContent = `${value.report.status} · ${value.search_method} · ${percent(after.positive_ratio)}`;
  } catch (error) { status.textContent = `오류: ${error.message}`; }
};
document.querySelector('#coverage').onclick = async () => {
  status.textContent = 'Coverage 계산 중…'; content.hidden = true;
  try {
    const values = await json('/coverage?window_days=7&min_reviews=30');
    fill('#coverage-list', values, item => `<li><strong>${item.title}</strong> — before ${item.before_count}, after ${item.after_count}, eligible ${item.eligible}${item.overlapping_patches.length ? `, overlaps ${item.overlapping_patches.length}` : ''}</li>`);
    coverageContent.hidden = false; status.textContent = `${values.length}개 후보의 coverage입니다.`;
  } catch (error) { status.textContent = `오류: ${error.message}`; }
};
loadPatches().catch(error => status.textContent = `오류: ${error.message}`);
</script></body></html>"""
