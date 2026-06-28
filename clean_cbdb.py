# -*- coding: utf-8 -*-
"""清洗 persons_cbdb_linked.csv 中 status='auto(仅朝代吻合,待复核)' 的行。
按 id 回查 CBDB 取 籍贯(IndexAddr) + 姓名长度 二次核验：
  - 名字长度不符(如 汪琼→鄧汪瓊) → 否决，清空 CBDB 列
  - 籍贯在岭南 → 升为 'auto-地缘+朝代吻合'(确认)
  - 籍贯在岭南以外省份 → 否决(同名异人)
  - 籍贯空缺 → 保留为 'auto-存疑(无籍贯佐证)'(留线索,不上图)
"""
import csv, json, time, urllib.request

SRC = 'persons_cbdb_linked.csv'
PURL = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=%s&o=json'

LINGNAN = ['廣東','广东','嶺南','岭南','南海','番禺','順德','顺德','新會','新会','香山','東莞','东莞',
 '增城','廣州','广州','韶州','曲江','始興','始兴','英德','英州','惠州','博羅','博罗','潮州','海陽','海阳',
 '揭陽','揭阳','澄海','嘉應','嘉应','梅州','大埔','瓊','琼','海南','廣西','广西','靈川','灵川','陽朔','阳朔',
 '平樂','平乐','高要','高明','開平','开平','四會','四会','德慶','德庆','陽江','阳江','茂名','吳川','吴川',
 '鶴山','鹤山','南雄','保昌','樂昌','乐昌','翁源','連州','连州','清遠','清远','肇慶','肇庆','端州','花縣',
 '花县','龍門','龙门','從化','从化','三水','龍川','龙川','河源','歸善','归善','西寧','郁南','廉江','信宜']
NON_LN = ['浙江','江蘇','江苏','福建','江西','湖南','湖北','安徽','河南','河北','山東','山东','山西','陝西',
 '陕西','四川','雲南','云南','貴州','贵州','北京','直隸','直隶','順天','顺天','錢塘','钱塘','仁和','紹興',
 '绍兴','蘇州','苏州','徽州','閩','闽','吳縣','常州','揚州','扬州','松江','嘉興','嘉兴','湖州','寧波','宁波',
 '太原','大名','保定','濟南','济南','開封','开封','洛陽','洛阳','成都','重慶','重庆','長沙','长沙','南昌',
 '武昌','桂林','臨海']

def fetch(pid):
    try:
        with urllib.request.urlopen(PURL % pid, timeout=20) as r:
            d = json.load(r)
        b = d['Package']['PersonAuthority']['PersonInfo']['Person']
        b = (b[0] if isinstance(b, list) else b).get('BasicInfo', {})
        return b.get('ChName',''), b.get('IndexAddr','') or ''
    except Exception:
        return None, None

rows = list(csv.DictReader(open(SRC, encoding='utf-8-sig')))
cols = list(rows[0].keys())
todo = [r for r in rows if r['CBDB比对状态'].startswith('auto(仅朝代')]
print('待复核行:', len(todo))

stat = {'confirm':0,'reject_name':0,'reject_geo':0,'doubt':0,'err':0}
log = []
for r in todo:
    cn, addr = fetch(r['CBDB编号'])
    if cn is None:
        stat['err'] += 1; time.sleep(0.25); continue
    name_ok = len(cn) == len(r['姓名'])
    in_ln = any(k in addr for k in LINGNAN)
    out_ln = any(k in addr for k in NON_LN)
    if not name_ok:
        verdict = 'reject_name'
        r['CBDB编号']=r['CBDB姓名']=r['CBDB朝代']=r['CBDB生卒']=r['CBDB链接']=''
        r['CBDB比对状态'] = 'no-match(名字不符:%s)' % cn
    elif in_ln:
        verdict = 'confirm'
        r['CBDB姓名'] = cn
        r['CBDB比对状态'] = 'auto-地缘+朝代吻合'
    elif out_ln:
        verdict = 'reject_geo'
        r['CBDB编号']=r['CBDB姓名']=r['CBDB朝代']=r['CBDB生卒']=r['CBDB链接']=''
        r['CBDB比对状态'] = 'no-match(籍贯非岭南:%s)' % addr
    else:
        verdict = 'doubt'
        r['CBDB姓名'] = cn
        r['CBDB比对状态'] = 'auto-存疑(无籍贯佐证)'
    stat[verdict] += 1
    log.append('  %s %s -> CBDB %s「%s」籍贯=%s ==> %s' %
               (r['id'], r['姓名'], r['CBDB编号'] or '—', cn, addr or '空', verdict))
    time.sleep(0.25)

with open(SRC, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

print('=== 清洗结果 ===')
print('确认(地缘吻合):%d  否决-名字不符:%d  否决-籍贯非岭南:%d  存疑保留:%d  网络错误:%d'
      % (stat['confirm'], stat['reject_name'], stat['reject_geo'], stat['doubt'], stat['err']))
ver = sum(1 for r in rows if r['CBDB比对状态']=='verified')
ays = sum(1 for r in rows if r['CBDB比对状态']=='auto(朝代+生卒吻合)')
ag = sum(1 for r in rows if r['CBDB比对状态']=='auto-地缘+朝代吻合')
dbt = sum(1 for r in rows if r['CBDB比对状态'].startswith('auto-存疑'))
linked = ver+ays+ag
print('清洗后:verified=%d + auto生卒=%d + auto地缘=%d = 高置信 %d ；存疑 %d' % (ver,ays,ag,linked,dbt))
print('\n'.join(log))
