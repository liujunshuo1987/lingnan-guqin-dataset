# -*- coding: utf-8 -*-
"""以 persons_cbdb_linked.csv 为权威源，重建：
 - palladio_persons.csv（所有 CBDB 匹配都带号/链接）
 - 个人网站 app/lingnan/data.json（仅 verified + auto朝代生卒吻合 才放可点 CBDB 链接）
"""
import csv, re, json, os

SITE = '/Users/sx/个人主页/app/lingnan'
DYN_FALLBACK = {'三国':250,'南北朝':500,'唐':700,'五代':940,'北宋':1050,'南宋':1200,
 '宋':1100,'元':1320,'明末清初':1644,'明末':1640,'明':1500,'清初':1670,'清末':1900,
 '清':1750,'近代':1920}
def rep_year(period, dyn):
    m = re.search(r'(\d{3,4})', period or '')
    if m: return int(m.group(1))
    for k,v in DYN_FALLBACK.items():
        if (dyn or '').startswith(k): return v
    return None

def high_conf(status):
    return status == 'verified' or status == 'auto(朝代+生卒吻合)'

rows = list(csv.DictReader(open('persons_cbdb_linked.csv', encoding='utf-8-sig')))

# --- palladio_persons.csv ---
pal_cols = ['id','姓名','异名','朝代','时期','年份','所属府地','现代区划','坐标',
            '交游圈','网络度数','在网络图','来源组','事迹','CBDB编号','CBDB链接','数据标记']
with open('palladio_persons.csv','w',encoding='utf-8',newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(pal_cols)
    for r in rows:
        coord = '%s,%s'%(r['lat'],r['lng']) if r['lat'] and r['lng'] else ''
        y = rep_year(r['时期'], r['朝代'])
        w.writerow([r['id'],r['姓名'],r['异名'],r['朝代'],r['时期'], y if y else '',
            r['所属府地'],r['现代行政区划'],coord,r['群体(网络类别)'],r['网络度数'],
            r['在网络图'],r['来源组'],r['事迹'],r['CBDB编号'],r['CBDB链接'],r['数据标记']])

# --- site data.json ---
persons=[]; by_name={}
for r in rows:
    if not (r['lat'] and r['lng']): continue
    y = rep_year(r['时期'], r['朝代'])
    if y is None: continue
    hc = high_conf(r['CBDB比对状态'])
    p={'id':r['id'],'name':r['姓名'],'year':y,
       'lat':round(float(r['lat']),4),'lng':round(float(r['lng']),4),
       'group':r['群体(网络类别)'],'deg':int(r['网络度数']) if r['网络度数'].strip().isdigit() else 0,
       'dyn':r['朝代'],'period':r['时期'],'deeds':r['事迹'],
       'cbdb':r['CBDB编号'] if hc else '', 'url':r['CBDB链接'] if hc else ''}
    persons.append(p); by_name[r['姓名']]=p

edges=[]
for r in csv.DictReader(open('palladio_edges.csv', encoding='utf-8'), delimiter=';'):
    if r['Source'] in by_name and r['Target'] in by_name:
        edges.append({'s':r['Source'],'t':r['Target'],'rel':r['关系'],
                      'w':int(r['权重']) if r['权重'].isdigit() else 1})

persons.sort(key=lambda p:p['year'])
out={'persons':persons,'edges':edges,'meta':{'n':len(persons),'n_edges':len(edges),
     'year_min':persons[0]['year'],'year_max':persons[-1]['year']}}
with open(os.path.join(SITE,'data.json'),'w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,separators=(',',':'))

linked = sum(1 for p in persons if p['url'])
total_cbdb = sum(1 for r in rows if r['CBDB编号'].strip())
print('palladio_persons.csv 重建: %d 行, 含CBDB号 %d' % (len(rows), total_cbdb))
print('site data.json: %d 人 / %d 边, 地图可点CBDB链接(高置信) %d' % (len(persons), len(edges), linked))
