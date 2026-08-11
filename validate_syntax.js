const fs = require('fs');
const { execSync } = require('child_process');
const vm = require('vm');

const html = fs.readFileSync('index.html', 'utf8');

// Extract all inline <script> blocks (no src attribute)
const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
let m, idx = 0, ok = 0, err = 0;
const blocks = [];
while ((m = re.exec(html)) !== null) {
  blocks.push(m[1]);
}

console.log('Inline script blocks found:', blocks.length);

blocks.forEach((code, i) => {
  // Skip empty
  if (!code.trim()) { console.log(`Block ${i}: empty, skip`); return; }
  try {
    new vm.Script(code, { filename: `block_${i}.js` });
    ok++;
    console.log(`Block ${i}: OK (${code.length} chars)`);
  } catch (e) {
    err++;
    console.log(`Block ${i}: SYNTAX ERROR -> ${e.message}`);
    // Try to locate line
    const stack = e.stack || '';
    const lm = stack.match(/block_\d+\.js:(\d+)/);
    if (lm) {
      const ln = parseInt(lm[1], 10);
      const lines = code.split('\n');
      if (lines[ln - 1] !== undefined) console.log(`  near line ${ln}: ${lines[ln - 1].slice(0, 120)}`);
    }
  }
});

console.log(`\n=== RESULT: ${ok} OK, ${err} errors ===`);
process.exit(err > 0 ? 1 : 0);
