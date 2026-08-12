// clean_explanations.js
// Remove promo/boilerplate garbage appended to question explanation (`x`) fields
// scraped from 233.com / chinaacc.com. Truncates each x: string at the first
// high-precision garbage sentinel. Fully-garbage fields (no real text) become ''.
//
// Usage:
//   node clean_explanations.js [--dry] [--file index.html]
const fs = require('fs');
const path = require('path');

const DRY = process.argv.includes('--dry');
const fileArg = process.argv.find(a => a.startsWith('--file='));
const file = (fileArg ? fileArg.split('=')[1] : path.join(__dirname, 'index.html'));

// HIGH-PRECISION sentinels: these strings only ever appear in source-site
// promotional/boilerplate fragments, never in a legitimate econ/ip explanation.
const SENTINELS = [
  '课程咨询免费微信学习群',
  '免费微信学习群温馨提示',
  '微信学习群温馨提示',
  '点击了解中级经济师课程',
  '华课网校',
  '中华会计网校',
  '233网校',
  '中级经济师课程',
  '限时抽好课',
  '试试手气',
  '告别低效备考',
  '随机立减',
  '免费微信学习群',
  '备考交流群',
  '扫码添加',
  '专属大额券',
  '恭喜你！获得',
  '责编：',
  '上一篇：',
  '上一篇',
  '相关新闻',
  '京ICP备',
  '网校客服',
  '免费试听',
  '报名入口',
  '加微信'
];

function readSingleQuotedString(str, start) {
  let i = start + 1, out = '';
  while (i < str.length) {
    const c = str[i];
    if (c === '\\') {
      const n = str[i + 1];
      if (n === 'n') out += '\n';
      else if (n === 't') out += '\t';
      else if (n === 'r') out += '\r';
      else out += n;
      i += 2; continue;
    }
    if (c === "'") return { value: out, end: i };
    out += c; i++;
  }
  return { value: out, end: i };
}

function jsEscape(s) {
  return s.replace(/\\/g, '\\\\')
          .replace(/'/g, "\\'")
          .replace(/\n/g, '\\n')
          .replace(/\r/g, '\\r')
          .replace(/\t/g, '\\t');
}

function firstSentinelAt(value) {
  let best = -1, found = null;
  for (const s of SENTINELS) {
    const at = value.indexOf(s);
    if (at !== -1 && (best === -1 || at < best)) { best = at; found = s; }
  }
  return { at: best, s: found };
}

let text = fs.readFileSync(file, 'utf8');
const ops = [];           // {start, end(inc quote), newStr}
let idx = 0, scanned = 0, truncated = 0, emptied = 0;

while ((idx = text.indexOf("x:", idx)) !== -1) {
  let p = idx + 2;
  while (p < text.length && /\s/.test(text[p])) p++;
  if (text[p] !== "'") { idx += 2; continue; }
  const { value, end } = readSingleQuotedString(text, p);
  scanned++;
  const { at, s } = firstSentinelAt(value);
  if (at === -1) { idx = end + 1; continue; }
  let real = value.slice(0, at).replace(/\s+$/, '');
  // drop an orphaned trailing comma/semicolon/period left by truncation
  real = real.replace(/[，。；、,\s]+$/, '');
  const origStart = p, origEnd = end; // include quotes
  if (real.length < 8) {
    // fully garbage: no real explanation to keep
    ops.push({ start: origStart, end: origEnd, newStr: "''" });
    emptied++;
  } else {
    ops.push({ start: origStart, end: origEnd, newStr: "'" + jsEscape(real) + "'" });
    truncated++;
  }
  idx = end + 1;
}

console.log(`Scanned x: fields        = ${scanned}`);
console.log(`Truncated (kept real)    = ${truncated}`);
console.log(`Emptied (fully garbage)  = ${emptied}`);
console.log(`Total modified           = ${ops.length}`);

if (DRY) {
  console.log('\n[DRY RUN] No file changes written.');
  process.exit(0);
}

// apply replacements in reverse order so indices stay valid
ops.sort((a, b) => b.start - a.start);
let out = text;
for (const op of ops) {
  out = out.slice(0, op.start) + op.newStr + out.slice(op.end + 1);
}
fs.writeFileSync(file, out, 'utf8');
console.log('\nFile updated:', file);
