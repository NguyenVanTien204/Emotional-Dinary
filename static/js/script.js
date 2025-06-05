const apiBaseURL = "/entries";  // Sử dụng đường dẫn tương đối

const entriesContainer = document.getElementById("entries");
const entryForm = document.getElementById("entryForm");
const formTitle = document.getElementById("formTitle");
const dateInput = document.getElementById("dateInput");
const contentInput = document.getElementById("contentInput");
const emotionsInput = document.getElementById("emotionsInput");
const formMessage = document.getElementById("formMessage");
const cancelEditBtn = document.getElementById("cancelEditBtn");

const calendarMonthYear = document.getElementById("calendarMonthYear");
const prevMonthBtn = document.getElementById("prevMonthBtn");
const nextMonthBtn = document.getElementById("nextMonthBtn");
const calendarBody = document.getElementById("calendarBody");
const filterResetBtn = document.getElementById("filterResetBtn");

let editMode = false;
let editEntryId = null;

let allEntries = [];
let filteredEntries = null; // null means no filter, else array of filtered
let currentCalendarDate = new Date(); // controls current month/year for calendar
let selectedDateFilter = null;
let calendarRenderToken = 0; // Token để kiểm soát render lịch

// Emotion scoring for color gradient (higher is better)
const emotionScores = {
  happy: 2,
  relaxed: 1.5,
  excited: 1,
  neutral: 0,
  anxious: -1,
  sad: -1.5,
  angry: -2
};
// Color gradient from green (good) to red (bad)
function getEmotionColor(score) {
  // score: -2 (red) ... 0 (yellow) ... 2 (green)
  // Clamp score
  score = Math.max(-2, Math.min(2, score));
  // Interpolate color
  // -2: #e57373 (red), 0: #fff176 (yellow), 2: #81c784 (green)
  if (score <= 0) {
    // Red to yellow
    // -2 -> 0: #e57373 to #fff176
    const t = (score + 2) / 2;
    return interpolateColor("#e57373", "#fff176", t);
  } else {
    // Yellow to green
    // 0 -> 2: #fff176 to #81c784
    const t = score / 2;
    return interpolateColor("#fff176", "#81c784", t);
  }
}
function interpolateColor(a, b, t) {
  // a, b: hex color strings, t: 0-1
  const ah = a.replace("#", "");
  const bh = b.replace("#", "");
  const ar = parseInt(ah.substring(0,2),16), ag = parseInt(ah.substring(2,4),16), ab = parseInt(ah.substring(4,6),16);
  const br = parseInt(bh.substring(0,2),16), bg = parseInt(bh.substring(2,4),16), bb = parseInt(bh.substring(4,6),16);
  const rr = Math.round(ar + (br-ar)*t);
  const rg = Math.round(ag + (bg-ag)*t);
  const rb = Math.round(ab + (bb-ab)*t);
  return `rgb(${rr},${rg},${rb})`;
}

function showMessage(msg, isError = false) {
  formMessage.textContent = msg;
  formMessage.style.color = isError ? "#d33" : "#2f5d32";
  setTimeout(() => {
    formMessage.textContent = "";
  }, 3500);
}

// *** Calendar rendering and logic ***

let emotionsCache = {}; // { "YYYY-MM": { map, timestamp } }
let lastCalendarYearMonth = ""; // Để xác định khi nào cần refetch

// Sửa lại hàm fetchEmotionsMap để lấy cả icon
async function fetchEmotionsMap(year, month) {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user || !user.user_id) return {};
  const ymKey = `${year}-${month+1}`;
  
  if (emotionsCache[ymKey] && Date.now() - emotionsCache[ymKey].timestamp < 60 * 1000) {
    return emotionsCache[ymKey].map;
  }    try {
    const res = await fetch(`/emotions?user_id=${encodeURIComponent(user.user_id)}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return {};
    const emotions = await res.json();
    const map = {};
    emotions.forEach(e => {
      if (e.date) {
        map[e.date] = {
          sentiment: e.sentiment,
          icon: e.icon
        };
      }
    });
    emotionsCache[ymKey] = { map, timestamp: Date.now() };
    return map;
  } catch {
    return {};
  }
}

// Giữ lại màu cho sentiment vì chỉ dùng cho hiển thị ở frontend
const sentimentColors = {
  positive: "#b7e7e1", // xanh mint dịu
  neutral: "#ffe9b0",  // vàng nhạt
  negative: "#f7b7b7"  // đỏ nhạt
};

async function renderCalendar(year, month) {
  const thisRenderToken = ++calendarRenderToken;
  calendarMonthYear.textContent = new Date(year, month).toLocaleDateString(undefined, {year: 'numeric', month: 'long'});
  calendarBody.style.opacity = 0.3;
  const emotionsMap = await fetchEmotionsMap(year, month);
  if (thisRenderToken !== calendarRenderToken) return;
  calendarBody.innerHTML = "";

  const firstDay = new Date(year, month, 1);
  const startWeekDay = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Lấy ngày hôm nay
  const today = new Date();
  const todayKey = formatDateKey(today.getFullYear(), today.getMonth() + 1, today.getDate());

  let dayNum = 1;
  for (let row = 0; row < 6; row++) {
    const tr = document.createElement("tr");
    for (let col = 0; col < 7; col++) {
      const td = document.createElement("td");
      if (row === 0 && col < startWeekDay) {
        td.classList.add("empty");
        tr.appendChild(td);
        continue;
      }
      if(dayNum > daysInMonth) {
        td.classList.add("empty");
        tr.appendChild(td);
        continue;
      }

      // Create day number container
      const dayDiv = document.createElement("div");
      dayDiv.textContent = dayNum;
      dayDiv.className = "calendar-day-number";
      td.appendChild(dayDiv);

      let dateKey = formatDateKey(year, month + 1, dayNum);

      // Đánh dấu ngày hôm nay
      if (dateKey === todayKey) {
        td.classList.add("today");
      }

      // Lấy entries cho ngày này một lần duy nhất
      const dayEntries = allEntries.filter(e => e.date === dateKey);
      
      // Xử lý hiển thị icon và sentiment
      if (dayEntries.length > 0) {
        td.classList.add("has-entry");
        
        if (emotionsMap[dateKey]) {
          td.style.background = sentimentColors[emotionsMap[dateKey].sentiment] || "#ffe9b0";
          // Lấy icon trực tiếp từ emotionsMap
          if (emotionsMap[dateKey].icon) {
            const iconSpan = document.createElement("span");
            iconSpan.textContent = emotionsMap[dateKey].icon;
            iconSpan.className = "calendar-icon-overlay";
            td.appendChild(iconSpan);
          }
        }

        // Click handler cho ngày có entries
        td.addEventListener("click", () => {
          if(selectedDateFilter === dateKey) {
            selectedDateFilter = null;
            filteredEntries = null;
            filterResetBtn.style.display = "none";
            entryForm.style.display = "none";
            entriesContainer.style.display = "none";
          } else {
            selectedDateFilter = dateKey;
            filteredEntries = dayEntries;
            filterResetBtn.style.display = "inline-block";
            entryForm.style.display = "block";
            entriesContainer.style.display = "grid";
            renderEntries(dayEntries);
          }
          updateCalendarSelection();
        });
      } else {
        // Click handler cho ngày không có entries
        td.addEventListener("click", () => {
          selectedDateFilter = dateKey;
          filteredEntries = [];
          filterResetBtn.style.display = "inline-block";
          entriesContainer.innerHTML = "<p style='color:#2f5d32; font-weight:600;'>No entries found for this date.</p>";
          entriesContainer.style.display = "grid";
          entryForm.style.display = "block";
          dateInput.value = dateKey;
          updateCalendarSelection();
        });
      }

      tr.appendChild(td);
      dayNum++;
    }
    calendarBody.appendChild(tr);
  }
  updateCalendarSelection();
  setTimeout(() => {
    calendarBody.style.transition = "opacity 0.35s";
    calendarBody.style.opacity = 1;
  }, 30);
}

// Lấy icon cho ngày (ưu tiên entry đầu tiên có icon)
function getCalendarIconForDate(dateKey) {
  const dayEntries = allEntries.filter(e => e.date === dateKey && e.icon && e.icon.length > 0);
  if (dayEntries.length > 0) return dayEntries[0].icon;
  return null;
}

function updateCalendarSelection() {
  // highlight selected date in calendar
  const tds = calendarBody.querySelectorAll("td:not(.empty)");
  tds.forEach(td => {
    const day = parseInt(td.textContent, 10);
    if (isNaN(day)) return;
    const dateKey = formatDateKey(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth()+1, day);
    if(selectedDateFilter === dateKey) {
      td.classList.add("selected");
    } else {
      td.classList.remove("selected");
    }
    // Đánh dấu lại today nếu chuyển tháng
    const today = new Date();
    const todayKey = formatDateKey(today.getFullYear(), today.getMonth() + 1, today.getDate());
    if (dateKey === todayKey) {
      td.classList.add("today");
    } else {
      td.classList.remove("today");
    }
  });
}

function formatDateKey(year, month, day) {
  // Format numbers with leading zeros
  const mm = month < 10 ? "0"+month : month;
  const dd = day < 10 ? "0"+day : day;
  return `${year}-${mm}-${dd}`;
}

prevMonthBtn.addEventListener("click", () => {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() -1 );
  renderCalendar(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth());
});
nextMonthBtn.addEventListener("click", () => {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() +1 );
  renderCalendar(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth());
});

filterResetBtn.addEventListener("click", () => {
  selectedDateFilter = null;
  filteredEntries = null;
  filterResetBtn.style.display = "none";
  entryForm.style.display = "none";
  entriesContainer.style.display = "none";
  renderEntries([]); // Clear entries
  updateCalendarSelection();
});

// *** Entries rendering and logic ***

function renderEntries(entries) {
  entriesContainer.innerHTML = "";
  if (!entries || entries.length === 0) {
    entriesContainer.innerHTML = "<p style='color:#2f5d32; font-weight:600;'>No entries found for this date.</p>";
    entryForm.style.display = "block"; // Cho phép thêm mới
    return;
  }
  entries.forEach(entry => {
    const card = document.createElement("div");
    card.className = "entry-card";

    const title = document.createElement("h3");
    title.textContent = new Date(entry.date).toLocaleDateString(undefined, {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'});
    card.appendChild(title);

    const contentP = document.createElement("p");
    contentP.className = "entry-content";
    contentP.textContent = entry.content;
    card.appendChild(contentP);

    if (entry.emotions.length > 0) {
      const emotionsDiv = document.createElement("div");
      emotionsDiv.className = "entry-emotions";
      entry.emotions.forEach(em => {
        const emTag = document.createElement("span");
        emTag.className = "emotion-tag";
        emTag.textContent = em;
        emotionsDiv.appendChild(emTag);
      });
      card.appendChild(emotionsDiv);
    }

    const actionsDiv = document.createElement("div");
    actionsDiv.className = "entry-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn-edit";
    editBtn.textContent = "Edit";
    editBtn.onclick = function(e) {
      e.stopPropagation();
      enterEditMode(entry);
    };
    actionsDiv.appendChild(editBtn);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn btn-delete";
    deleteBtn.textContent = "Delete";
    deleteBtn.onclick = function(e) {
      e.stopPropagation();
      // Only show the confirmation dialog, no debug alerts/logs
      if (!entry._id) {
        alert("No entry ID found for deletion.");
        return;
      }
      deleteEntry(entry._id);
    };
    actionsDiv.appendChild(deleteBtn);

    card.appendChild(actionsDiv);

    const dateDiv = document.createElement("div");
    dateDiv.className = "entry-date";
    dateDiv.textContent = entry.date;
    card.appendChild(dateDiv);

    entriesContainer.appendChild(card);
  });
}

// *** Entry CRUD logic ***

function getAuthHeaders() {
  const user = JSON.parse(localStorage.getItem("user"));
  return user && user.token ? { "Authorization": "Bearer " + user.token, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

async function fetchEntries() {
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.user_id) return;
    const res = await fetch(apiBaseURL + "?user_id=" + encodeURIComponent(user.user_id), {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch entries");
    allEntries = await res.json();
    // Xóa cache cảm xúc khi CRUD
    emotionsCache = {};
    renderCalendar(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth());
    if (selectedDateFilter) {
      const dayEntries = allEntries.filter(e => e.date === selectedDateFilter);
      renderEntries(dayEntries);
      entriesContainer.style.display = "grid";
    } else {
      entriesContainer.style.display = "none";
    }
  } catch (err) {
    showMessage("Error loading entries.", true);
  }
}

async function addEntry(entry) {
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.user_id) return;
    entry.user_id = user.user_id;
    // Không gửi icon vì sẽ được tạo ở backend
    delete entry.icon;
    const res = await fetch(apiBaseURL, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(entry)
    });
    if (!res.ok) throw new Error("Failed to add entry");
    showMessage("Entry added!");
    entryForm.reset();
    entryForm.style.display = "none";
    emotionsCache = {}; // Clear cache để refetch cảm xúc
    fetchEntries();
  } catch (err) {
    showMessage("Error adding entry.", true);
  }
}

async function updateEntry(id, entry) {
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.user_id) return;
    
    // Log để debug
    console.log("Updating entry:", id, entry);
    
    entry.user_id = user.user_id;
    // Đảm bảo không gửi icon
    delete entry.icon;

    const res = await fetch(`${apiBaseURL}/${id}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(entry)
    });

    if (!res.ok) {
      throw new Error(`Failed to update entry: ${res.status} ${res.statusText}`);
    }

    // Lấy dữ liệu entry đã cập nhật từ response
    const updatedEntry = await res.json();
    
    // Cập nhật lại trong allEntries
    const index = allEntries.findIndex(e => e._id === id);
    if (index !== -1) {
      allEntries[index] = updatedEntry;
    }

    showMessage("Entry updated!");
    
    // Reset form và UI state
    entryForm.reset();
    entryForm.style.display = "none";
    editMode = false;
    editEntryId = null;
    cancelEditBtn.style.display = "none";
    emotionsCache = {};

    // Render lại calendar và entries
    await fetchEntries(); // Fetch lại toàn bộ để đảm bảo dữ liệu đồng bộ
    
  } catch (err) {
    console.error("Update error:", err);
    showMessage("Error updating entry: " + err.message, true);
  }
}

async function deleteEntry(id) {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!id || !user || !user.user_id) {
    showMessage("No entry ID provided for deletion.", true);
    return;
  }
  if (!confirm("Delete this entry?")) return;
  try {
    const res = await fetch(`${apiBaseURL}/${id}?user_id=${encodeURIComponent(user.user_id)}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Failed to delete entry");

    // Xóa entry khỏi allEntries array
    allEntries = allEntries.filter(e => e._id !== id);
    
    showMessage("Entry deleted!");
    emotionsCache = {};
    
    // Reset form và clear selection
    entryForm.reset();
    entryForm.style.display = "none";
    editMode = false;
    editEntryId = null;
    
    // Render lại calendar và entries
    await renderCalendar(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth());
    if (selectedDateFilter) {
      const dayEntries = allEntries.filter(e => e.date === selectedDateFilter);
      if (dayEntries.length === 0) {
        // Nếu không còn entries nào cho ngày đã chọn
        entriesContainer.innerHTML = "<p style='color:#2f5d32; font-weight:600;'>No entries found for this date.</p>";
        selectedDateFilter = null;
        filteredEntries = null;
        filterResetBtn.style.display = "none";
      } else {
        renderEntries(dayEntries);
      }
    }
  } catch (err) {
    showMessage("Error deleting entry.", true);
  }
}

function enterEditMode(entry) {
  editMode = true;
  editEntryId = entry._id;
  formTitle.textContent = "Edit Entry";
  dateInput.value = entry.date;
  contentInput.value = entry.content;
  emotionsInput.value = entry.emotions.join(", ");
  entryForm.style.display = "block";
  cancelEditBtn.style.display = "inline-block";
  formMessage.textContent = "";
}

function exitEditMode() {
  editMode = false;
  editEntryId = null;
  formTitle.textContent = "Add New Entry";
  entryForm.reset();
  entryForm.style.display = "none";
  cancelEditBtn.style.display = "none";
  formMessage.textContent = "";
  document.getElementById("iconInput").value = getRandomIcon("neutral");
}

// *** Form logic ***

document.addEventListener("DOMContentLoaded", () => {
  fetchEntries();
  entryForm.style.display = "none";
  entriesContainer.style.display = "none";
});

// Khi click vào ngày trên lịch để tạo mới entry
calendarBody.addEventListener("click", (e) => {
  if (e.target.tagName === "TD" && !e.target.classList.contains("empty")) {
    const day = parseInt(e.target.textContent, 10);
    if (!isNaN(day)) {
      const dateKey = formatDateKey(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth() + 1, day);
      dateInput.value = dateKey; // Luôn set ngày vào ô Date
      // Reset form và icon picker nếu không ở edit mode
      if (!editMode) {
        entryForm.reset();
        dateInput.value = dateKey;
        document.getElementById("iconInput").value = ICON_SETS["neutral"][0];
        renderIconPicker("neutral", ICON_SETS["neutral"][0]);
      }
    }
  }
});

entryForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  const entry = {
    date: dateInput.value,
    content: contentInput.value.trim(),
    emotions: emotionsInput.value.split(",").map(s => s.trim().toLowerCase()).filter(Boolean)
  };

  if (!entry.date || !entry.content) {
    showMessage("Date and content are required.", true);
    return;
  }

  if (editMode && editEntryId) {
    console.log("Submitting edit for entry:", editEntryId);
    await updateEntry(editEntryId, entry);
  } else {
    await addEntry(entry);
  }
});

cancelEditBtn.addEventListener("click", () => {
  exitEditMode();
});
