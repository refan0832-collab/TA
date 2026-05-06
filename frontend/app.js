// ===============================
// ESP32 POWER MONITOR - FINAL
// ===============================

class PowerMonitor {
  constructor() {
    this.API_URL = "http://localhost:5000/api/current";
    this.currentThreshold = 4.0; // 🔥 batas ampere
    this.isConnected = false;

    this.initChart();
    this.start();
  }

  // ===============================
  // INIT CHART
  // ===============================
  initChart() {
    const ctx = document.getElementById("chart");

    this.data = {
      labels: [],
      datasets: [
        {
          label: "Tegangan (V)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.2)",
          tension: 0.3,
          fill: true
        },
        {
          label: "Arus (A)",
          data: [],
          borderColor: "#22c55e",
          backgroundColor: "rgba(34,197,94,0.2)",
          tension: 0.3,
          fill: false
        },
        {
          label: "Daya (W)",
          data: [],
          borderColor: "#f97316",
          backgroundColor: "rgba(249,115,22,0.2)",
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
        animation: false,
        plugins: {
          legend: {
            labels: { color: "white" }
          }
        },
        scales: {
          x: {
            ticks: { color: "white" }
          },
          y: {
            ticks: { color: "white" }
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
      const token = localStorage.getItem("pm_token");
      const res = await fetch(this.API_URL, {
        headers: token ? { "Authorization": "Bearer " + token } : {}
      });
      if (!res.ok) throw new Error("Server error");

      const data = await res.json();
      this.isConnected = true;

      return {
        voltage: Number(data.tegangan ?? data.voltage ?? 0),
        current: Number(data.arus ?? data.current ?? 0),
        power: Number(data.daya ?? data.power ?? 0),
        frequency: Number(data.frekuensi ?? data.frequency ?? 50)
      };

    } catch (err) {
      console.warn("⚠ Backend offline:", err);
      this.isConnected = false;
      return this.mockData();
    }
  }

  // ===============================
  // MOCK DATA (fallback)
  // ===============================
  mockData() {
    return {
      voltage: (220 + Math.random() * 5).toFixed(1),
      current: (2 + Math.random() * 3).toFixed(2),
      power: (500 + Math.random() * 200).toFixed(0),
      frequency: 50
    };
  }

  // ===============================
  // UPDATE UI + WARNING SYSTEM
  // ===============================
  updateUI(d) {
    document.getElementById("tegangan").textContent = d.voltage;
    document.getElementById("daya").textContent = d.power;
    document.getElementById("frekuensi").textContent = d.frequency;

    const arusEl = document.getElementById("arus");
    const arusCard = arusEl.closest(".kpi-card");

    arusEl.textContent = d.current;

    // 🔴 WARNING AMPERE
    if (d.current > this.currentThreshold) {
      arusEl.classList.add("blink-red");
      arusCard.classList.add("warning-card");
    } else {
      arusEl.classList.remove("blink-red");
      arusCard.classList.remove("warning-card");
    }

    // STATUS KONEKSI
    const status = document.getElementById("connectionStatus");

    if (this.isConnected) {
      status.textContent = "● Online";
      status.style.color = "#22c55e";
      status.classList.remove("offline");
    } else {
      status.textContent = "● Offline";
      status.style.color = "#ef4444";
      status.classList.add("offline");
    }
  }

  // ===============================
  // UPDATE CHART
  // ===============================
  updateChart(d) {
    const time = new Date().toLocaleTimeString("id-ID");

    this.data.labels.push(time);
    this.data.datasets[0].data.push(d.voltage);
    this.data.datasets[1].data.push(d.current);
    this.data.datasets[2].data.push(d.power);

    // batasi data (biar ringan)
    if (this.data.labels.length > 20) {
      this.data.labels.shift();
      this.data.datasets.forEach(ds => ds.data.shift());
    }

    this.chart.update();
  }

  // ===============================
  // MAIN LOOP
  // ===============================
  async loop() {
    const d = await this.fetchData();

    if (d) {
      this.updateUI(d);
      this.updateChart(d);
    }
  }

  // ===============================
  // START SYSTEM
  // ===============================
  start() {
    this.loop();
    setInterval(() => this.loop(), 1000); // 1 detik
  }
}


// ===============================
// LOGIN MANAGER
// ===============================

class LoginManager {
  constructor() {
    this.API_URL = "http://localhost:5000/api/auth/login";

    this.btnLogin   = document.getElementById("loginBtn");
    this.inputUser  = document.getElementById("loginUsername");
    this.inputPass  = document.getElementById("loginPassword");
    this.alertEl    = document.getElementById("loginAlert");
    this.togglePass = document.getElementById("togglePass");

    this.bindEvents();
  }

  // ===============================
  // BIND EVENTS
  // ===============================
  bindEvents() {
    this.btnLogin.addEventListener("click", () => this.doLogin());

    // Enter key support
    [this.inputUser, this.inputPass].forEach(el => {
      el.addEventListener("keydown", e => {
        if (e.key === "Enter") this.doLogin();
      });
    });

    // Toggle password visibility
    if (this.togglePass) {
      this.togglePass.addEventListener("click", () => {
        const isPass = this.inputPass.type === "password";
        this.inputPass.type = isPass ? "text" : "password";
        this.togglePass.textContent = isPass ? "🙈" : "👁";
      });
    }
  }

  // ===============================
  // SHOW ALERT
  // ===============================
  showAlert(msg, type = "error") {
    this.alertEl.textContent = msg;
    this.alertEl.className = `login-alert ${type}`;
    this.alertEl.style.display = "block";
  }

  hideAlert() {
    this.alertEl.style.display = "none";
  }

  // ===============================
  // SET LOADING STATE
  // ===============================
  setLoading(on) {
    const btnText   = this.btnLogin.querySelector(".btn-text");
    const btnLoader = this.btnLogin.querySelector(".btn-loader");

    this.btnLogin.disabled = on;
    btnText.style.display   = on ? "none" : "inline";
    btnLoader.style.display = on ? "inline" : "none";
  }

  // ===============================
  // DO LOGIN
  // ===============================
  async doLogin() {
    const username = this.inputUser.value.trim();
    const password = this.inputPass.value.trim();

    this.hideAlert();

    // Validasi kosong
    if (!username || !password) {
      this.showAlert("⚠ Username dan password wajib diisi.");
      return;
    }

    this.setLoading(true);

    try {
      const res = await fetch(this.API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (res.ok && data.token) {
        // Simpan token + user info
        localStorage.setItem("pm_token", data.token);
        localStorage.setItem("pm_user", JSON.stringify({
          username: data.username || username,
          role: data.role || "user"
        }));

        this.showAlert("✅ Login berhasil! Mengalihkan...", "success");

        setTimeout(() => {
          window.location.href = "index.html";
        }, 1000);

      } else {
        // Fallback: cek credential lokal jika backend offline
        this._localFallback(username, password);
      }

    } catch (err) {
      console.warn("Backend offline, coba fallback lokal:", err);
      this._localFallback(username, password);
    } finally {
      this.setLoading(false);
    }
  }

  // ===============================
  // LOCAL FALLBACK (demo)
  // ===============================
  _localFallback(username, password) {
    const DEMO_USERS = [
      { username: "admin",    password: "admin123",  role: "admin" },
      { username: "operator", password: "operator1", role: "operator" },
      { username: "viewer",   password: "viewer123", role: "viewer"  }
    ];

    const match = DEMO_USERS.find(
      u => u.username === username && u.password === password
    );

    if (match) {
      const fakeToken = btoa(`${match.username}:${Date.now()}`);
      localStorage.setItem("pm_token", fakeToken);
      localStorage.setItem("pm_user", JSON.stringify({
        username: match.username,
        role: match.role
      }));

      this.showAlert("✅ Login berhasil (mode demo)! Mengalihkan...", "success");

      setTimeout(() => {
        window.location.href = "index.html";
      }, 1000);

    } else {
      this.showAlert("❌ Username atau password salah. Coba lagi.");
      this.inputPass.value = "";
      this.inputPass.focus();
    }
  }
}


// ===============================
// AUTH GUARD (untuk dashboard)
// ===============================

function authGuard() {
  const token = localStorage.getItem("pm_token");
  if (!token) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

// ===============================
// LOGOUT
// ===============================

function doLogout() {
  localStorage.removeItem("pm_token");
  localStorage.removeItem("pm_user");
  window.location.href = "login.html";
}

// ===============================
// INJECT LOGOUT BUTTON ke header
// ===============================

function injectLogoutButton() {
  const header = document.querySelector(".header");
  if (!header) return;

  const userRaw  = localStorage.getItem("pm_user");
  const userInfo = userRaw ? JSON.parse(userRaw) : null;

  const right = document.createElement("div");
  right.style.display = "flex";
  right.style.alignItems = "center";
  right.style.gap = "1rem";

  // Tampilkan nama user
  if (userInfo) {
    const userBadge = document.createElement("span");
    userBadge.textContent = `👤 ${userInfo.username} (${userInfo.role})`;
    userBadge.style.cssText = "font-size:0.85rem;opacity:0.7;";
    right.appendChild(userBadge);
  }

  // Koneksi status tetap ada
  const existingStatus = document.getElementById("connectionStatus");
  if (existingStatus) right.appendChild(existingStatus);

  // Tombol logout
  const btn = document.createElement("button");
  btn.textContent = "🚪 Logout";
  btn.className = "logout-btn";
  btn.addEventListener("click", doLogout);
  right.appendChild(btn);

  // Ganti isi kanan header
  const children = Array.from(header.children);
  children.forEach(c => {
    if (c.id === "connectionStatus") c.remove();
  });
  header.appendChild(right);
}


// ===============================
// INIT APP
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  const isLoginPage    = !!document.getElementById("loginBtn");
  const isDashboard    = !!document.getElementById("chart");

  if (isLoginPage) {
    // Kalau sudah login, langsung redirect
    if (localStorage.getItem("pm_token")) {
      window.location.href = "index.html";
      return;
    }
    new LoginManager();
  }

  if (isDashboard) {
    if (!authGuard()) return;
    injectLogoutButton();
    new PowerMonitor();
  }
});