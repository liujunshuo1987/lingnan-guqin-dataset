# 岭南琴学数据集 / Lingnan Guqin Dataset

明清岭南古琴琴人与琴谱的结构化数据集，含**人物权威表、社会网络、历史地理坐标、琴谱传承谱系**，并对接 [CBDB 中国历代人物传记资料库](https://cbdb.fas.harvard.edu/)。底层考据出自刘峻铄博士论文《嶺南琴學文獻與琴史研究》（中山大学，2020）。

> A structured dataset of Guqin players and tablatures in Ming–Qing Lingnan (Guangdong): a person authority file, a social network, historical-geographic coordinates, and a tablature-transmission stemma, aligned to the China Biographical Database (CBDB).

## 数据文件

| 文件 | 内容 | 行数 |
|---|---|---|
| `persons_unified.csv` | 人物权威表（唯一 id、籍贯、经纬度、交游圈、**网络度数**、事迹） | 226 |
| `persons_cbdb_linked.csv` | 上表 + CBDB 编号/朝代/生卒/比对状态/链接 | 226 |
| `works_scores.csv` | 琴谱作品权威表（含原曲、关键传谱人） | 42 |
| `transmission_edges.csv` | 古冈遗谱四曲（醉渔唱晚·碧涧流泉·渔樵问答·鸥鹭忘机）传承边 | 50 |
| `palladio_persons.csv` | Palladio 就绪人物表（分号分隔，坐标合并，含年份字段） | 226 |
| `palladio_edges.csv` | Palladio 就绪关系表（Source;Target;关系;权重） | 66 |
| `build_*.py` | 全部可复跑的构建脚本 | — |

## 关键发现（数据已坐实）

- **黄景星是网络枢纽**：度中心性 24，断层第一（第二名黄文玉仅 11）——以图论坐实其「岭南琴派基石」论断。
- **四曲皆汇于《悟雪山房琴谱》**：入度 4 / 出度 10。四处「古冈遗谱」标注的真实上游分别是松风阁（韩晶清宫谱）、琴学軔端（×2）、梧冈琴谱，**无一为宋代古冈遗谱**。

## CBDB 对接方法

按**姓名→朝代+生卒+籍贯消歧**匹配，杜绝同名异人。当前 13 人已逐一 WebFetch 核验（见 `persons_cbdb_linked.csv` 中 `CBDB比对状态=verified`）：

- 陈献章 29570 · 张九龄 3130 · 湛若水 131191 · 黄佐 30674 · 邝露 73479 · 陈恭尹 65498 · 屈大均 30190 · 梁佩兰 63883 · 黎简 91347 · 陈澧 54955 · 石汝砺 38678 · 欧阳辟 97542 · 白玉蟾（CBDB 入「葛长庚」24353）

随后用 `complete_cbdb.py` 联网批量补全其余行（严格朝代+生卒消歧），**全表共 76 人匹配 CBDB**：13 人 `verified`（人工核验）+ 约 18 人 `auto(朝代+生卒吻合)`（高置信）+ 其余 `auto(仅朝代吻合,待复核)`（仅供线索，需人工复核）。`persons_cbdb_linked.csv` 的 `CBDB比对状态` 列标明每行的置信层级。

典型陷阱：**黄景星**在 CBDB 仅有一个明代 1474 的同名异人（id 201688），故标 `no-match`；**白玉蟾**须按本名「葛长庚」才能查得。这正是必须按朝代+生卒消歧、不能纯按名匹配的原因。

> CBDB API：`https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=陳獻章&o=json`

## 在 Palladio 中打开（即时地图/网络/时间轴）

1. 打开 <https://hdlab.stanford.edu/palladio/> → **Start**。
2. 把 `palladio_persons.csv` 拖入（或粘贴）。设定字段类型：`坐标`→**Coordinates**、`年份`→**Number**、`CBDB链接`→**URL**。
3. **Map** 视图：以 `坐标` 落点，可按 `年份` 时间轴过滤，看「新会→广州」扩散。
4. 加载 `palladio_edges.csv` 作为扩展表 → **Graph** 视图：`Source`/`Target` 成网，看黄景星枢纽。
5. **Gallery/Table** 可点 `CBDB链接` 跳转人物权威记录。

> 注：Palladio 是**客户端探索工具，不托管公开站点**。可引用的在线成果靠下方 DOI。

## 让它「可引用」：Zenodo → DOI

1. 把本目录的 `*.csv` + `README.md` + `CITATION.cff` + `LICENSE.txt` 打成一个仓库/压缩包。
2. 登录 <https://zenodo.org/>（可绑 GitHub 仓库，打 tag 即自动存档并版本化 DOI）。
3. 上传，元数据从 `CITATION.cff` 带入；类型选 **Dataset**；许可选 **CC-BY-4.0**。
4. **Publish** → 获得形如 `10.5281/zenodo.XXXXXXX` 的 DOI，回填到本 README 顶部徽章。

## 引用 / Citation

见 `CITATION.cff`。数据许可 CC-BY-4.0（见 `LICENSE.txt`）。CBDB 编号字段的再利用须遵循 [CBDB 自身使用条款](https://cbdb.fas.harvard.edu/) 并致谢。

## 已知待办

- 17 行 `数据标记`（合并单元格拆分、群体行如「朱/严二秀才」「袁大敬等父子」）需人工复核。
- `杨恩锡`(N38)、`李澄宇`(N44) 为网络专有，待补地理坐标。
- CBDB unchecked 行可本机联网批量补全。
