# -*- coding: utf-8 -*-
"""从 transmission_edges.csv 抽取每个谱本的"段式结构"，产出四曲结构演变 JSON。
段数来自每条边对 target 形态的描述(演变特征)。"""
import csv, re, json

CN = {'十三':13,'十二':12,'十一':11,'十':10,'两':2,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
SEG = re.compile(r'(十三|十二|十一|十|两|二|三|四|五|六|七|八|九)段')
def seg_of(feat):
    m = SEG.search(feat or '')
    return CN[m.group(1)] if m else None

YEAR_FB = [('刘志方',1400),('古传',1400),('原曲',1400),('杨表正',1600),
           ('韩畕',1655),('蔗湖',1851),('招鉴芬',1920),('以六正五之斋秘谱',1875)]
def year_of(name):
    m = re.search(r'(\d{3,4})', name or '')
    if m: return int(m.group(1))
    for k, y in YEAR_FB:
        if k in (name or ''): return y
    return None

def flags(feat):
    f = feat or ''
    out = []
    if '泛音起首' in f: out.append('泛音起首')
    elif '加泛音尾声' in f or '泛音尾声' in f: out.append('泛音尾声')
    elif '泛音增益' in f: out.append('泛音增益')
    elif '无泛音' in f: out.append('无泛音')
    if '打圆' in f: out.append('打圆起音')
    if '加词' in f or '正文对音' in f: out.append('加词')
    if '半轮' in f: out.append('半轮')
    if '徽分' in f: out.append('徽分音')
    if '吟猱' in f: out.append('吟猱')
    m = re.search(r'(中吕均[商徵宫角羽]音|商意系统|姑洗之律|[商徵宫角羽]音)', f)
    if m: out.append(m.group(1))
    return out

rows = list(csv.DictReader(open('transmission_edges.csv', encoding='utf-8-sig')))
pieces = {}
for r in rows:
    p = r['曲名']
    d = pieces.setdefault(p, {'nodes': {}, 'edges': []})
    s, t, feat = r['source'], r['target'], r['演变特征']
    # target 的形态由本条边描述
    tn = d['nodes'].setdefault(t, {'name': t, 'year': year_of(t), 'seg': None, 'feat': '', 'flags': []})
    sg = seg_of(feat)
    if sg: tn['seg'] = sg
    tn['feat'] = feat
    tn['flags'] = flags(feat)
    d['nodes'].setdefault(s, {'name': s, 'year': year_of(s), 'seg': None, 'feat': '(源/原曲)', 'flags': []})
    d['edges'].append({'s': s, 't': t, 'feat': feat, 'w': int(r['weight']) if r['weight'].isdigit() else 1})

# 段数补录：来源 = 刘峻铄论文逐版对照表(懷古/石上流泉/醉渔/渔樵 各曲版本段数)
OVERRIDE = {
 '鸥鹭忘机': {'韩畕':6, '松风阁':6, '悟雪山房':6, '蓼怀堂':5, '思齐堂':3, '徽言秘旨':7, '五知斋':3, '神奇秘谱':2},
 '碧涧流泉(石上流泉)': {'琴谱正传':6,'西麓堂':8,'真传正宗':8,'乐仙':8,'徽言秘旨':8,
                  '琴学軔端':5,'悟雪山房':7,'琴学入门':5,'天闻阁':8},
 '渔樵问答': {'真传正宗':9,'悟雪山房':7,'琴学入门':10},
 '懷古': {'西麓堂':3,'梧冈':3,'太音传习':3,'文会堂':3,'古音正宗':3,'琴苑心传':3,
            '悟雪山房':4,'蔗湖':4,'以六正五':4,'双琴书屋':4,'招鉴芬':4},
}
filled = 0
for p, d in pieces.items():
    ov = OVERRIDE.get(p, {})
    for n in d['nodes'].values():
        for k, v in ov.items():
            if k in n['name']:
                if not n['seg']: filled += 1
                n['seg'] = v
                break

# 传谱人小传：从 works_scores.csv 备注列读入，挂到对应节点
import os
NAMEBIO = {}
if os.path.exists('works_scores.csv'):
    for w in csv.DictReader(open('works_scores.csv', encoding='utf-8-sig')):
        if (w.get('备注') or '').strip():
            NAMEBIO[w['名称']] = w['备注'].strip()
for p, d in pieces.items():
    for n in d['nodes'].values():
        n['bio'] = NAMEBIO.get(n['name'], '')

out = {}
for p, d in pieces.items():
    nodes = list(d['nodes'].values())
    out[p] = {'nodes': nodes, 'edges': d['edges']}

json.dump(out, open('/tmp/structure.json', 'w', encoding='utf-8'), ensure_ascii=False)
import os
site = '/Users/sx/个人主页/app/lingnan'
if os.path.isdir(site):
    json.dump(out, open(os.path.join(site,'structure.json'),'w',encoding='utf-8'), ensure_ascii=False)
print('\n>>> 段数补录(论文来源): 新填 %d 本' % filled)

print('=== 四曲结构抽取核对 ===')
for p, d in out.items():
    segs = [n for n in d['nodes'] if n['seg']]
    print(f'\n【{p}】 {len(d["nodes"])}本 / {len(d["edges"])}边 / {len(segs)}本有明确段数')
    for n in sorted(d['nodes'], key=lambda x: (x['year'] or 0)):
        seg = f'{n["seg"]}段' if n['seg'] else '—'
        fl = '/'.join(n['flags']) if n['flags'] else ''
        wx = ' ★悟雪' if '悟雪山房' in n['name'] else ''
        print(f"  {n['year'] or '?'}  {seg:>4}  {n['name']}{wx}  [{fl}]")
