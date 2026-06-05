import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

def load_raw_data(file_path: str) -> pd.DataFrame:
    """加载原始DeepReview数据集"""
    print(f"正在加载原始数据: {file_path}")
    return pd.read_json(file_path)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """数据清洗"""
    # 1. 移除重复论文
    df = df.drop_duplicates(subset=['paper_id'])
    
    # 2. 过滤无效评论（少于20个字符）并处理评分
    def process_reviews(reviews):
        processed = []
        for r in reviews:
            if len(r.get('comments', '')) >= 20:
                # 处理评分字段，转换为数值类型
                for score_key in ['novelty_score', 'technical_score', 'presentation_score']:
                    if score_key in r:
                        score = r[score_key]
                        if isinstance(score, str):
                            # 尝试从字符串中提取数字
                            try:
                                # 例如 '3 good' -> 3
                                r[score_key] = float(score.split()[0])
                            except:
                                r[score_key] = 3.0  # 默认值
                    else:
                        r[score_key] = 3.0  # 默认值
                processed.append(r)
        return processed
    
    df['reviews'] = df['reviews'].apply(process_reviews)
    
    # 3. 移除无有效审稿的论文
    df = df[df['reviews'].apply(len) > 0]
    
    # 4. 填充缺失值
    if 'abstract' in df.columns:
        df['abstract'] = df['abstract'].fillna('')
    else:
        df['abstract'] = ''
    
    print(f"清洗后保留论文: {len(df)}篇")
    return df

def analyze_data(df: pd.DataFrame, output_dir: Path):
    """数据分析与可视化"""
    print("\n数据分析:")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 评分分布分析
    all_scores = []
    for reviews in df['reviews']:
        for r in reviews:
            if 'novelty_score' in r:
                all_scores.append(r['novelty_score'])
    
    if all_scores:
        plt.figure(figsize=(10, 6))
        plt.hist(all_scores, bins=10, alpha=0.7)
        plt.title('创新性评分分布')
        plt.xlabel('分数')
        plt.ylabel('数量')
        plt.savefig(output_dir / 'score_distribution.png')
        print(f"已保存评分分布图: {output_dir/'score_distribution.png'}")
    
    # 2. 领域分布分析
    if 'domain' in df.columns:
        domain_counts = df['domain'].value_counts()
        print("\n领域分布:")
        print(domain_counts)
        plt.figure(figsize=(10, 6))
        domain_counts.plot(kind='bar')
        plt.title('论文领域分布')
        plt.savefig(output_dir / 'domain_distribution.png')
        print(f"已保存领域分布图: {output_dir/'domain_distribution.png'}")

def process_data(input_path: str, output_dir: str):
    """核心处理流程"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 加载数据
    raw_df = load_raw_data(input_path)
    
    # 2. 数据清洗
    cleaned_df = clean_data(raw_df)
    
    # 3. 数据分析
    analyze_data(cleaned_df, output_path)
    
    # 4. 保存处理结果
    output_file = output_path / "deepreview_processed.parquet"
    cleaned_df.to_parquet(str(output_file))
    print(f"处理后的数据已保存至: {output_file}")
    
    return cleaned_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DeepReview数据处理器')
    parser.add_argument('--input', type=str, required=True, help='原始数据文件路径')
    parser.add_argument('--output', type=str, required=True, help='处理结果输出目录')
    args = parser.parse_args()
    
    process_data(args.input, args.output)