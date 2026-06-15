# 前沿 AI 考核 · 题目一：Memory Systems that Evolve

这是我的题目一提交：在 Flash-Searcher 上用 `deepseek-v4-flash`，在 xBench-DeepSearch 前 20 条任务上跑了 No-Memory 对照、MemEvolve 进化产物（lightweight_memory）和两个人工 memory baseline（ExpeL、Voyager），并做了轨迹级的成功/失败 case 分析。共 **5 组实验、100 条任务**（主实验 4 组 80 条 + 1 组方法级 patch 的 ablation 20 条；另有若干冒烟/调试重跑不计入报告）。

实验基于官方实现 [bingreeky/MemEvolve](https://github.com/bingreeky/MemEvolve)（commit `6035d56`）。原代码不在本仓库里，改动以 diff 形式放在 `patches/`，按下面的步骤可以完整复现。

## 主结果

| 设置 | 准确率 | 平均 token/任务 | 平均 API 调用 | memory 实际注入率 |
|---|---|---|---|---|
| No-Memory（对照） | **18/20 (90%)** | 189,015 | 15.8 | — |
| **Lightweight**（MemEvolve 自动进化产物） | **18/20 (90%)** | 264,103 (+40%) | 27.3 (+73%) | 20/20 |
| ExpeL（semantic baseline） | **17/20 (85%)** | 274,383 (+45%) | 18.2 (+15%) | 19/20 |
| Voyager（procedural baseline） | **18/20 (90%)** | 200,074 (+6%) | 16.7 (+6%) | **0/20**（记忆库静默为空） |

![Accuracy vs cost](assets/accuracy_vs_cost.png)

主要发现：强基线（90%）下 memory 的准确率收益约等于 0，成本却显著上升；收益（问题框架固定、策略迁移）和伤害（未验证的中间结论被记忆"钉死"）集中在难题上互相抵消；Voyager 的技能抽取和深搜任务结构性不匹配、静默失效。过程中还发现并修复了 xBench 判分统计恒为 0% 的 harness bug，并给 lightweight 的 working memory 做了一个"验证门控" patch + ablation（结果为负向，但机制层面的分析见报告 §6.1）。

**完整报告：[REPORT.md](REPORT.md)**（实验设置 / 结果 / case 分析 / limitation / 改进与 ablation）

## 仓库结构

```
REPORT.md                                      实验报告（核心交付物，含轨迹证据附录）
results/summary_per_task.csv                   逐任务汇总（100 行，不含题文，可公开，支撑全部表/图）
results/case_evidence.md                       脱敏 case 证据（store 统计 + 分歧任务 guidance 摘录/归因）
scripts/summarize_results.py                   结果汇总脚本（task_id 对齐 + 去重）
scripts/make_summary_csv.py                    生成 results/summary_per_task.csv
scripts/make_figures.py                        报告插图生成脚本
patches/0001-fix-xbench-accuracy-report.patch  xBench 判分统计 bug 修复
patches/0002-add-verification-gating.patch     working memory 验证门控（方法级 patch）
assets/                                        报告插图
```

`results/summary_per_task.csv` 是去掉题文后的逐任务指标，可公开核对结果。完整原始轨迹（5 组 jsonl）和记忆库终态含 xBench 解密明文，按官方要求不上传公网、线下提供。

## 复现步骤

> ⚠️ `patches/0002`（验证门控）会改写 `lightweight_memory_provider.py`，**只用于 ablation**。主实验四组**不要**应用它，否则跑出来的"原版 Lightweight"已被污染。主实验和 ablation 各用一份独立 checkout。

**共同准备（环境 + 数据）：** 下面"主实验"或"ablation"任一段把仓库 clone 好、`cd` 进 `Flash-Searcher-main` 之后，先执行这一段，再跑对应的实验命令。

```bash
# 前提：已 clone MemEvolve 并 cd 到其 Flash-Searcher-main 目录（见下面两段）
pip install -r requirements.txt                 # Python 3.10
python -m playwright install chromium           # crawl4ai 的浏览器内核
cp .env.example .env                            # 按下面填写
# 数据：xBench-DS 2505 版加密 CSV 放到 ./data/xbench/DeepSearch.csv，
#       xbench-evals 仓库 zip 解压为 ./xbench-evals-main/（判分代码依赖）
```

`.env` 关键项（**裁判模型务必显式设置**，否则 runner 默认落到 `gemini-2.5-flash`、xBench 会判全错）：

```ini
OPENAI_API_KEY=<你的 DeepSeek key>
OPENAI_BASE_URL=https://api.deepseek.com/v1     # OpenAI SDK 读这个
OPENAI_API_BASE=https://api.deepseek.com/v1     # runner 代码读这个，两个都设最稳
DEFAULT_MODEL=deepseek-v4-flash                 # 被试模型
DEFAULT_JUDGE_MODEL=deepseek-v4-flash           # 裁判模型（关键！见下方命令也显式传 --judge_model 双保险）
SERPER_API_KEY=<你的 Serper key>                # 网页搜索
WEB_ACCESS_PROVIDER=crawl4ai                    # 本地抓取，免 key
```

**主实验 4 组（只 apply 0001）：**

```bash
git clone https://github.com/bingreeky/MemEvolve.git && cd MemEvolve
git checkout 6035d56
git apply ../memevolve-assessment/patches/0001-fix-xbench-accuracy-report.patch
cp ../memevolve-assessment/scripts/summarize_results.py Flash-Searcher-main/
cd Flash-Searcher-main   # 完成上面的“共同准备”

# Run 0: No-Memory 对照（concurrency=4 仅为省时，见报告 §2 耗时脚注）
python run_flash_searcher_mm_xbench.py \
    --infile ./data/xbench/DeepSearch.csv --outfile ./xbench_output/nomem_20.jsonl \
    --judge_model deepseek-v4-flash --sample_num 20 --max_steps 40 --concurrency 4

# Run 1–3: 三个 memory system（串行，每个跑前清空自己的 storage）
for p in lightweight_memory expel voyager; do
    rm -rf "storage/$p"
    python run_flash_searcher_mm_xbench.py \
        --infile ./data/xbench/DeepSearch.csv --outfile "./xbench_output/${p%_memory}_20.jsonl" \
        --memory_provider "$p" --judge_model deepseek-v4-flash --sample_num 20 --max_steps 40
done

python summarize_results.py xbench_output/*_20.jsonl   # 汇总
```
> 注：上面 `${p%_memory}` 让 lightweight_memory 的输出文件名为 `lightweight_20.jsonl`，expel/voyager 不受影响。

**ablation（额外 apply 0002，用一份干净 checkout）：**

```bash
git clone https://github.com/bingreeky/MemEvolve.git memevolve-ablation && cd memevolve-ablation
git checkout 6035d56
git apply ../memevolve-assessment/patches/0001-fix-xbench-accuracy-report.patch
git apply ../memevolve-assessment/patches/0002-add-verification-gating.patch
cp ../memevolve-assessment/scripts/summarize_results.py Flash-Searcher-main/
cd Flash-Searcher-main   # 完成“共同准备”
rm -rf storage/lightweight_memory
python run_flash_searcher_mm_xbench.py \
    --infile ./data/xbench/DeepSearch.csv --outfile ./xbench_output/lightweight_gated_20.jsonl \
    --memory_provider lightweight_memory --judge_model deepseek-v4-flash --sample_num 20 --max_steps 40
```

总成本参考：5 组 100 条约 2,400 万 token，DeepSeek-V4-Flash 计价 20 元左右；全程不需要 GPU。
