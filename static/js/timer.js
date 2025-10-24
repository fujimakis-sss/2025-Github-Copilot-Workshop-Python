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
const tagInput = document.getElementById('tagInput');
const recentTagsDatalist = document.getElementById('recentTags');
const tagStatsContent = document.getElementById('tagStatsContent');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    fetchState();
    loadRecentTags();
    loadTagStats();
    setInterval(fetchState, 60000); // 1分毎に再同期
    setInterval(loadTagStats, 60000); // 1分毎にタグ統計更新
});

// LocalStorage からタグを取得
function getRecentTagsFromStorage() {
    const tags = localStorage.getItem('recentTags');
    return tags ? JSON.parse(tags) : [];
}

// LocalStorage にタグを保存
function saveTagToStorage(tag) {
    if (!tag || tag.trim() === '') return;
    
    let tags = getRecentTagsFromStorage();
    // 既存のタグを削除（重複防止）
    tags = tags.filter(t => t !== tag);
    // 先頭に追加
    tags.unshift(tag);
    // 最大10個まで保持
    tags = tags.slice(0, 10);
    
    localStorage.setItem('recentTags', JSON.stringify(tags));
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

async function loadRecentTags() {
    try {
        const response = await fetch('/api/pomodoro/tags/recent');
        const tags = await response.json();
        
        // LocalStorageのタグとマージ
        const localTags = getRecentTagsFromStorage();
        const allTags = [...new Set([...localTags, ...tags])];
        
        // datalist更新
        recentTagsDatalist.innerHTML = '';
        allTags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            recentTagsDatalist.appendChild(option);
        });
    } catch (error) {
        console.error('最近のタグ取得エラー:', error);
    }
}

async function loadTagStats() {
    try {
        const response = await fetch('/api/pomodoro/stats/by-tag');
        const stats = await response.json();
        
        // タグ統計を表示
        if (stats.length === 0) {
            tagStatsContent.innerHTML = '<p class="no-stats">タグ別統計はまだありません</p>';
        } else {
            tagStatsContent.innerHTML = stats.map(stat => {
                const hours = Math.floor(stat.total_focus_seconds / 3600);
                const minutes = Math.floor((stat.total_focus_seconds % 3600) / 60);
                const timeStr = hours > 0 ? `${hours}時間${minutes}分` : `${minutes}分`;
                
                return `
                    <div class="tag-stat-item">
                        <span class="tag-name">${stat.tag || '(タグなし)'}</span>
                        <span class="tag-count">${stat.completed_focus_count}回</span>
                        <span class="tag-time">${timeStr}</span>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('タグ統計取得エラー:', error);
    }
}

async function startFocus() {
    const tag = tagInput.value.trim();
    try {
        const response = await fetch('/api/pomodoro/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: 25, tag: tag || null })
        });
        if (response.ok) {
            if (tag) {
                saveTagToStorage(tag);
                loadRecentTags();
            }
            await fetchState();
            await loadTagStats();
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
    const tag = tagInput.value.trim();
    try {
        const response = await fetch('/api/pomodoro/break', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: 5, tag: tag || null })
        });
        if (response.ok) {
            if (tag) {
                saveTagToStorage(tag);
                loadRecentTags();
            }
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
            await loadTagStats();
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
        tagInput.disabled = false;
    } else {
        startBtn.disabled = true;
        breakBtn.disabled = true;
        stopBtn.disabled = false;
        tagInput.disabled = true;
    }
    
    // 統計
    completedCount.textContent = state.completed_focus_count;
    const hours = Math.floor(state.total_focus_seconds / 3600);
    const minutes = Math.floor((state.total_focus_seconds % 3600) / 60);
    totalTime.textContent = hours > 0 ? `${hours}時間${minutes}分` : `${minutes}分`;
    
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
            loadTagStats(); // タグ統計も更新
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
