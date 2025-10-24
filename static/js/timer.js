// グローバル状態
let currentMode = 'idle';
let remainingSeconds = 0;
let timerInterval = null;
const CIRCLE_CIRCUMFERENCE = 754; // 2 * π * 120

// Preset configurations
const PRESETS = {
    'default': { focus: 25, break: 5 },
    'long': { focus: 50, break: 10 },
    'short': { focus: 15, break: 3 }
};

// DOM要素
const timerText = document.getElementById('timerText');
const statusText = document.getElementById('statusText');
const progressCircle = document.getElementById('progressCircle');
const startBtn = document.getElementById('startBtn');
const breakBtn = document.getElementById('breakBtn');
const stopBtn = document.getElementById('stopBtn');
const completedCount = document.getElementById('completedCount');
const totalTime = document.getElementById('totalTime');
const presetRadios = document.querySelectorAll('input[name="preset"]');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    loadSelectedPreset();
    fetchState();
    setInterval(fetchState, 60000); // 1分毎に再同期
    
    // Preset change listener
    presetRadios.forEach(radio => {
        radio.addEventListener('change', handlePresetChange);
    });
});

// Load selected preset from localStorage
function loadSelectedPreset() {
    const savedPreset = localStorage.getItem('selectedPreset') || 'default';
    const radio = document.querySelector(`input[name="preset"][value="${savedPreset}"]`);
    if (radio) {
        radio.checked = true;
    }
}

// Handle preset change
function handlePresetChange(event) {
    const selectedPreset = event.target.value;
    localStorage.setItem('selectedPreset', selectedPreset);
}

// Get current preset durations
function getCurrentPreset() {
    const selectedRadio = document.querySelector('input[name="preset"]:checked');
    const presetKey = selectedRadio ? selectedRadio.value : 'default';
    return PRESETS[presetKey];
}

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
        const preset = getCurrentPreset();
        const response = await fetch('/api/pomodoro/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: preset.focus })
        });
        if (response.ok) {
            await fetchState();
        } else {
            const error = await response.json();
            alert(error.error || '開始に失敗しました');
        }
    } catch (error) {
        console.error('開始エラー:', error);
        alert('開始に失敗しました');
    }
}

async function startBreak() {
    try {
        const preset = getCurrentPreset();
        const response = await fetch('/api/pomodoro/break', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: preset.break })
        });
        if (response.ok) {
            await fetchState();
        } else {
            const error = await response.json();
            alert(error.error || '休憩開始に失敗しました');
        }
    } catch (error) {
        console.error('休憩開始エラー:', error);
        alert('休憩開始に失敗しました');
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
        statusText.textContent = '作業中';
        progressCircle.style.stroke = '#667eea';
    } else if (currentMode === 'break') {
        statusText.textContent = '休憩中';
        progressCircle.style.stroke = '#48bb78';
    } else {
        statusText.textContent = '待機中';
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
    totalTime.textContent = hours > 0 ? `${hours}時間${minutes}分` : `${minutes}分`;
    
    // タイマー開始/停止
    if (currentMode !== 'idle' && remainingSeconds > 0) {
        startCountdown(state.planned_duration_sec);
    } else {
        stopCountdown();
        updateTimerDisplay(remainingSeconds, state.planned_duration_sec);
    }
}

// カウントダウン
let plannedDurationSec = 0;

function startCountdown(duration_sec) {
    if (timerInterval) return;
    
    plannedDurationSec = duration_sec;
    
    timerInterval = setInterval(() => {
        if (remainingSeconds > 0) {
            remainingSeconds--;
            updateTimerDisplay(remainingSeconds, plannedDurationSec);
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

function updateTimerDisplay(seconds, totalSeconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    timerText.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
    
    // プログレスリング更新
    if (!totalSeconds) {
        const preset = getCurrentPreset();
        totalSeconds = currentMode === 'focus' ? preset.focus * 60 : (currentMode === 'break' ? preset.break * 60 : preset.focus * 60);
    }
    const progress = totalSeconds > 0 ? (totalSeconds - seconds) / totalSeconds : 0;
    const offset = CIRCLE_CIRCUMFERENCE * (1 - progress);
    progressCircle.style.strokeDashoffset = offset;
}

// イベントリスナー
startBtn.addEventListener('click', startFocus);
breakBtn.addEventListener('click', startBreak);
stopBtn.addEventListener('click', stopSession);
