// グローバル状態
let currentMode = 'idle';
let remainingSeconds = 0;
let timerInterval = null;
const CIRCLE_CIRCUMFERENCE = 754; // 2 * π * 120

// DOM要素
const timerText = document.getElementById('timerText');
const statusText = document.getElementById('statusText');
const progressCircle = document.getElementById('progressCircle');
const startBtn = document.getElementById('startBtn');
const breakBtn = document.getElementById('breakBtn');
const stopBtn = document.getElementById('stopBtn');
const completedCount = document.getElementById('completedCount');
const totalTime = document.getElementById('totalTime');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    fetchState();
    setInterval(fetchState, 60000); // 1分毎に再同期
});

// API呼び出し
async function fetchState() {
    try {
        const response = await fetch('/api/pomodoro/state');
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('状態取得エラー:', error);
    }
}

async function startFocus() {
    try {
        const response = await fetch('/api/pomodoro/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: 25 })
        });
        if (response.ok) {
            await fetchState();
        } else {
            const error = await response.json();
            alert(error.error || i18n.startFailed);
        }
    } catch (error) {
        console.error('開始エラー:', error);
        alert(i18n.startFailed);
    }
}

async function startBreak() {
    try {
        const response = await fetch('/api/pomodoro/break', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: 5 })
        });
        if (response.ok) {
            await fetchState();
        } else {
            const error = await response.json();
            alert(error.error || i18n.breakFailed);
        }
    } catch (error) {
        console.error('休憩開始エラー:', error);
        alert(i18n.breakFailed);
    }
}

async function stopSession() {
    try {
        const response = await fetch('/api/pomodoro/stop', {
            method: 'POST'
        });
        if (response.ok) {
            await fetchState();
        }
    } catch (error) {
        console.error('停止エラー:', error);
    }
}

// UI更新
function updateUI(state) {
    currentMode = state.mode;
    remainingSeconds = state.remaining_seconds;
    
    // ステータステキスト
    if (currentMode === 'focus') {
        statusText.textContent = i18n.working;
        progressCircle.style.stroke = '#667eea';
    } else if (currentMode === 'break') {
        statusText.textContent = i18n.breaking;
        progressCircle.style.stroke = '#48bb78';
    } else {
        statusText.textContent = i18n.idle;
        progressCircle.style.stroke = '#cbd5e0';
    }
    
    // ボタン状態
    if (currentMode === 'idle') {
        startBtn.disabled = false;
        breakBtn.disabled = false;
        stopBtn.disabled = true;
    } else {
        startBtn.disabled = true;
        breakBtn.disabled = true;
        stopBtn.disabled = false;
    }
    
    // 統計
    completedCount.textContent = state.completed_focus_count;
    const hours = Math.floor(state.total_focus_seconds / 3600);
    const minutes = Math.floor((state.total_focus_seconds % 3600) / 60);
    totalTime.textContent = hours > 0 ? `${hours}${i18n.hours}${minutes}${i18n.minutes}` : `${minutes}${i18n.minutes}`;
    
    // タイマー開始/停止
    if (currentMode !== 'idle' && remainingSeconds > 0) {
        startCountdown();
    } else {
        stopCountdown();
        updateTimerDisplay(remainingSeconds);
    }
}

// カウントダウン
function startCountdown() {
    if (timerInterval) return;
    
    timerInterval = setInterval(() => {
        if (remainingSeconds > 0) {
            remainingSeconds--;
            updateTimerDisplay(remainingSeconds);
        } else {
            stopCountdown();
            fetchState(); // 終了時に再取得
        }
    }, 1000);
}

function stopCountdown() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    timerText.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
    
    // プログレスリング更新
    const totalSeconds = currentMode === 'focus' ? 25 * 60 : (currentMode === 'break' ? 5 * 60 : 25 * 60);
    const progress = totalSeconds > 0 ? (totalSeconds - seconds) / totalSeconds : 0;
    const offset = CIRCLE_CIRCUMFERENCE * (1 - progress);
    progressCircle.style.strokeDashoffset = offset;
}

// イベントリスナー
startBtn.addEventListener('click', startFocus);
breakBtn.addEventListener('click', startBreak);
stopBtn.addEventListener('click', stopSession);
