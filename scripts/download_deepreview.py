from datasets import load_dataset
import json
import os
from pathlib import Path

def download_deepreview(dataset_name="WestLakeNLP/DeepReview-13K", output_dir="data/raw"):
    """下载DeepReview数据集"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"正在加载数据集: {dataset_name}")
    
    # 检查HF_TOKEN环境变量
    if "HF_TOKEN" not in os.environ:
        print("错误: 缺少HF_TOKEN环境变量")
        print("请在Hugging Face网站获取访问令牌，然后设置环境变量:")
        print("export HF_TOKEN=your_token_here")
        print("或直接在代码中设置:")
        print("os.environ['HF_TOKEN'] = 'your_token_here'")
        return None
    
    # 加载数据集
    try:
        ds = load_dataset(dataset_name, token=True)
    except Exception as e:
        print(f"加载数据集失败: {e}")
        print("请确保HF_TOKEN正确且有权访问该数据集")
        return None
    
    print(f"数据集加载完成！包含以下分割:")
    for split in ds:
        print(f"- {split}: {len(ds[split])} 条记录")
    
    # 处理训练集
    if "train" in ds:
        train_data = ds["train"]
        print(f"\n处理训练集: {len(train_data)} 条记录")
        
        # 转换为列表格式
        train_list = []
        for i, item in enumerate(train_data):
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
            
            train_list.append(data_item)
        
        # 保存为JSON文件
        output_file = output_path / "deepreview.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(train_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据集已保存至: {output_file}")
        print(f"共保存: {len(train_list)} 篇论文")
    
    return output_path / "deepreview.json"

if __name__ == "__main__":
    # 示例: 直接设置HF_TOKEN
    os.environ['HF_TOKEN'] = 'HF_TOKEN_REMOVED'
    
    # 下载数据集
    output_file = download_deepreview()

    if output_file:
        print(f"\n下载完成！文件位置: {output_file}")
    else:
        print("\n下载失败，请检查HF_TOKEN设置")