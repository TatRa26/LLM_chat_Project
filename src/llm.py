import logging

from openai import OpenAI

from configs import config

logger = logging.getLogger(__name__)

class LlamaService:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_url
        )
        
        self.system_prompt = {
            "role": "system",
            "content": "Ты - полезный ассистент, который всегда отвечает на русском языке. "
                      "Твои ответы должны быть информативными, но краткими и по существу."
        }
    
    def generate_response(self, prompt: str, history: list[dict[str, str]]) -> str:
        try:
            messages = [self.system_prompt]
            messages.extend(history[-5:])  # Наивная реализация истории
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=256,
                top_p=0.95
            )
            response = response.choices[0].message.content.strip()

        except Exception as e:
            logger.exception(f'Ошибка при обращении к API: {str(e)}')
            response = 'Извините, что-то пошло не так. Попробуйте еще раз!'

        return response
