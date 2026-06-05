from datasets import load_dataset
import json
import os
from pathlib import Path

def process_deepreview(dataset_name="WestLakeNLP/DeepReview-13K", output_dir="data/processed"):
    """处理DeepReview数据集"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"正在加载数据集: {dataset_name}")
    
    # 检查HF_TOKEN
    if "HF_TOKEN" not in os.environ:
        # 使用硬编码的token
        os.environ['HF_TOKEN'] = 'HF_TOKEN_REMOVED'
    
    # 加载数据集
    try:
        # 直接从Hugging Face加载
        ds = load_dataset(dataset_name, token=True)
        
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
            if "reviewer_comments" in item and item["reviewer_comments"]:
                try:
                    # 解析reviewer_comments字段
                    if isinstance(item["reviewer_comments"], str):
                        import json
                        reviewer_comments = json.loads(item["reviewer_comments"])
                    else:
                        reviewer_comments = item["reviewer_comments"]
                    
                    # 检查是否是列表
                    if isinstance(reviewer_comments, list):
                        for review in reviewer_comments:
                            if isinstance(review, dict):
                                review_item = {
                                    "reviewer_id": review.get("id", ""),
                                    "comments": review.get("content", {}).get("summary", review.get("content", "")),
                                    "novelty_score": review.get("content", {}).get("contribution", 3.0),
                                    "technical_score": review.get("content", {}).get("soundness", 3.0),
                                    "presentation_score": review.get("content", {}).get("presentation", 3.0)
                                }
                                data_item["reviews"].append(review_item)
                except Exception as e:
                    # 解析失败时跳过
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
    output_file = process_deepreview()
    if output_file:
        print(f"\n处理完成！文件位置: {output_file}")
    else:
        print("\n处理失败，请检查输入文件")