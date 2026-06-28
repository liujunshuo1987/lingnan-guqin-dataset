# -*- coding: utf-8 -*-
"""把 persons_unified 升级为：① CBDB 链接表 ② Palladio 就绪包（人物+关系）。
CBDB 种子为 WebFetch 实测核对（按朝代+生卒+籍贯消歧），可用 query_cbdb() 在本地联网补全其余。
"""
import csv, re, json
try:
    import urllib.request, urllib.parse
except Exception:
    urllib = None

# ---------- CBDB 已核验种子 (按 person id) ----------
# (cbdb_id, cbdb_name, cbdb_dynasty, cbdb_dates, status)
SEED = {
 'P014': ('29570','陳獻章','明','1428-1500','verified'),
 'P015': ('131191','湛若水','明','1466-1560','verified'),
 'P016': ('30674','黃佐','明','1490-1566','verified'),
 'P030': ('73479','鄺露','清','1604-1650','verified'),
 'P040': ('65498','陳恭尹','清','1631-1700','verified'),
 'P041': ('30190','屈大均','清','1630-1696','verified'),
 'P042': ('63883','梁佩蘭','清','1632-1708','verified'),
 'P058': ('91347','黎簡','清','1748-1799','verified'),
 'P085': ('54955','陳澧','清','1810-1882','verified'),
 'P191': ('3130','張九齡','唐','678-740','verified'),
 'P195': ('38678','石汝礪','宋','?-?','verified'),
 'P204': ('24353','葛長庚(白玉蟾)','宋','1134-1229','verified'),
 'P209': ('97542','歐陽辟','宋','?-?','verified'),
 'P189': ('158150','侯安都','未詳','?-?','candidate-待核'),
 'P070': ('','','','','no-match(明1474_201688为同名异人,晚清覆盖薄)'),
}
CBDB_URL = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={}'

def query_cbdb(name, want_dynasty=None, want_year=None):
    """本地联网用：按名查 CBDB，按朝代/生卒消歧。返回 (id,name,dyn,dates) 或 None。
    sandbox 无网络，故默认不在本脚本内调用；用户本机可解开 ENABLE_LIVE。"""
    if urllib is None: return None
    url = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=%s&o=json' % urllib.parse.quote(name)
    try:
        data = json.load(urllib.request.urlopen(url, timeout=20))
    except Exception:
        return None
    pkg = data.get('Package',{}).get('PersonAuthority',{}).get('PersonInfo',{}).get('Person')
    if not pkg: return None
    cands = pkg if isinstance(pkg,list) else [pkg]
    best=None
    for c in cands:
        basic=c.get('BasicInfo',c)
        dyn=basic.get('Dynasty',''); by=basic.get('YearBirth',''); dy=basic.get('YearDeath','')
        score=0
        if want_dynasty and want_dynasty in str(dyn): score+=2
        if want_year and by and abs(int(by)-want_year)<=40: score+=2
        if best is None or score>best[0]:
            best=(score, basic.get('PersonId',''), basic.get('NameChn',''), dyn, '%s-%s'%(by,dy))
    if best and best[0]>0:
        return best[1:]
    return None

ENABLE_LIVE = False  # 本机联网补全时改 True

DYN_FALLBACK = {'三国':250,'南北朝':500,'唐':700,'五代':940,'北宋':1050,'南宋':1200,
 '宋':1100,'元':1320,'明末清初':1644,'明末':1640,'明':1500,'清初':1670,'清末':1900,
 '清':1750,'近代':1920}

def rep_year(period, dyn):
    m = re.search(r'(\d{3,4})', period or '')
    if m: return m.group(1)
    for k,v in DYN_FALLBACK.items():
        if (dyn or '').startswith(k): return str(v)
    return ''

rows = list(csv.DictReader(open('persons_unified.csv', encoding='utf-8-sig')))

# ---------- ① CBDB 链接表 ----------
linked_cols = list(rows[0].keys()) + ['CBDB编号','CBDB姓名','CBDB朝代','CBDB生卒','CBDB比对状态','CBDB链接']
n_ver=0; n_nomatch=0
for r in rows:
    s = SEED.get(r['id'])
    if ENABLE_LIVE and s is None and r['朝代'] and r['朝代'] not in ('近代',):
        q = query_cbdb(r['姓名'], r['朝代'], int(rep_year(r['时期'],r['朝代']) or 0) or None)
        if q: s = (q[0],q[1],q[2],q[3],'auto-需复核')
    if s:
        cid,cn,cdyn,cdates,st = s
        r['CBDB编号']=cid; r['CBDB姓名']=cn; r['CBDB朝代']=cdyn; r['CBDB生卒']=cdates
        r['CBDB比对状态']=st; r['CBDB链接']=CBDB_URL.format(cid) if cid else ''
        if st=='verified': n_ver+=1
        if st.startswith('no-match'): n_nomatch+=1
    else:
        for c in ['CBDB编号','CBDB姓名','CBDB朝代','CBDB生卒','CBDB链接']: r[c]=''
        r['CBDB比对状态']='unchecked'

with open('persons_cbdb_linked.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f, fieldnames=linked_cols); w.writeheader(); w.writerows(rows)

# ---------- ② Palladio 人物表 (分号分隔, 坐标合并) ----------
pal_cols=['id','姓名','异名','朝代','时期','年份','所属府地','现代区划','坐标',
          '交游圈','网络度数','在网络图','来源组','事迹','CBDB编号','CBDB链接','数据标记']
with open('palladio_persons.csv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    w.writerow(pal_cols)
    for r in rows:
        coord = '%s,%s'%(r['lat'],r['lng']) if r['lat'] and r['lng'] else ''
        w.writerow([r['id'],r['姓名'],r['异名'],r['朝代'],r['时期'],rep_year(r['时期'],r['朝代']),
            r['所属府地'],r['现代行政区划'],coord,r['群体(网络类别)'],r['网络度数'],
            r['在网络图'],r['来源组'],r['事迹'],r['CBDB编号'],r['CBDB链接'],r['数据标记']])

# ---------- ② Palladio 关系表 ----------
NODES="""N1 黄景星|N2 黄文玉|N3 黄炳堃|N4 庆瑞|N5 朱启连|N6 陈献章|N7 黄观炯|N8 黄鸣盛|N9 何洛书|N10 何文祥|N11 盛复初|N12 张文焯|N13 莫锡龄|N14 陈世堂|N15 陈灼奎|N16 陈绮石|N17 潘名熊|N18 冯筠|N19 释以直|N20 莫韵石|N21 莫延芳|N22 赵古农|N23 胡准|N24 杨锡泉|N25 何耀琨|N26 黄淇|N27 黄崇干|N28 释玉堂|N29 黄玉衔|N30 梁树基|N31 陈其锟|N32 苏敬衡|N33 金树本|N34 卢桐君|N35 何子桂|N36 曾望颜|N37 吴家树|N38 杨恩锡|N39 阮寅|N40 王宾|N41 冯有光|N42 陈燕|N43 陈小屏|N44 李澄宇|N45 郑绩|N46 李芝仙|N47 周振麟|N48 张淑娟|N49 陈澧|N50 李梦庚|N51 黄绍昌|N52 何煜恒|N53 张志清|N54 陶邵学|N55 宋彦成|N56 陈叔举|N57 章珠垣|N58 高大林|N59 叶秩甫|N60 杨兆桂|N61 容心言|N62 招鉴芬|N63 卢家炳|N64 郑健候|N65 杨新伦"""
nm={}
for tok in NODES.split('|'):
    i,nme=tok.split(' '); nm[i]=nme
EDGES="""N6 N1 思想源泉(白沙心学) 1|N8 N1 家学(传古冈遗谱) 3|N7 N1 师承(启蒙指法) 3|N9 N1 师承(授大操) 3|N10 N1 师承(授碧天秋思) 2|N11 N1 师承(授金门待漏) 2|N12 N1 师承(授水仙操) 2|N13 N1 长辈鼓励 1|N14 N1 师承(授雁落平沙) 2|N1 N2 师承(叔侄授琴) 3|N1 N3 师承(叔祖授琴) 3|N1 N15 授琴/琴社核心 2|N1 N16 联作琴社 2|N1 N17 琴社交游 2|N1 N18 授琴/琴社交游 2|N1 N19 琴社交游/泛舟 1|N1 N20 订谱(岳阳三醉) 2|N1 N21 订谱(同门畏友) 2|N1 N24 授琴/琴谱作序 2|N1 N26 家学(子校字) 1|N1 N27 家学(侄同订谱) 2|N22 N1 琴谱作序 1|N23 N1 琴谱参订 1|N25 N1 琴谱作序 1|N2 N36 琴脔参订 1|N2 N29 挚友/琴脔作序 2|N2 N31 题咏(广州故交) 1|N32 N2 长官赏识/题序 1|N33 N2 同僚题咏 1|N37 N2 同僚题咏 1|N2 N30 授琴(折服拜师) 2|N2 N34 授业弟子 1|N2 N35 授业弟子 1|N2 N3 家学(父子) 3|N3 N38 传琴/影响滇省 3|N3 N39 琴诗之友(双目失明) 1|N40 N3 为黄炳堃鼓琴 1|N3 N41 听琴赠答 1|N42 N38 传谱(金陵派) 2|N43 N38 滇省琴交 1|N50 N38 传谱(粤东鹤山) 2|N44 N4 师承(广陵派) 3|N4 N46 授琴瑟/合奏 3|N4 N47 授琴/合奏 2|N4 N48 授琴瑟(谊女) 1|N4 N45 梦香园主客/合奏 2|N45 N49 梦香园雅集 1|N45 N50 梦香园雅集 1|N45 N23 梦香园雅集 1|N45 N51 梦香园雅集 1|N4 N61 家族血脉(祖孙) 3|N52 N5 启蒙引荐 1|N53 N5 师承(授琴) 3|N54 N5 师承(授琴律) 3|N5 N55 授琴/切磋 2|N5 N56 授琴/切磋 2|N5 N57 晚清琴圈/修琴 1|N5 N58 晚清琴圈/修琴 1|N5 N59 晚清琴圈切磋 1|N5 N60 深厚琴交/论绿绮台 2|N61 N62 借抄古冈遗谱 2|N61 N63 授琴(容授卢) 2|N64 N65 授琴(郑授杨) 3|N63 N65 授琴(卢授杨) 2|N56 N61 民国交游桥梁 1|N56 N65 民国交游桥梁 1"""
with open('palladio_edges.csv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    w.writerow(['Source','Target','关系','权重'])
    ne=0
    for tok in EDGES.split('|'):
        parts=tok.split(' '); s,t,wt=parts[0],parts[1],parts[-1]; lab=' '.join(parts[2:-1])
        w.writerow([nm[s],nm[t],lab,wt]); ne+=1

print('=== DH 升级包 构建报告 ===')
print('① persons_cbdb_linked.csv  (CBDB列已加)')
print(f'   已核验 CBDB 匹配: {n_ver}  明确无匹配: {n_nomatch}  其余 unchecked (待本机联网补全)')
print('② palladio_persons.csv  (%d 行, 分号分隔, 坐标合并, 年份字段供时间轴)' % len(rows))
print('   palladio_edges.csv   (%d 条关系, Source;Target;关系;权重)' % ne)
print('   有坐标可上图: %d' % sum(1 for r in rows if r['lat'] and r['lng']))
