const messagesEl = document.getElementById('messages');
const recordBtn = document.getElementById('record-btn');
const statusEl = document.getElementById('status');
const meNameEl = document.getElementById('me-name');

let mediaRecorder;
let audioChunks = [];
let ws;
let isRecording = false;
let startTime = 0;
let startY = 0;
let isCanceling = false;
let currentAudio = null; 

// ==========================================
// 🌟 终极修复：前端自己生成名字，彻底摆脱后端依赖
// ==========================================
let myName = localStorage.getItem("voice_chat_name_final");

// 如果是新用户第一次进来（本地没名字）
if (!myName) {
    // 生成一个 100 - 999 的随机数字，拼在后面
    const randomNum = Math.floor(Math.random() * 900) + 100;
    myName = "圆周率_" + randomNum; 
    localStorage.setItem("voice_chat_name_final", myName); // 死锁在本地
}
meNameEl.textContent = myName; // 进页面立刻显示名字！

function showThinking() {
    removeThinking(); 
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = 'thinking-indicator';
    thinkingDiv.className = 'msg system-msg';
    thinkingDiv.innerHTML = `<span class="content" style="color: #a62626; animation: pulse 1.5s infinite;">AI 正在疯狂思考中...</span>`;
    messagesEl.appendChild(thinkingDiv);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeThinking() {
    const indicator = document.getElementById('thinking-indicator');
    if (indicator) indicator.remove();
}

function loadHistory() {
    // 换用 v6 终极仓库，彻底洗清之前的脏数据
    let history = JSON.parse(localStorage.getItem("voice_history_v6") || "[]");
    history.forEach((msg, index) => {
        const isSelf = (msg.sender === myName);
        appendVoiceBubble(msg.sender, msg.duration, msg.base64Audio, isSelf, msg.isPlayed, index);
    });
}

function saveToHistory(sender, duration, base64Audio, isPlayed) {
    let history = JSON.parse(localStorage.getItem("voice_history_v6") || "[]");
    if (history.length >= 50) history = []; // 满50条直接清空，重新开始
    history.push({ sender, duration, base64Audio, isPlayed });
    localStorage.setItem("voice_history_v6", JSON.stringify(history));
}

function connectWebSocket() {
    const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
    ws = new WebSocket(proto + location.host + '/ws/audio');

    ws.onopen = () => {
        statusEl.textContent = '已连接';
        statusEl.style.color = '#00ffaa';
        recordBtn.disabled = false;
        recordBtn.textContent = '按住说话 (上滑取消)';
    };

    ws.onmessage = (event) => {
        const text = event.data;
        
        // 彻底无视后端的名字分配，因为前端已经自己生成好了
        if (text.startsWith("SYSTEM_INIT::")) {
            return; 
        }

        try {
            const msgData = JSON.parse(text);
            if (msgData.type === 'voice') {
                const isSelf = (msgData.sender === myName);
                if (!isSelf) removeThinking();

                appendVoiceBubble(msgData.sender, msgData.duration, msgData.audio, isSelf, false);
                saveToHistory(msgData.sender, msgData.duration, msgData.audio, false);
            }
        } catch (e) {
            console.error("解析消息失败", text);
        }
    };

    ws.onclose = () => {
        statusEl.textContent = '未连接';
        statusEl.style.color = '#a62626';
        recordBtn.disabled = true;
        setTimeout(connectWebSocket, 2000);
    };
}

async function initMicrophone() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            if (isCanceling) {
                audioChunks = [];
                return; 
            }
            const duration = Math.round((Date.now() - startTime) / 1000) || 1;
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                const base64Audio = reader.result;
                const msgData = {
                    type: 'voice',
                    sender: myName, // 发送自己生成的名字
                    duration: duration,
                    audio: base64Audio
                };
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(msgData));
                    showThinking();
                }
            };
            audioChunks = [];
        };
    } catch (err) {
        alert("麦克风被拒绝，请刷新重试");
    }
}

function appendVoiceBubble(sender, duration, audioUrl, isSelf, isPlayed = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${isSelf ? 'self' : 'ai'}`;
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'sender-name';
    nameSpan.textContent = sender;
    nameSpan.style.display = 'block';
    nameSpan.style.fontSize = '11px';
    nameSpan.style.color = '#666';
    nameSpan.style.marginBottom = '2px';
    nameSpan.style.textAlign = isSelf ? 'right' : 'left';

    const bubbleWrap = document.createElement('div');
    bubbleWrap.style.position = 'relative'; 
    bubbleWrap.style.display = 'inline-block';

    const bubble = document.createElement('div');
    bubble.className = 'voice-bubble';
    bubble.textContent = `${duration}"`;
    
    const redDot = document.createElement('div');
    redDot.className = 'red-dot';
    if (isSelf || isPlayed) redDot.style.display = 'none';

    bubble.onclick = () => {
        redDot.style.display = 'none';
        
        // 标记已读
        let history = JSON.parse(localStorage.getItem("voice_history_v6") || "[]");
        for(let i = history.length - 1; i >= 0; i--) {
            if(history[i].sender === sender && history[i].duration === duration && !history[i].isPlayed) {
                history[i].isPlayed = true;
                break;
            }
        }
        localStorage.setItem("voice_history_v6", JSON.stringify(history));

        // 防止重叠
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
        currentAudio = new Audio(audioUrl);
        currentAudio.play();
    };

    bubbleWrap.appendChild(bubble);
    bubbleWrap.appendChild(redDot);

    const container = document.createElement('div');
    container.appendChild(nameSpan);
    container.appendChild(bubbleWrap);
    msgDiv.appendChild(container);
    
    messagesEl.appendChild(msgDiv);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function startRecord(e) {
    if (e) e.preventDefault();
    if (!mediaRecorder || isRecording) return;
    startY = e.clientY || (e.touches && e.touches[0].clientY);
    isCanceling = false;
    audioChunks = [];
    mediaRecorder.start();
    isRecording = true;
    startTime = Date.now();
    recordBtn.textContent = '松开结束 (上滑取消)';
    recordBtn.style.backgroundColor = 'var(--accent)';
    recordBtn.style.color = '#fff';
    document.addEventListener('mousemove', moveRecord);
    document.addEventListener('mouseup', stopRecord);
    document.addEventListener('touchmove', moveRecord, { passive: false });
    document.addEventListener('touchend', stopRecord);
}

function moveRecord(e) {
    if (!isRecording) return;
    if (e.cancelable) e.preventDefault(); 
    const currentY = e.clientY || (e.touches && e.touches[0].clientY);
    const deltaY = startY - currentY; 
    if (deltaY > 40) { 
        if (!isCanceling) {
            isCanceling = true;
            recordBtn.textContent = '松开取消';
            recordBtn.style.backgroundColor = '#333'; 
            recordBtn.style.color = '#ff4d4d';
        }
    } else {
        if (isCanceling) {
            isCanceling = false;
            recordBtn.textContent = '松开结束 (上滑取消)';
            recordBtn.style.backgroundColor = 'var(--accent)';
            recordBtn.style.color = '#fff';
        }
    }
}

function stopRecord(e) {
    if (!isRecording || !mediaRecorder) return;
    mediaRecorder.stop();
    isRecording = false;
    recordBtn.textContent = '按住说话 (上滑取消)';
    recordBtn.style.backgroundColor = '#16161c';
    recordBtn.style.color = 'var(--text)';
    document.removeEventListener('mousemove', moveRecord);
    document.removeEventListener('mouseup', stopRecord);
    document.removeEventListener('touchmove', moveRecord);
    document.removeEventListener('touchend', stopRecord);
}

recordBtn.addEventListener('mousedown', startRecord);
recordBtn.addEventListener('touchstart', startRecord);

loadHistory();
connectWebSocket();
initMicrophone();