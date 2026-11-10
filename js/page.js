/* Does the 1974 border still show? Lancashire and Yorkshire in business names, on a plain MapLibre base map (OpenFreeMap
 * Positron). Every OpenStreetMap feature in and around historic Lancashire and Yorkshire whose name says Lancashire, Lancs,
 * Yorkshire or Yorks (and, as a separate layer, Red Rose or White Rose), the historic county line, the line of the Yorkshire
 * counties since 1974, and the areas moved in 1974.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const RED = '#C0392B', NAVY = '#1F3A68';
  const TYPE = { private: 'business, club or venue', chain: 'chain or brand branch', public: 'public body' };
  let map = null, D = null, B = null;
  const state = { private: true, chain: false, public: false, rose: true };
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function filt() {
    const types = Object.keys(TYPE).filter(t => state[t]);
    const f = ['all', ['in', ['get', 't'], ['literal', types]]];
    map.setFilter('pts', f.concat([['==', ['get', 'r'], 0]]));
    map.setFilter('rose', state.rose ? f.concat([['==', ['get', 'r'], 1]]) : ['==', 1, 0]);
    document.querySelectorAll('.chip[data-t]').forEach(x => x.setAttribute('aria-pressed', !!state[x.dataset.t]));
    const n = D.f.filter(x => state[x[5]] && (x[4] === 'L' || x[4] === 'Y')).length;
    document.getElementById('nShown').textContent = n.toLocaleString('en-GB');
  }
  function popup(i, ll) {
    const x = D.f[i];
    const word = { L: 'Lancashire', Y: 'Yorkshire', rL: 'Red Rose (Lancashire’s emblem)', rY: 'White Rose (Yorkshire’s emblem)' }[x[4]];
    let h = `<b class="t">${esc(x[2])}</b><div class="nt">${esc(x[6] || 'named feature')}</div><table>`;
    h += `<tr><td>Name says</td><td><b style="color:${x[4].endsWith('L') ? RED : NAVY}">${word}</b></td></tr>`;
    h += `<tr><td>Kind</td><td>${TYPE[x[5]]}</td></tr>`;
    h += `<tr><td>Historic county</td><td>${esc(x[7] || 'outside')}</td></tr><tr><td>County today</td><td>${esc(x[8] || 'outside')}</td></tr>`;
    if (x[9]) h += `<tr><td>Area</td><td>${esc(D.z[x[9]] || x[9])}</td></tr>`;
    h += '</table>';
    h += `<p class="nt">Source: <a href="https://www.openstreetmap.org/${esc(x[3])}" target="_blank" rel="noopener">OpenStreetMap ${esc(x[3])}</a> (ODbL). A name says nothing about when it was chosen.</p>`;
    new maplibregl.Popup({ maxWidth: '320px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    const feats = D.f.map((x, i) => ({ type: 'Feature', properties: { i, c: x[4].endsWith('L') ? 'L' : 'Y', r: x[4].startsWith('r') ? 1 : 0, t: x[5], n: x[2] }, geometry: { type: 'Point', coordinates: [x[0], x[1]] } }));
    map.addSource('f', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Names: © OpenStreetMap contributors (ODbL)' });
    map.addSource('b', { type: 'geojson', data: B, attribution: 'Historic counties: Historic County Borders Project; districts: ONS (OGL v3.0)' });
    const first = map.getStyle().layers.find(l => l.type === 'symbol').id;
    map.addLayer({ id: 'movedY', type: 'fill', source: 'b', filter: ['all', ['==', ['get', 'layer'], 'moved'], ['==', ['slice', ['get', 'zone'], 0, 2], 'T_']], paint: { 'fill-color': '#8FA9D6', 'fill-opacity': 0.38 } }, first);
    map.addLayer({ id: 'movedL', type: 'fill', source: 'b', filter: ['all', ['==', ['get', 'layer'], 'moved'], ['==', ['slice', ['get', 'zone'], 0, 2], 'L_']], paint: { 'fill-color': '#E8A49A', 'fill-opacity': 0.34 } }, first);
    map.addLayer({ id: 'movedO', type: 'line', source: 'b', filter: ['==', ['get', 'layer'], 'moved'], paint: { 'line-color': '#6E604E', 'line-width': 0.8, 'line-opacity': 0.6 } }, first);
    map.addLayer({ id: 'modOut', type: 'line', source: 'b', filter: ['==', ['get', 'layer'], 'modern'], paint: { 'line-color': '#7A6A9A', 'line-width': 0.9, 'line-opacity': 0.55 } }, first);
    map.addLayer({ id: 'histOut', type: 'line', source: 'b', filter: ['==', ['get', 'layer'], 'historic'], paint: { 'line-color': '#2B2119', 'line-width': 1.1, 'line-dasharray': [3, 2], 'line-opacity': 0.55 } }, first);
    map.addLayer({ id: 'lineMod', type: 'line', source: 'b', filter: ['==', ['get', 'layer'], 'line_mod'], paint: { 'line-color': '#5B2A86', 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 2, 11, 4] } });
    map.addLayer({ id: 'lineHist', type: 'line', source: 'b', filter: ['==', ['get', 'layer'], 'line_hist'], paint: { 'line-color': '#2B2119', 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 2, 11, 3.5], 'line-dasharray': [2, 1.4] } });
    const rad = ['interpolate', ['linear'], ['zoom'], 5, 3, 9, 5, 13, 8];
    map.addLayer({ id: 'rose', type: 'circle', source: 'f', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 3, 9, 4.5, 13, 7], 'circle-color': 'rgba(255,255,255,0.85)', 'circle-stroke-color': ['match', ['get', 'c'], 'L', RED, NAVY], 'circle-stroke-width': 1.8 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'f', paint: { 'circle-radius': rad, 'circle-color': ['match', ['get', 'c'], 'L', RED, '#FFFFFF'], 'circle-stroke-color': ['match', ['get', 'c'], 'L', '#FFFFFF', NAVY], 'circle-stroke-width': ['match', ['get', 'c'], 'L', 1.2, 2.2] } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'f', minzoom: 11, layout: { 'text-field': ['get', 'n'], 'text-size': 11, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.0], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['pts', 'rose'].forEach(l => { map.on('click', l, e => { const f = e.features[0]; popup(f.properties.i, f.geometry.coordinates); }); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    map.on('click', 'movedY', e => { if (map.queryRenderedFeatures(e.point, { layers: ['pts', 'rose'] }).length) return; const p = e.features[0].properties; new maplibregl.Popup({ maxWidth: '300px' }).setLngLat(e.lngLat).setHTML(`<b class="t">${esc(p.name)}</b><p class="nt">${esc(D.zn[p.zone] || '')}</p>`).addTo(map); });
    map.on('click', 'movedL', e => { if (map.queryRenderedFeatures(e.point, { layers: ['pts', 'rose'] }).length) return; const p = e.features[0].properties; new maplibregl.Popup({ maxWidth: '300px' }).setLngLat(e.lngLat).setHTML(`<b class="t">${esc(p.name)}</b><p class="nt">${esc(D.zn[p.zone] || '')}</p>`).addTo(map); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyM').addEventListener('change', e => vis(['movedY', 'movedL', 'movedO'], e.target.checked));
    document.getElementById('lyH').addEventListener('change', e => vis(['lineHist', 'histOut'], e.target.checked));
    document.getElementById('lyN').addEventListener('change', e => vis(['lineMod', 'modOut'], e.target.checked));
    document.getElementById('lyL').addEventListener('change', e => vis(['lbl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'lbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.getElementById('lyR').addEventListener('change', e => { state.rose = e.target.checked; filt(); });
    document.querySelectorAll('.chip[data-t]').forEach(b => b.addEventListener('click', () => { state[b.dataset.t] = !state[b.dataset.t]; filt(); }));
    filt();
  }
  function go(it) {
    fold(true);
    map.flyTo({ center: it.ll, zoom: it.z || 13, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.25 : 0.15))] });
    if (it.i != null) map.once('moveend', () => { const x = D.f[it.i]; if (!state[x[5]]) { state[x[5]] = true; filt(); } popup(it.i, it.ll); });
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.f.map((x, i) => ({ t: x[2], s: x[8] || x[7] || '', nn: norm(x[2]), i, ll: [x[0], x[1]] }));
    D.p.forEach(p => idx.push({ t: p[0], s: 'place', nn: norm(p[0]), ll: [p[1], p[2]], z: 12, place: 1 }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      const a = idx.filter(x => x.nn.startsWith(v)), b = idx.filter(x => !x.nn.startsWith(v) && v.length > 2 && x.nn.includes(v));
      items = a.concat(b).sort((x, y) => (y.place || 0) - (x.place || 0)).slice(0, 14);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const p = D.p.find(x => x[0] === a.dataset.go); if (!p) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go({ ll: [p[1], p[2]], z: 11 }); }));
  }
  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/boundaries.geojson').then(r => r.json())]).then(([d, b]) => {
    D = d; B = b;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-3.35, 53.35], [-1.45, 54.45]], fitBoundsOptions: { padding: small ? { top: 10, bottom: 70, left: 10, right: 10 } : { top: 40, bottom: 40, left: 380, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 17 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
  }).catch(e => { const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load (it needs WebGL). The essay below has every result.'; console.error(e); });
})();
