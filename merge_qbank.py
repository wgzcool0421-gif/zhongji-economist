#!/usr/bin/env python3
"""Merge new QBANK questions into index.html - idempotent & robust"""
import re

# Read new question files
with open('new_econ_questions.js', 'r', encoding='utf-8') as f:
    new_econ = f.read()

with open('new_ip_questions.js', 'r', encoding='utf-8') as f:
    new_ip = f.read()

# Read index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Idempotency check =====
econ_already = '2021-2023历年真题补充(来自233网校)' in content
ip_already = '2024-2026历年真题补充(来自233网校)' in content

if econ_already:
    print("ECON_QBANK: Questions already inserted (skipping)")
if ip_already:
    print("IP_QBANK: Questions already inserted (skipping)")

# ===== Insert ECON questions into ECON_QBANK =====
if not econ_already:
    # Find the end of ECON_QBANK (the `];` after last question, before IP_QBANK)
    ip_qbank_pos = content.find('const IP_QBANK = [')
    # Find the last `];` before IP_QBANK
    econ_section = content[:ip_qbank_pos]
    last_econ_close = econ_section.rfind('];')
    
    if last_econ_close >= 0:
        insert_block = f"""
  // ===== 2021-2023历年真题补充(来自233网校) =====
{new_econ.rstrip()}
"""
        content = content[:last_econ_close] + insert_block + content[last_econ_close:]
        print("ECON_QBANK: Insertion successful")
    else:
        print("ECON_QBANK: Could not find insertion point!")

# ===== Insert IP questions into IP_QBANK =====
if not ip_already:
    # Find the end of IP_QBANK (the `];` after last question, before PAST_PAPERS)
    past_papers_pos = content.find('const PAST_PAPERS')
    ip_section = content[:past_papers_pos]
    last_ip_close = ip_section.rfind('];')
    
    if last_ip_close >= 0:
        insert_block = f"""
  // ===== 2024-2026历年真题补充(来自233网校) =====
{new_ip.rstrip()}
"""
        content = content[:last_ip_close] + insert_block + content[last_ip_close:]
        print("IP_QBANK: Insertion successful")
    else:
        print("IP_QBANK: Could not find insertion point!")

# Write back
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open('index.html', 'r', encoding='utf-8') as f:
    new_content = f.read()

# Count using regex (more reliable)
econ_start = new_content.find('const ECON_QBANK = [')
econ_end = new_content.find('const IP_QBANK = [', econ_start)
ip_start = econ_end
ip_end = new_content.find('const PAST_PAPERS', ip_start)

econ_count = len(re.findall(r"^\s*\{ch:", new_content[econ_start:econ_end], re.MULTILINE))
ip_count = len(re.findall(r"^\s*\{ch:", new_content[ip_start:ip_end], re.MULTILINE))

print(f"\nVerification:")
print(f"  ECON_QBANK: {econ_count} questions")
print(f"  IP_QBANK: {ip_count} questions")
print(f"  Total: {econ_count + ip_count} questions")
