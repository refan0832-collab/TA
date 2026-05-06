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
      const res = await fetch(this.API_URL);
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
// INIT APP
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  new PowerMonitor();
});