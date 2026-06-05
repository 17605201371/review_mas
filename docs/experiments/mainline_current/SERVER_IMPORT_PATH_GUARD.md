# Server Import Path Guard

## 问题

服务器 conda 环境中存在旧代码目录 `/root/zssmas`。如果直接运行 `conda run -n DrMAS-qwen35 python ...`，Python 可能优先导入旧 `agent_system`，导致测试或推理没有使用当前主线 `/root/zssmas_mainline` 的代码。

## 当前修复

- 在当前仓库新增 `agent_system/__init__.py`，使其成为显式 package。
- 新增 sanity / 后续实验命令应使用：

```bash
PYTHONPATH=/root/zssmas_mainline /opt/conda/bin/conda run -n DrMAS-qwen35 python <script.py>
```

## 论文主试验要求

所有服务器端主试验命令、dry-run、sanity 都必须记录 `PYTHONPATH` 或等效路径保护，避免复现实验误导入旧代码。
