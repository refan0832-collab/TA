// ===============================
// ESP32 POWER MONITOR FINAL
// SESSION LOGIN VERSION
// ===============================

class PowerMonitor {

  constructor() {

    this.API_URL =
      "http://localhost:5000/api/current";

    this.currentThreshold = 4.0;

    this.isConnected = false;

    this.initChart();

    this.emptyState();

    this.start();
  }

  // ===============================
  // EMPTY STATE
  // ===============================
  emptyState() {

    document.getElementById(
      "tegangan"
    ).textContent = "-";

    document.getElementById(
      "arus"
    ).textContent = "-";

    document.getElementById(
      "daya"
    ).textContent = "-";

    document.getElementById(
      "frekuensi"
    ).textContent = "-";
  }

  // ===============================
  // CHART
  // ===============================
  initChart() {

    const ctx =
      document.getElementById("chart");

    this.data = {

      labels: [],

      datasets: [

        {
          label: "Tegangan (V)",

          data: [],

          borderColor: "#3b82f6",

          backgroundColor:
            "rgba(59,130,246,0.2)",

          tension: 0.3,

          fill: true
        },

        {
          label: "Arus (A)",

          data: [],

          borderColor: "#22c55e",

          backgroundColor:
            "rgba(34,197,94,0.2)",

          tension: 0.3,

          fill: false
        },

        {
          label: "Daya (W)",

          data: [],

          borderColor: "#f97316",

          backgroundColor:
            "rgba(249,115,22,0.2)",

          tension: 0.3,

          fill: true
        }
      ]
    };

    this.chart = new Chart(ctx, {

      type: "line",

      data: this.data,

      options: {

        responsive: true,

        maintainAspectRatio: false,

        animation: false,

        plugins: {

          legend: {

            labels: {
              color: "white"
            }
          }
        },

        scales: {

          x: {

            ticks: {
              color: "white"
            }
          },

          y: {

            ticks: {
              color: "white"
            }
          }
        }
      }
    });
  }

  // ===============================
  // FETCH DATA
  // ===============================
  async fetchData() {

    try {

      const token =
        sessionStorage.getItem(
          "pm_token"
        );

      const res =
        await fetch(this.API_URL, {

          headers: token
            ? {
                Authorization:
                  "Bearer " + token
              }
            : {}
        });

      if (!res.ok) {
        throw new Error(
          "Server Error"
        );
      }

      const data =
        await res.json();

      this.isConnected = true;

      return {

        voltage:
          Number(
            data.tegangan ??
            data.voltage ??
            0
          ),

        current:
          Number(
            data.arus ??
            data.current ??
            0
          ),

        power:
          Number(
            data.daya ??
            data.power ??
            0
          ),

        frequency:
          Number(
            data.frekuensi ??
            data.frequency ??
            0
          )
      };

    } catch (err) {

      console.warn(
        "Backend Offline:",
        err
      );

      this.isConnected = false;

      return null;
    }
  }

  // ===============================
  // UPDATE UI
  // ===============================
  updateUI(d) {

    // OFFLINE
    if (!this.isConnected || !d) {

      this.emptyState();

      // RESET CHART
      this.data.labels = [];

      this.data.datasets.forEach(ds => {
        ds.data = [];
      });

      this.chart.update();

    }

    // ONLINE
    else {

      document.getElementById(
        "tegangan"
      ).textContent =
        d.voltage;

      document.getElementById(
        "arus"
      ).textContent =
        d.current;

      document.getElementById(
        "daya"
      ).textContent =
        d.power;

      document.getElementById(
        "frekuensi"
      ).textContent =
        d.frequency;
    }

    // WARNING AMPERE
    const arusEl =
      document.getElementById("arus");

    const arusCard =
      arusEl.closest(".kpi-card");

    if (
      this.isConnected &&
      d &&
      d.current >
        this.currentThreshold
    ) {

      arusEl.classList.add(
        "blink-red"
      );

      arusCard.classList.add(
        "warning-card"
      );

    } else {

      arusEl.classList.remove(
        "blink-red"
      );

      arusCard.classList.remove(
        "warning-card"
      );
    }

    // STATUS
    const status =
      document.getElementById(
        "connectionStatus"
      );

    if (status) {

      if (this.isConnected) {

        status.textContent =
          "● Online";

        status.style.color =
          "#22c55e";

      } else {

        status.textContent =
          "● Offline";

        status.style.color =
          "#ef4444";
      }
    }
  }

  // ===============================
  // UPDATE CHART
  // ===============================
  updateChart(d) {

    if (
      !this.isConnected ||
      !d
    ) return;

    const time =
      new Date()
      .toLocaleTimeString("id-ID");

    this.data.labels.push(time);

    this.data.datasets[0]
      .data.push(d.voltage);

    this.data.datasets[1]
      .data.push(d.current);

    this.data.datasets[2]
      .data.push(d.power);

    // LIMIT DATA
    if (
      this.data.labels.length > 20
    ) {

      this.data.labels.shift();

      this.data.datasets.forEach(ds => {
        ds.data.shift();
      });
    }

    this.chart.update();
  }

  // ===============================
  // LOOP
  // ===============================
  async loop() {

    const d =
      await this.fetchData();

    this.updateUI(d);

    this.updateChart(d);
  }

  // ===============================
  // START
  // ===============================
  start() {

    this.loop();

    setInterval(() => {

      this.loop();

    }, 1000);
  }
}


// ===============================
// LOGIN MANAGER
// ===============================

class LoginManager {

  constructor() {

    this.API_URL =
      "http://localhost:5000/api/auth/login";

    this.btnLogin =
      document.getElementById(
        "loginBtn"
      );

    this.inputUser =
      document.getElementById(
        "loginUsername"
      );

    this.inputPass =
      document.getElementById(
        "loginPassword"
      );

    this.alertEl =
      document.getElementById(
        "loginAlert"
      );

    this.togglePass =
      document.getElementById(
        "togglePass"
      );

    this.bindEvents();
  }

  // ===============================
  // EVENTS
  // ===============================
  bindEvents() {

    this.btnLogin.addEventListener(
      "click",
      () => this.doLogin()
    );

    [
      this.inputUser,
      this.inputPass
    ].forEach(el => {

      el.addEventListener(
        "keydown",
        e => {

          if (e.key === "Enter") {
            this.doLogin();
          }
        }
      );
    });

    // TOGGLE PASSWORD
    if (this.togglePass) {

      this.togglePass.addEventListener(
        "click",
        () => {

          const isPass =
            this.inputPass.type ===
            "password";

          this.inputPass.type =
            isPass
              ? "text"
              : "password";

          this.togglePass.textContent =
            isPass
              ? "🙈"
              : "👁";
        }
      );
    }
  }

  // ===============================
  // ALERT
  // ===============================
  showAlert(
    msg,
    type = "error"
  ) {

    this.alertEl.textContent =
      msg;

    this.alertEl.className =
      `login-alert ${type}`;

    this.alertEl.style.display =
      "block";
  }

  hideAlert() {

    this.alertEl.style.display =
      "none";
  }

  // ===============================
  // LOADING
  // ===============================
  setLoading(on) {

    const btnText =
      this.btnLogin.querySelector(
        ".btn-text"
      );

    const btnLoader =
      this.btnLogin.querySelector(
        ".btn-loader"
      );

    this.btnLogin.disabled =
      on;

    btnText.style.display =
      on ? "none" : "inline";

    btnLoader.style.display =
      on ? "inline" : "none";
  }

  // ===============================
  // LOGIN
  // ===============================
  async doLogin() {

    const username =
      this.inputUser.value.trim();

    const password =
      this.inputPass.value.trim();

    this.hideAlert();

    if (
      !username ||
      !password
    ) {

      this.showAlert(
        "⚠ Username dan password wajib diisi."
      );

      return;
    }

    this.setLoading(true);

    try {

      const res =
        await fetch(
          this.API_URL,
          {

            method: "POST",

            headers: {
              "Content-Type":
                "application/json"
            },

            body: JSON.stringify({
              username,
              password
            })
          }
        );

      const data =
        await res.json();

      if (
        res.ok &&
        data.token
      ) {

        // SESSION STORAGE
        sessionStorage.setItem(
          "pm_token",
          data.token
        );

        sessionStorage.setItem(
          "pm_user",
          JSON.stringify({

            username:
              data.username,

            role:
              data.role
          })
        );

        this.showAlert(
          "✅ Login berhasil!",
          "success"
        );

        setTimeout(() => {

          window.location.href =
            "index.html";

        }, 1000);

      } else {

        this.showAlert(
          data.error ||
          "❌ Login gagal."
        );
      }

    } catch (err) {

      console.error(err);

      this.showAlert(
        "❌ Backend tidak dapat dihubungi."
      );

    } finally {

      this.setLoading(false);
    }
  }
}


// ===============================
// AUTH GUARD
// ===============================
function authGuard() {

  const token =
    sessionStorage.getItem(
      "pm_token"
    );

  if (!token) {

    window.location.href =
      "login.html";

    return false;
  }

  return true;
}


// ===============================
// LOGOUT
// ===============================
function doLogout() {

  sessionStorage.removeItem(
    "pm_token"
  );

  sessionStorage.removeItem(
    "pm_user"
  );

  window.location.href =
    "login.html";
}


// ===============================
// HEADER
// ===============================
function injectLogoutButton() {

  const header =
    document.querySelector(
      ".header"
    );

  if (!header) return;

  const userRaw =
    sessionStorage.getItem(
      "pm_user"
    );

  const userInfo =
    userRaw
      ? JSON.parse(userRaw)
      : null;

  const right =
    document.createElement("div");

  right.style.display = "flex";

  right.style.alignItems =
    "center";

  right.style.gap = "1rem";

  // USER
  if (userInfo) {

    const userBadge =
      document.createElement(
        "span"
      );

    userBadge.textContent =
      `👤 ${userInfo.username} (${userInfo.role})`;

    userBadge.style.fontSize =
      "0.9rem";

    right.appendChild(
      userBadge
    );
  }

  // STATUS
  const status =
    document.getElementById(
      "connectionStatus"
    );

  if (status) {
    right.appendChild(status);
  }

  // LOGOUT BUTTON
  const btn =
    document.createElement(
      "button"
    );

  btn.textContent =
    "🚪 Logout";

  btn.className =
    "logout-btn";

  btn.addEventListener(
    "click",
    doLogout
  );

  right.appendChild(btn);

  header.appendChild(right);
}


// ===============================
// SIDEBAR TOGGLE
// ===============================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('menuToggle');
    
    if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        toggle.classList.remove('active');
    } else {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        toggle.classList.add('active');
    }
}

// Tutup sidebar saat klik overlay atau di luar
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('menuToggle');
    
    if (!sidebar || !toggle) return;
    
    if (e.target === overlay) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        toggle.classList.remove('active');
        return;
    }
    
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        if (sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            toggle.classList.remove('active');
        }
    }
});

// Handle resize window
window.addEventListener('resize', function() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('menuToggle');
    
    if (!sidebar || !toggle) return;
    
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    toggle.classList.remove('active');
});


// ===============================
// CLOCK / WAKTU REAL-TIME (tambahan baru)
// ===============================

function updateClock() {
    const now = new Date();
    
    // Format waktu: 14:30:45
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeString = `${hours}:${minutes}:${seconds}`;
    
    // Format tanggal: Senin, 9 Mei 2026
    const days = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    
    const dayName = days[now.getDay()];
    const date = now.getDate();
    const month = months[now.getMonth()];
    const year = now.getFullYear();
    const dateString = `${dayName}, ${date} ${month} ${year}`;
    
    // Update DOM
    const clockTime = document.getElementById('clockTime');
    const clockDate = document.getElementById('clockDate');
    
    if (clockTime) clockTime.textContent = timeString;
    if (clockDate) clockDate.textContent = dateString;
}

// Jalankan segera dan update setiap detik
updateClock();
setInterval(updateClock, 1000);


// ===============================
// INIT APP
// ===============================
document.addEventListener(
  "DOMContentLoaded",
  () => {

    const isLoginPage =
      !!document.getElementById(
        "loginBtn"
      );

    const isDashboard =
      !!document.getElementById(
        "chart"
      );

    // LOGIN PAGE
    if (isLoginPage) {

      if (
        sessionStorage.getItem(
          "pm_token"
        )
      ) {

        window.location.href =
          "index.html";

        return;
      }

      new LoginManager();
    }

    // DASHBOARD
    if (isDashboard) {

      if (!authGuard()) return;

      injectLogoutButton();

      new PowerMonitor();
    }
  }
);


// ===============================
// AUTO LOGOUT WHEN TAB CLOSED
// ===============================