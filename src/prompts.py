# src/prompts.py

PROMPTS = {
    "polish_text": {
        "system": "You are a seasoned copywriter. Your task is to optimize the provided text. Please output only the optimized text without any introductory remarks or explanations.",
        "user_template": "Polish and optimize the following text:\n\n{text}"
    },
    "summarize_points": {
        "system": "You are an efficient information analyst. Your task is to extract key points from the text and present them in an unordered list (using '-'). Output only the final bullet point list.",
        "user_template": "Summarize the main points of the following text:\n\n{text}"
    }
}

TRANSLATE_PROMPT = {
    "system": "You are a professional translator. Your task is to accurately translate the user's text into {target_language}. Provide only the translated text.",
    "user_template": "Please translate the following text into {target_language}:\n\n{text}"
}

def get_prompt_messages(action: str, text: str, **kwargs) -> list | None:
    """Generates the 'messages' list for the API payload."""
    
    if action == "translate":
        target_language = kwargs.get("target_language")
        if not target_language:
            return None
        system_content = TRANSLATE_PROMPT["system"].format(target_language=target_language)
        user_content = TRANSLATE_PROMPT["user_template"].format(target_language=target_language, text=text)
    else:
        prompt_data = PROMPTS.get(action)
        if not prompt_data:
            return None
        system_content = prompt_data["system"]
        user_content = prompt_data["user_template"].format(text=text)

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]