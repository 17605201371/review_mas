#!/bin/bash
# 创建Python虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装核心依赖
pip install pandas scikit-learn pyarrow matplotlib

# 安装开发依赖
pip install pytest pytest-cov

echo "环境设置完成！运行 'source .venv/bin/activate' 激活环境"