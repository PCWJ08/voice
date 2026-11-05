# --- 硅基流动 语音识别 (ASR) 配置 ---
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")

SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

ASR_MODEL = "FunAudioLLM/SenseVoiceSmall"


# --- 智谱 AI 配置 ---
ZHIPU_API_KEY =os.getenv("ZHIPU_API_KEY", "")

ZHIPU_BASE_URL = "https://apihub.agnes-ai.com/v1"
#"https://open.bigmodel.cn/api/paas/v4/"

ZHIPU_MODEL = "agnes-3.0-flash"
#"glm-4-flash-250414"


# --- 精神病人人设与音色分配 ---
AI_PERSONAS = {
    "老K ": {
        "prompt": "你是一个脾气火爆、说话直来直去的大叔，性格粗俗。你喜欢用不耐烦、大声的语气反驳别人，能少量说脏话。字数绝对不能超过12个字！",
        "voice": "zh-CN-YunxiNeural" 
    },
    "小橘": {
        "prompt": "你是一个高高在上、喜欢说风凉话的小人，总是蔑视别人。你总觉得人类很蠢，喜欢用嘲讽、阴阳的语气说话。字数绝对不能超过12个字！",
        "voice": "zh-CN-XiaoxiaoNeural" 
    }
}