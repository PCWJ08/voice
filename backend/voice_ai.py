import base64
import io
from openai import AsyncOpenAI
import config

# 硅基流动完全兼容 OpenAI 接口，所以直接用这个库
voice_client = AsyncOpenAI(
    base_url=config.SILICONFLOW_BASE_URL,
    api_key=config.SILICONFLOW_API_KEY
)

async def audio_to_text(base64_audio: str) -> str:
    """
    接收前端传来的 Base64 音频，返回识别出的文字
    """
    try:
        # 1. 剥离前端的 data:audio/webm;base64, 前缀
        if "," in base64_audio:
            base64_data = base64_audio.split(",")[1]
        else:
            base64_data = base64_audio
            
        # 2. 将 Base64 还原成二进制数据（Bytes）
        audio_bytes = base64.b64decode(base64_data)
        
        # 3. 包装成文件格式，因为 OpenAPI 的语音接口需要一个文件对象
        audio_file = ("audio.webm", io.BytesIO(audio_bytes), "audio/webm")

        # 4. 呼叫硅基流动的语音识别模型
        response = await voice_client.audio.transcriptions.create(
            model=config.ASR_MODEL,
            file=audio_file
        )
        
        return response.text

    except Exception as e:
        print(f"❌ [语音识别报错]: {e}", flush=True)
        return "（没听清或识别失败）"