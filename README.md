# 前沿 AI 考核 · 题目一：Memory Systems that Evolve

这是我的题目一提交：在 Flash-Searcher 上用 `deepseek-v4-flash`，在 xBench-DeepSearch 前 20 条任务上跑了 No-Memory 对照、MemEvolve 进化产物（lightweight_memory）和两个人工 memory baseline（ExpeL、Voyager），共 6 组实验（含一组方法级 patch 的 ablation）、120 条任务，并做了轨迹级的成功/失败 case 分析。

实验基于官方实现 [bingreeky/MemEvolve](https://github.com/bingreeky/MemEvolve)（commit `6035d56`）。原代码不在本仓库里，我的改动以 diff 形式放在 `patches/`，按下面的步骤可以完整复现。

## 主结果

| 设置 | 准确率 | 平均 token/任务 | 平均 API 调用 | memory 实际注入率 |
|---|---|---|---|---|
| No-Memory（对照） | **18/20 (90%)** | 189,015 | 15.8 | — |
| **Lightweight**（MemEvolve 自动进化产物） | **18/20 (90%)** | 264,103 (+40%) | 27.3 (+73%) | 20/20 |
| ExpeL（semantic baseline） | **17/20 (85%)** | 274,383 (+45%) | 18.2 | 19/20 |
| Voyager（procedural baseline） | **18/20 (90%)** | 200,074 (+6%) | 16.7 | **0/20**（记忆库静默为空） |

我的主要发现：强基线（90%）下 memory 的准确率收益约等于 0，成本却显著上升；收益（问题框架固定、策略迁移）和伤害（未验证的中间结论被记忆"钉死"）集中在难题上互相抵消；Voyager 的技能抽取和深搜任务结构性不匹配、静默失效。过程中我还发现并修复了 xBench 判分统计恒为 0% 的 harness bug，并给 lightweight 的 working memory 做了一个"验证门控" patch + ablation（结果为负向，但机制层面的分析见报告 §6.1）。

**完整报告：[REPORT.md](REPORT.md)**（实验设置 / 结果 / case 分析 / limitation / 改进与 ablation）

## 仓库结构

```
REPORT.md                                      实验报告（核心交付物）
scripts/summarize_results.py                   结果汇总脚本（task_id 对齐 + 去重）
patches/0001-fix-xbench-accuracy-report.patch  xBench 判分统计 bug 修复
patches/0002-add-verification-gating.patch     working memory 验证门控（方法级 patch）
```

原始轨迹（5 组 jsonl）和记忆库终态在我本地归档。因为里面含 xBench 解密后的题目明文，官方要求不上传公网，需要的话可以线下提供。

## 复现步骤

```bash
# 1. 克隆官方仓库，固定到我实验时的版本，应用 patch
git clone https://github.com/bingreeky/MemEvolve.git && cd MemEvolve
git checkout 6035d56
git apply ../memevolve-assessment/patches/0001-fix-xbench-accuracy-report.patch
git apply ../memevolve-assessment/patches/0002-add-verification-gating.patch  # 仅复现 ablation 时需要
cp ../memevolve-assessment/scripts/summarize_results.py Flash-Searcher-main/

# 2. 环境（Python 3.10）
cd Flash-Searcher-main
pip install -r requirements.txt
python -m playwright install chromium          # crawl4ai 的浏览器内核
cp .env.example .env                            # 填入 DeepSeek key 和 Serper key，
                                                # DEFAULT_MODEL/裁判模型设为 deepseek-v4-flash，
                                                # WEB_ACCESS_PROVIDER=crawl4ai

# 3. 数据：xBench-DS 2505 版加密 CSV 放到 ./data/xbench/DeepSearch.csv，
#    并把 xbench-evals 仓库 zip 解压为 ./xbench-evals-main/（判分代码依赖）

# 4. 跑实验（memory_provider 依次换成 expel / voyager；每次先清空对应 storage）
python run_flash_searcher_mm_xbench.py \
    --infile ./data/xbench/DeepSearch.csv \
    --outfile ./xbench_output/nomem_20.jsonl \
    --sample_num 20 --max_steps 40 --concurrency 4

rm -rf storage/lightweight_memory
python run_flash_searcher_mm_xbench.py \
    --infile ./data/xbench/DeepSearch.csv \
    --outfile ./xbench_output/lightweight_20.jsonl \
    --memory_provider lightweight_memory \
    --sample_num 20 --max_steps 40

# 5. 汇总
python summarize_results.py xbench_output/*_20.jsonl
```

总成本参考：6 组 × 20 条约 2,500 万 token，DeepSeek-V4-Flash 计价 20 元左右；全程不需要 GPU。
