(function () {
  "use strict";

  var FIELD_KR = {
    patient_no: "환자번호",
    patient_name: "환자명",
    patient_rrn: "주민등록번호",
    patient_gender: "성별",
    patient_birth: "생년월일",
    patient_address: "주소",
    patient_email: "이메일",
    patient_tel: "전화번호",
    patient_foreign: "외국인 여부",
    patient_passport: "여권번호",
    patient_hypass_YN: "하이패스 사용",
    patient_last_visit: "최근 방문일",
    guardian: "보호자",
    created_date: "생성일시",
    last_modified_date: "수정일시",
    intt_cd: "기관코드",
    app_user_id: "앱 사용자 ID",
    blood_type: "혈액형",
    height_cm: "키(cm)",
    weight_kg: "몸무게(kg)",
  };

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

  function rowTable(obj, title) {
    var keys = Object.keys(obj || {}).filter(function (k) {
      return k.indexOf("_sha256") === -1 && obj[k] !== undefined;
    });
    var html =
      '<h3 class="pg-modal__sect">' +
      esc(title) +
      '</h3><table class="league pg-modal__table"><tbody>';
    keys.forEach(function (k) {
      var label = FIELD_KR[k] || k;
      html +=
        "<tr><th>" +
        esc(label) +
        "</th><td>" +
        esc(obj[k]) +
        "</td></tr>";
    });
    html += "</tbody></table>";
    return html;
  }

  function buildModalHtml(data) {
    var p = data.patient || {};
    var html = rowTable(p, "환자 마스터");
    if (data.profile) {
      html += rowTable(data.profile, "앱·웨어러블 프로필");
    }
    return html || "<p>데이터 없음</p>";
  }

  window.openPgPatientModal = function (patientNo) {
    fetch("/api/dashboard/pg-patient/" + encodeURIComponent(String(patientNo)))
      .then(function (r) {
        if (!r.ok) {
          return r.json().then(function (j) {
            var d = j.detail;
            var msg =
              typeof d === "string"
                ? d
                : Array.isArray(d)
                  ? d
                      .map(function (x) {
                        return x.msg || "";
                      })
                      .join(", ")
                  : r.status;
            throw new Error(msg || String(r.status));
          });
        }
        return r.json();
      })
      .then(function (data) {
        var body = el("pgPatientModalBody");
        var modal = el("pgPatientModal");
        if (!body || !modal) {
          return;
        }
        body.innerHTML = buildModalHtml(data);
        modal.classList.remove("pg-modal--hidden");
        modal.setAttribute("aria-hidden", "false");
      })
      .catch(function (e) {
        alert(e.message || "조회 실패");
      });
  };

  function closePgPatientModal() {
    var modal = el("pgPatientModal");
    if (!modal) {
      return;
    }
    modal.classList.add("pg-modal--hidden");
    modal.setAttribute("aria-hidden", "true");
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    if (!t || !t.closest) {
      return;
    }
    var btn = t.closest(".pg-patient-cell");
    if (!btn) {
      return;
    }
    var pn = btn.getAttribute("data-patient-no");
    if (!pn || window.openPgPatientModal === undefined) {
      return;
    }
    ev.preventDefault();
    window.openPgPatientModal(pn);
  });

  document.addEventListener("DOMContentLoaded", function () {
    var modal = el("pgPatientModal");
    if (modal) {
      var btnClose = el("pgPatientModalClose");
      var backdrop = modal.querySelector(".pg-modal__backdrop");
      if (btnClose) {
        btnClose.addEventListener("click", closePgPatientModal);
      }
      if (backdrop) {
        backdrop.addEventListener("click", closePgPatientModal);
      }
    }

    var syncBtn = el("pgSyncMysqlBtn");
    if (syncBtn) {
      syncBtn.addEventListener("click", function () {
        syncBtn.disabled = true;
        fetch("/api/dashboard/etl/sync-postgres-to-mysql", { method: "POST" })
          .then(function (r) {
            if (!r.ok) {
              return r.json().then(function (j) {
                var d = j.detail;
                var msg =
                  typeof d === "string"
                    ? d
                    : Array.isArray(d)
                      ? d
                          .map(function (x) {
                            return x.msg || "";
                          })
                          .join(", ")
                      : r.status;
                throw new Error(msg || String(r.status));
              });
            }
            return r.json();
          })
          .then(function (res) {
            var ok = res && res.ok === true;
            alert(ok ? "MySQL 동기화가 완료되었습니다." : JSON.stringify(res));
            if (typeof window.refreshPgStats === "function") {
              window.refreshPgStats();
            } else {
              location.reload();
            }
          })
          .catch(function (e) {
            alert(e.message || "동기화 실패");
          })
          .finally(function () {
            syncBtn.disabled = false;
          });
      });
    }
  });
})();
