import pandas as pd
from vllm import LLM, SamplingParams
import sys

def main():
    # 1. 下载测试集
    try:
        df = pd.read_parquet('/reviewF/datasets/drmas_review/test.parquet')
        paper_content = df['prompt'].iloc[0][0]['content']
    except Exception as e:
        print(f"[Error] Failed to load dataset: {e}")
        sys.exit(1)

    # 2. 配置 Reviewer Agent 系统 Prompt
    system_prompt = (
        "You are an expert academic reviewer. Please provide a detailed review for the following paper. "
        "Your review should include:\n"
        "1. Summary: A brief overview of the contribution.\n"
        "2. Strengths: What makes this paper good.\n"
        "3. Weaknesses: Technical flaws or areas for improvement.\n"
        "4. Conclusion: Final recommendation.\n"
        "Please use academic tone and format your response clearly."
    )
    
    # 构建对话格式
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"The paper content is:\n\n{paper_content}"}
    ]

    # 3. 加载模型及执行推理
    model_path = '/reviewF/datasets/models/Qwen/Qwen2___5-1___5B-Instruct'
    try:
        llm = LLM(model=model_path, gpu_memory_utilization=0.6, enforce_eager=True)
        # 注意：此处使用 chat 模板以确保 1.5B-Instruct 正确响应指令
        sampling_params = SamplingParams(temperature=0.4, top_p=0.9, max_tokens=1024)
        
        print("\n" + "="*80)
        print(f"[Input] Paper Title Sample: Temporal Causal Mechanism Transfer for Few-shot Action Recognition")
        print("="*80 + "\n")

        print("\n[Inferencing] Generating academic review report...\n")
        outputs = llm.chat(messages, sampling_params)
        
        # 4. 打印生成结果
        for output in outputs:
            generated_text = output.outputs[0].text
            print("\n" + "*"*30 + " ACADEMIC REVIEW REPORT " + "*"*30)
            print(generated_text)
            print("*"*34 + " END OF REPORT " + "*"*34 + "\n")
    except Exception as e:
        print(f"[Error] Inference failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
