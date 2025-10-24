// Statistics Chart Management
let currentPeriod = 'weekly';

// Initialize statistics on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStats(currentPeriod);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const period = btn.dataset.period;
            switchPeriod(period);
        });
    });
});

async function loadStats(period) {
    try {
        const endpoint = period === 'weekly' 
            ? '/api/pomodoro/stats/weekly' 
            : '/api/pomodoro/stats/monthly';
        
        const response = await fetch(endpoint);
        const data = await response.json();
        
        updateChart(data, period);
        updateSummary(data, period);
    } catch (error) {
        console.error('統計の読み込みエラー:', error);
    }
}

function updateChart(data, period) {
    const container = document.getElementById('chartContainer');
    
    // Find max value for scaling
    const maxMinutes = Math.max(...data.map(d => d.total_seconds / 60), 1);
    
    // Build chart HTML
    const barsHTML = data.map(d => {
        const date = new Date(d.date);
        const label = `${date.getMonth() + 1}/${date.getDate()}`;
        const minutes = Math.round(d.total_seconds / 60);
        const height = (minutes / maxMinutes) * 100;
        
        return `
            <div class="chart-bar">
                <div class="bar-column" style="height: ${height}%">
                    ${minutes > 0 ? `<span class="bar-value">${minutes}分</span>` : ''}
                </div>
                <span class="bar-label">${label}</span>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `<div class="chart-bars">${barsHTML}</div>`;
}

function updateSummary(data, period) {
    // Calculate average focus time per day
    const totalMinutes = data.reduce((sum, d) => sum + d.total_seconds / 60, 0);
    const avgMinutes = Math.round(totalMinutes / data.length);
    const avgHours = Math.floor(avgMinutes / 60);
    const avgMins = avgMinutes % 60;
    
    document.getElementById('avgFocusTime').textContent = 
        avgHours > 0 ? `${avgHours}時間${avgMins}分` : `${avgMins}分`;
    
    // Calculate total sessions
    const totalSessions = data.reduce((sum, d) => sum + d.focus_count, 0);
    document.getElementById('totalSessions').textContent = totalSessions;
    
    // Calculate comparison with previous period
    const currentPeriodDays = period === 'weekly' ? 7 : 30;
    const halfPoint = Math.floor(currentPeriodDays / 2);
    
    const firstHalf = data.slice(0, halfPoint);
    const secondHalf = data.slice(halfPoint);
    
    const firstHalfTotal = firstHalf.reduce((sum, d) => sum + d.total_seconds, 0);
    const secondHalfTotal = secondHalf.reduce((sum, d) => sum + d.total_seconds, 0);
    
    let comparisonText = '-';
    const comparisonEl = document.getElementById('comparison');
    
    if (firstHalfTotal > 0) {
        const change = ((secondHalfTotal - firstHalfTotal) / firstHalfTotal) * 100;
        const changeRounded = Math.round(change);
        
        if (changeRounded > 0) {
            comparisonText = `+${changeRounded}% ↑`;
            comparisonEl.style.color = '#48bb78';
        } else if (changeRounded < 0) {
            comparisonText = `${changeRounded}% ↓`;
            comparisonEl.style.color = '#f56565';
        } else {
            comparisonText = '変化なし';
            comparisonEl.style.color = '#718096';
        }
    } else if (secondHalfTotal > 0) {
        comparisonText = '新規データ';
        comparisonEl.style.color = '#48bb78';
    } else {
        comparisonEl.style.color = '#718096';
    }
    
    comparisonEl.textContent = comparisonText;
}

function switchPeriod(period) {
    if (period === currentPeriod) return;
    
    currentPeriod = period;
    
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.period === period) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Load new data
    loadStats(period);
}
