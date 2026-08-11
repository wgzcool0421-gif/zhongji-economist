const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('index.html', 'utf8');

// Extract a top-level `const NAME = [...];` array via balanced-bracket matching
function extractArray(name) {
  const startMarker = `const ${name} = [`;
  const start = html.indexOf(startMarker);
  if (start === -1) return { ok: false, reason: 'marker not found' };
  let i = start + startMarker.length - 1; // at '['
  let depth = 0, inStr = false, strCh = '', escape = false;
  // scan for matching close bracket
  for (; i < html.length; i++) {
    const c = html[i];
    if (escape) { escape = false; continue; }
    if (c === '\\') { escape = true; continue; }
    if (inStr) {
      if (c === strCh) inStr = false;
      continue;
    }
    if (c === '"' || c === "'" || c === '`') { inStr = true; strCh = c; continue; }
    if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) { i++; break; } }
  }
  const arrText = html.slice(start + `const ${name} = `.length, i); // includes brackets
  // Evaluate safely
  try {
    const arr = vm.runInNewContext(arrText, { JSON, Math, Array, Object, String, Number, RegExp });
    return { ok: true, arr };
  } catch (e) {
    return { ok: false, reason: e.message };
  }
}

for (const name of ['ECON_QBANK', 'IP_QBANK', 'PAST_PAPERS']) {
  const res = extractArray(name);
  if (!res.ok) { console.log(`${name}: EXTRACT/EVAL FAILED -> ${res.reason}`); continue; }
  const arr = res.arr;
  console.log(`\n${name}: ${arr.length} items`);
  let bad = 0;
  arr.forEach((q, idx) => {
    if (!q || typeof q !== 'object') { bad++; if (bad <= 10) console.log(`  item ${idx}: not object`); return; }
    const hasQ = typeof q.q === 'string' && q.q.trim().length > 0;
    const hasO = Array.isArray(q.o) && q.o.length >= 2;
    const hasA = q.a !== undefined && q.a !== null;
    if (!hasQ || !hasO || !hasA) {
      bad++;
      if (bad <= 10) console.log(`  item ${idx}: q=${typeof q.q}, o=${Array.isArray(q.o)?q.o.length:'n/a'}, a=${q.a}`);
      return;
    }
    const indices = Array.isArray(q.a) ? q.a : [q.a];
    for (const a of indices) {
      if (typeof a !== 'number' || a < 0 || a >= q.o.length) {
        bad++;
        if (bad <= 10) console.log(`  item ${idx}: answer index OOR a=${q.a} opts=${q.o.length}`);
        break;
      }
    }
  });
  console.log(`  malformed/invalid: ${bad}`);
}
