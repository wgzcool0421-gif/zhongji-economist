import re

# Read the new questions file
with open('ip_chinaacc_new.js', 'r', encoding='utf-8') as f:
    new_content = f.read()

# Read index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Each question is on its own line starting with "  {ch:"
new_lines = [line for line in new_content.split('\n') if line.strip().startswith('{ch:')]
print(f'New question lines in file: {len(new_lines)}')

# Extract existing IP question texts for dedup
ip_start = content.find('const IP_QBANK = [')
# Find the '];' that ends IP_QBANK - look for pattern: }];\n\n// 
# The PAST_PAPERS is defined as "const PAST_PAPERS = {" not "["
search_start = ip_start
ip_end = -1
while True:
    next_close = content.find('];', search_start)
    if next_close == -1:
        break
    after = content[next_close+2:next_close+60].strip()
    # Check if this looks like end of array followed by code/comment
    if after.startswith('//') and ('BILIBILI' in after or 'DATA' in after):
        ip_end = next_close + 2
        break
    elif next_close - search_start > 500:  # This might be it if we've gone far enough
        ip_end = next_close + 2
        break
    search_start = next_close + 1

if ip_end == -1:
    print('ERROR: Could not find end of IP_QBANK')
    exit(1)

ip_segment = content[ip_start:ip_end]
existing_qs = set()
for m in re.finditer(r"q:'([^']*)'", ip_segment):
    existing_qs.add(m.group(1))

print(f'Existing IP_QBANK: {len(existing_qs)} questions')

# Deduplicate
unique_new = []
dup_count = 0
for line in new_lines:
    q_match = re.search(r"q:'([^']*)'", line)
    if not q_match:
        continue
    q_text = q_match.group(1).replace("\\'", "'")
    q_norm = q_text.strip().replace(' ', '')
    
    is_dup = False
    for eq in existing_qs:
        eq_norm = eq.strip().replace(' ', '')
        if len(q_norm) > 10 and q_norm[:10] == eq_norm[:10]:
            is_dup = True
            break
    if is_dup:
        dup_count += 1
    else:
        unique_new.append(line)

print(f'Duplicates: {dup_count}')
print(f'Unique new: {len(unique_new)}')

if unique_new:
    # Insert before the ]; that ends IP_QBANK
    insert_pos = ip_end - 2
    insert_block = '\n' + '\n'.join(unique_new) + '\n'
    content = content[:insert_pos] + insert_block + content[insert_pos:]
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Merged {len(unique_new)} new questions into IP_QBANK')
else:
    print('No new unique questions to merge')
