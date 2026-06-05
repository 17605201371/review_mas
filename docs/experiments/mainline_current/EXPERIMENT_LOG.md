# Experiment Log (Root Index)

快速索引。详细内容在 `docs/experiments/`。

## 三份汇总文档

| 文档 | 内容 |
|---|---|
| [`docs/experiments/EXPERIMENT_LOG.md`](docs/experiments/EXPERIMENT_LOG.md) | 按时间排序的完整流水账（所有实验） |
| [`docs/experiments/POSITIVE_EXPERIMENTS.md`](docs/experiments/POSITIVE_EXPERIMENTS.md) | 成功改动（主线保留） |
| [`docs/experiments/FAILED_EXPERIMENTS.md`](docs/experiments/FAILED_EXPERIMENTS.md) | 失败改动 + "不要重做" 列表 |

## 当前主线

`p25.1 baseline + explicit recovery phase + flaw_fix_v2 (+0.0417) + TQC observability v1`

- **Mean reward (Layer 3, 10 样本)**: **0.6251**
- **Decision correct**: 9/10
- **分支**: `codex/p25-1-explicit-mainline`
- **最新 commit**: `e1f8f1e` (回滚 Recovery Entry Decision v1 defer 行为)

## 归档原始文档位置

| 子目录 | 内容 |
|---|---|
| `docs/experiments/archive/p25_0/` | p25.0 基线建立相关（7 文档） |
| `docs/experiments/archive/p25_1/` | p25.1 iteration subset + flaw_fix_v2 compare（11 文档） |
| `docs/experiments/archive/progression_gate_v1/` | progression_gate_v1 失败实验（5 文档） |
| `docs/experiments/archive/forensic_v2/` | Target / recovery push 溯源（5 文档） |
| `docs/experiments/archive/tqc_and_red_v1/` | TQC audit + Recovery Entry Decision v1 失败（3 文档） |

## 运行日志

所有 `.log` 文件已归档到 `logs/`。
