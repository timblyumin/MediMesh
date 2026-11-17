(function () {
  "use strict";

  var DATA_URL = "sample_dashboard_data.json";

  var LEVELS = { good: 0, warning: 1, critical: 2 };
  var MARKS = { good: "Steady", warning: "Watch", critical: "Overloaded" };
  var ICONS = { good: "●", warning: "▲", critical: "■" };

  var state = { data: null, selected: null };

  function worst() {
    var out = "good";
    for (var i = 0; i < arguments.length; i++) {
      var level = arguments[i];
      if (level && LEVELS[level] > LEVELS[out]) out = level;
    }
    return out;
  }

  function levelFor(value, warnAt, critAt) {
    if (typeof value !== "number" || !isFinite(value)) return null;
    if (value >= critAt) return "critical";
    if (value >= warnAt) return "warning";
    return "good";
  }

  function hourLevel(row, t) {
    if (row.forecast) {
      var gap = (row.required_staff || 0) - (row.scheduled_staff || 0);
      return levelFor(gap, t.staffing_gap_warning, t.staffing_gap_critical) || "good";
    }
    return worst(
      levelFor(row.wait, t.wait_warning, t.wait_critical),
      levelFor(row.occupancy, t.occupancy_warning, t.occupancy_critical)
    );
  }

  function clock(iso) {
    var d = new Date(iso);
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function longDate(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
  }

  function minutes(v) { return Math.round(v) + " min"; }
  function percent(v) { return Math.round(v) + "%"; }

  function tile(label, value, unit, note, level) {
    var div = document.createElement("div");
    div.className = "tile";
    var l = document.createElement("p");
    l.className = "label";
    l.textContent = label;
    var v = document.createElement("p");
    v.className = "value";
    v.textContent = value;
    if (unit) {
      var u = document.createElement("span");
      u.className = "unit";
      u.textContent = unit;
      v.appendChild(u);
    }
    var n = document.createElement("p");
    n.className = "note";
    n.textContent = note;
    if (level && level !== "good") n.setAttribute("data-level", level);
    div.appendChild(l);
    div.appendChild(v);
    div.appendChild(n);
    return div;
  }

  function renderTiles(row, forecastRow, t) {
    var host = document.getElementById("tiles");
    host.innerHTML = "";
    if (!row) return;

    var waitLevel = levelFor(row.wait, t.wait_warning, t.wait_critical);
    var occLevel = levelFor(row.occupancy, t.occupancy_warning, t.occupancy_critical);
    host.appendChild(tile(
      "Wait time", Math.round(row.wait), "min",
      waitLevel === "good" ? "Under the " + t.wait_warning + " min threshold"
        : "Over the " + (waitLevel === "critical" ? t.wait_critical : t.wait_warning) + " min threshold",
      waitLevel
    ));
    host.appendChild(tile(
      "Bed occupancy", Math.round(row.occupancy), "%",
      occLevel === "good" ? "Under " + t.occupancy_warning + "%"
        : "Over " + (occLevel === "critical" ? t.occupancy_critical : t.occupancy_warning) + "%",
      occLevel
    ));
    host.appendChild(tile("Patients this hour", Math.round(row.volume), "",
      Math.round(row.staff) + " staff on duty", "good"));

    if (forecastRow) {
      var gap = forecastRow.required_staff - forecastRow.scheduled_staff;
      var gapLevel = levelFor(gap, t.staffing_gap_warning, t.staffing_gap_critical) || "good";
      host.appendChild(tile(
        "Expected next hour", Math.round(forecastRow.pred_volume), "",
        gap > 0 ? "Short " + gap + " staff" : "Staffing covers it",
        gapLevel
      ));
    }
  }

  function renderState(level, row, forecastRow, t) {
    var band = document.getElementById("state");
    band.setAttribute("data-level", level);
    document.getElementById("state-mark").textContent = MARKS[level];

    var reasons = [];
    if (row) {
      if (row.wait >= t.wait_warning) reasons.push("wait time is " + minutes(row.wait));
      if (row.occupancy >= t.occupancy_warning) reasons.push("beds are " + percent(row.occupancy) + " full");
    }
    if (forecastRow) {
      var gap = forecastRow.required_staff - forecastRow.scheduled_staff;
      if (gap > 0) {
        reasons.push("next hour needs " + forecastRow.required_staff +
          " staff against " + forecastRow.scheduled_staff + " scheduled");
      }
    }

    var detail = document.getElementById("state-detail");
    detail.textContent = reasons.length
      ? reasons.join("; ").replace(/^./, function (c) { return c.toUpperCase(); }) + "."
      : "Wait time, beds and staffing are all inside their thresholds.";
  }

  function renderStrip(rows, t) {
    var strip = document.getElementById("strip");
    strip.innerHTML = "";
    var waits = rows.map(function (r) { return r.wait; })
      .filter(function (v) { return typeof v === "number"; });
    var peak = Math.max.apply(null, waits.concat([t.wait_critical]));

    rows.forEach(function (row, i) {
      var level = hourLevel(row, t);
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "hour";
      btn.setAttribute("data-level", level);
      btn.setAttribute("data-forecast", String(!!row.forecast));
      btn.setAttribute("aria-pressed", String(i === state.selected));

      var hr = document.createElement("span");
      hr.className = "hr";
      hr.textContent = clock(row.time);

      var val = document.createElement("span");
      val.className = "wait";
      val.textContent = row.forecast ? Math.round(row.pred_volume) : Math.round(row.wait);

      var bar = document.createElement("span");
      bar.className = "bar";
      var fill = document.createElement("i");
      fill.style.width = row.forecast ? "100%"
        : Math.max(2, Math.min(100, (row.wait / peak) * 100)) + "%";
      bar.appendChild(fill);

      var tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = row.forecast ? "patients ahead" : (i === 0 ? "min wait" : "\u00A0");

      btn.appendChild(hr);
      btn.appendChild(val);
      btn.appendChild(bar);
      btn.appendChild(tag);
      btn.setAttribute("aria-label", clock(row.time) + ", " + MARKS[level]);
      btn.addEventListener("click", function () { select(i); });
      strip.appendChild(btn);
    });
  }

  function chartRows(rows, actualKey, predKey) {
    return rows.map(function (row, i) {
      return {
        label: clock(row.time),
        tick: i % 3 === 0 || i === rows.length - 1 ? clock(row.time) : "",
        actual: typeof row[actualKey] === "number" ? row[actualKey] : null,
        predicted: typeof row[predKey] === "number" ? row[predKey] : null,
        forecast: !!row.forecast
      };
    });
  }

  function renderTable(id, rows, actualKey, predKey, unit) {
    var table = document.getElementById(id);
    var caption = table.querySelector("caption");
    table.innerHTML = "";
    if (caption) table.appendChild(caption);
    var head = document.createElement("thead");
    head.innerHTML = "<tr><th>Hour</th><th>Actual</th><th>Model</th></tr>";
    table.appendChild(head);
    var body = document.createElement("tbody");
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      var a = typeof row[actualKey] === "number" ? Math.round(row[actualKey]) + unit : "—";
      var p = typeof row[predKey] === "number" ? Math.round(row[predKey]) + unit : "—";
      tr.innerHTML = "<td>" + clock(row.time) + "</td><td>" + a + "</td><td>" + p + "</td>";
      body.appendChild(tr);
    });
    table.appendChild(body);
  }

  function renderStaffing(forecastRow, t) {
    var host = document.getElementById("staffing");
    host.innerHTML = "";
    if (!forecastRow) {
      host.textContent = "No forecast hour in this data.";
      return;
    }
    var need = forecastRow.required_staff;
    var have = forecastRow.scheduled_staff;
    var gap = need - have;
    var level = levelFor(gap, t.staffing_gap_warning, t.staffing_gap_critical) || "good";
    var top = Math.max(need, have, 1);

    var chip = document.createElement("p");
    chip.className = "chip";
    chip.setAttribute("data-level", level);
    chip.textContent = ICONS[level] + " " + (gap > 0 ? "Short " + gap + " staff at " + clock(forecastRow.time)
      : "Covered at " + clock(forecastRow.time));
    host.appendChild(chip);

    [["Needed", need], ["Scheduled", have]].forEach(function (pair) {
      var row = document.createElement("p");
      row.style.margin = "0.5rem 0 0";
      row.textContent = pair[0] + ": " + pair[1] + " staff";
      var meter = document.createElement("span");
      meter.className = "bar";
      meter.style.display = "block";
      meter.style.height = "10px";
      meter.style.background = "var(--rule)";
      meter.style.marginTop = "0.25rem";
      var fill = document.createElement("i");
      fill.style.display = "block";
      fill.style.height = "100%";
      fill.style.width = (pair[1] / top) * 100 + "%";
      fill.style.background = pair[0] === "Needed" && gap > 0 ? "var(--crit)" : "var(--series)";
      meter.appendChild(fill);
      host.appendChild(row);
      host.appendChild(meter);
    });

    var note = document.createElement("p");
    note.style.cssText = "margin:0.75rem 0 0;font-size:0.8125rem;color:var(--ink-muted)";
    note.textContent = "Based on " + Math.round(forecastRow.pred_volume) +
      " patients expected and the staffing ratio set in staffing_demand.py.";
    host.appendChild(note);
  }

  function renderFactors(factors) {
    var list = document.getElementById("factors");
    list.innerHTML = "";
    (factors || []).forEach(function (f) {
      var li = document.createElement("li");
      var name = document.createElement("span");
      name.textContent = f.factor;
      var share = document.createElement("span");
      share.className = "share";
      share.textContent = Math.round(f.share * 100) + "%";
      var meter = document.createElement("span");
      meter.className = "meter";
      var fill = document.createElement("i");
      fill.style.width = Math.max(1, f.share * 100) + "%";
      meter.appendChild(fill);
      li.appendChild(name);
      li.appendChild(share);
      li.appendChild(meter);
      list.appendChild(li);
    });
  }

  function select(index) {
    state.selected = index;
    var rows = state.data.hours;
    var t = state.data.thresholds;
    var row = rows[index];
    var forecastRow = rows.filter(function (r) { return r.forecast; }).pop();

    Array.prototype.forEach.call(document.querySelectorAll(".hour"), function (btn, i) {
      btn.setAttribute("aria-pressed", String(i === index));
    });

    if (row.forecast) {
      var lastActual = rows.filter(function (r) { return !r.forecast; }).pop();
      renderTiles(lastActual, forecastRow, t);
      renderState(hourLevel(row, t), lastActual, forecastRow, t);
      document.getElementById("clock").textContent = clock(row.time) + " (ahead)";
    } else {
      renderTiles(row, forecastRow, t);
      renderState(hourLevel(row, t), row, forecastRow, t);
      document.getElementById("clock").textContent = clock(row.time);
    }
  }

  function render(data) {
    state.data = data;
    var rows = data.hours;
    var t = data.thresholds;
    var forecastRow = rows.filter(function (r) { return r.forecast; }).pop();

    document.getElementById("unit").textContent = data.unit;
    document.getElementById("stamp").textContent =
      "Data through " + longDate(data.generated_at) + ", " + clock(data.generated_at) +
      " · thresholds: " + t.wait_warning + " min wait, " + t.occupancy_warning + "% beds";

    renderStrip(rows, t);
    renderStaffing(forecastRow, t);
    renderFactors(data.factors);

    MediMeshCharts.lineChart(document.getElementById("chart-wait"), {
      rows: chartRows(rows, "wait", "pred_wait"),
      critical: t.wait_critical,
      criticalLabel: t.wait_critical + " min",
      format: minutes,
      summary: "Wait time in minutes over the last hours, actual against the model."
    });
    MediMeshCharts.lineChart(document.getElementById("chart-occupancy"), {
      rows: chartRows(rows, "occupancy", "pred_occupancy"),
      critical: t.occupancy_critical,
      criticalLabel: t.occupancy_critical + "%",
      format: percent,
      summary: "Bed occupancy percent over the last hours, actual against the model."
    });
    renderTable("table-wait", rows, "wait", "pred_wait", " min");
    renderTable("table-occupancy", rows, "occupancy", "pred_occupancy", "%");

    var lastActualIndex = rows.length - 1;
    while (lastActualIndex > 0 && rows[lastActualIndex].forecast) lastActualIndex--;
    select(lastActualIndex);
  }

  function fail(message) {
    var box = document.getElementById("fallback");
    box.hidden = false;
    box.textContent = message;
    document.getElementById("state-detail").textContent = "No data loaded.";
  }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    if (!state.data) return;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { render(state.data); }, 150);
  });

  fetch(DATA_URL, { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(render)
    .catch(function (err) {
      fail("Could not load " + DATA_URL + " (" + err.message +
        "). Run scripts/export_dashboard_data.py, and serve this folder over http rather than opening the file directly.");
    });
})();
