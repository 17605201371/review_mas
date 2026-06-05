from datasets import load_from_disk
import json
import os
from pathlib import Path

def process_deepreview_arrow(cache_dir="/Users/zss/.cache/huggingface/datasets/WestLakeNLP___deep_review-13_k", output_dir="data/processed"):
    """处理DeepReview Arrow格式数据集"""
    cache_path = Path(cache_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 检查缓存目录
    if not cache_path.exists():
        print(f"错误: 未找到缓存目录 {cache_path}")
        return None
    
    print(f"正在处理数据集: {cache_path}")
    
    # 加载数据集
    try:
        # 从缓存目录加载
        ds = load_from_disk(cache_path / "default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23")
        
        print(f"\n数据集加载完成！包含以下分割:")
        for split in ds:
            print(f"- {split}: {len(ds[split])} 条记录")
    except Exception as e:
        print(f"加载数据集失败: {e}")
        return None
    
    # 处理训练集
    if "train" in ds:
        train_data = ds["train"]
        print(f"\n处理训练集: {len(train_data)} 条记录")
        
        # 处理数据
        processed_data = []
        
        for i, item in enumerate(train_data):
            if i % 1000 == 0:
                print(f"处理进度: {i}/{len(train_data)}", end='\r')
            
            # 构建数据结构
            data_item = {
                "paper_id": item.get("id", f"train_{i}"),
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "reviews": []
            }
            
            # 处理审稿信息
            if "reviews" in item and item["reviews"]:
                for review in item["reviews"]:
                    review_item = {
                        "reviewer_id": review.get("reviewer_id", ""),
                        "comments": review.get("content", ""),
                        "novelty_score": review.get("scores", {}).get("novelty", 3.0),
                        "technical_score": review.get("scores", {}).get("technical", 3.0),
                        "presentation_score": review.get("scores", {}).get("presentation", 3.0)
                    }
                    data_item["reviews"].append(review_item)
            
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
        print(f"原始记录数: {len(train_data)}")
        print(f"有效论文数: {len(processed_data)}")
        
        # 计算平均审稿数
        total_reviews = sum(len(item["reviews"]) for item in processed_data)
        if processed_data:
            avg_reviews = total_reviews / len(processed_data)
            print(f"平均每篇论文审稿数: {avg_reviews:.2f}")
        
        return output_file
    else:
        print("错误: 数据集中没有train分割")
        return None

if __name__ == "__main__":
    # 处理数据集
    output_file = process_deepreview_arrow()
    if output_file:
        print(f"\n处理完成！文件位置: {output_file}")
    else:
        print("\n处理失败，请检查输入文件")