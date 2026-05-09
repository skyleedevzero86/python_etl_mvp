(function () {
  "use strict";

  const STATS_URL = "/api/dashboard/stats";

  const fmtKRW = new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  });

  function el(id) {
    return document.getElementById(id);
  }

  function renderGauge(g) {
    const chartDom = el("cGauge");
    const chart = echarts.init(chartDom);
    el("gaugeTitle").textContent = g.title;

    chart.setOption({
      series: [
        {
          type: "gauge",
          startAngle: 200,
          endAngle: -20,
          min: 0,
          max: g.max_value,
          splitNumber: 6,
          progress: { show: true, width: 14, itemStyle: { color: "#eab308" } },
          axisLine: { lineStyle: { width: 14, color: [[1, "#e5e7eb"]] } },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { distance: 18, color: "#6b7280", fontSize: 10 },
          anchor: { show: true, size: 16, itemStyle: { color: "#16a34a" } },
          title: { show: false },
          detail: {
            valueAnimation: true,
            fontSize: 22,
            offsetCenter: [0, "60%"],
            formatter: function (v) {
              return Math.round(v).toLocaleString("ko-KR");
            },
            color: "#111827",
          },
          data: [{ value: g.current, name: "" }],
        },
      ],
    });

    window.addEventListener("resize", function () {
      chart.resize();
    });
  }

  function renderVisitor(t) {
    const chart = echarts.init(el("cVisitor"));

    chart.setOption({
      grid: { left: 40, right: 16, top: 24, bottom: 28 },
      xAxis: { type: "category", data: t.labels, axisLine: { lineStyle: { color: "#cbd5f5" } } },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { type: "dashed", color: "#e5e7eb" } },
      },
      tooltip: { trigger: "axis" },
      series: [
        {
          type: "line",
          smooth: true,
          symbolSize: 6,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(249,115,22,0.35)" },
              { offset: 1, color: "rgba(249,115,22,0.02)" },
            ]),
          },
          lineStyle: { color: "#ea580c", width: 2 },
          itemStyle: { color: "#ea580c" },
          data: t.values,
        },
      ],
    });

    window.addEventListener("resize", function () {
      chart.resize();
    });
  }

  function renderPie(parts) {
    const chart = echarts.init(el("cPie"));
    const total = parts.reduce(function (s, p) {
      return s + p.value;
    }, 0);

    el("pieTotal").textContent =
      "합계 " + Math.round(total).toLocaleString("ko-KR") + " 건";

    chart.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["34%", "62%"],
          label: { formatter: "{b}\n{d}%" },
          data: parts.map(function (p) {
            return { value: p.value, name: p.name };
          }),
        },
      ],
      color: ["#6366f1", "#06b6d4", "#f59e0b", "#34d399", "#f472b6", "#94a3b8"],
    });

    window.addEventListener("resize", function () {
      chart.resize();
    });
  }

  function renderBar(p) {
    const chart = echarts.init(el("cBar"));
    chart.setOption({
      grid: { left: 100, right: 24, top: 10, bottom: 24 },
      xAxis: {
        type: "value",
        splitLine: { lineStyle: { type: "dashed", color: "#eee" } },
      },
      yAxis: {
        type: "category",
        data: p.categories.slice().reverse(),
        axisLabel: { overflow: "truncate", width: 90 },
      },
      series: [
        {
          type: "bar",
          barWidth: 22,
          data: p.values.slice().reverse(),
          itemStyle: {
            color: function (params) {
              const c = ["#22c55e", "#3b82f6", "#eab308"];
              return c[params.dataIndex % c.length];
            },
          },
          label: { show: true, position: "right", fontSize: 11 },
        },
      ],
    });

    window.addEventListener("resize", function () {
      chart.resize();
    });
  }

  function renderLeague(rows) {
    const tb = el("leagueTable");

    tb.innerHTML =
      "<tr><th>순위</th><th>진료과</th><th>추정액</th><th>목표</th><th>추세</th></tr>";

    rows.forEach(function (r, i) {
      const targetLine = Math.max.apply(null, r.spark.concat([1])) * 0.9;
      const tr = document.createElement("tr");
      const tdSp = document.createElement("td");
      const sparkId = "sp_" + i;

      tdSp.innerHTML =
        '<div class="spark" id="' + sparkId + '"></div>';

      tr.innerHTML =
        "<td>" +
        (i + 1) +
        "</td><td>" +
        r.name +
        "</td><td class=\"money\">" +
        fmtKRW.format(r.actual) +
        "</td><td class=\"money\">" +
        fmtKRW.format(r.target) +
        "</td>";

      tr.appendChild(tdSp);
      tb.appendChild(tr);

      requestAnimationFrame(function () {
        const sparkEl = document.getElementById(sparkId);

        const sp = echarts.init(sparkEl);

        sp.setOption({
          grid: { left: 0, right: 0, top: 2, bottom: 2 },
          xAxis: {
            type: "category",
            show: false,
            data: r.spark.map(function (_, j) {
              return j;
            }),
          },
          yAxis: { type: "value", show: false },
          series: [
            {
              type: "line",
              smooth: true,
              symbol: "none",
              lineStyle: { width: 1.8, color: "#16a34a" },
              areaStyle: { color: "rgba(22,163,74,0.12)" },
              markLine: {
                silent: true,
                symbol: "none",
                lineStyle: { color: "#eab308", type: "dashed", width: 1 },
                data: [{ yAxis: targetLine }],
              },
              data: r.spark,
            },
          ],
        });
      });
    });
  }

  function renderKpi(k, timeline) {
    el("kpiLabel").textContent = k.label;
    el("kpiActual").textContent = fmtKRW.format(k.actual);
    el("kpiTarget").textContent = fmtKRW.format(k.target);

    const g = el("kpiGrowth");
    const up = k.growth_pct >= 0;

    g.className = "growth" + (up ? "" : " bad");
    g.querySelector("span").textContent = up ? "▲" : "▼";
    el("kpiPct").textContent =
      Math.abs(k.growth_pct) + "% 최근 30일 대비 그 이전 30일";

    const sparkChart = echarts.init(el("cKpiSpark"));

    sparkChart.setOption({
      grid: { left: 0, right: 0, top: 4, bottom: 0 },
      xAxis: { type: "category", show: false, data: timeline.labels },
      yAxis: { type: "value", show: false },
      series: [
        {
          type: "line",
          smooth: true,
          symbol: "none",
          lineStyle: { width: 1.5, color: "#2563eb" },
          areaStyle: { color: "rgba(37,99,235,0.12)" },
          data: timeline.values,
        },
      ],
    });

    window.addEventListener("resize", function () {
      sparkChart.resize();
    });
  }

  fetch(STATS_URL)
    .then(function (r) {
      if (!r.ok) {
        throw new Error("API " + r.status);
      }
      return r.json();
    })
    .then(function (d) {
      renderGauge(d.gauge);
      renderVisitor(d.timeline);
      renderPie(d.pie_sales);
      renderLeague(d.league_table);
      renderBar(d.production);
      renderKpi(d.kpi, d.timeline);
    })
    .catch(function (e) {
      var errBox = el("dashErr");

      errBox.classList.remove("err--hidden");
      errBox.textContent =
        "통계를 불러오지 못했습니다. 데이터베이스 연결과 스키마를 확인하세요. 상세: " +
        e.message;
    });

  var PG_URL = "/api/dashboard/postgresql-stats";

  function esc(s) {
    if (s === null || s === undefined) {
      return "";
    }
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function countByKey(rows, key) {
    var found = rows.filter(function (x) {
      return x.table_key === key;
    })[0];
    return found ? found.total_count : "—";
  }

  function renderPgPanel(d) {
    var root = el("pgPanelInner");
    var errBox = el("pgPanelErr");
    if (!root) {
      return;
    }

    if (!d.connected) {
      errBox.classList.remove("err--hidden");
      errBox.textContent =
        d.message || "PostgreSQL 에 연결되지 않았습니다.";
      root.innerHTML = "";
      return;
    }

    errBox.classList.add("err--hidden");

    var v = d.vitals_aggregate || {};
    var etl = d.etl || {};
    var tc = d.table_counts || [];

    var html = "";
    html += '<div class="pg-kpi-row">';
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">환자 마스터</div><div class="pg-kpi__val">' +
      esc(countByKey(tc, "Patient")) +
      "</div></div>";
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">생체 측정 총건수</div><div class="pg-kpi__val">' +
      esc(v.total_vitals) +
      "</div></div>";
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">금일 생체 측정</div><div class="pg-kpi__val">' +
      esc(v.today_vitals) +
      "</div></div>";
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">MySQL 미동기화(생체)</div><div class="pg-kpi__val">' +
      esc(v.pending_mysql_sync) +
      "</div></div>";
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">MySQL 미동기화(일별)</div><div class="pg-kpi__val">' +
      esc(v.pending_daily_mysql_sync) +
      "</div></div>";
    html +=
      '<div class="pg-kpi"><div class="pg-kpi__label">24h 평균 심박</div><div class="pg-kpi__val">' +
      (v.avg_heart_rate_24h != null ? esc(v.avg_heart_rate_24h) : "—") +
      "</div></div>";
    html += "</div>";

    var metaParts = [];
    if (d.generated_at) {
      metaParts.push("집계 시각: " + esc(d.generated_at));
    }
    if (etl.wearable_updated_at) {
      metaParts.push("ETL 커서 갱신: " + esc(etl.wearable_updated_at));
    }
    html +=
      '<p class="pg-muted">' +
      (metaParts.length ? metaParts.join(" · ") : "") +
      "</p>";

    html += '<div class="pg-split">';
    html += '<div><h3 style="margin:0 0 8px;font-size:0.95rem;">진료 이벤트 유형 비중</h3><div id="pgCatPie" class="pg-chart-box"></div></div>';
    html +=
      '<div><h3 style="margin:0 0 8px;font-size:0.95rem;">테이블별 건수</h3><div class="pg-table-wrap"><table class="league"><thead><tr><th>테이블</th><th>건수</th></tr></thead><tbody>';

    tc.forEach(function (r) {
      html +=
        "<tr><td>" +
        esc(r.label_kr || r.sql_name) +
        "</td><td>" +
        esc(r.total_count) +
        "</td></tr>";
    });

    html += "</tbody></table></div></div></div>";

    html += '<h3 style="margin:20px 0 8px;font-size:0.95rem;">최근 생체 측정 (12건)</h3>';
    html +=
      '<div class="pg-table-wrap"><table class="league"><thead><tr><th>측정 ID</th><th>환자</th><th>시각</th><th>심박</th><th>혈압</th><th>체온</th><th>스트레스</th><th>MySQL 동기화</th></tr></thead><tbody>';

    (d.recent_vitals || []).forEach(function (r) {
      var pnKey = r.patient_no_key != null ? String(r.patient_no_key) : "";
      html +=
        "<tr><td>" +
        esc(r.vital_id) +
        '</td><td><button type="button" class="pg-patient-cell" data-patient-no="' +
        esc(pnKey) +
        '">' +
        esc(r.patient_no) +
        "</button></td><td>" +
        esc(r.measured_at) +
        "</td><td>" +
        esc(r.heart_rate_bpm) +
        "</td><td>" +
        esc(r.blood_pressure_systolic) +
        "/" +
        esc(r.blood_pressure_diastolic) +
        "</td><td>" +
        esc(r.body_temp_c) +
        "</td><td>" +
        esc(r.stress_score) +
        "</td><td>" +
        (r.synced_mysql ? "예" : "아니오") +
        "</td></tr>";
    });

    html += "</tbody></table></div>";

    html +=
      '<h3 style="margin:20px 0 8px;font-size:0.95rem;">최근 진료·검사 타임라인 (15건)</h3>';
    var showMysqlTid = d.include_mysql_treatment_id_column === true;
    html += '<div class="pg-table-wrap"><table class="league"><thead><tr>';
    html +=
      "<th>이벤트 ID</th><th>환자</th><th>유형</th><th>일자</th><th>진료과</th><th>제목</th><th>상태</th>";
    if (showMysqlTid) {
      html += "<th>MySQL 진료 ID</th>";
    }
    html += "</tr></thead><tbody>";

    (d.recent_clinical_events || []).forEach(function (r) {
      var pnKeyEv = r.patient_no_key != null ? String(r.patient_no_key) : "";
      html +=
        "<tr><td>" +
        esc(r.clinical_event_id) +
        '</td><td><button type="button" class="pg-patient-cell" data-patient-no="' +
        esc(pnKeyEv) +
        '">' +
        esc(r.patient_no) +
        "</button></td><td>";
      html += esc(r.category_kr || r.category) + "</td><td>";
      html += esc(r.occurred_on) + "</td><td>";
      html += esc(r.department) + "</td><td>";
      html += esc(r.title) + "</td><td>";
      html += esc(r.status_kr || r.status || "");
      html += "</td>";
      if (showMysqlTid) {
        html += "<td>" + esc(r.source_mysql_treatment_id) + "</td>";
      }
      html += "</tr>";
    });

    html += "</tbody></table></div>";

    root.innerHTML = html;

    var pieDom = document.getElementById("pgCatPie");
    if (pieDom && window.echarts && (d.clinical_by_category || []).length) {
      var chart = echarts.init(pieDom);
      chart.setOption({
        tooltip: { trigger: "item" },
        series: [
          {
            type: "pie",
            radius: ["30%", "68%"],
            label: { formatter: "{b}\n{d}%" },
            data: (d.clinical_by_category || []).map(function (c) {
              return {
                value: c.count,
                name: c.label_kr || c.category,
              };
            }),
          },
        ],
        color: ["#6366f1", "#06b6d4", "#f59e0b", "#34d399", "#f472b6", "#94a3b8"],
      });
      window.addEventListener("resize", function () {
        chart.resize();
      });
    }
  }

  fetch(PG_URL)
    .then(function (r) {
      if (!r.ok) {
        throw new Error("API " + r.status);
      }
      return r.json();
    })
    .then(renderPgPanel)
    .catch(function (e) {
      var errBox = el("pgPanelErr");
      var root = el("pgPanelInner");
      if (!errBox || !root) {
        return;
      }
      errBox.classList.remove("err--hidden");
      errBox.textContent =
        "PostgreSQL 통계를 불러오지 못했습니다. " + e.message;
      root.innerHTML = "";
    });

  window.refreshPgStats = function () {
    fetch(PG_URL)
      .then(function (r) {
        if (!r.ok) {
          throw new Error("API " + r.status);
        }
        return r.json();
      })
      .then(renderPgPanel)
      .catch(function (e) {
        var errBox = el("pgPanelErr");
        var root = el("pgPanelInner");
        if (errBox) {
          errBox.classList.remove("err--hidden");
          errBox.textContent =
            "PostgreSQL 통계를 불러오지 못했습니다. " + e.message;
        }
        if (root) {
          root.innerHTML = "";
        }
      });
  };
})();
