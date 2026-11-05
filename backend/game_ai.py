import base64
import edge_tts
import re
from openai import AsyncOpenAI
import config

llm_client = AsyncOpenAI(
    base_url=config.ZHIPU_BASE_URL,
    api_key=config.ZHIPU_API_KEY
)

BAD_WORDS = ["操"]

async def generate_ai_reply(player_name: str, user_text: str) -> str:
    persona = config.AI_PERSONAS[player_name]
    
    safe_text = user_text
    for word in BAD_WORDS:
        safe_text = safe_text.replace(word, "*")
        
    prompt = f"{persona['prompt']}\n\n用户说：“{safe_text}”\n直接输出回复（不超过12字，绝不解释）："
    try:
        response = await llm_client.chat.completions.create(
            model=config.ZHIPU_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.9
        )
        result = response.choices[0].message.content.strip().replace("“", "").replace("”", "")
        for word in BAD_WORDS:
            result = result.replace(word, "*")
        return result
    except Exception as e:
        print(f"❌ [模型报错] {player_name}: {e}", flush=True)
        return ""

async def text_to_base64_audio(text: str, voice: str, role: str = "normal") -> str:
    if not text or not re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]', text):
        return ""

    try:
        rate = "+10%" if "老K " in role else "-15%"
        pitch = "-10Hz" if "老K " in role else "+15Hz"
        volume = "+20%" if "老K " in role else "-8%"

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
                
        return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"❌ [TTS 报错] : {e}", flush=True)
        return ""