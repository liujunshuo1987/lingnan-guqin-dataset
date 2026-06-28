# -*- coding: utf-8 -*-
"""人工二次裁定 clean_cbdb 后仍存疑的边界行（依据回查到的籍贯）。"""
import csv
SRC = 'persons_cbdb_linked.csv'

# 籍贯明确非岭南且与本人不符 → 否决
REJECT = {'P007','P025','P105','P112','P143','P172','P187','P200','P211','P218'}
# 籍贯实为岭南/与本人原籍吻合 → 确认 (P207苏敬衡:CBDB沾化=渤海,与"寓海南(渤海)"吻合)
CONFIRM = {'P010','P169','P207'}

rows = list(csv.DictReader(open(SRC, encoding='utf-8-sig')))
cols = list(rows[0].keys())
nr = nc = 0
for r in rows:
    if r['id'] in REJECT:
        r['CBDB编号']=r['CBDB姓名']=r['CBDB朝代']=r['CBDB生卒']=r['CBDB链接']=''
        r['CBDB比对状态']='no-match(籍贯非岭南·人工核)'
        nr += 1
    elif r['id'] in CONFIRM:
        r['CBDB比对状态']='auto-地缘+朝代吻合'
        nc += 1
with open(SRC,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)

def cnt(s): return sum(1 for r in rows if r['CBDB比对状态']==s)
def pre(s): return sum(1 for r in rows if r['CBDB比对状态'].startswith(s))
hi = cnt('verified')+cnt('auto(朝代+生卒吻合)')+cnt('auto-地缘+朝代吻合')
print('人工否决 %d，确认 %d' % (nr,nc))
print('最终：verified=%d  auto生卒=%d  auto地缘=%d  → 高置信合计 %d' %
      (cnt('verified'),cnt('auto(朝代+生卒吻合)'),cnt('auto-地缘+朝代吻合'),hi))
print('     存疑(无籍贯佐证)=%d  no-match系=%d  unchecked=%d' %
      (pre('auto-存疑'), pre('no-match'), cnt('unchecked')))
print('     全表有CBDB号 = %d' % sum(1 for r in rows if r['CBDB编号'].strip()))
