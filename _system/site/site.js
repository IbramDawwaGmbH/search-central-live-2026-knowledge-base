/* Web edition of the knowledge base: mobile menu, label filter on the all-claims page, kit filters (also the claim filter
   of a thing's card), copy buttons, the pre-launch checklist, offline search (things, claims, topics, sessions, kits and glossary, with
   aliases, typo tolerance and a speaker filter), and the few moving parts of the Deep Dive motion (off-screen pause, the home
   figures counting up, the page-head fish darting away when clicked, the search bot's reactions; none with reduced motion). */
(function () {
  'use strict';
  var d = document;
  function $(sel, root) { return (root || d).querySelector(sel); }
  function all(sel, root) { return Array.prototype.slice.call((root || d).querySelectorAll(sel)); }
  function plural(n, w) { return n + ' ' + w + (n === 1 ? '' : 's'); }
  function el(tag, cls, text) { var x = d.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }

  // the page's style is the build's (from _system/theme.yaml); a style a reader picked in an earlier version is forgotten
  try { window.localStorage.removeItem('kb-style'); } catch (err) { /* storage blocked: nothing was kept */ }
/* edition: community */
  // the published community edition (build_site.py leaves this block out of the full edition's copy): 404.html on the web
  // resolves its links from the site root (a <base>), so a link to "#id" (the skip link) must stay on this page
  if ($('base')) {
    d.addEventListener('click', function (ev) {
      var a = ev.target.closest ? ev.target.closest('a[href^="#"]') : null, t = a && d.getElementById(a.getAttribute('href').slice(1));
      if (!t) return;
      ev.preventDefault();
      t.scrollIntoView();
      if (t.focus) t.focus();
    });
  }
/* edition: end */

  // mobile menu
  var btn = $('.menu-btn'), nav = d.getElementById('site-nav');
  if (btn && nav) {
    btn.hidden = false;
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // label filter on the all-claims page
  var filt = d.getElementById('claim-filter');
  if (filt) {
    filt.hidden = false;
    var note = $('.filter-n', filt);
    filt.addEventListener('change', function () {
      var on = all('input:checked', filt).map(function (i) { return i.value; }), n = 0;
      all('.claim[data-label]').forEach(function (c) { var show = on.indexOf(c.getAttribute('data-label')) >= 0; c.hidden = !show; if (show) n++; });
      all('.claim-group').forEach(function (g) { g.hidden = !$('.claim:not([hidden])', g); });
      note.textContent = plural(n, 'claim') + ' shown';
    });
  }

  // kit pages: filters (an item shows when, in every group, one ticked value is among its data-<name> values)
  all('.kit-filter').forEach(function (f) {
    var sel = f.getAttribute('data-items'), noun = f.getAttribute('data-noun'), note = $('.filter-n', f), items = all(sel);
    f.hidden = false;
    function apply() {
      var groups = {}, n = 0;
      all('input[type=checkbox]', f).forEach(function (i) { groups[i.name] = groups[i.name] || []; if (i.checked) groups[i.name].push(i.value); });
      items.forEach(function (c) {
        var show = Object.keys(groups).every(function (g) {
          return (c.getAttribute('data-' + g) || '').split(' ').some(function (v) { return groups[g].indexOf(v) >= 0; });
        });
        c.hidden = !show; if (show) n++;
      });
      all('[data-group]').forEach(function (g) { g.hidden = !$(sel + ':not([hidden])', g); });
      note.textContent = n + ' of ' + plural(items.length, noun) + ' shown';
    }
    f.addEventListener('change', apply);
    apply();
  });

  // copy buttons: the text of .copy-src (or its data-copy) in the same .copyable box
  all('.copyable .copy').forEach(function (b) {
    var box = b.closest('.copyable'), src = box && $('.copy-src', box), label = b.textContent;
    if (!src) return;
    b.hidden = false;
    function done(ok) { b.textContent = ok ? 'Copied' : 'Press Ctrl+C'; setTimeout(function () { b.textContent = label; }, 1600); }
    function fallback() {
      var r = d.createRange(), s = window.getSelection(), ok = false;
      r.selectNodeContents(src); s.removeAllRanges(); s.addRange(r);
      try { ok = d.execCommand('copy'); } catch (err) { ok = false; }
      done(ok);
    }
    b.addEventListener('click', function () {
      var text = src.getAttribute('data-copy') || src.textContent;
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
      else fallback();
    });
  });

  // pre-launch checklist: ticks are kept in this browser (localStorage may be blocked: then they last until the page closes)
  var cl = d.getElementById('checklist');
  if (cl) {
    var KEY = 'kb-prelaunch-checklist', boxes = all('input[type=checkbox]', cl), prog = d.getElementById('cl-progress'), reset = d.getElementById('cl-reset'), saved = {};
    try { saved = JSON.parse(window.localStorage.getItem(KEY) || '{}') || {}; } catch (err) { saved = {}; }
    var save = function () { try { window.localStorage.setItem(KEY, JSON.stringify(saved)); } catch (err) { /* storage blocked */ } };
    var count = function () { prog.textContent = boxes.filter(function (b) { return b.checked; }).length + ' of ' + boxes.length + ' ticked'; };
    boxes.forEach(function (b) {
      b.checked = saved[b.value] === true;
      b.addEventListener('change', function () { if (b.checked) saved[b.value] = true; else delete saved[b.value]; save(); count(); });
    });
    reset.hidden = false;
    reset.addEventListener('click', function () { boxes.forEach(function (b) { b.checked = false; }); saved = {}; save(); count(); });
    count();
  }

  // Deep Dive motion: site.css draws and moves the art; this pauses what is off screen, counts the home figures up, lets the
  // page-head fish dart away when clicked, and lets the search bot react. Nothing here runs in an Art Deco build, and nothing
  // moves for a reader who asks for reduced motion (switching it on mid-visit stops what is running).
  var deep = d.documentElement.getAttribute('data-style') === 'deep-dive';
  var calmQ = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null, calm = !!(calmQ && calmQ.matches), stills = [];
  function moving() { return deep && !calm; }
  if (calmQ) {
    var onCalm = function () { calm = calmQ.matches; if (calm) stills.forEach(function (f) { f(); }); };
    if (calmQ.addEventListener) calmQ.addEventListener('change', onCalm); else if (calmQ.addListener) calmQ.addListener(onCalm);
  }
  if (deep) (function () {
    var IO = 'IntersectionObserver' in window;

    // pause the art of the masthead, page head, hero and footer while it is off screen or the tab is hidden
    var areas = all('.mast, .page-head, .hero, .foot'), seen = areas.map(function () { return true; });
    function mark() { areas.forEach(function (a, i) { a.classList.toggle('dd-off', d.hidden || !seen[i]); }); }
    if (areas.length) {
      if (IO) {
        var pio = new IntersectionObserver(function (es) { es.forEach(function (x) { seen[areas.indexOf(x.target)] = x.isIntersecting; }); mark(); });
        areas.forEach(function (a) { pio.observe(a); });
      }
      d.addEventListener('visibilitychange', mark);
    }

    // the home figures count up from 0 the first time they come into view; only a plain integer counts (the "3" of 3/3), and the
    // figure ends as exactly the original markup. Screen readers get the real value meanwhile.
    var lists = all('.hero + .wrap > .stats'), figs = [];
    lists.forEach(function (s) {
      all('dd', s).forEach(function (dd) {
        var t = dd.firstChild, m = t && t.nodeType === 3 && /^(\s*)(\d+)(\s*)$/.exec(t.data);
        if (m && !dd.hasAttribute('aria-label')) figs.push({ dd: dd, t: t, n: +m[2], pre: m[1], post: m[3], html: dd.innerHTML });
      });
    });
    function countUp(fs) {
      var t0 = null, over = false;
      function end() { if (over) return; over = true; fs.forEach(function (f) { f.dd.innerHTML = f.html; f.dd.removeAttribute('aria-label'); }); }
      function step(now) {
        if (over) return;
        if (t0 === null) t0 = now;
        var p = Math.min(1, (now - t0) / 1300), k = 1 - Math.pow(1 - p, 3);  // ease-out cubic
        fs.forEach(function (f) { f.t.data = f.pre + Math.round(f.n * k) + f.post; });
        if (p < 1) window.requestAnimationFrame(step); else end();
      }
      fs.forEach(function (f) { f.dd.setAttribute('aria-label', f.dd.textContent.trim()); f.t.data = f.pre + '0' + f.post; });
      stills.push(end);
      window.requestAnimationFrame(step);
    }
    if (figs.length && IO && window.requestAnimationFrame) {
      var cio = new IntersectionObserver(function (es) {
        es.forEach(function (x) {
          if (!x.isIntersecting) return;
          cio.unobserve(x.target);
          var fs = figs.filter(function (f) { return x.target.contains(f.dd); });
          if (moving() && fs.length) countUp(fs);
        });
      }, { threshold: 0.4 });
      lists.forEach(function (s) { cio.observe(s); });
    }

    // the page-head fish: each <i class="dd-fish"> fills the .dd-reef box and draws its fish (background centre/contain) in the
    // accent's 300x150 coordinates; data-box="x y w h" is the fish's box there. A click inside a box sends that fish darting off
    // (.dd-dart); it stays away 2.5-3.3 s, then swims back (.dd-back). Only a pointer that reaches the reef itself counts: the
    // head's text, links and controls lie above it (site.css), so a click on them, or anywhere else, is left alone.
    all('.page-head').forEach(function (head) {
      var reef = $('.dd-reef', head);
      if (!reef) return;
      var fish = all('.dd-fish', reef).map(function (f, i) {
        var b = (f.getAttribute('data-box') || '').trim().split(/[\s,]+/).map(Number);
        return { el: f, i: i, box: b.length === 4 && b.every(function (v) { return isFinite(v); }) ? b : null, busy: false, gen: 0, tm: 0 };
      }).filter(function (f) { return f.box; });
      if (!fish.length) return;
      function hit(x, y) {
        var r = reef.getBoundingClientRect();
        if (!r.width || !r.height) return null;  // hidden at this width
        var s = Math.min(r.width / 300, r.height / 150), px = (x - r.left - (r.width - 300 * s) / 2) / s, py = (y - r.top - (r.height - 150 * s) / 2) / s;
        for (var k = fish.length - 1; k >= 0; k--) {  // the fish drawn last is on top
          var b = fish[k].box;
          if (px >= b[0] && px <= b[0] + b[2] && py >= b[1] && py <= b[1] + b[3]) return fish[k];
        }
        return null;
      }
      // after an animation of this fish ends (or ms later, if none runs), unless the fish was reset meanwhile
      function wait(f, gen, ms, next) {
        var tm;
        function go(ev) {
          if (ev && ev.target !== f.el) return;
          f.el.removeEventListener('animationend', go); clearTimeout(tm);
          if (gen === f.gen) next();
        }
        f.el.addEventListener('animationend', go);
        tm = f.tm = setTimeout(go, ms);
      }
      function settle(f) { f.gen++; clearTimeout(f.tm); f.el.classList.remove('dd-dart', 'dd-back'); f.busy = false; }
      function dart(f) {
        var gen = ++f.gen;
        f.busy = true;
        reef.classList.remove('dd-hover');
        f.el.classList.remove('dd-back');
        f.el.classList.add('dd-dart');
        wait(f, gen, 650, function () {
          f.tm = setTimeout(function () {
            if (gen !== f.gen) return;
            f.el.classList.remove('dd-dart');
            f.el.classList.add('dd-back');
            wait(f, gen, 1300, function () { settle(f); });
          }, 2500 + f.i * 400);
        });
      }
      reef.addEventListener('pointermove', function (ev) {
        var f = moving() && ev.target === reef ? hit(ev.clientX, ev.clientY) : null;
        reef.classList.toggle('dd-hover', !!(f && !f.busy));
      });
      reef.addEventListener('pointerleave', function () { reef.classList.remove('dd-hover'); });
      reef.addEventListener('click', function (ev) {
        if (!moving() || ev.target !== reef) return;
        var f = hit(ev.clientX, ev.clientY);
        if (f && !f.busy) dart(f);
      });
      stills.push(function () { fish.forEach(settle); reef.classList.remove('dd-hover'); });
    });
  })();

  // search: things, claims, topics, sessions, the two kits and the glossary, all in this browser. build_site.py writes the index
  // (window.KB_SEARCH): the records, which of their fields are searched, the aliases, the vocabulary and the proven speakers.
  var S = window.KB_SEARCH, form = d.getElementById('search-form');
  if (!S || !form) return;
  var input = d.getElementById('q'), out = d.getElementById('results'), status = d.getElementById('search-status'), fbox = d.getElementById('search-filters');
  var note = d.getElementById('search-note');
  // the diver bot's line under the search box (shown by the CSS in Deep Dive only): reading while nothing is asked, pointing
  // the way when nothing matches
  var guide = d.getElementById('search-guide'), READY = 'Ready when you are: every thing, claim, topic, session, kit item and glossary term is down here, waiting for a word.';
  function say(pose, text) {
    if (!guide) return;
    guide.hidden = !pose;
    if (pose) { guide.setAttribute('data-pose', pose); $('.bot-say', guide).textContent = text; }
  }
  // Deep Dive motion: the bot blows one bubble when a search starts showing results (.dd-blow, once) and looks puzzled while
  // nothing matches (.dd-puzzled); n is the number of results, -1 when nothing is asked. site.css draws both.
  var found = false, blowT;
  function react(n) {
    var was = found;
    found = n > 0;
    if (!guide || !moving()) return;
    guide.classList.toggle('dd-puzzled', n === 0);
    if (found && !was) {
      guide.classList.remove('dd-blow');
      void guide.offsetWidth;  // restart the one-shot animation
      guide.classList.add('dd-blow');
      clearTimeout(blowT);
      blowT = setTimeout(function () { guide.classList.remove('dd-blow'); }, 1700);
    }
  }
  if (guide) stills.push(function () { clearTimeout(blowT); guide.classList.remove('dd-blow', 'dd-puzzled'); });
  // Matching ignores case and accents in every script: NFD, combining marks removed, a few letters with no decomposition
  // spelled out (ł -> l). Anything that is not a letter or digit separates words. (build_site.py fold() is the same.)
  var SPELL = { 'ł': 'l', 'đ': 'd', 'ð': 'd', 'ø': 'o', 'ı': 'i', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe', 'þ': 'th', 'ς': 'σ' };
  function fold(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/\p{M}+/gu, '').replace(/[łđðøıßæœþς]/g, function (c) { return SPELL[c]; }); }
  function norm(s) { return ' ' + fold(s).replace(/[^\p{L}\p{N}]+/gu, ' ').trim() + ' '; }

  // result groups in the order they are shown: [key in KB_SEARCH, heading, noun, plural, shown before "Show all"]
  var GROUPS = [['things', 'Things', 'thing', 'things', 6], ['glossary', 'Glossary', 'glossary term', 'glossary terms', 6], ['topics', 'Topics', 'topic', 'topics', 10],
    ['reqs', 'Developer requirements', 'requirement', 'requirements', 6], ['facts', 'Facts', 'fact', 'facts', 5], ['myths', 'Myths', 'myth', 'myths', 5],
    ['angles', 'Story angles', 'story angle', 'story angles', 4], ['quotes', 'Quotes', 'quote', 'quotes', 4], ['sessions', 'Sessions', 'session', 'sessions', 10],
    ['claims', 'Claims', 'claim', 'claims', 40]];
  function count(n, g) { return n + ' ' + (n === 1 ? g[2] : g[3]); }
  function pick(x, names) { return names.split(' ').map(function (n) { return x[n] == null ? '' : String(x[n]); }).join(' '); }
  var recs = [];
  GROUPS.forEach(function (g) {
    var f = S.fields[g[0]];
    (S[g[0]] || []).forEach(function (x, i) { recs.push({ k: g[0], i: i, x: x, a: norm(pick(x, f[0])), b: norm(pick(x, f[1])) }); });
  });
  // aliases: a name typed as it is listed here also finds the other names of the same thing (GSC, Search Console)
  var ALIAS = S.aliases || {}, ALIAS_NAME = S.alias_names || {}, ALIAS_MAX = 1, VOC = S.vocab ? S.vocab.split(' ') : [];
  Object.keys(ALIAS).forEach(function (k) { ALIAS_MAX = Math.max(ALIAS_MAX, k.split(' ').length); });

  var labels = {}, day = '', who = '', open = {}, literal = false;
  Object.keys(S.labels).forEach(function (k) { labels[k] = true; });

  // filters for claim results: one checkbox per label, a day select and a speaker select (names only where proven)
  fbox.appendChild(el('span', 'k', 'Claims'));
  Object.keys(S.labels).forEach(function (k) {
    var lab = el('label'), cb = el('input'), b = el('span', 'badge lab lab-' + k, S.labels[k]);
    cb.type = 'checkbox'; cb.checked = true; cb.value = k;
    cb.addEventListener('change', function () { labels[k] = cb.checked; run(); });
    lab.appendChild(cb); lab.appendChild(b); fbox.appendChild(lab);
  });
  function select(id, text, opts, onchange) {
    var sel = el('select'), sl = el('label');
    sel.id = id; sl.htmlFor = id; sl.className = 'vh'; sl.textContent = text;
    opts.forEach(function (o) {
      if (o.group) {
        var og = d.createElement('optgroup'); og.label = o.group;
        o.opts.forEach(function (p) { var op = el('option', null, p[1]); op.value = p[0]; og.appendChild(op); });
        sel.appendChild(og);
      } else { var op = el('option', null, o[1]); op.value = o[0]; sel.appendChild(op); }
    });
    sel.addEventListener('change', function () { onchange(sel.value); run(); });
    fbox.appendChild(sl); fbox.appendChild(sel);
    return sel;
  }
  var days = [];
  S.claims.forEach(function (c) { if (days.indexOf(c.d) < 0) days.push(c.d); });
  select('f-day', 'Day', [['', 'All days']].concat(days.map(function (n) { return [String(n), 'Day ' + n]; })), function (v) { day = v; });
  var SP = S.speakers || { names: [], groups: [] }, WHO = { google: 'Google', community: 'A community speaker', unattributed: 'Google or community, not recorded', audience: 'The audience' };
  SP.groups.forEach(function (g) { WHO[g.id] = WHO[g.id] || g.label.charAt(0).toUpperCase() + g.label.slice(1); });
  select('f-speaker', 'Speaker', [['', 'All speakers'],
    { group: 'Named speakers', opts: SP.names.map(function (s) { return ['n:' + s.name, s.name + ' (' + s.claims + ')']; }) },
    { group: 'Who said it', opts: SP.groups.map(function (g) { return ['g:' + g.id, WHO[g.id] + ' (' + g.claims + ')']; }) }], function (v) { who = v; });
  function heard(x) { return !who || (who.charAt(0) === 'n' ? x.p === who.slice(2) : x.g === who.slice(2)); }

  function terms(q) { return norm(q).trim().split(' ').filter(Boolean); }
  function occurs(t) { return recs.some(function (r) { return r.a.indexOf(t) >= 0 || r.b.indexOf(t) >= 0; }); }
  // Damerau-Levenshtein distance (adjacent swaps count once), given up as soon as it must exceed k
  function dist(a, b, k) {
    if (Math.abs(a.length - b.length) > k) return k + 1;
    var p2 = null, p1 = [], cur, i, j;
    for (j = 0; j <= b.length; j++) p1[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i];
      var low = i;
      for (j = 1; j <= b.length; j++) {
        var v = Math.min(p1[j] + 1, cur[j - 1] + 1, p1[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, p2[j - 2] + 1);
        cur[j] = v; if (v < low) low = v;
      }
      if (low > k) return k + 1;
      p2 = p1; p1 = cur;
    }
    return p1[b.length];
  }
  // the closest word of the index: one edit away (two for words of 8 letters or more), the most frequent word first
  function suggest(t) {
    var best = null, bd = (t.length >= 8 ? 2 : 1) + 1;
    for (var i = 0; i < VOC.length && bd > 1; i++) {
      var w = VOC[i];
      if (Math.abs(w.length - t.length) >= bd) continue;
      var x = dist(t, w, bd - 1);
      if (x < bd) { bd = x; best = w; }
    }
    return best;
  }
  function unit(t) { return ALIAS[t] ? { t: t, alts: [t].concat(ALIAS[t]), alias: true } : { t: t, alts: [t] }; }
  // the query as units, each a list of alternatives: the words typed, an alias with its other names, or a typo's correction
  function parse(q) {
    var ts = terms(q), units = [], fixed = [], i = 0;
    while (i < ts.length) {
      var u = null;
      for (var n = Math.min(ALIAS_MAX, ts.length - i); n > 1 && !u; n--) {
        var p = ts.slice(i, i + n).join(' ');
        if (ALIAS[p]) { u = unit(p); i += n; }
      }
      if (!u) {
        var t = ts[i++];
        u = unit(t);
        if (!literal && !u.alias && t.length >= 4 && /\p{L}/u.test(t) && !occurs(t)) {
          var s = suggest(t);
          if (s) { fixed.push([t, s]); u = unit(s); }
        }
      }
      units.push(u);
    }
    return { units: units, fixed: fixed };
  }
  // how well one name matches one field: a whole word 3, the start of a word 2, inside a word 1; the other names of an alias
  // count only as whole words
  function fscore(text, w, whole) {
    if (text.indexOf(' ' + w + ' ') >= 0) return 3;
    if (whole) return 0;
    return text.indexOf(' ' + w) >= 0 ? 2 : text.indexOf(w) >= 0 ? 1 : 0;
  }
  function find(units) {
    var res = {};
    GROUPS.forEach(function (g) { res[g[0]] = []; });
    recs.forEach(function (r) {
      var score = 0;
      for (var j = 0; j < units.length; j++) {
        var best = 0, alts = units[j].alts;
        for (var m = 0; m < alts.length; m++) {
          var sa = fscore(r.a, alts[m], m > 0), s = Math.max(sa ? sa + 3 : 0, fscore(r.b, alts[m], m > 0));
          if (s > best) best = s;
        }
        if (!best) return;
        score += best;
      }
      res[r.k].push({ r: r, s: score });
    });
    Object.keys(res).forEach(function (k) { res[k].sort(function (x, y) { return y.s - x.s || x.r.i - y.r.i; }); });
    return res;
  }
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  // one pattern for the marks: what was typed anywhere, the other names of an alias as whole words only
  function pattern(units) {
    var ps = [];
    units.forEach(function (u) {
      u.alts.forEach(function (a, m) { ps.push([a.length, m ? '(?<![\\p{L}\\p{N}])' + esc(a) + '(?![\\p{L}\\p{N}])' : esc(a)]); });
    });
    return ps.sort(function (x, y) { return y[0] - x[0]; }).map(function (x) { return x[1]; }).join('|');
  }
  // Highlight matches found in the folded text, mapped back to the original characters ("Łukasz" for "lukasz").
  function hl(text, P) {
    var f = d.createDocumentFragment(), folded = '', start = [], end = [], i = 0, last = 0, m;
    if (!P) { f.appendChild(d.createTextNode(text)); return f; }
    while (i < text.length) {
      var ch = String.fromCodePoint(text.codePointAt(i)), x = fold(ch);
      for (var j = 0; j < x.length; j++) { start.push(i); end.push(i + ch.length); }
      folded += x; i += ch.length;
    }
    var re = new RegExp(P, 'gu');
    while ((m = re.exec(folded))) {
      if (!m[0]) { re.lastIndex++; continue; }
      var a = Math.max(start[m.index], last), b = end[m.index + m[0].length - 1];
      while (b < text.length && /\p{M}/u.test(text[b])) b++;  // keep combining accents inside the mark
      if (a >= b) continue;
      if (a > last) f.appendChild(d.createTextNode(text.slice(last, a)));
      f.appendChild(el('mark', null, text.slice(a, b)));
      last = b;
    }
    if (last < text.length) f.appendChild(d.createTextNode(text.slice(last)));
    return f;
  }
  // a passage of a long text: its start, or the stretch around the first match when that comes later
  function excerpt(text, P, n) {
    var at = P ? fold(text).search(new RegExp(P, 'u')) : -1, s = 0;
    if (at > n / 2) { s = text.lastIndexOf(' ', at - 50); s = s < 0 ? 0 : s + 1; }
    var t = text.slice(s, s + n);
    if (s + n < text.length) t = t.replace(/\s+\S*$/, '') + '…';
    return (s ? '…' : '') + t;
  }
  function link(href, text, P, cls) { var a = el('a', cls); a.href = href; a.appendChild(hl(text, P)); return a; }
  function para(li, cls, text, P) { var p = el('p', cls); p.appendChild(hl(text, P)); li.appendChild(p); }
  function heading(title, n) { var h = el('h2', 'res-h', title); h.appendChild(el('span', 'count', String(n))); return h; }
  function badges(parts, id) {
    var p = el('p', 'res-b');
    parts.forEach(function (b) { if (b) p.appendChild(b); });
    p.appendChild(el('span', 'sp'));
    p.appendChild(el('span', 'cid', id));
    return p;
  }
  function stBadge(st) { return el('span', 'badge ver st-' + st, S.statuses[st]); }
  function claimItem(c, P) {
    var li = el('li'), art = el('article', 'claim c-' + c.l), head = el('div', 'claim-head');
    head.appendChild(el('span', 'badge lab lab-' + c.l, S.labels[c.l]));
    if (S.grades[c.v]) head.appendChild(el('span', 'badge ver ver-' + c.v.replace('/', ''), S.grades[c.v]));
    head.appendChild(el('span', 'sp'));
    var id = el('a', 'cid', c.id); id.href = c.u; head.appendChild(id);
    art.appendChild(head);
    para(art, 'claim-text', c.t, P);
    if (c.q) { var bq = el('blockquote', 'quote'); para(bq, null, '“' + c.q + '”', P); art.appendChild(bq); }
    var by = el('p', 'claim-by');
    if (c.w) by.appendChild(el('span', 'by', c.w));
    by.appendChild(el('span', 'in', 'Day ' + c.d + ' · ' + c.s));
    art.appendChild(by);
    li.appendChild(art);
    return li;
  }
  var RENDER = {
    things: function (x, P) {
      var li = el('li', 'res-ent ek-' + x.ki);
      li.appendChild(link(x.u, x.n, P, 'res-t'));
      var m = el('span', 'res-m');
      m.appendChild(el('span', 'ekind ek-' + x.ki, x.k));
      m.appendChild(d.createTextNode(' ' + plural(x.c, 'claim')));
      if (x.al) { m.appendChild(d.createTextNode(' · also ')); m.appendChild(hl(x.al, P)); }
      li.appendChild(m);
      para(li, 'res-s', x.s, P);
      return li;
    },
    glossary: function (x, P) { var li = el('li'); li.appendChild(link(x.u, x.n, P, 'res-t')); para(li, 'res-s', x.df, P); return li; },
    topics: function (x, P) {
      var li = el('li');
      li.appendChild(link(x.u, x.n, P, 'res-t'));
      li.appendChild(el('span', 'res-m', x.a + ' · ' + plural(x.c, 'claim')));
      para(li, 'res-s', excerpt(x.s, P, 320), P);
      return li;
    },
    reqs: function (x, P) {
      var li = el('li');
      li.appendChild(badges([el('span', 'lv lv-' + x.lv, S.levels[x.lv]), stBadge(x.st)], x.id));
      li.appendChild(link(x.u, x.n, P, 'res-t'));
      li.appendChild(el('span', 'res-m', x.ar));
      para(li, 'res-s', excerpt(x.w + ' ' + x.h, P, 240), P);
      return li;
    },
    facts: function (x, P) { var li = el('li'); li.appendChild(badges([stBadge(x.st), el('span', 'uchip', x.us)], x.id)); li.appendChild(link(x.u, x.t, P, 'res-t')); return li; },
    myths: function (x, P) {
      var li = el('li');
      li.appendChild(badges([stBadge(x.st)], x.id));
      li.appendChild(link(x.u, 'Myth: ' + x.m, P, 'res-t'));
      para(li, 'res-s', 'Fact: ' + x.f, P);
      return li;
    },
    angles: function (x, P) {
      var li = el('li');
      li.appendChild(link(x.u, x.n, P, 'res-t'));
      li.appendChild(el('span', 'res-m', x.id + ' · for ' + x.au));
      para(li, 'res-s', x.h, P);
      return li;
    },
    quotes: function (x, P) {
      var li = el('li');
      li.appendChild(link(x.u, '“' + x.q + '”', P, 'res-t'));
      li.appendChild(el('span', 'res-m', x.cr + (x.p ? ' · Speaker ' + x.p : '') + ' · ' + x.id));
      return li;
    },
    sessions: function (x, P) {
      var li = el('li');
      li.appendChild(link(x.u, x.n, P, 'res-t'));
      li.appendChild(el('span', 'res-m', 'Day ' + x.d + (x.tm ? ', ' + x.tm : '') + ' · ' + x.k + (x.w ? ' · ' + x.w : '') + ' · ' + plural(x.c, 'claim')));
      return li;
    },
    claims: claimItem
  };
  function button(text, fn, cls) { var b = el('button', cls || 'show-all', text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  function explain(fixed, units, q) {
    note.textContent = '';
    if (fixed.length) {
      var p = el('p');
      p.appendChild(d.createTextNode('Showing results for '));
      var s = q.trim();
      fixed.forEach(function (f) { s = (' ' + norm(s).trim() + ' ').replace(' ' + f[0] + ' ', ' ' + f[1] + ' ').trim(); });
      p.appendChild(el('strong', null, s));
      p.appendChild(d.createTextNode(' (you typed '));
      p.appendChild(el('em', null, q.trim()));
      p.appendChild(d.createTextNode('). '));
      p.appendChild(button('Search for “' + q.trim() + '” instead', function () { literal = true; run(); input.focus(); }, 'linkish'));
      note.appendChild(p);
    }
    var al = units.filter(function (u) { return u.alias; });
    if (al.length) {
      var a = el('p', 'res-alias');
      a.appendChild(d.createTextNode('Also searching other names: '));
      var nm = function (k) { return ALIAS_NAME[k] || k; };
      a.appendChild(d.createTextNode(al.map(function (u) { return nm(u.t) + ' = ' + u.alts.slice(1).map(nm).join(', '); }).join('; ') + '.'));
      note.appendChild(a);
    }
    note.hidden = !note.firstChild;
  }
  function run() {
    var q = input.value, ts = terms(q);
    try { history.replaceState(null, '', ts.length ? '?q=' + encodeURIComponent(q) : location.pathname); } catch (err) { /* file:// may refuse */ }
    out.textContent = '';
    if (!ts.length) {
      say('read', READY);
      react(-1);
      explain([], [], '');
      status.textContent = q.trim() ? 'Nothing to search for in “' + q.trim() + '”: type a word or a number.' : 'Type a word or a number to search things, claims, topics, sessions, the two kits and the glossary.';
      fbox.hidden = true; return;
    }
    var pq = parse(q), P = pattern(pq.units), res = find(pq.units);
    explain(pq.fixed, pq.units, q);
    var shown = {}, total = 0, parts = [];
    GROUPS.forEach(function (g) {
      var k = g[0], hs = res[k];
      if (k === 'claims') hs = hs.filter(function (h) { return labels[h.r.x.l] && (!day || String(h.r.x.d) === day) && heard(h.r.x); });
      if (k === 'quotes') hs = hs.filter(function (h) { return heard(h.r.x); });
      shown[k] = hs; total += hs.length;
      if (hs.length) parts.push(count(hs.length, g));
    });
    status.textContent = total ? plural(total, 'result') + ' for “' + q.trim() + '”: ' + parts.join(', ') + '.' : 'No results for “' + q.trim() + '”. Try fewer or shorter words.';
    fbox.hidden = !res.claims.length && !res.quotes.length;
    // with results the bot stays above them (so the page does not jump and its bubble can be seen); Art Deco hides the bot box
    if (total) say('read', 'Here is what I found on the reef. The closest matches come first.');
    else say('point', res.claims.length || res.quotes.length ? 'The filters hide every claim that matched: tick more labels, choose all days or all speakers.'
      : 'Nothing on this reef matches every word. Try one word, a shorter one, or a topic name such as canonical, robots.txt or JavaScript.');
    react(total);
    GROUPS.forEach(function (g) {
      var k = g[0], hs = shown[k];
      if (!hs.length) return;
      out.appendChild(heading(g[1], hs.length));
      var ul = el('ul', 'res-list' + (k === 'claims' ? ' cl' : ' k-' + k));
      hs.slice(0, open[k] ? hs.length : g[4]).forEach(function (h) { ul.appendChild(RENDER[k](h.r.x, P)); });
      out.appendChild(ul);
      if (hs.length > g[4] && !open[k]) out.appendChild(button('Show all ' + count(hs.length, g), function () { open[k] = true; run(); }));
    });
  }
  var timer;
  input.addEventListener('input', function () { clearTimeout(timer); open = {}; literal = false; timer = setTimeout(run, 120); });
  form.addEventListener('submit', function (ev) { ev.preventDefault(); open = {}; literal = false; run(); });
  var q0 = new URLSearchParams(location.search).get('q');
  if (q0) { input.value = q0; run(); } else say('read', READY);
})();
