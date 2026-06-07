// ===============================
// ESP32 POWER MONITOR FINAL
// ===============================

class PowerMonitor {

  constructor() {

    // API
    this.API_URL =
      "/api/current";

    this.ESP_STATUS_URL =
      "/api/esp-status";

    // LIMIT
    this.currentThreshold =
      4.0;

    // STATUS
    this.isConnected = false;
    this.isEspOnline = false;

    // CHART
    this.chart = null;

    // INIT
    this.initChart();

    this.emptyState();

    this.start();
  }

  // ===============================
  // EMPTY STATE
  // ===============================

  emptyState() {

    const ids = [

      "tegangan",
      "arus",
      "daya",
      "frekuensi",
      "pf"
    ];

    ids.forEach(id => {

      const el =
        document.getElementById(id);

      if (el) {

        el.textContent = "-";
      }
    });
  }

  // ===============================
  // INIT CHART
  // ===============================

  initChart() {

    const ctx =
      document.getElementById(
        "chart"
      );

    if (!ctx) return;

    this.data = {

      labels: [],

      datasets: [

        {
          label:
            "Tegangan (V)",

          data: [],

          borderColor:
            "#3b82f6",

          backgroundColor:
            "rgba(59,130,246,0.15)",

          tension: 0.35,

          fill: true
        },

        {
          label:
            "Arus (A)",

          data: [],

          borderColor:
            "#22c55e",

          backgroundColor:
            "rgba(34,197,94,0.15)",

          tension: 0.35,

          fill: false
        },

        {
          label:
            "Daya (W)",

          data: [],

          borderColor:
            "#f97316",

          backgroundColor:
            "rgba(249,115,22,0.15)",

          tension: 0.35,

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

              color: "#fff"
            }
          }
        },

        scales: {

          x: {

            ticks: {

              color: "#cbd5e1"
            },

            grid: {

              color:
                "rgba(255,255,255,0.05)"
            }
          },

          y: {

            ticks: {

              color: "#cbd5e1"
            },

            grid: {

              color:
                "rgba(255,255,255,0.05)"
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

      // =========================
      // FETCH CURRENT DATA
      // =========================

      const dataRes =
        await fetch(
          this.API_URL
        );

      // =========================
      // FETCH ESP STATUS
      // =========================

      const espRes =
        await fetch(
          this.ESP_STATUS_URL
        );

      if (!dataRes.ok) {

        throw new Error(
          "Backend Error"
        );
      }

      const data =
        await dataRes.json();

      // =========================
      // ESP STATUS
      // =========================

      if (espRes.ok) {

        const esp =
          await espRes.json();

        this.isEspOnline =
          esp.esp_online === true;

      } else {

        this.isEspOnline = false;
      }

      this.isConnected = true;

      return {

        voltage:
          Number(
            data.tegangan || 0
          ),

        current:
          Number(
            data.arus || 0
          ),

        power:
          Number(
            data.daya || 0
          ),

        frequency:
          Number(
            data.frekuensi || 0
          ),

        pf:
          Number(
            data.pf || 0
          )
      };

    } catch (err) {

      console.warn(
        "[Backend Offline]",
        err.message
      );

      this.isConnected = false;

      this.isEspOnline = false;

      return null;
    }
  }

  // ===============================
  // KPI BADGE
  // ===============================

  updateKpiBadges(d) {

    // =========================
    // VOLTAGE
    // =========================

    const vBadge =
      document.getElementById(
        "voltageBadge"
      );

    const vText =
      document.getElementById(
        "voltageBadgeText"
      );

    if (vBadge && vText) {

      if (!d) {

        vBadge.className =
          "kpi-badge unknown";

        vText.textContent = "-";

      } else if (

        d.voltage >= 210 &&
        d.voltage <= 240

      ) {

        vBadge.className =
          "kpi-badge normal";

        vText.textContent =
          "Normal";

      } else {

        vBadge.className =
          "kpi-badge warning";

        vText.textContent =
          "Warning";
      }
    }

    // =========================
    // CURRENT
    // =========================

    const cBadge =
      document.getElementById(
        "currentBadge"
      );

    const cText =
      document.getElementById(
        "currentBadgeText"
      );

    if (cBadge && cText) {

      if (!d) {

        cBadge.className =
          "kpi-badge unknown";

        cText.textContent = "-";

      } else if (

        d.current >
        this.currentThreshold

      ) {

        cBadge.className =
          "kpi-badge warning";

        cText.textContent =
          "Warning";

      } else {

        cBadge.className =
          "kpi-badge normal";

        cText.textContent =
          "Normal";
      }
    }
  }

  // ===============================
  // UPDATE UI
  // ===============================

  updateUI(d) {

    if (!d) {

      this.emptyState();

      return;
    }

    const tegangan =
      Number(d.voltage || 0);

    const arus =
      Number(d.current || 0);

    const daya =
      Number(d.power || 0);

    const frekuensi =
      Number(d.frequency || 0);

    const pf =
      Number(d.pf || 0);

    // =========================
    // KPI VALUE
    // =========================

    document.getElementById(
      "tegangan"
    ).textContent =
      tegangan.toFixed(1);

    document.getElementById(
      "arus"
    ).textContent =
      arus.toFixed(2);

    document.getElementById(
      "daya"
    ).textContent =
      daya.toFixed(1);

    document.getElementById(
      "frekuensi"
    ).textContent =
      frekuensi.toFixed(1);

    document.getElementById(
      "pf"
    ).textContent =
      pf.toFixed(2);

    // =========================
    // STATUS
    // =========================

    const status =
      document.getElementById(
        "connectionStatus"
      );

    if (status) {

      status.textContent =
        this.isConnected
          ? "● Online"
          : "● Offline";

      status.style.color =
        this.isConnected
          ? "#22c55e"
          : "#ef4444";
    }

    // =========================
    // WARNING AMPERE
    // =========================

    const arusEl =
      document.getElementById(
        "arus"
      );

    if (!arusEl) return;

    const arusCard =
      arusEl.closest(
        ".kpi-card"
      );

    if (

      arus >
      this.currentThreshold

    ) {

      arusEl.classList.add(
        "blink-red"
      );

      arusCard?.classList.add(
        "warning-card"
      );

    } else {

      arusEl.classList.remove(
        "blink-red"
      );

      arusCard?.classList.remove(
        "warning-card"
      );
    }
  }

  // ===============================
  // UPDATE CHART
  // ===============================

  updateChart(d) {

    if (!this.chart || !d)
      return;

    const time =
      new Date()
      .toLocaleTimeString(
        "id-ID"
      );

    this.data.labels.push(
      time
    );

    this.data.datasets[0]
      .data.push(
        d.voltage
      );

    this.data.datasets[1]
      .data.push(
        d.current
      );

    this.data.datasets[2]
      .data.push(
        d.power
      );

    // LIMIT
    if (

      this.data.labels.length >
      20

    ) {

      this.data.labels.shift();

      this.data.datasets
        .forEach(ds => {

          ds.data.shift();
        });
    }

    this.chart.update();
  }

  // ===============================
  // STATUS PANEL
  // ===============================

  updateStatusPanel(d) {

    const espPillText =
      document.getElementById(
        "espPillText"
      );

    if (espPillText) {

      espPillText.textContent =
        this.isEspOnline
          ? "Online"
          : "Offline";
    }

    const lastUpdate =
      document.getElementById(
        "lastUpdateValue"
      );

    if (lastUpdate) {

      lastUpdate.textContent =

        d

        ? new Date()
            .toLocaleTimeString(
              "id-ID"
            )

        : "-";
    }
  }

  // ===============================
  // LOOP
  // ===============================

  async loop() {

    const d =
      await this.fetchData();

    this.updateUI(d);

    this.updateChart(d);

    this.updateStatusPanel(d);

    this.updateKpiBadges(d);
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
// AUTO START
// ===============================

document.addEventListener(

  "DOMContentLoaded",

  () => {

    new PowerMonitor();
  }
);