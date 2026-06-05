from datasets import load_dataset
import json
import os

def check_dataset_structure(dataset_name="WestLakeNLP/DeepReview-13K"):
    """检查数据集结构"""
    print(f"正在加载数据集: {dataset_name}")
    
    # 检查HF_TOKEN
    if "HF_TOKEN" not in os.environ:
        # 使用硬编码的token
        os.environ['HF_TOKEN'] = 'HF_TOKEN_REMOVED'
    
    # 加载数据集
    try:
        # 只加载前10条记录
        ds = load_dataset(dataset_name, token=True, split="train[:10]")
        
        print(f"\n数据集加载完成！共 {len(ds)} 条记录")
        
        # 查看第一条记录
        print("\n第一条记录:")
        print(json.dumps(ds[0], ensure_ascii=False, indent=2))
        
        # 检查字段
        print("\n字段列表:")
        if ds and len(ds) > 0:
            for key in ds[0].keys():
                print(f"- {key}")
        
        # 检查reviews字段
        print("\nReviews字段检查:")
        for i, item in enumerate(ds):
            if "reviews" in item:
                print(f"记录 {i}: reviews字段存在")
                if item["reviews"]:
                    print(f"  包含 {len(item['reviews'])} 条评论")
                    if item["reviews"] and len(item["reviews"]) > 0:
                        print(f"  第一条评论:")
                        print(json.dumps(item["reviews"][0], ensure_ascii=False, indent=4))
                else:
                    print(f"  reviews字段为空")
            else:
                print(f"记录 {i}: 没有reviews字段")
        
        # 检查其他可能的字段名
        print("\n其他可能的字段检查:")
        if ds and len(ds) > 0:
            for key in ds[0].keys():
                if "review" in key.lower():
                    print(f"- {key}")
    
    except Exception as e:
        print(f"加载数据集失败: {e}")

if __name__ == "__main__":
    check_dataset_structure()
