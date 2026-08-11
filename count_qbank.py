import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

ip_start = content.find('const IP_QBANK = [')
pp_start = content.find('const PAST_PAPERS', ip_start)
ip_section = content[ip_start:pp_start]
ip_count = len(re.findall(r'\{ch:', ip_section))
print(f'IP_QBANK: {ip_count} questions')

econ_start = content.find('const ECON_QBANK = [')
ip_qbank_start = content.find('const IP_QBANK = [')
econ_section = content[econ_start:ip_qbank_start]
econ_count = len(re.findall(r'\{ch:', econ_section))
print(f'ECON_QBANK: {econ_count} questions')

pp_start2 = content.find('const PAST_PAPERS', ip_start)
end_marker = content.find('const BILI_DEFAULTS', pp_start2)
pp_section = content[pp_start2:end_marker]
pp_count = len(re.findall(r'\{id:', pp_section))
print(f'PAST_PAPERS: {pp_count} questions')

print(f'TOTAL: {ip_count + econ_count + pp_count} questions')
