import pandas as pd
import json
import os
from pathlib import Path

def process_deepreview_csv(input_dir="data/raw", output_dir="data/processed"):
    """处理DeepReview CSV格式数据集"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 检查输入文件
    train_file = input_path / "train.csv"
    if not train_file.exists():
        print(f"错误: 未找到训练文件 {train_file}")
        print("请确保数据集已下载到 data/raw/ 目录")
        return None
    
    print(f"正在处理数据集: {train_file}")
    print(f"文件大小: {train_file.stat().st_size / 1024 / 1024 / 1024:.2f} GB")
    
    # 读取CSV文件
    try:
        # 分批读取以处理大文件
        chunks = []
        total_rows = 0
        
        for chunk in pd.read_csv(train_file, chunksize=10000):
            total_rows += len(chunk)
            print(f"已读取: {total_rows} 行")
            chunks.append(chunk)
        
        df = pd.concat(chunks)
        print(f"\n数据集加载完成！共 {len(df)} 条记录")
        print(f"列名: {list(df.columns)}")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None
    
    # 处理数据
    processed_data = []
    
    for i, row in df.iterrows():
        if i % 1000 == 0:
            print(f"处理进度: {i}/{len(df)}", end='\r')
        
        # 构建数据结构
        data_item = {
            "paper_id": row.get("id", f"paper_{i}"),
            "title": row.get("title", ""),
            "abstract": row.get("abstract", ""),
            "reviews": []
        }
        
        # 处理审稿信息
        if "reviews" in row and pd.notna(row["reviews"]):
            try:
                # 解析reviews字段（可能是JSON格式）
                reviews = json.loads(row["reviews"])
                if isinstance(reviews, list):
                    for review in reviews:
                        review_item = {
                            "reviewer_id": review.get("reviewer_id", ""),
                            "comments": review.get("content", ""),
                            "novelty_score": review.get("scores", {}).get("novelty", 3.0),
                            "technical_score": review.get("scores", {}).get("technical", 3.0),
                            "presentation_score": review.get("scores", {}).get("presentation", 3.0)
                        }
                        data_item["reviews"].append(review_item)
            except:
                # 如果解析失败，跳过
                pass
        
        # 只保留有审稿意见的数据
        if data_item["reviews"]:
            processed_data.append(data_item)
    
    print(f"\n处理完成！共保留 {len(processed_data)} 篇有效论文")
    
    # 保存处理后的数据
    output_file = output_path / "deepreview_processed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存至: {output_file}")
    print(f"文件大小: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 生成统计信息
    print("\n数据集统计信息:")
    print(f"原始记录数: {len(df)}")
    print(f"有效论文数: {len(processed_data)}")
    
    # 计算平均审稿数
    total_reviews = sum(len(item["reviews"]) for item in processed_data)
    if processed_data:
        avg_reviews = total_reviews / len(processed_data)
        print(f"平均每篇论文审稿数: {avg_reviews:.2f}")
    
    return output_file

if __name__ == "__main__":
    # 处理数据集
    output_file = process_deepreview_csv()
    if output_file:
        print(f"\n处理完成！文件位置: {output_file}")
    else:
        print("\n处理失败，请检查输入文件")