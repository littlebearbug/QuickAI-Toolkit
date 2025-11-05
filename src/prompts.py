# src/prompts.py

PROMPTS = {
    "translate_chinese": {
        "system": "你是一位精通简体中文的专业翻译家。你的任务是只翻译用户提供的文本，不添加任何与翻译无关的解释、评论或原文。请确保翻译结果自然、流畅且精准地传达原文的含义。",
        "user_template": "请将以下文本翻译成简体中文：\n\n{text}"
    },
    "polish_text": {
        "system": "你是一位资深的文案编辑和语言润色专家。你的任务是优化和改进用户提供的文本，使其在语法、风格、清晰度和说服力上都达到最高标准。请直接输出优化后的文本，不要包含任何前言、结尾或解释性文字。",
        "user_template": "请润色和优化以下文本：\n\n{text}"
    },
    "summarize_points": {
        "system": "你是一位高效的信息分析师。你的任务是精准地从用户提供的文本中提取核心要点，并以无序列表（使用'-'作为前缀）的形式清晰地呈现。总结应全面且简洁，只输出最终的要点列表。",
        "user_template": "请总结以下文本的要点：\n\n{text}"
    }
}

def get_prompt_payload(action: str, text: str, model_name: str) -> dict | None:
    """
    Generates the payload for the OpenAI-compatible API call.
    """
    prompt_data = PROMPTS.get(action)
    if not prompt_data:
        return None
    
    user_content = prompt_data["user_template"].format(text=text)
    
    return {
        "model": model_name,
        "messages": [
            {"role": "system", "content": prompt_data["system"]},
            {"role": "user", "content": user_content}
        ],
        "stream": True
    }