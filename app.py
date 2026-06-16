import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit_autorefresh import st_autorefresh


if __name__ == "__main__" and get_script_run_ctx() is None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    raise SystemExit


try:
    from firebase_config import root

    FIREBASE_IMPORT_ERROR = None
except Exception as exc:
    root = None
    FIREBASE_IMPORT_ERROR = exc


MONITORING_POINTS = [
    {
        "key": "x_direction_housing_A",
        "label": "A-X",
        "housing": "Housing A",
        "axis": "X",
    },
    {
        "key": "y_direction_housing_A",
        "label": "A-Y",
        "housing": "Housing A",
        "axis": "Y",
    },
    {
        "key": "x_direction_housing_B",
        "label": "B-X",
        "housing": "Housing B",
        "axis": "X",
    },
    {
        "key": "y_direction_housing_B",
        "label": "B-Y",
        "housing": "Housing B",
        "axis": "Y",
    },
]

NUMERIC_FIELDS = (
    "RMS",
    "Kurtosis",
    "Skewness",
    "CrestFactor",
    "PeakAmp",
    "PeakFreq_Hz",
    "SpectralCentroid_Hz",
    "SpectralBandwidth_Hz",
)

FAULT_INFO = {
    "Normal": {
        "severity": "Low",
        "location": "Healthy Machine",
        "recommendation": "No action required. Continue live monitoring.",
        "score": 100,
        "rul": 180,
    },
    "Misalign_01": {
        "severity": "Medium",
        "location": "Coupling",
        "recommendation": "Check shaft alignment during the next inspection window.",
        "score": 80,
        "rul": 120,
    },
    "Misalign_03": {
        "severity": "Medium",
        "location": "Coupling",
        "recommendation": "Realign shafts and verify coupling condition.",
        "score": 65,
        "rul": 90,
    },
    "Misalign_05": {
        "severity": "High",
        "location": "Coupling",
        "recommendation": "Schedule immediate alignment and reduce load if possible.",
        "score": 50,
        "rul": 60,
    },
    "BPFI_03": {
        "severity": "Medium",
        "location": "Inner Race Bearing",
        "recommendation": "Inspect inner race bearing and lubrication condition.",
        "score": 70,
        "rul": 90,
    },
    "BPFI_10": {
        "severity": "High",
        "location": "Inner Race Bearing",
        "recommendation": "Plan bearing replacement and increase inspection frequency.",
        "score": 45,
        "rul": 45,
    },
    "BPFI_30": {
        "severity": "Critical",
        "location": "Inner Race Bearing",
        "recommendation": "Replace bearing immediately and avoid extended operation.",
        "score": 20,
        "rul": 15,
    },
    "BPFO_03": {
        "severity": "Medium",
        "location": "Outer Race Bearing",
        "recommendation": "Inspect outer race bearing and lubrication condition.",
        "score": 70,
        "rul": 90,
    },
    "BPFO_10": {
        "severity": "High",
        "location": "Outer Race Bearing",
        "recommendation": "Plan bearing replacement and monitor vibration closely.",
        "score": 45,
        "rul": 45,
    },
    "BPFO_30": {
        "severity": "Critical",
        "location": "Outer Race Bearing",
        "recommendation": "Replace bearing immediately and isolate the machine.",
        "score": 20,
        "rul": 15,
    },
    "Unbalance_0583mg": {
        "severity": "Low",
        "location": "Rotor",
        "recommendation": "Monitor rotor vibration level.",
        "score": 90,
        "rul": 150,
    },
    "Unbalance_1169mg": {
        "severity": "Medium",
        "location": "Rotor",
        "recommendation": "Schedule rotor balancing and inspect mounts.",
        "score": 75,
        "rul": 120,
    },
    "Unbalance_1751mg": {
        "severity": "Medium",
        "location": "Rotor",
        "recommendation": "Check balancing and inspect coupling alignment.",
        "score": 65,
        "rul": 90,
    },
    "Unbalance_2239mg": {
        "severity": "High",
        "location": "Rotor",
        "recommendation": "Balance rotor urgently and reduce operating stress.",
        "score": 45,
        "rul": 45,
    },
    "Unbalance_3318mg": {
        "severity": "Critical",
        "location": "Rotor",
        "recommendation": "Stop machine and perform immediate rotor balancing.",
        "score": 20,
        "rul": 15,
    },
}

SEVERITY_RANK = {
    "Low": 0,
    "Medium": 1,
    "High": 2,
    "Critical": 3,
}

SEVERITY_COLORS = {
    "Low": "#22c55e",
    "Medium": "#f59e0b",
    "High": "#ef4444",
    "Critical": "#dc2626",
    "Unknown": "#94a3b8",
}

PAGES = [
    "Overview",
    "Machine Dashboard",
    "Analytics",
    "Reports",
]


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --sx-bg: #080b12;
            --sx-panel: #101724;
            --sx-panel-soft: #142033;
            --sx-border: rgba(148, 163, 184, 0.20);
            --sx-muted: #94a3b8;
            --sx-text: #f8fafc;
            --sx-blue: #38bdf8;
            --sx-green: #22c55e;
            --sx-orange: #f59e0b;
            --sx-red: #ef4444;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.10), transparent 32rem),
                linear-gradient(180deg, #080b12 0%, #0b1020 100%);
        }

        section[data-testid="stSidebar"] {
            background: #0b1020;
            border-right: 1px solid var(--sx-border);
        }

        .block-container {
            padding-top: 2.1rem;
            padding-bottom: 3rem;
        }

        .sx-title-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.2rem 0 1.2rem;
            border-bottom: 1px solid var(--sx-border);
            margin-bottom: 1.2rem;
        }

        .sx-kicker {
            color: var(--sx-blue);
            font-size: 0.76rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .sx-title {
            color: var(--sx-text);
            font-size: 2.25rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0.2rem 0;
        }

        .sx-subtitle {
            color: var(--sx-muted);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }

        .sx-status {
            min-width: 210px;
            border: 1px solid var(--sx-border);
            background: rgba(16, 23, 36, 0.78);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            text-align: right;
        }

        .sx-status strong {
            display: block;
            color: var(--sx-text);
            font-size: 1rem;
        }

        .sx-status span {
            color: var(--sx-muted);
            font-size: 0.8rem;
        }

        .sx-card {
            border: 1px solid var(--sx-border);
            background: linear-gradient(180deg, rgba(20, 32, 51, 0.92), rgba(12, 18, 30, 0.92));
            border-radius: 8px;
            padding: 1rem;
            min-height: 118px;
        }

        .sx-card-label {
            color: var(--sx-muted);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .sx-card-value {
            color: var(--sx-text);
            font-size: 1.85rem;
            line-height: 1.1;
            font-weight: 800;
            margin-top: 0.5rem;
        }

        .sx-card-meta {
            color: var(--sx-muted);
            font-size: 0.82rem;
            margin-top: 0.45rem;
        }

        .sx-section-title {
            color: var(--sx-text);
            font-size: 1.1rem;
            font-weight: 800;
            margin: 1.4rem 0 0.65rem;
        }

        .sx-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            padding: 0.22rem 0.65rem;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .sx-point {
            border: 1px solid var(--sx-border);
            background: rgba(16, 23, 36, 0.88);
            border-radius: 8px;
            padding: 0.95rem;
            min-height: 170px;
        }

        .sx-point-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }

        .sx-point-name {
            color: var(--sx-text);
            font-size: 1.15rem;
            font-weight: 800;
        }

        .sx-point-meta {
            color: var(--sx-muted);
            font-size: 0.8rem;
        }

        .sx-readings {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem;
            margin-top: 0.75rem;
        }

        .sx-reading {
            border-top: 1px solid var(--sx-border);
            padding-top: 0.45rem;
        }

        .sx-reading span {
            color: var(--sx-muted);
            display: block;
            font-size: 0.73rem;
        }

        .sx-reading strong {
            color: var(--sx-text);
            font-size: 0.98rem;
        }

        .sx-bench {
            display: grid;
            grid-template-columns: repeat(7, minmax(105px, 1fr));
            gap: 0.75rem;
            overflow-x: auto;
            padding: 0.9rem;
            border: 1px solid var(--sx-border);
            background: rgba(16, 23, 36, 0.72);
            border-radius: 8px;
        }

        .sx-node {
            border: 1px solid var(--sx-border);
            border-top: 3px solid var(--sx-blue);
            background: rgba(8, 13, 24, 0.88);
            border-radius: 8px;
            padding: 0.8rem;
            min-height: 92px;
        }

        .sx-node strong {
            color: var(--sx-text);
            display: block;
            font-size: 0.92rem;
        }

        .sx-node span {
            color: var(--sx-muted);
            font-size: 0.76rem;
        }

        .sx-action {
            border-left: 4px solid var(--sx-blue);
            background: rgba(56, 189, 248, 0.10);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            color: var(--sx-text);
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, value))


def safe_text(value, default="Unknown"):
    if value in (None, ""):
        return default
    return str(value).strip()


def format_number(value, decimals=2, suffix=""):
    return f"{safe_float(value):.{decimals}f}{suffix}"


def is_fault_active(fault):
    return safe_text(fault, "Normal") not in {"Normal", "Healthy", "None"}


def normalize_fault_label(fault):
    fault = safe_text(fault, "Normal")

    if "BPFI" in fault:
        return "BPFI_10"
    if "BPFO" in fault:
        return "BPFO_10"
    if "Misalign" in fault:
        return "Misalign_03"
    if "Unbalance" in fault:
        return "Unbalance_1169mg"
    if fault in FAULT_INFO:
        return fault
    return "Normal"


def infer_health_score(point):
    if "HealthScore" in point and point["HealthScore"] not in (None, ""):
        return clamp(safe_float(point["HealthScore"]))

    severity = safe_text(point.get("Severity"), "Low")
    rms = safe_float(point.get("RMS"))

    severity_penalty = {
        "Low": 0,
        "Medium": 12,
        "High": 28,
        "Critical": 55,
    }.get(severity, 8)

    return clamp(100 - (rms * 4.5) - severity_penalty)


def normalize_point(meta, raw_point):
    raw_point = raw_point if isinstance(raw_point, dict) else {}
    point = {
        "key": meta["key"],
        "label": meta["label"],
        "housing": meta["housing"],
        "axis": meta["axis"],
        "Channel": safe_text(raw_point.get("Channel"), meta["key"]),
        "Fault": safe_text(raw_point.get("Fault"), "Normal"),
        "Condition": safe_text(raw_point.get("Condition"), "Healthy"),
        "Severity": safe_text(raw_point.get("Severity"), "Low"),
    }

    for field in NUMERIC_FIELDS:
        point[field] = safe_float(raw_point.get(field, 0))

    point["HealthScore"] = infer_health_score({**raw_point, **point})
    point["FaultProfile"] = normalize_fault_label(point["Fault"])
    point["FaultActive"] = is_fault_active(point["Fault"])

    return point


def normalize_payload(payload):
    payload = payload if isinstance(payload, dict) else {}
    return [
        normalize_point(meta, payload.get(meta["key"], {}))
        for meta in MONITORING_POINTS
    ]


def sample_current_data():
    base_point = {
        "RMS": 1.2,
        "Kurtosis": 3.1,
        "Skewness": 0.2,
        "CrestFactor": 2.4,
        "PeakAmp": 0.8,
        "PeakFreq_Hz": 50.0,
        "SpectralCentroid_Hz": 120.0,
        "SpectralBandwidth_Hz": 35.0,
        "Fault": "Normal",
        "Severity": "Low",
        "Condition": "Healthy",
        "HealthScore": 95,
    }

    return {
        "x_direction_housing_A": {
            **base_point,
            "Channel": "x_direction_housing_A",
            "RMS": 1.18,
            "HealthScore": 96,
        },
        "y_direction_housing_A": {
            **base_point,
            "Channel": "y_direction_housing_A",
            "RMS": 1.31,
            "HealthScore": 94,
        },
        "x_direction_housing_B": {
            **base_point,
            "Channel": "x_direction_housing_B",
            "RMS": 1.44,
            "HealthScore": 93,
        },
        "y_direction_housing_B": {
            **base_point,
            "Channel": "y_direction_housing_B",
            "RMS": 1.27,
            "HealthScore": 95,
        },
    }


def read_current_data(allow_demo_fallback):
    if root is None:
        error = f"Firebase configuration error: {FIREBASE_IMPORT_ERROR}"
        if allow_demo_fallback:
            return sample_current_data(), "demo", error
        return None, "error", error

    try:
        payload = root.child("current_data").get()
    except Exception as exc:
        if allow_demo_fallback:
            return sample_current_data(), "demo", str(exc)
        return None, "error", str(exc)

    if not isinstance(payload, dict) or not payload:
        message = "No current_data payload found in Firebase."
        if allow_demo_fallback:
            return sample_current_data(), "demo", message
        return None, "empty", message

    return payload, "live", None


def compute_summary(points):
    rms_values = [point["RMS"] for point in points]
    health_values = [point["HealthScore"] for point in points]
    active_faults = [point for point in points if point["FaultActive"]]

    worst_point = max(
        points,
        key=lambda point: (
            SEVERITY_RANK.get(point["Severity"], -1),
            point["RMS"],
        ),
    )

    active_profile = next(
        (point["FaultProfile"] for point in active_faults),
        "Normal",
    )
    profile = FAULT_INFO.get(active_profile, FAULT_INFO["Normal"])
    overall_health = clamp(sum(health_values) / max(len(health_values), 1))

    if any(point["Severity"] == "Critical" for point in active_faults):
        status = "Critical"
    elif any(point["Severity"] == "High" for point in active_faults):
        status = "High Risk"
    elif active_faults:
        status = "Warning"
    else:
        status = "Healthy"

    if overall_health < 50 or status in {"Critical", "High Risk"}:
        priority = "High"
    elif overall_health < 80 or active_faults:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "avg_rms": sum(rms_values) / max(len(rms_values), 1),
        "max_rms": max(rms_values) if rms_values else 0,
        "velocity_rms": (sum(rms_values) / max(len(rms_values), 1)) * 4.5,
        "fault_count": len(active_faults),
        "active_faults": active_faults,
        "overall_health": overall_health,
        "worst_point": worst_point,
        "status": status,
        "priority": priority,
        "fault": active_profile,
        "profile": profile,
        "rul": profile["rul"],
        "recommendation": profile["recommendation"],
    }


def points_to_dataframe(points):
    return pd.DataFrame(
        [
            {
                "Point": point["label"],
                "Housing": point["housing"],
                "Axis": point["axis"],
                "Fault": point["Fault"],
                "Condition": point["Condition"],
                "Severity": point["Severity"],
                "Health Score": round(point["HealthScore"], 1),
                "RMS": round(point["RMS"], 3),
                "Kurtosis": round(point["Kurtosis"], 3),
                "Skewness": round(point["Skewness"], 3),
                "Crest Factor": round(point["CrestFactor"], 3),
                "Peak Amp": round(point["PeakAmp"], 3),
                "Peak Freq Hz": round(point["PeakFreq_Hz"], 3),
            }
            for point in points
        ]
    )


def feature_matrix(points):
    rows = []
    for field, label in [
        ("RMS", "RMS"),
        ("Kurtosis", "Kurtosis"),
        ("Skewness", "Skewness"),
        ("CrestFactor", "Crest Factor"),
        ("PeakAmp", "Peak Amplitude"),
        ("PeakFreq_Hz", "Peak Frequency Hz"),
    ]:
        row = {"Feature": label}
        for point in points:
            row[point["label"]] = round(point[field], 3)
        rows.append(row)
    return pd.DataFrame(rows)


def severity_badge(severity):
    color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["Unknown"])
    return (
        f'<span class="sx-pill" style="color:{color};background:{color}18;">'
        f"{escape(severity)}</span>"
    )


def worst_severity(*points):
    return max(
        (point["Severity"] for point in points),
        key=lambda severity: SEVERITY_RANK.get(severity, -1),
        default="Unknown",
    )


def kpi_card(label, value, meta="", accent="#38bdf8"):
    st.markdown(
        f"""
        <div class="sx-card" style="border-top: 3px solid {accent};">
            <div class="sx-card-label">{escape(label)}</div>
            <div class="sx-card-value">{escape(str(value))}</div>
            <div class="sx-card-meta">{escape(str(meta))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(machine_name, summary, data_mode, loaded_at):
    status_color = {
        "Healthy": "#22c55e",
        "Warning": "#f59e0b",
        "High Risk": "#ef4444",
        "Critical": "#dc2626",
    }.get(summary["status"], "#94a3b8")

    mode_label = "LIVE DATA" if data_mode == "live" else "DEMO FALLBACK"
    mode_color = "#22c55e" if data_mode == "live" else "#f59e0b"

    st.markdown(
        f"""
        <div class="sx-title-row">
            <div>
                <div class="sx-kicker">Sentinel-X Current Data Console</div>
                <div class="sx-title">Predictive Maintenance Dashboard</div>
                <div class="sx-subtitle">
                    {escape(machine_name)} | Active supervision for vibration,
                    health and fault localization.
                </div>
            </div>
            <div class="sx-status">
                <span class="sx-pill" style="color:{mode_color};background:{mode_color}18;">
                    {mode_label}
                </span>
                <strong style="color:{status_color}; margin-top:0.55rem;">
                    {escape(summary["status"])}
                </strong>
                <span>Updated {escape(loaded_at.strftime("%H:%M:%S"))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_notice(data_mode, data_error):
    if data_mode == "live":
        return

    if data_mode == "demo":
        st.warning(
            "Firebase is unavailable. The interface is using local demo data so you can verify the dashboard layout."
        )
    else:
        st.error("Unable to load current Firebase data.")

    if data_error:
        with st.expander("Firebase diagnostic details"):
            st.code(data_error)


def render_kpis(summary):
    cols = st.columns(5)
    with cols[0]:
        kpi_card("Health Score", f"{summary['overall_health']:.0f}%", "Average of current points", "#22c55e")
    with cols[1]:
        kpi_card("Machine Status", summary["status"], f"Priority: {summary['priority']}", "#38bdf8")
    with cols[2]:
        kpi_card("Faulty Points", summary["fault_count"], "Out of 4 monitored points", "#f59e0b")
    with cols[3]:
        kpi_card("Avg RMS", format_number(summary["avg_rms"], 2, " g"), "Current vibration level", "#a78bfa")
    with cols[4]:
        kpi_card("Velocity RMS", format_number(summary["velocity_rms"], 2, " mm/s"), "Derived estimate", "#fb7185")


def render_point_card(point):
    severity = point["Severity"]
    color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["Unknown"])
    fault_text = point["Fault"] if point["FaultActive"] else "Normal"

    st.markdown(
        f"""
        <div class="sx-point" style="border-top: 3px solid {color};">
            <div class="sx-point-head">
                <div>
                    <div class="sx-point-name">{escape(point["label"])}</div>
                    <div class="sx-point-meta">{escape(point["housing"])} | Axis {escape(point["axis"])}</div>
                </div>
                {severity_badge(severity)}
            </div>
            <div class="sx-point-meta">Fault</div>
            <div style="color:#f8fafc;font-weight:800;">{escape(fault_text)}</div>
            <div class="sx-readings">
                <div class="sx-reading"><span>RMS</span><strong>{point["RMS"]:.2f} g</strong></div>
                <div class="sx-reading"><span>Health</span><strong>{point["HealthScore"]:.0f}%</strong></div>
                <div class="sx-reading"><span>Peak Amp</span><strong>{point["PeakAmp"]:.2f}</strong></div>
                <div class="sx-reading"><span>Peak Freq</span><strong>{point["PeakFreq_Hz"]:.1f} Hz</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bench(points):
    by_label = {point["label"]: point for point in points}

    def node(title, subtitle, color="#38bdf8"):
        return (
            f'<div class="sx-node" style="border-top-color:{color};">'
            f"<strong>{escape(title)}</strong><span>{escape(subtitle)}</span></div>"
        )

    bx = by_label["B-X"]
    by = by_label["B-Y"]
    ax = by_label["A-X"]
    ay = by_label["A-Y"]

    html = "".join(
        [
            node("Motor", "2.24 kW drive"),
            node("Torque Meter", "Transmission load"),
            node("Gearbox", "Speed coupling"),
            node(
                "Housing B",
                f"B-X {bx['RMS']:.2f}g | B-Y {by['RMS']:.2f}g",
                SEVERITY_COLORS.get(worst_severity(bx, by), "#94a3b8"),
            ),
            node("Rotor", "Balance zone"),
            node(
                "Housing A",
                f"A-X {ax['RMS']:.2f}g | A-Y {ay['RMS']:.2f}g",
                SEVERITY_COLORS.get(worst_severity(ax, ay), "#94a3b8"),
            ),
            node("Brake", "Load endpoint"),
        ]
    )

    st.markdown(f'<div class="sx-bench">{html}</div>', unsafe_allow_html=True)


def plot_rms(points):
    df = pd.DataFrame(
        {
            "Point": [point["label"] for point in points],
            "RMS": [point["RMS"] for point in points],
            "Severity": [point["Severity"] for point in points],
        }
    )
    fig = px.bar(
        df,
        x="Point",
        y="RMS",
        color="Severity",
        color_discrete_map=SEVERITY_COLORS,
        template="plotly_dark",
        title="Current RMS by Monitoring Point",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=390,
        margin=dict(l=10, r=10, t=54, b=10),
    )
    return fig


def plot_health(points):
    df = pd.DataFrame(
        {
            "Point": [point["label"] for point in points],
            "Health Score": [point["HealthScore"] for point in points],
        }
    )
    fig = px.line(
        df,
        x="Point",
        y="Health Score",
        markers=True,
        template="plotly_dark",
        title="Current Health Distribution",
    )
    fig.update_yaxes(range=[0, 100])
    fig.add_hline(y=80, line_dash="dash", annotation_text="Healthy")
    fig.add_hline(y=50, line_dash="dash", annotation_text="Warning")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=390,
        margin=dict(l=10, r=10, t=54, b=10),
    )
    return fig


def plot_fft(points):
    df = pd.DataFrame(
        {
            "Point": [point["label"] for point in points],
            "Peak Frequency Hz": [point["PeakFreq_Hz"] for point in points],
            "Peak Amplitude": [point["PeakAmp"] for point in points],
        }
    )
    fig = px.scatter(
        df,
        x="Peak Frequency Hz",
        y="Peak Amplitude",
        text="Point",
        size="Peak Amplitude",
        template="plotly_dark",
        title="Current Peak Frequency Map",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=390,
        margin=dict(l=10, r=10, t=54, b=10),
    )
    return fig


def plot_health_gauge(summary):
    value = summary["overall_health"]
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "font": {"color": "#f8fafc"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                "bar": {"color": "#38bdf8"},
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.35)"},
                    {"range": [50, 80], "color": "rgba(245, 158, 11, 0.35)"},
                    {"range": [80, 100], "color": "rgba(34, 197, 94, 0.35)"},
                ],
            },
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def render_overview(points, summary):
    render_kpis(summary)

    left, right = st.columns([1.3, 0.9])
    with left:
        st.markdown('<div class="sx-section-title">Current Monitoring Points</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        for column, point in zip(cols, points):
            with column:
                render_point_card(point)

    with right:
        st.markdown('<div class="sx-section-title">Maintenance Decision</div>', unsafe_allow_html=True)
        profile = summary["profile"]
        st.markdown(
            f"""
            <div class="sx-action">
                <div class="sx-card-label">Active fault profile</div>
                <div class="sx-card-value">{escape(summary["fault"])}</div>
                <div class="sx-card-meta">
                    Location: {escape(profile["location"])}<br>
                    RUL estimate: {summary["rul"]} days<br>
                    Priority: {escape(summary["priority"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(summary["recommendation"])

    st.markdown('<div class="sx-section-title">Current Data Table</div>', unsafe_allow_html=True)
    st.dataframe(points_to_dataframe(points), hide_index=True, width="stretch")


def render_machine_dashboard(points, summary):
    st.markdown('<div class="sx-section-title">Machine Layout</div>', unsafe_allow_html=True)
    render_bench(points)

    st.markdown('<div class="sx-section-title">Point Diagnostics</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for column, point in zip(cols, points):
        with column:
            render_point_card(point)

    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(plot_rms(points), width="stretch")
    with right:
        st.plotly_chart(plot_health_gauge(summary), width="stretch")

    if summary["active_faults"]:
        st.markdown('<div class="sx-section-title">Fault Localization</div>', unsafe_allow_html=True)
        for point in summary["active_faults"]:
            st.error(
                f"{point['label']} | {point['Fault']} | {point['Condition']} | {point['Severity']}"
            )
    else:
        st.success("No active fault reported by the current monitoring points.")


def render_analytics(points):
    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(plot_rms(points), width="stretch")
    with right:
        st.plotly_chart(plot_health(points), width="stretch")

    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(plot_fft(points), width="stretch")
    with right:
        st.markdown('<div class="sx-section-title">Feature Matrix</div>', unsafe_allow_html=True)
        st.dataframe(feature_matrix(points), hide_index=True, width="stretch")

    st.markdown('<div class="sx-section-title">Current Snapshot</div>', unsafe_allow_html=True)
    st.dataframe(points_to_dataframe(points), hide_index=True, width="stretch")


def generate_report(machine_id, machine_name, points, summary, data_mode):
    lines = [
        "SENTINEL-X PREDICTIVE MAINTENANCE REPORT",
        "=" * 52,
        f"Generated at       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Data mode          : {data_mode.upper()}",
        f"Machine ID         : {machine_id}",
        f"Machine Name       : {machine_name}",
        "",
        "GLOBAL STATUS",
        "-" * 52,
        f"Machine status     : {summary['status']}",
        f"Health score       : {summary['overall_health']:.1f} %",
        f"Priority           : {summary['priority']}",
        f"Active fault       : {summary['fault']}",
        f"Fault location     : {summary['profile']['location']}",
        f"Estimated RUL      : {summary['rul']} days",
        f"Average RMS        : {summary['avg_rms']:.3f} g",
        f"Maximum RMS        : {summary['max_rms']:.3f} g",
        f"Velocity RMS       : {summary['velocity_rms']:.3f} mm/s",
        "",
        "RECOMMENDATION",
        "-" * 52,
        summary["recommendation"],
        "",
        "MONITORING POINTS",
        "-" * 52,
    ]

    for point in points:
        lines.extend(
            [
                f"{point['label']} ({point['housing']} / Axis {point['axis']})",
                f"  Fault       : {point['Fault']}",
                f"  Condition   : {point['Condition']}",
                f"  Severity    : {point['Severity']}",
                f"  Health      : {point['HealthScore']:.1f} %",
                f"  RMS         : {point['RMS']:.3f} g",
                f"  Kurtosis    : {point['Kurtosis']:.3f}",
                f"  Skewness    : {point['Skewness']:.3f}",
                f"  CrestFactor : {point['CrestFactor']:.3f}",
                f"  PeakAmp     : {point['PeakAmp']:.3f}",
                f"  PeakFreq    : {point['PeakFreq_Hz']:.3f} Hz",
                "",
            ]
        )

    return "\n".join(lines)


def render_reports(points, summary, machine_id, machine_name, data_mode, raw_payload):
    report_text = generate_report(machine_id, machine_name, points, summary, data_mode)
    current_df = points_to_dataframe(points)

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="sx-section-title">Maintenance Report</div>', unsafe_allow_html=True)
        st.text_area("Report preview", report_text, height=420)
        st.download_button(
            "Download TXT report",
            data=report_text,
            file_name=f"sentinel_x_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            width="stretch",
        )

    with right:
        st.markdown('<div class="sx-section-title">Export Current Data</div>', unsafe_allow_html=True)
        st.download_button(
            "Download current snapshot CSV",
            data=current_df.to_csv(index=False).encode("utf-8"),
            file_name=f"sentinel_x_current_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch",
        )
        st.download_button(
            "Download raw current_data JSON",
            data=json.dumps(raw_payload, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name=f"sentinel_x_current_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch",
        )

        st.markdown('<div class="sx-section-title">Action Checklist</div>', unsafe_allow_html=True)
        if summary["active_faults"]:
            st.checkbox("Inspect faulty monitoring point", value=False)
            st.checkbox("Verify lubrication condition", value=False)
            st.checkbox("Check bearing and coupling condition", value=False)
            st.checkbox("Schedule maintenance intervention", value=False)
        else:
            st.checkbox("Continue normal monitoring", value=True)
            st.checkbox("Keep automatic refresh enabled", value=True)

    with st.expander("Raw current_data payload"):
        st.json(raw_payload)


def render_sidebar():
    st.sidebar.title("Sentinel-X")
    st.sidebar.caption("Current-data maintenance console")

    page = st.sidebar.radio("Navigation", PAGES)
    machine = st.sidebar.selectbox(
        "Machine",
        ["Motor A", "Motor B", "Motor C"],
        index=0,
    )

    st.sidebar.divider()
    auto_refresh = st.sidebar.toggle("Auto refresh", value=True)
    refresh_seconds = st.sidebar.slider("Refresh interval", 3, 30, 5)
    demo_fallback = st.sidebar.toggle("Demo fallback if Firebase fails", value=True)

    if auto_refresh:
        st_autorefresh(
            interval=refresh_seconds * 1000,
            key="sentinel_x_refresh",
        )

    return page, machine, demo_fallback


def main():
    st.set_page_config(
        page_title="Sentinel-X Maintenance Console",
        page_icon="SX",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_theme()

    page, machine, demo_fallback = render_sidebar()
    machine_id = "MTR-001"
    machine_name = f"{machine} | Industrial Motor"
    loaded_at = datetime.now()

    raw_payload, data_mode, data_error = read_current_data(demo_fallback)
    if raw_payload is None:
        st.error("No current data available. Check Firebase credentials and current_data path.")
        if data_error:
            st.code(data_error)
        st.stop()

    points = normalize_payload(deepcopy(raw_payload))
    summary = compute_summary(points)

    render_header(machine_name, summary, data_mode, loaded_at)
    render_data_notice(data_mode, data_error)

    if page == "Overview":
        render_overview(points, summary)
    elif page == "Machine Dashboard":
        render_machine_dashboard(points, summary)
    elif page == "Analytics":
        render_analytics(points)
    else:
        render_reports(points, summary, machine_id, machine_name, data_mode, raw_payload)


if __name__ == "__main__":
    main()
