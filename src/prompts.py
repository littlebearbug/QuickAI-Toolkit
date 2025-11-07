# src/prompts.py

# Keep the static prompts for non-translation tasks
PROMPTS = {
    "polish_text": {
        "system": "You are a seasoned copywriter and language polishing expert. Your task is to optimize and improve the text provided by users, ensuring it meets the highest standards in terms of grammar, style, clarity, and persuasiveness. Please output only the optimized text without any introductory remarks, conclusions, or explanatory language.",
        "user_template": "Polish and optimize the following text:\n\n{text}"
    },
    "summarize_points": {
        "system": "You are an efficient information analyst. Your task is to precisely extract key points from the text provided by users and present them clearly in an unordered list (using '-' as a prefix). The summary should be comprehensive yet concise, outputting only the final bullet point list.",
        "user_template": "Summarize the main points of the following text:\n\n{text}"
    }
}

# NEW: A generic template for all translation tasks
TRANSLATE_PROMPT = {
    "system": "You are a professional translator. Your task is to accurately translate the user's text into {target_language}. Provide only the translated text, without any additional explanations, comments, or the original text.",
    "user_template": "Please translate the following text into {target_language}:\n\n{text}"
}

def get_prompt_payload(action: str, text: str, model_name: str, **kwargs) -> dict | None:
    """
    Generates the payload for the API call based on the action.
    For translation, it uses kwargs to get the target language.
    """

    if action == "translate":
        target_language = kwargs.get("target_language")
        if not target_language:
            return None
        
        system_content = TRANSLATE_PROMPT["system"].format(target_language=target_language)
        user_content = TRANSLATE_PROMPT["user_template"].format(target_language=target_language, text=text)

        return {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "stream": True
        }
    
    # Handle other, non-translation actions
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