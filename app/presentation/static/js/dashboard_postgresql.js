(function () {
  "use strict";

  var API = "/api/dashboard/postgresql-stats";

  function el(id) {
    return document.getElementById(id);
  }

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
    var f = rows.filter(function (x) {
      return x.table_key === key;
    })[0];
    return f ? f.total_count : "—";
  }

  function metaLine(d) {
    var etl = d.etl || {};
    var parts = [];
    if (d.generated_at) {
      parts.push("집계 시각: " + esc(d.generated_at));
    }
    if (etl.wearable_updated_at) {
      parts.push("ETL 커서 갱신: " + esc(etl.wearable_updated_at));
    }
    return parts.join(" · ");
  }

  function renderKpi(d) {
    var v = d.vitals_aggregate || {};
    var tc = d.table_counts || [];
    var row = el("pgKpiRow");
    if (!row) {
      return;
    }
    var cells = [
      ["환자 마스터", countByKey(tc, "Patient")],
      ["앱 프로필", countByKey(tc, "user_app_profile")],
      ["생체 측정 행", v.total_vitals],
      ["금일 생체 측정", v.today_vitals],
      ["진료 이벤트", countByKey(tc, "patient_clinical_event")],
      ["MySQL 미동기화(생체)", v.pending_mysql_sync],
      ["MySQL 미동기화(일별)", v.pending_daily_mysql_sync],
      ["24h 평균 심박", v.avg_heart_rate_24h != null ? v.avg_heart_rate_24h : "—"],
    ];
    row.innerHTML = cells
      .map(function (pair) {
        return (
          '<div class="pg-kpi"><div class="pg-kpi__label">' +
          esc(pair[0]) +
          '</div><div class="pg-kpi__val">' +
          esc(pair[1]) +
          "</div></div>"
        );
      })
      .join("");
    var meta = el("pgMeta");
    if (meta) {
      meta.textContent = metaLine(d);
    }
  }

  function renderTableBar(tc) {
    var chartDom = el("pgTableBar");
    if (!chartDom || !window.echarts) {
      return;
    }
    var names = (tc || []).map(function (r) {
      return r.label_kr || r.sql_name;
    });
    var vals = (tc || []).map(function (r) {
      return Math.max(0, r.total_count);
    });
    var chart = echarts.init(chartDom);
    chart.setOption({
      grid: { left: 120, right: 24, top: 16, bottom: 24 },
      xAxis: {
        type: "value",
        splitLine: { lineStyle: { type: "dashed", color: "#eee" } },
      },
      yAxis: {
        type: "category",
        data: names.slice().reverse(),
        axisLabel: { overflow: "truncate", width: 110, fontSize: 11 },
      },
      tooltip: { trigger: "axis" },
      series: [
        {
          type: "bar",
          barWidth: 16,
          data: vals.slice().reverse(),
          itemStyle: { color: "#4f46e5" },
          label: { show: true, position: "right", fontSize: 10 },
        },
      ],
    });
    window.addEventListener("resize", function () {
      chart.resize();
    });
  }

  function renderClinicalPie(cats) {
    var chartDom = el("pgClinicalPie");
    if (!chartDom || !window.echarts || !(cats || []).length) {
      return;
    }
    var chart = echarts.init(chartDom);
    chart.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["28%", "65%"],
          label: { formatter: "{b}\n{d}%" },
          data: (cats || []).map(function (c) {
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

  function fillTable(id, headerHtml, rowsHtml) {
    var t = el(id);
    if (!t) {
      return;
    }
    t.innerHTML = headerHtml + rowsHtml;
  }

  function renderAll(d) {
    if (!d.connected) {
      el("pgErr").classList.remove("err--hidden");
      el("pgErr").textContent =
        d.message || "PostgreSQL 에 연결되지 않았습니다.";
      return;
    }
    el("pgErr").classList.add("err--hidden");

    renderKpi(d);
    renderTableBar(d.table_counts || []);
    renderClinicalPie(d.clinical_by_category || []);

    var ch =
      "<tr><th>유형</th><th>건수</th></tr>" +
      (d.clinical_by_category || [])
        .map(function (c) {
          return (
            "<tr><td>" +
            esc(c.label_kr || c.category) +
            "</td><td>" +
            esc(c.count) +
            "</td></tr>"
          );
        })
        .join("");
    fillTable("pgClinicalTable", "", ch);

    var vh =
      "<tr><th>측정 ID</th><th>환자</th><th>시각</th><th>심박</th><th>혈압</th><th>체온</th><th>스트레스</th><th>출처</th><th>MySQL 동기화</th></tr>";
    var vr =
      (d.recent_vitals || [])
        .map(function (r) {
          var pnKey = r.patient_no_key != null ? String(r.patient_no_key) : "";
          return (
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
            esc(r.source_channel) +
            "</td><td>" +
            (r.synced_mysql ? "예" : "아니오") +
            "</td></tr>"
          );
        })
        .join("") || '<tr><td colspan="9">데이터 없음</td></tr>';
    fillTable("pgVitalsTable", "", vh + vr);

    var wh =
      "<tr><th>환자</th><th>기준일</th><th>걸음</th><th>목표</th><th>수면(h)</th><th>스트레스</th><th>MySQL 동기화</th></tr>";
    var wr =
      (d.daily_wellness_sample_rows || [])
        .map(function (r) {
          var pnKeyW = r.patient_no_key != null ? String(r.patient_no_key) : "";
          return (
            "<tr><td><button type=\"button\" class=\"pg-patient-cell\" data-patient-no=\"" +
            esc(pnKeyW) +
            "\">" +
            esc(r.patient_no) +
            "</button></td><td>" +
            esc(r.summary_date) +
            "</td><td>" +
            esc(r.step_count) +
            "</td><td>" +
            esc(r.step_goal) +
            "</td><td>" +
            esc(r.sleep_hours) +
            "</td><td>" +
            esc(r.stress_level) +
            "</td><td>" +
            (r.synced_mysql ? "예" : "아니오") +
            "</td></tr>"
          );
        })
        .join("") || '<tr><td colspan="7">데이터 없음</td></tr>';
    fillTable("pgWellnessTable", "", wh + wr);

    var showMysqlTid = d.include_mysql_treatment_id_column === true;
    var eh =
      "<tr><th>이벤트 ID</th><th>환자</th><th>유형</th><th>일자</th><th>진료과</th><th>제목</th><th>상태</th>";
    if (showMysqlTid) {
      eh += "<th>MySQL 진료 ID</th>";
    }
    eh += "</tr>";
    var er =
      (d.recent_clinical_events || [])
        .map(function (r) {
          var pnKeyEv = r.patient_no_key != null ? String(r.patient_no_key) : "";
          var row =
            "<tr><td>" +
            esc(r.clinical_event_id) +
            "</td><td><button type=\"button\" class=\"pg-patient-cell\" data-patient-no=\"" +
            esc(pnKeyEv) +
            "\">" +
            esc(r.patient_no) +
            "</button></td><td>" +
            esc(r.category_kr || r.category) +
            "</td><td>" +
            esc(r.occurred_on) +
            "</td><td>" +
            esc(r.department) +
            "</td><td>" +
            esc(r.title) +
            "</td><td>" +
            esc(r.status_kr || r.status || "") +
            "</td>";
          if (showMysqlTid) {
            row += "<td>" + esc(r.source_mysql_treatment_id) + "</td>";
          }
          return row + "</tr>";
        })
        .join("") ||
      '<tr><td colspan="' +
      (showMysqlTid ? "8" : "7") +
      '">데이터 없음</td></tr>';
    fillTable("pgEventsTable", "", eh + er);
  }

  fetch(API)
    .then(function (r) {
      if (!r.ok) {
        throw new Error("HTTP " + r.status);
      }
      return r.json();
    })
    .then(renderAll)
    .catch(function (e) {
      el("pgErr").classList.remove("err--hidden");
      el("pgErr").textContent = "불러오기 실패: " + e.message;
    });

  window.refreshPgStats = function () {
    fetch(API)
      .then(function (r) {
        if (!r.ok) {
          throw new Error("HTTP " + r.status);
        }
        return r.json();
      })
      .then(renderAll)
      .catch(function (e) {
        el("pgErr").classList.remove("err--hidden");
        el("pgErr").textContent = "불러오기 실패: " + e.message;
      });
  };
})();
