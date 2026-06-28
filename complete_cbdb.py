# -*- coding: utf-8 -*-
"""联网补全 persons_cbdb_linked.csv 中 status=unchecked 的行。
严格按 朝代根 + 生卒(±60) 消歧，杜绝同名异人（如黄景星明1474）。
保留人工 verified / no-match / candidate 行不动。结果写回原文件。"""
import csv, re, json, time, urllib.request, urllib.parse

SRC = 'persons_cbdb_linked.csv'
URL = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=%s&o=json'
PURL = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=%s'

DYN_PAIRS = [
    ('三国', ['三國','吳','蜀','魏']),
    ('南北朝', ['南北朝','陳','梁','齊']),
    ('唐', ['唐']),
    ('五代', ['五代','十國','南漢']),
    ('宋', ['宋']),
    ('元', ['元']),
    ('明', ['明']),
    ('清', ['清']),
    ('近代', ['清','民國','中華民國']),
    ('民国', ['民國','中華民國']),
]
def dyn_roots(s):
    r = set()
    for k, v in DYN_PAIRS:
        if k in (s or ''):
            r.update(v)
    return r

def rep_year(period):
    m = re.search(r'(\d{3,4})', period or '')
    return int(m.group(1)) if m else None

def fetch(name):
    try:
        with urllib.request.urlopen(URL % urllib.parse.quote(name), timeout=20) as r:
            d = json.load(r)
    except Exception as e:
        return None, 'err:%s' % e
    try:
        pi = d['Package']['PersonAuthority']['PersonInfo']['Person']
    except Exception:
        return [], 'no-person'
    if not pi:
        return [], 'empty'
    return (pi if isinstance(pi, list) else [pi]), 'ok'

def basic(c):
    b = c.get('BasicInfo', c)
    by = b.get('YearBirth', ''); dy = b.get('YearDeath', '')
    return {
        'id': b.get('PersonId', ''), 'name': b.get('ChName', ''),
        'dyn': b.get('Dynasty', '') or '', 'addr': b.get('IndexAddr', '') or '',
        'by': int(by) if str(by).isdigit() else None,
        'dy': int(dy) if str(dy).isdigit() else None,
    }

rows = list(csv.DictReader(open(SRC, encoding='utf-8-sig')))
cols = list(rows[0].keys())
todo = [r for r in rows if r['CBDB比对状态'] == 'unchecked' and r['朝代'].strip()]
print('待查 unchecked(有朝代): %d' % len(todo))

n_match = n_no = n_err = 0
for r in todo:
    roots = dyn_roots(r['朝代'])
    yr = rep_year(r['时期'])
    cands, st = fetch(r['姓名'])
    if cands is None:
        n_err += 1; time.sleep(0.3); continue
    infos = [basic(c) for c in cands]
    dy_hit = []   # 朝代且生卒吻合
    d_only = []   # 仅朝代吻合(对方无生卒)
    for b in infos:
        dok = any(rt in b['dyn'] for rt in roots) if roots else False
        if not dok:
            continue
        if yr and b['by'] is not None:
            if abs(b['by'] - yr) <= 60:
                dy_hit.append((abs(b['by'] - yr), b))
            # 朝代对但生卒差>60 → 视为同名异人，丢弃
        else:
            d_only.append(b)
    pick = None; conf = ''
    if dy_hit:
        dy_hit.sort(key=lambda x: x[0])
        pick = dy_hit[0][1]
        conf = 'auto(朝代+生卒吻合)' if len(dy_hit) == 1 else 'auto(多候选取生卒最近,待复核)'
    elif len(d_only) == 1 and len(infos) <= 3:
        pick = d_only[0]
        conf = 'auto(仅朝代吻合,待复核)'
    if pick and pick['id']:
        r['CBDB编号'] = pick['id']; r['CBDB姓名'] = pick['name']
        r['CBDB朝代'] = pick['dyn']
        r['CBDB生卒'] = '%s-%s' % (pick['by'] or '?', pick['dy'] or '?')
        r['CBDB比对状态'] = conf
        r['CBDB链接'] = PURL % pick['id']
        n_match += 1
    else:
        r['CBDB比对状态'] = 'no-match-auto'
        n_no += 1
    time.sleep(0.3)

with open(SRC, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

ver = sum(1 for r in rows if r['CBDB比对状态'] == 'verified')
auto = sum(1 for r in rows if r['CBDB比对状态'].startswith('auto'))
print('=== 完成 ===')
print('本轮新增 auto 匹配: %d  无匹配: %d  网络错误: %d' % (n_match, n_no, n_err))
print('总计: 人工verified=%d  auto=%d  合计有CBDB号=%d / %d' %
      (ver, auto, ver + auto, len(rows)))
print('--- 新增 auto 匹配清单 ---')
for r in rows:
    if r['CBDB比对状态'].startswith('auto'):
        print('  %s %s -> %s %s %s [%s]' % (r['id'], r['姓名'], r['CBDB编号'],
              r['CBDB朝代'], r['CBDB生卒'], r['CBDB比对状态']))
