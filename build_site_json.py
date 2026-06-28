# -*- coding: utf-8 -*-
"""把 palladio_persons.csv + palladio_edges.csv 转成个人网站用的 data.json。"""
import csv, json, os

SITE = '/Users/sx/个人主页/app/lingnan'
os.makedirs(SITE, exist_ok=True)

persons = []
by_name = {}
for r in csv.DictReader(open('palladio_persons.csv', encoding='utf-8'), delimiter=';'):
    coord = r['坐标'].strip()
    if not coord:
        continue
    try:
        lat, lng = [float(x) for x in coord.split(',')]
    except Exception:
        continue
    try:
        year = int(r['年份'])
    except Exception:
        continue
    deg = int(r['网络度数']) if r['网络度数'].strip().isdigit() else 0
    p = {
        'id': r['id'], 'name': r['姓名'], 'year': year,
        'lat': round(lat, 4), 'lng': round(lng, 4),
        'group': r['交游圈'], 'deg': deg,
        'dyn': r['朝代'], 'period': r['时期'],
        'deeds': r['事迹'], 'cbdb': r['CBDB编号'], 'url': r['CBDB链接'],
    }
    persons.append(p)
    by_name[r['姓名']] = p

edges = []
for r in csv.DictReader(open('palladio_edges.csv', encoding='utf-8'), delimiter=';'):
    s, t = r['Source'], r['Target']
    if s in by_name and t in by_name:
        edges.append({'s': s, 't': t, 'rel': r['关系'],
                      'w': int(r['权重']) if r['权重'].isdigit() else 1})

persons.sort(key=lambda p: p['year'])
out = {'persons': persons, 'edges': edges,
       'meta': {'n': len(persons), 'n_edges': len(edges),
                'year_min': persons[0]['year'], 'year_max': persons[-1]['year']}}
with open(os.path.join(SITE, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

print('persons(有坐标):', len(persons), ' edges(两端都有坐标):', len(edges))
print('年份范围:', out['meta']['year_min'], '-', out['meta']['year_max'])
print('写入:', os.path.join(SITE, 'data.json'))
