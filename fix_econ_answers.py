#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix ECON_QBANK answer indices that were imported as 1-based (A=1) instead of 0-based (A=0).
OOR signature: answer index == number_of_options (e.g. a=3 when len=3, a=4 when len=4).

Rule:
  - If an answer set has any index >= n (OOR) AND contains no 0 -> pure 1-based, subtract 1 from ALL indices.
  - If an answer set has any index >= n AND contains a 0 -> mixed/corrupt, subtract 1 from ONLY the OOR index(es).
  - After fix, all indices must be in [0, n-1]; otherwise skip (flag for manual review).
Only the `a:` token in each line is rewritten; everything else is preserved.
"""
import re, json, sys

PATH = 'index.html'
with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate ECON_QBANK array via balanced brackets
start_marker = 'const ECON_QBANK = ['
start = content.find(start_marker)
assert start != -1, 'ECON_QBANK not found'
arr_start = start + len(start_marker) - 1  # position of '['
depth = 0
in_str = False
str_ch = ''
escape = False
i = arr_start
for i in range(arr_start, len(content)):
    c = content[i]
    if escape:
        escape = False
        continue
    if c == '\\':
        escape = True
        continue
    if in_str:
        if c == str_ch:
            in_str = False
        continue
    if c in ('"', "'", '`'):
        in_str = True
        str_ch = c
        continue
    if c == '[':
        depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0:
            break
arr_end = i  # position of closing ']'
section = content[arr_start:arr_end + 1]

# Process line by line
lines = section.split('\n')
changed = 0
skipped = 0
re_o = re.compile(r'o:(\[.*?\])')
re_a = re.compile(r'a:(\[[^\]]*\]|\d+)')

for li, line in enumerate(lines):
    m_o = re_o.search(line)
    m_a = re_a.search(line)
    if not m_o or not m_a:
        continue
    try:
        opts = json.loads(m_o.group(1))
    except Exception:
        continue
    n = len(opts)
    a_raw = m_a.group(1)
    if a_raw.startswith('['):
        a_list = [int(x) for x in a_raw[1:-1].split(',') if x.strip() != '']
        was_array = True
    else:
        a_list = [int(a_raw)]
        was_array = False

    oor = [x for x in a_list if x >= n or x < 0]
    if not oor:
        continue  # already valid, leave alone

    has_zero = any(x == 0 for x in a_list)
    if has_zero:
        new_a = [x - 1 if x >= n else x for x in a_list]
    else:
        new_a = [x - 1 for x in a_list]

    # dedup + sort + validate
    new_a = sorted(set(new_a))
    if any(x < 0 or x >= n for x in new_a):
        skipped += 1
        sys.stderr.write(f'  SKIP line {li}: would be invalid after fix; orig a={a_list} n={n}\n')
        continue

    if len(new_a) == 1 and not was_array:
        new_a_str = str(new_a[0])
    else:
        new_a_str = '[' + ','.join(str(x) for x in new_a) + ']'

    lines[li] = line[:m_a.start()] + 'a:' + new_a_str + line[m_a.end():]
    changed += 1

new_section = '\n'.join(lines)
content = content[:arr_start] + new_section + content[arr_end + 1:]

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Changed: {changed} questions')
print(f'Skipped (needs manual review): {skipped}')
