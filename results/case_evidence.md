# Case 证据（脱敏）

> 这份文件把报告 §3 / §6.1 case 分析依赖的关键证据集中到一处，方便评审不取线下原始轨迹也能核主要论点。脱敏尺度与报告正文一致：题意为转述、答案只留判分所需的短值、`memory_guidance` 取摘录。完整原始轨迹（含 xBench 解密题文）按官方要求不上传公网，线下提供。
>
> 字段来源：`score`/`tokens`/`api_calls`/`status`/`trajectory_logged` 来自 `results/summary_per_task.csv`；`memory_guidance` 摘录来自各组原始 jsonl 轨迹的对应字段。

## 一、记忆库终态统计（store stats，纯计数，无题文）

各 memory system 跑完 20 条任务后的存储归档统计——支撑报告中"ExpeL 积累 80 条 insights""Voyager 静默为空""Lightweight 自带冷启动"等论点：

| 设置 | 存储终态 | 说明 |
|---|---|---|
| Lightweight（原版） | strategic 41 条 + operational 38 条 | 初始注入 7 条冷启动（5 策略 + 2 操作），跑完增长到 79 条 |
| ExpeL | insights 80 条 + success_trajectories 17 条 | semantic insight + episodic 成功轨迹库 |
| Voyager | memories **0 条** | 技能抽取对深搜轨迹**静默失败**，全程零存储零注入（Case E） |
| Lightweight + 门控 | strategic / operational（同量级） | 条目带 `(source: …)` / `[UNVERIFIED]` 标注 |

## 二、四条分歧任务 × 各设置（逐题可审计表）

分数与资源来自 `summary_per_task.csv`；✅=对，❌=错。

### 任务 5（Case A）：电影台词 → GB/T 11881-2006 计算题，golden=12

| 设置 | 判分 | tokens | 关键证据（memory_guidance 摘录 / 行为） | 最终答案 |
|---|---|---|---|---|
| No-Memory | ❌ | 69,919 | 无注入 | 8 |
| Lightweight | ✅ | 179,363 | 第 1 步注入正确问题框架："GB/T 11881-2006 是羽毛相关国标；目标是算 10 个合规品最少需几只家禽" | 12 |
| ExpeL | ✅ | 129,647 | 注入的"相似成功案例"内容无关（B站视频题），但迁移了"拆子目标→并行检索→交叉验证"策略骨架 | 12 |
| Voyager | ❌ | 147,950 | 零注入 | 8 |

注：Lightweight 注入里第 2 条"GB/T 11881-2006 likely related to down and feather products"其实是**错误假设**（实为羽毛球国标），但未影响最终数值，原版"侥幸"答对——对照门控版（下方任务 5 门控）。

### 任务 9（Case C）：北京地铁第二近站点，golden=16 号线 玉渊潭东门–木樨地

| 设置 | 判分 | tokens | 关键证据 | 最终答案 |
|---|---|---|---|---|
| No-Memory | ✅ | 282,061 | 无注入 | 16 号线 玉渊潭东门–木樨地 |
| Lightweight | ✅ | 204,506 | working memory 正常 | 16 号线 玉渊潭东门–木樨地 |
| ExpeL | ❌ | 317,467 | 注入**完全无关**的"相似成功案例"（明日方舟「两面包夹芝士」梗视频干员职业题），agent 顺噪声跑偏 | 14 号线 高家园–望京南（676 米，错线） |
| Voyager | ✅ | 440,289 | 零注入 | 16 号线 玉渊潭东门–木樨地 |

ExpeL 注入摘录：
```
ExpeL Similar successful case for '在首次提到"两面包夹芝士"的视频中，up主最后提到的干员是什么职业':
1. 分解问题为可搜索的子目标：先确定"两面包夹芝士"这个梗的出处视频…
2. 使用精准关键词进行网络搜索…  5. 查询干员的官方职业…
```
同一条无关案例在任务 10 的 ExpeL 注入里也出现——是检索器对这两题的系统性误召回，非偶发。

### 任务 10（Case B）：北京三祠堂等距点，golden=6~7 km

| 设置 | 判分 | tokens | 关键证据 | 最终答案 |
|---|---|---|---|---|
| No-Memory | ✅ | 359,828 | 无注入 | 约 6.87 km |
| Lightweight | ❌ | 1,728,852 | **残缺坐标被当"已确认事实"注入**：两祠堂有坐标、于谦祠仅地址无坐标，缺口无标记，后续拿残缺数据硬算外心、不再质疑 | 27 km |
| ExpeL | ❌ | 1,952,325 | 注入与几何无关的相似案例（纯噪声），反复检索烧掉基线整组一半 token | 4.44 km |
| Voyager | ❌ | 1,020,314 | 零注入；失败属该题高方差 | 11.53 km |
| Lightweight + 门控 | ❌ | 1,050,337 | 别名猜测被标 `Unverified`；"百科未提供坐标"记为显式缺口；先补坐标（带 Wikipedia 来源）再算，token −39% | 26.85 km |

Lightweight 原版注入摘录（残缺坐标被钉死）：
```
**Key Information & Constraints:**
1. 文天祥祠坐标：39°56′3.49″N 116°24′14.37″E
2. 袁崇焕祠坐标：39°53′36.96″N 116°25′54.23″E
3. 于谦祠搜索结果未提供经纬度，仅给出地址：东城区西裱褙胡同23号
```
门控版注入摘录（缺口被显式追踪）：
```
Unverified working hypotheses:
1~3. 三祠堂别名猜测…
Caution: items above are hypotheses, not established facts. Before using any
unverified or missing value in reasoning or calculations, verify it via search first.
```
答案仍错（26.85 km）的真因是三祠堂近共线、外心对坐标误差极敏感（数值病态），不归 memory 层管。

### 任务 17（Case D）：央财历任校长姓氏统计，golden=王

| 设置 | 判分 | tokens | 关键证据 | 最终答案 |
|---|---|---|---|---|
| No-Memory | ❌ | 251,518 | 无注入 | 陈、王并列 |
| Lightweight | ❌ | 212,484 | 注入正常但不解决裁量问题 | 陈、王并列 |
| ExpeL | ❌ | 538,143 | — | 陈、王并列 |
| Voyager | ✅ | 308,690 | 零注入；纯采样运气 | 王 |

瓶颈在"哪些前身机构校长算数"的边界裁量与聚合推理，memory 帮不上忙。

## 三、ablation 中的不可归因记录

| 记录 | 现象 | 处理 |
|---|---|---|
| lightweight-gated · 任务 9 | `status=success`、`trajectory_logged=0`（全 100 条唯一一条轨迹未落盘）、跑了 37 次调用 / 727 s 后答"无"放弃、score=0 | 轨迹缺失无法用 `memory_guidance` 复盘，**不计入门控机制证据**（详见报告 §6.1） |

CSV 里可直接筛 `trajectory_logged=0` 复核此条。
