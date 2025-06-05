// Các biến và hàm tiện ích
const chartsApiUrl = "";  // Sử dụng đường dẫn tương đối
let currentTab = "frequency"; // frequency, sentiment, search, stress, insights

// Khởi tạo các biểu đồ
Chart.defaults.color = '#2f5d32';
Chart.defaults.font.family = 'Poppins';

function getAuthHeaders() {
    const user = JSON.parse(localStorage.getItem("user"));
    return user && user.token 
        ? { "Authorization": "Bearer " + user.token, "Content-Type": "application/json" }
        : { "Content-Type": "application/json" };
}

// A. Tần suất cảm xúc theo thời gian
async function renderEmotionFrequencyChart(period = 'week') {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const chartWrapper = document.querySelector('.chart-wrapper');
    try {
        loadingIndicator.style.display = 'block';
        chartWrapper.style.opacity = '0.5';
        console.log('Fetching data for period:', period);

        const url = `http://localhost:5000/emotions/stats?period=${period}`;
        const response = await fetch(url, {
            headers: getAuthHeaders(),
            cache: 'no-store'
        });

        if (!response.ok) {
            const text = await response.text();
            console.error('Fetch error:', response.status, text);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const chartData = await response.json();
        console.log('Received data:', chartData);

        const ctx = document.getElementById('frequencyChart');
        if (window.currentChart instanceof Chart) {
            window.currentChart.destroy();
        }

        // Tìm giá trị lớn nhất để scale trục y đúng số lần xuất hiện
        const allData = chartData.datasets[0].data;
        const maxY = Math.max(1, ...allData);

        window.currentChart = new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: `Emotion Frequency - ${period === 'week' ? 'Last Week' : period === 'month' ? 'Last Month' : 'Last Year'}`,
                        font: { size: 16, weight: 600 }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        suggestedMax: maxY < 5 ? 5 : Math.ceil(maxY * 1.15),
                        title: {
                            display: true,
                            text: 'Số lần xuất hiện'
                        },
                        grid: { color: '#f0f0f0' }
                    }
                }
            }
        });

        // Update summary cards
        document.getElementById('positiveCount').textContent = chartData.datasets[0].data[0];
        document.getElementById('neutralCount').textContent = chartData.datasets[0].data[1];
        document.getElementById('negativeCount').textContent = chartData.datasets[0].data[2];

    } catch (err) {
        console.error('Error rendering frequency chart:', err);
        chartWrapper.innerHTML = `<p style="color: red;">Error loading chart: ${err.message}</p>`;
    } finally {
        loadingIndicator.style.display = 'none';
        chartWrapper.style.opacity = '1';
    }
}

// B. Nhóm cảm xúc tích cực/tiêu cực
async function renderSentimentOverview() {
  try {
    const response = await fetch(
      `${chartsApiUrl}/sentiment-overview`,
      { headers: getAuthHeaders() }
    );
    const data = await response.json();
    
    const ctx = document.getElementById('sentimentPie').getContext('2d');
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
          data: [data.positive, data.neutral, data.negative],
          backgroundColor: ['#81c784', '#fff176', '#e57373']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  } catch (err) {
    console.error('Error rendering sentiment overview:', err);
  }
}

// C. Tìm kiếm theo keyword
async function searchEntries(query) {
  try {
    const response = await fetch(
      `${chartsApiUrl}/search?q=${encodeURIComponent(query)}`,
      { headers: getAuthHeaders() }
    );
    const results = await response.json();
    renderSearchResults(results);
    renderWordCloud(results.wordFrequencies);
  } catch (err) {
    console.error('Error searching entries:', err);
  }
}

// D. Phân tích stress
async function analyzeStressLevels() {
  try {
    const response = await fetch(
      `${chartsApiUrl}/stress-analysis`,
      { headers: getAuthHeaders() }
    );
    const data = await response.json();
    renderStressChart(data);
  } catch (err) {
    console.error('Error analyzing stress:', err);
  }
}

// E. Insights và Tips
async function loadEntryInsights(entryId) {
  try {
    const response = await fetch(
      `${chartsApiUrl}/insights/${entryId}`,
      { headers: getAuthHeaders() }
    );
    const data = await response.json();
    showInsightsPopup(data);
  } catch (err) {
    console.error('Error loading insights:', err);
  }
}

// Thêm helper function để format dates
function formatChartDate(date, period) {
  const d = new Date(date);
  if (period === 'week') {
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  } else if (period === 'month') {
    return d.toLocaleDateString('en-US', { day: '2-digit', month: 'short' });
  }
  return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

// Tab chuyển đổi
function switchTab(tab) {
    document.querySelectorAll('.chart-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(tab + 'Section').classList.add('active');
    currentTab = tab;
    if (tab === 'search') {
        // Kiểm tra phần tử tồn tại trước khi gọi
        if (document.getElementById('searchResults') && document.getElementById('wordcloud')) {
            loadNegativeInsights();
        }
    }
}

// Tìm kiếm entry và render kết quả + wordcloud
async function searchEntries(keyword) {
    const resultDiv = document.getElementById('searchResults');
    const wordcloudDiv = document.getElementById('wordcloud');
    resultDiv.innerHTML = 'Đang tìm kiếm...';
    wordcloudDiv.innerHTML = '';
    try {
        const url = `http://localhost:5000/entries/search?q=${encodeURIComponent(keyword)}`;
        const response = await fetch(url, { headers: getAuthHeaders() });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text);
        }
        const data = await response.json();
        // Render entries
        if (data.entries.length === 0) {
            resultDiv.innerHTML = '<p>Không tìm thấy entry phù hợp.</p>';
        } else {
            resultDiv.innerHTML = data.entries.map(e =>
                `<div class="entry-result">
                    <div><b>${e.date}</b></div>
                    <div>${e.content}</div>
                </div>`
            ).join('');
        }
        // Render wordcloud
        if (data.wordcloud.length > 0) {
            wordcloudDiv.innerHTML = data.wordcloud.map(w =>
                `<span style="font-size:${12 + w.value * 2}px;margin:4px;display:inline-block;color:#2f5d32;">${w.text}</span>`
            ).join('');
        }
    } catch (err) {
        resultDiv.innerHTML = `<span style="color:red;">Lỗi: ${err.message}</span>`;
    }
}

// Tự động lấy entries tiêu cực/lặp lại nhiều và render pie chart + wordcloud + thống kê
async function loadNegativeInsights() {
    const resultDiv = document.getElementById('searchResults');
    const wordcloudDiv = document.getElementById('wordcloud');
    let pieDiv = document.getElementById('negativePieChartDiv');
    if (!pieDiv) {
        pieDiv = document.createElement('div');
        pieDiv.id = 'negativePieChartDiv';
        pieDiv.style = 'margin-bottom:32px;display:flex;justify-content:center;';
        resultDiv.parentNode.insertBefore(pieDiv, resultDiv);
    }
    // Tăng kích thước canvas
    pieDiv.innerHTML = `<canvas id="negativePieChart" width="600" height="600" style="max-width:600px;max-height:600px;margin:auto;"></canvas>`;

    resultDiv.innerHTML = 'Đang phân tích...';
    wordcloudDiv.innerHTML = '';
    try {
        const url = `http://localhost:5000/entries/negative-insights`;
        const response = await fetch(url, { headers: getAuthHeaders() });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text);
        }
        const data = await response.json();

        let statsHtml = `
            <div style="margin-bottom:16px;">
                <b>Number of days with negative words:</b> ${data.negative_count} / ${data.total_entries}
                (${data.negative_ratio}%)
            </div>
        `;

        if (data.top_negative_words && data.top_negative_words.length > 0) {
            const labels = data.top_negative_words.map(w => w.keyword);
            const values = data.top_negative_words.map(w => w.count);
            const colors = [
                "#e57373", "#ffd54f", "#81c784", "#4fc3f7", "#ba68c8",
                "#ffb74d", "#7986cb", "#a1887f", "#90a4ae", "#f06292"
            ];
            const ctx = document.getElementById('negativePieChart').getContext('2d');
            if (window.negativePieChart && typeof window.negativePieChart.destroy === 'function') {
                window.negativePieChart.destroy();
            }
            window.negativePieChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors.slice(0, labels.length)
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: 'bottom' },
                        title: {
                            display: true,
                            text: 'The highest frequency of occurrence of negative words',
                            font: { size: 18, weight: 700 }
                        }
                    }
                }
            });
        } else {
            pieDiv.innerHTML = '<div style="color:#888;text-align:center;">Không có từ tiêu cực nào đủ thống kê.</div>';
        }

        resultDiv.innerHTML = statsHtml;

        // Render wordcloud, loại bỏ các từ không có nghĩa hoặc lỗi hiển thị
        const bannedWords = [
            "today", "didn", "lost", "gentle", "felt", "soft", "lonely", "surviving", "vulnerable", "tired", "compassionate", "anxious", "coping", "hurt", "just", "numb", "acceptance", "even", "still", "pain", "taught", "patience", "than", "less", "chose", "like", "grief", "visited", "hide", "one", "brave", "okay", "judge", "sadness", "warm", "again", "got", "rejected", "expected", "myself", "run", "here", "bit", "alone", "small", "noticed", "quiet", "day", "healing", "hope"
        ];
        if (data.wordcloud.length > 0) {
            wordcloudDiv.innerHTML = data.wordcloud
                .filter(w => !bannedWords.includes(w.text))
                .map(w =>
                    `<span style="font-size:${12 + w.value * 2}px;margin:4px;display:inline-block;color:#2f5d32;">${w.text}</span>`
                ).join('');
        }
    } catch (err) {
        resultDiv.innerHTML = `<span style="color:red;">Lỗi: ${err.message}</span>`;
        if (pieDiv) pieDiv.innerHTML = '';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  console.log('Page loaded, initializing chart...');
  renderEmotionFrequencyChart('week');

  // Đặt event listener ở đây để chắc chắn phần tử đã tồn tại
  document.getElementById('periodSelect').addEventListener('change', function(e) {
      const period = e.target.value;
      console.log('Period changed to:', period);
      renderEmotionFrequencyChart(period);
  });

  // Tab event
  document.getElementById('tabChart').onclick = () => switchTab('emotionFrequency');
  document.getElementById('tabSearch').onclick = () => switchTab('search');
  // XÓA các event liên quan đến searchBtn và searchInput vì không còn input/button tìm kiếm
});
