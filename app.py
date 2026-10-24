import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(page_title="AquaSentinel | Water Network Operations", page_icon="💧", layout="wide", initial_sidebar_state="expanded")

# ----------------------------- Visual system -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#08140f;--panel:#102319;--panel2:#0b1c13;--line:#284735;--muted:#a3b9aa;--lime:#b6f36b;--cyan:#5ee7ed;--red:#ff6f61;--amber:#ffcc66}
.stApp{background:linear-gradient(180deg,#08140f 0%,#0b1c13 100%);color:#e8f3eb;font-family:'Manrope',sans-serif}
[data-testid="stSidebar"]{background:#0b1c13;border-right:1px solid #284735}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:#e8f3eb!important}
p,li,label{color:#c7d8cc}
div[data-testid="stMetric"]{background:#102319;border:1px solid #284735;padding:16px;border-radius:16px;box-shadow:0 2px 8px #00000018}
div[data-testid="stMetricLabel"]{color:#a3b9aa}
div[data-testid="stMetricValue"]{font-family:'DM Mono',monospace;font-size:1.55rem;color:#e8f3eb}
div[data-testid="stAlert"]{border-radius:14px}
.stButton>button{border-radius:11px;border:1px solid #3c6249;min-height:2.65rem;font-weight:700;background:#14281d;color:#eaf8ee}
.stButton>button[kind="primary"]{background:#b6f36b;color:#102018;border:0}
div[data-testid="stDataFrame"]{border:1px solid #284735;border-radius:12px;overflow:hidden}
.as-eyebrow{font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.12em;color:#a3b9aa;font-size:.72rem}
.as-hero{border:1px solid #284735;background:linear-gradient(115deg,#102319,#0b1c13);border-radius:22px;padding:24px 28px;margin-bottom:16px;box-shadow:0 5px 22px #00000018}
.as-pulse{display:inline-block;width:8px;height:8px;border-radius:50%;background:#b6f36b;box-shadow:0 0 0 5px #b6f36b1c;margin-right:8px}
.as-card{border:1px solid #284735;background:#102319;border-radius:15px;padding:16px;box-shadow:0 2px 8px #00000012}
.as-muted{color:#a3b9aa;font-size:.86rem}
.as-big{font-size:1.3rem;font-weight:800}
[data-testid="stRadio"] label{padding:7px 10px;border-radius:10px}
[data-testid="stRadio"] label:hover{background:#173d28}
[data-testid="stPlotlyChart"]{background:#0b1c13;border:1px solid #284735;border-radius:16px;padding:8px}
[data-testid="stMarkdownContainer"] a{color:#b6f36b}
[data-testid="stSelectbox"] div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#102319;color:#e8f3eb;border-color:#284735}
[data-testid="stDataFrame"] *{color:#e8f3eb}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Session state -----------------------------
defaults = {
    "scenario": "Active leak • Segment B–C",
    "repair_state": "Open",
    "crew": "North Response Team",
    "events": [],
    "alarm_enabled": False,
    "scenario_nonce": 0,
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ----------------------------- Sidebar controls -----------------------------
with st.sidebar:
    st.markdown("<div class='as-eyebrow'>AQUASENTINEL / CONTROL ROOM</div>", unsafe_allow_html=True)
    st.title("Mission controls")
    scenarios = ["Active leak • Segment B–C", "Normal network", "Demand surge", "Sensor failure", "Pipe burst • Segment C–D"]
    scenario = st.selectbox("Incident scenario", scenarios, index=scenarios.index(st.session_state.scenario))
    st.session_state.scenario = scenario
    severity = st.slider("Leak severity", 1, 10, 7, help="Controls the simulated size of the leak event.")
    noise = st.slider("Sensor noise", 0, 20, 5, help="Adds realistic-looking variation to simulated telemetry.")
    st.session_state.crew = st.selectbox("Response crew", ["North Response Team", "South Response Team", "Rapid Repair Unit"])
    st.markdown("---")
    st.markdown("**Demo controls**")
    if st.button("↻ Reset incident", use_container_width=True):
        st.session_state.repair_state = "Open"
        st.session_state.events = []
        st.session_state.scenario_nonce += 1
        st.rerun()
    st.markdown("<div class='as-muted'>Data source: deterministic scenario simulator<br>Detection: explainable rules, not trained AI<br>Physical sensors: not connected</div>", unsafe_allow_html=True)

# ----------------------------- Simulated telemetry model -----------------------------
rng = np.random.default_rng(20261023 + st.session_state.scenario_nonce + severity + int(datetime.now().timestamp() // 10))
n = 90
times = pd.date_range(end=datetime.now(), periods=n, freq="10s")
p = np.full(n, 3.15, dtype=float)
qin = np.full(n, 24.0, dtype=float)
qout = np.full(n, 23.4, dtype=float)
acoustic = np.full(n, 0.12, dtype=float)
if scenario == "Active leak • Segment B–C":
    p[54:] = 3.15 - .13*severity
    qin[54:] = 24 + .65*severity
    qout[54:] = 23.4 - .08*severity
    acoustic[54:] = .12 + .075*severity
elif scenario == "Pipe burst • Segment C–D":
    p[54:] = 3.15 - .22*severity
    qin[54:] = 24 + 1.0*severity
    qout[54:] = 23.4 - .18*severity
    acoustic[54:] = .12 + .11*severity
elif scenario == "Demand surge":
    p[54:] = 2.5
    qin[54:] = 30
    qout[54:] = 29.5
    acoustic[54:] = .18
elif scenario == "Sensor failure":
    p[76:] = np.nan
    qin[76:] = np.nan
    qout[76:] = np.nan
    acoustic[76:] = np.nan
p += rng.normal(0, noise*.004, n)
qin += rng.normal(0, noise*.035, n)
qout += rng.normal(0, noise*.035, n)
acoustic += rng.normal(0, noise*.0015, n)
if st.session_state.repair_state in ("Repaired", "Verified") and scenario in ("Active leak • Segment B–C", "Pipe burst • Segment C–D"):
    p[70:] = 3.12 + rng.normal(0, .025, n-70)
    qin[70:] = 24 + rng.normal(0, .10, n-70)
    qout[70:] = 23.4 + rng.normal(0, .10, n-70)
    acoustic[70:] = .13 + rng.normal(0, .01, n-70)

df = pd.DataFrame({"Time":times, "Pressure (bar)":p, "Inlet flow (L/s)":qin, "Outlet flow (L/s)":qout, "Acoustic anomaly":acoustic})
fault = scenario == "Sensor failure"
leak_scenario = scenario in ("Active leak • Segment B–C", "Pipe burst • Segment C–D")
is_repaired = st.session_state.repair_state in ("Repaired", "Verified") and leak_scenario
if fault:
    status, severity_label, segment = "SENSOR FAULT", "CRITICAL", "Node D"
    explanation = "Telemetry has dropped out. The system isolates the data-quality incident instead of falsely calling missing readings a leak."
elif leak_scenario and not is_repaired:
    status = "PIPE BURST SUSPECTED" if scenario.startswith("Pipe burst") else "LEAK SUSPECTED"
    severity_label = "CRITICAL" if scenario.startswith("Pipe burst") or severity >= 8 else "HIGH"
    segment = "C–D" if scenario.startswith("Pipe burst") else "B–C"
    explanation = "Sustained pressure deviation + inlet/outlet imbalance + acoustic anomaly exceed the scenario's configured rule thresholds."
elif scenario == "Demand surge":
    status, severity_label, segment = "DEMAND ANOMALY", "MEDIUM", "Network-wide"
    explanation = "Flow rises while inlet/outlet remain broadly balanced. This is treated as a demand event, not confirmed leakage."
elif is_repaired:
    status, severity_label, segment = "REPAIR VERIFIED", "RESOLVED", "B–C" if scenario.startswith("Active leak") else "C–D"
    explanation = "Simulated post-repair pressure and flow return to the baseline envelope. Field verification would still be required in a real deployment."
else:
    status, severity_label, segment = "NETWORK NORMAL", "LOW", "—"
    explanation = "Pressure, flow balance and acoustic indicator are within the configured baseline envelope."

# Reset workflow state to open when user changes scenario (except same)
if "last_scenario" not in st.session_state: st.session_state.last_scenario = scenario
if st.session_state.last_scenario != scenario:
    st.session_state.last_scenario = scenario
    st.session_state.repair_state = "Open"
    st.session_state.events = []

latest_p = p[~np.isnan(p)][-1] if np.any(~np.isnan(p)) else np.nan
latest_in = qin[~np.isnan(qin)][-1] if np.any(~np.isnan(qin)) else np.nan
latest_out = qout[~np.isnan(qout)][-1] if np.any(~np.isnan(qout)) else np.nan
imbalance = max(0, latest_in-latest_out) if np.isfinite(latest_in) and np.isfinite(latest_out) else np.nan
# Illustrative estimate, explicitly tied to the simulated flow difference
estimated_loss_l_min = max(0, float(np.nanmean(qin[-10:]-qout[-10:]))) * 60 if not fault else np.nan

# ----------------------------- Hero -----------------------------
st.markdown(f"""
<div class="as-hero">
 <div class="as-eyebrow"><span class="as-pulse"></span>WATER NETWORK DIGITAL TWIN • INCIDENT RESPONSE</div>
 <h1 style="font-size:2.35rem;margin:.35rem 0 .25rem">AquaSentinel</h1>
 <div style="font-size:1.02rem;color:#c1d7c7">From invisible leakage to an actionable repair workflow.</div>
 <div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">
  <span style="border:1px solid #42664a;border-radius:100px;padding:5px 10px;font-size:.78rem">02 / Anomaly triage</span>
  <span style="border:1px solid #42664a;border-radius:100px;padding:5px 10px;font-size:.78rem">03 / Locate segment</span>
  <span style="border:1px solid #42664a;border-radius:100px;padding:5px 10px;font-size:.78rem">04 / Repair & verify</span>
 </div>
</div>
""", unsafe_allow_html=True)
clock_cols = st.columns([1, 1])
with clock_cols[0]:
    st.markdown("<div class='as-muted'>LIVE SYSTEM CLOCK · LOCAL DEVICE TIME</div>", unsafe_allow_html=True)
with clock_cols[1]:
    components.html("""<div style='text-align:right;font:600 18px ui-monospace,monospace;color:#167d69'><span id='as-clock'>--:--:--</span><div style='font:12px system-ui;color:#667580;margin-top:3px' id='as-date'>Synchronizing local time…</div></div><script>function tick(){const d=new Date();document.getElementById('as-clock').textContent=d.toLocaleTimeString();document.getElementById('as-date').textContent=d.toLocaleDateString(undefined,{weekday:'short',year:'numeric',month:'short',day:'numeric'});}tick();setInterval(tick,1000);</script>""", height=48)

if status in ("LEAK SUSPECTED","PIPE BURST SUSPECTED"):
    st.error(f"🚨 {status}  •  Segment {segment}  •  Severity {severity_label}")
elif status == "SENSOR FAULT":
    st.warning("⚠️ SENSOR FAULT • Telemetry integrity compromised — investigate node before leak classification.")
elif status == "DEMAND ANOMALY":
    st.warning("◈ DEMAND ANOMALY • Demand surge detected; leak not confirmed.")
elif status == "REPAIR VERIFIED":
    st.success("✓ REPAIR VERIFIED • Simulated readings returned to baseline.")
else:
    st.success("✓ NETWORK NORMAL • No active anomaly in this scenario.")

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Pressure", "—" if fault else f"{latest_p:.2f} bar", "sensor telemetry")
m2.metric("Inlet flow", "—" if fault else f"{latest_in:.1f} L/s", "simulated")
m3.metric("Outlet flow", "—" if fault else f"{latest_out:.1f} L/s", "simulated")
m4.metric("Flow imbalance", "—" if fault else f"{imbalance:.2f} L/s", "inlet − outlet")
m5.metric("Telemetry quality", "DEGRADED" if fault else "VALID", "input integrity gate")

st.markdown(f"<div class='as-muted'>Current assessment: {explanation} &nbsp; • &nbsp; Selected scenario: {scenario}</div>", unsafe_allow_html=True)

# ----------------------------- Main navigation -----------------------------
PAGE_NAMES = ["Overview", "Live pipe twin", "Network map", "Repair operations", "Detection engine", "Leak localization", "Components guide", "Real-world water loss & research"]
with st.sidebar:
    st.markdown("<div class='as-eyebrow'>WORKSPACE</div>", unsafe_allow_html=True)
    page = st.radio("Navigate AquaSentinel", PAGE_NAMES, index=0, label_visibility="collapsed", key="main_navigation")
    st.markdown("<div class='as-muted' style='padding:8px 10px'>Overview → Investigate → Locate → Respond</div>", unsafe_allow_html=True)

if page == "Overview":
    left, right = st.columns([1.7,1])
    with left:
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Scatter(x=df["Time"], y=df["Pressure (bar)"], name="Pressure (bar)", line=dict(color="#167d69",width=3), connectgaps=False), secondary_y=False)
        fig.add_trace(go.Scatter(x=df["Time"], y=df["Inlet flow (L/s)"], name="Inlet flow (L/s)", line=dict(color="#2d8293",width=2.5), connectgaps=False), secondary_y=True)
        fig.add_trace(go.Scatter(x=df["Time"], y=df["Outlet flow (L/s)"], name="Outlet flow (L/s)", line=dict(color="#bd8536",width=2.5,dash="dot"), connectgaps=False), secondary_y=True)
        fig.add_vline(x=times[54], line_dash="dash", line_color="#ff6f61", annotation_text="Scenario event", annotation_position="top")
        fig.update_layout(title=dict(text="Telemetry stream · 15-minute scenario window", x=0.02, y=0.99, xanchor="left", yanchor="top", pad=dict(b=16)), height=610, paper_bgcolor="#0b1c13", plot_bgcolor="#0b1c13", font_color="#e8f3eb", margin=dict(l=24,r=24,t=112,b=28), legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="left", x=0), hovermode="x unified")
        fig.update_xaxes(gridcolor="#284735")
        fig.update_yaxes(title_text="Pressure (bar)", gridcolor="#284735", secondary_y=False)
        fig.update_yaxes(title_text="Flow (L/s)", secondary_y=True)
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=1.06, xanchor="left", x=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Decision trace")
        checks = [
            ("Pressure deviation", "TRIGGERED" if leak_scenario and not is_repaired else "CLEAR" if not fault else "NO DATA", "Δ from 3.15 bar baseline"),
            ("Inlet/outlet balance", "TRIGGERED" if leak_scenario and not is_repaired else "CLEAR" if not fault else "NO DATA", "Compare upstream and downstream"),
            ("Acoustic signature", "TRIGGERED" if leak_scenario and not is_repaired else "CLEAR" if not fault else "NO DATA", "Simulated anomaly indicator"),
            ("Sensor integrity", "FAULT" if fault else "OK", "Missing telemetry check"),
        ]
        for title,flag,detail in checks:
            color = "#ff6f61" if flag in ("TRIGGERED","FAULT") else "#b6f36b" if flag=="CLEAR" or flag=="OK" else "#ffcc66"
            st.markdown(f"<div class='as-card' style='margin-bottom:8px'><div style='display:flex;justify-content:space-between;gap:8px'><b>{title}</b><span style='color:{color};font-family:monospace'>{flag}</span></div><div class='as-muted'>{detail}</div></div>", unsafe_allow_html=True)
        st.caption("Telemetry quality reports whether the selected scenario has usable input channels. It is not a leak probability; classifications are explained in the Detection Engine.")
    st.markdown("### Incident timeline")
    st.caption("Read the chart left to right: baseline → injected scenario change → response. Pressure is on the left axis; flow is on the right axis.")
    event_rows = [
        {"Time": times[54].strftime("%H:%M:%S"), "Event": "Scenario change injected", "System response": "Telemetry pattern changes"},
        {"Time": (times[54]+timedelta(seconds=10)).strftime("%H:%M:%S"), "Event": "Rule engine evaluates signals", "System response": status},
        {"Time": (times[54]+timedelta(seconds=20)).strftime("%H:%M:%S"), "Event": "Triage / location hint", "System response": f"Segment {segment}"},
    ]
    if st.session_state.events:
        event_rows += st.session_state.events
    st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)

if page == "Live pipe twin":
    st.markdown("### Interactive pipeline digital twin")
    st.markdown("<div class='as-card'><b>Live incident experience</b><br><span class='as-muted'>Enable sound, trigger a leak or burst, inspect the changing indicators, then repair and verify recovery. Leak and burst use different synthesized sound profiles.</span></div>", unsafe_allow_html=True)
    st.caption("Trigger a leak and observe the pipeline, sensor response, alert and repair-state transition. This is an animated simulation, not a physical feed.")
    initial_leak = "true" if leak_scenario and not is_repaired else "false"
    components.html(r"""
<div id="aqua-twin" style="font-family:Arial,sans-serif;background:#08140f;color:#e8f3eb;border:1px solid #2a4d38;border-radius:18px;padding:16px">
<style>
#aqua-twin *{box-sizing:border-box}#aqua-twin .bar{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px}
#aqua-twin .badge{border-radius:999px;padding:7px 12px;font:bold 12px monospace;background:#133421;color:#b6f36b;border:1px solid #2c6b43}
#aqua-twin .badge.red{background:#391916;color:#ffb5aa;border-color:#a7483b}
#aqua-twin button{padding:11px 14px;border-radius:9px;border:1px solid #3c6249;background:#14281d;color:#eaf8ee;font-weight:bold;cursor:pointer}
#aqua-twin button.primary{background:#b6f36b;color:#102018;border-color:#b6f36b}
#aqua-twin .btns{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
#aqua-twin .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:12px}
#aqua-twin .stat{padding:12px;border:1px solid #284735;background:#102319;border-radius:11px}
#aqua-twin .muted{color:#a3b9aa;font-size:12px}#aqua-twin .val{font-size:22px;font-weight:800;margin-top:5px}
#aqua-twin svg{width:100%;height:auto;background:#0a1b13;border-radius:12px}
@media(max-width:600px){#aqua-twin .grid{grid-template-columns:1fr}}
</style>
<div class="bar"><div><div style="font-size:20px;font-weight:800;color:#c5f78b">PIPELINE / NODE B–C</div><div class="muted">Pressure + flow + acoustic anomaly fusion</div></div><div id="twBadge" class="badge">SYSTEM NORMAL</div></div>
<div class="btns"><button id="twLeak" class="primary" type="button">⚠ Trigger leak</button><button id="twBurst" type="button">💥 Simulate burst</button><button id="twRepair" type="button">🔧 Repair & verify</button><button id="twReset" type="button">↻ Reset</button><button id="twSound" type="button">🔊 Enable alarm</button></div>
<svg viewBox="0 0 960 410" role="img" aria-label="Animated pipeline showing reservoir, sensors, flow direction, leak spray and response alarm">
<defs><linearGradient id="metal" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#b4c6c4"/><stop offset=".3" stop-color="#526c6b"/><stop offset=".7" stop-color="#304544"/><stop offset="1" stop-color="#94aaa7"/></linearGradient><linearGradient id="waterfill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#6bf0f3"/><stop offset="1" stop-color="#087db4"/></linearGradient><clipPath id="pipeclip"><rect x="75" y="155" width="810" height="82" rx="18"/></clipPath></defs>
<rect x="14" y="14" width="932" height="382" rx="14" fill="#0b1c13" stroke="#244333"/>
<text x="35" y="44" fill="#b6f36b" font-size="14" font-family="monospace">DISTRIBUTION MAIN • SCHEMATIC</text>
<g transform="translate(38 108)"><path d="M0 0 h65 v118 h-65 z" fill="#153a2a" stroke="#7ca58a" stroke-width="2"/><path d="M6 48 h53 v64 h-53 z" fill="#137eb1"/><text x="32" y="-12" text-anchor="middle" fill="#eaf8ee" font-size="12">RESERVOIR</text></g>
<rect x="75" y="148" width="810" height="96" rx="20" fill="url(#metal)" stroke="#c2d0cb" stroke-width="2"/>
<rect x="85" y="159" width="790" height="74" rx="14" fill="url(#waterfill)" clip-path="url(#pipeclip)"/>
<g id="twDots" fill="#e2ffff"><circle cx="105" cy="178" r="4"/><circle cx="165" cy="212" r="4"/><circle cx="225" cy="180" r="4"/><circle cx="285" cy="212" r="4"/><circle cx="345" cy="180" r="4"/><circle cx="405" cy="212" r="4"/><circle cx="465" cy="180" r="4"/><circle cx="525" cy="212" r="4"/><circle cx="585" cy="180" r="4"/><circle cx="645" cy="212" r="4"/><circle cx="705" cy="180" r="4"/><circle cx="765" cy="212" r="4"/><circle cx="825" cy="180" r="4"/></g>
<g id="twA"><rect x="250" y="70" width="118" height="58" rx="9" fill="#173d28" stroke="#b6f36b" stroke-width="2"/><text x="309" y="91" text-anchor="middle" fill="#f1fff4" font-size="12" font-weight="bold">PRESSURE</text><text x="309" y="109" text-anchor="middle" fill="#b6f36b" font-size="12">NODE A</text><path d="M309 128 V148" stroke="#b6f36b" stroke-width="4"/></g>
<g id="twB"><rect x="648" y="70" width="118" height="58" rx="9" fill="#173d28" stroke="#b6f36b" stroke-width="2"/><text x="707" y="91" text-anchor="middle" fill="#f1fff4" font-size="12" font-weight="bold">PRESSURE</text><text x="707" y="109" text-anchor="middle" fill="#b6f36b" font-size="12">NODE B</text><path d="M707 128 V148" stroke="#b6f36b" stroke-width="4"/></g>
<g id="twLeakPoint"><path d="M610 244 v34" stroke="#cad9d5" stroke-width="18"/><path d="M610 244 v34" stroke="#138bc0" stroke-width="10"/><g id="twSpray" opacity="0"><path d="M610 270 Q580 288 558 309 M610 270 Q615 302 618 326 M610 270 Q646 288 671 306" fill="none" stroke="#60e8ff" stroke-width="6" stroke-linecap="round"/><circle class="drop" cx="556" cy="310" r="5" fill="#b5f7ff"/><circle class="drop" cx="618" cy="327" r="5" fill="#b5f7ff"/><circle class="drop" cx="672" cy="307" r="5" fill="#b5f7ff"/></g><text x="610" y="356" text-anchor="middle" fill="#ff9f91" font-size="14" font-weight="bold">LEAK POINT</text></g>
<g id="twAlarm" transform="translate(790 57)"><rect width="112" height="70" rx="10" fill="#1b2a20" stroke="#4e7657"/><circle id="twLamp" cx="24" cy="25" r="10" fill="#9bea55"/><path d="M49 20 q13 10 0 20 M57 13 q22 17 0 34" fill="none" stroke="#9bea55" stroke-width="3"/><text x="58" y="58" text-anchor="middle" fill="#e8f3eb" font-size="10">ALARM NODE</text></g>
<text x="90" y="282" fill="#9fb9aa" font-size="12">Water flow →</text><path d="M90 294 h100 l-12 -7 m12 7 l-12 7" fill="none" stroke="#5ee7ed" stroke-width="3"/>
<text x="40" y="378" fill="#a3b9aa" font-size="11">Sensor telemetry is simulated • no physical devices connected</text>
</svg>
<div id="twMsg" class="stat" style="margin-top:10px">Normal operation: pressure and flow remain within baseline.</div>
<div class="grid"><div class="stat"><div class="muted">Pressure</div><div id="twPressure" class="val">3.15 bar</div></div><div class="stat"><div class="muted">Flow imbalance</div><div id="twFlow" class="val">0.60 L/s</div></div><div class="stat"><div class="muted">Detection state</div><div id="twDetect" class="val">NORMAL</div></div></div>
<div class="muted" style="margin-top:10px">Use “Trigger leak” or “Simulate burst” to see the system response. “Repair & verify” resets the simulated readings. Sound is synthesized in-browser: leak = rushing-water hiss + warning pulse; burst = deeper pressure thump + stronger rapid alarm. Click Enable sound first (browser audio permission).</div>
<script>
(function(){
const r=document.getElementById('aqua-twin');if(!r||r.dataset.ready)return;r.dataset.ready='1';
const q=id=>r.querySelector('#'+id);let mode=__MODE__,sound=false,ctx=null,alarmTimer=null,noiseNode=null,noiseGain=null,noiseFilter=null,rumble=null,rumbleGain=null,alarmNodes=[];
function stopAudio(){if(alarmTimer){clearInterval(alarmTimer);alarmTimer=null}try{if(noiseGain)noiseGain.gain.setTargetAtTime(0,ctx.currentTime,.08);if(rumbleGain)rumbleGain.gain.setTargetAtTime(0,ctx.currentTime,.08);alarmNodes.forEach(n=>{try{n.stop()}catch(e){}});alarmNodes=[]}catch(e){}if(noiseNode){try{noiseNode.stop()}catch(e){}noiseNode=null}noiseGain=null;noiseFilter=null;rumble=null;rumbleGain=null}
function tone(freq,duration,volume,wave='sine'){if(!sound||!ctx)return;try{const o=ctx.createOscillator(),g=ctx.createGain();o.type=wave;o.frequency.setValueAtTime(freq,ctx.currentTime);g.gain.setValueAtTime(.0001,ctx.currentTime);g.gain.exponentialRampToValueAtTime(volume,ctx.currentTime+.025);g.gain.exponentialRampToValueAtTime(.0001,ctx.currentTime+duration);o.connect(g);g.connect(ctx.destination);o.start();o.stop(ctx.currentTime+duration+.03);alarmNodes.push(o);o.onended=()=>{alarmNodes=alarmNodes.filter(n=>n!==o)}}catch(e){}}
function startAudio(){stopAudio();if(!sound||!ctx||(mode!=='leak'&&mode!=='burst'))return;try{const len=2*ctx.sampleRate,buf=ctx.createBuffer(1,len,ctx.sampleRate),data=buf.getChannelData(0);for(let i=0;i<len;i++)data[i]=(Math.random()*2-1)*(.55+.45*Math.random());noiseNode=ctx.createBufferSource();noiseNode.buffer=buf;noiseNode.loop=true;noiseFilter=ctx.createBiquadFilter();noiseFilter.type='lowpass';noiseFilter.frequency.value=mode==='burst'?1450:2350;noiseGain=ctx.createGain();noiseGain.gain.value=mode==='burst'?.11:.045;noiseNode.connect(noiseFilter);noiseFilter.connect(noiseGain);noiseGain.connect(ctx.destination);noiseNode.start();rumble=ctx.createOscillator();rumble.type='sawtooth';rumble.frequency.value=mode==='burst'?54:78;rumbleGain=ctx.createGain();rumbleGain.gain.value=mode==='burst'?.045:.012;rumble.connect(rumbleGain);rumbleGain.connect(ctx.destination);rumble.start();if(mode==='burst'){tone(95,.7,.22,'triangle');tone(170,.45,.12,'sawtooth')}let phase=0;const pulse=()=>{if(!sound||!ctx)return;phase++;if(mode==='burst'){tone(880,.22,.055,'square');setTimeout(()=>tone(660,.22,.045,'square'),230)}else{tone(740,.12,.035,'sine');setTimeout(()=>tone(590,.12,.03,'sine'),180)}};pulse();alarmTimer=setInterval(pulse,mode==='burst'?760:1250)}catch(e){q('twMsg').textContent+=' Audio could not start in this browser.'}}
function draw(){const bad=mode==='leak'||mode==='burst';q('twSpray').setAttribute('opacity',bad?'1':'0');q('twBadge').className='badge'+(bad?' red':'');q('twBadge').textContent=mode==='burst'?'PIPE BURST SUSPECTED':mode==='leak'?'LEAK SUSPECTED':mode==='repaired'?'REPAIR VERIFIED':'SYSTEM NORMAL';q('twMsg').textContent=mode==='burst'?'CRITICAL: rapid pressure collapse + flow imbalance. Isolate Segment C–D and dispatch rapid response.':mode==='leak'?'ALERT: pressure drop, flow imbalance and acoustic anomaly indicate a suspected leak at Segment B–C.':mode==='repaired'?'Repair action simulated. Pressure and flow returned to baseline; verification complete.':'Normal operation: pressure and flow remain within baseline.';q('twPressure').textContent=bad?(mode==='burst'?'1.05 bar':'2.05 bar'):'3.15 bar';q('twFlow').textContent=bad?(mode==='burst'?'8.40 L/s':'3.20 L/s'):'0.60 L/s';q('twDetect').textContent=mode==='burst'?'CRITICAL':mode==='leak'?'LEAK ALERT':mode==='repaired'?'VERIFIED':'NORMAL';q('twLamp').setAttribute('fill',bad?'#ff6f61':'#9bea55');q('twB').querySelector('rect').setAttribute('stroke',bad?'#ff6f61':'#b6f36b');if(bad&&sound&&ctx){startAudio()}else if(!bad){stopAudio()}}
q('twLeak').onclick=()=>{mode='leak';draw()};q('twBurst').onclick=()=>{mode='burst';draw()};q('twRepair').onclick=()=>{mode='repaired';draw()};q('twReset').onclick=()=>{mode='normal';draw()};q('twSound').onclick=async()=>{if(!sound){try{const AC=window.AudioContext||window.webkitAudioContext;ctx=new AC();await ctx.resume();sound=true;q('twSound').textContent='🔇 Disable sound';q('twSound').setAttribute('aria-pressed','true');draw();if(mode==='normal')q('twMsg').textContent='Sound enabled. Trigger a leak or burst to hear distinct water turbulence and alarm tones.'}catch(e){q('twMsg').textContent='Audio is unavailable in this browser. Try Chrome/Edge and check device volume.'}}else{sound=false;stopAudio();q('twSound').textContent='🔊 Enable sound';q('twSound').setAttribute('aria-pressed','false')}};
function anim(){r.querySelectorAll('#twDots circle').forEach(c=>{let x=+c.getAttribute('cx')+1.4;if(x>865)x=95;c.setAttribute('cx',x)});r.querySelectorAll('.drop').forEach(d=>{if(mode==='leak'||mode==='burst'){let y=+d.getAttribute('cy')+(mode==='burst'?2.6:1.7);if(y>345)y=305;d.setAttribute('cy',y)}});requestAnimationFrame(anim)}draw();anim()})();
</script>
""".replace("__MODE__", "'leak'" if leak_scenario and not is_repaired else "'normal'"), height=700, scrolling=False)
    st.markdown("#### What the animation represents")
    st.markdown("- **Pressure node:** detects sustained pressure change.\n- **Flow balance:** compares inlet and outlet flow.\n- **Alarm state:** triggers when multiple simulated indicators agree.\n- **Repair & verify:** restores simulated baseline and closes the incident workflow.")

if page == "Network map":
    st.markdown("### Network topology / probable fault zone")
    st.caption("Schematic network map; nodes and distances are illustrative.")
    nodes = pd.DataFrame({
        "Node":["Reservoir","A • upstream","B • monitor","C • monitor","D • downstream"],
        "x":[0,1.3,2.8,4.4,6.0],"y":[0,0.2,0.1,-0.1,0.2],
        "role":["Supply","Pressure node","Pressure + flow","Pressure + acoustic","Downstream check"],
        "status":["Supply","Normal","Alert" if segment=="B–C" and leak_scenario and not is_repaired else "Monitoring","Alert" if segment=="C–D" and leak_scenario and not is_repaired else "Monitoring","Monitoring"]
    })
    figmap=go.Figure()
    for i in range(len(nodes)-1):
        seg_alert = (segment=="B–C" and i==2) or (segment=="C–D" and i==3)
        figmap.add_trace(go.Scatter(x=[nodes.x[i],nodes.x[i+1]],y=[nodes.y[i],nodes.y[i+1]],mode="lines",line=dict(color="#c94f4f" if seg_alert and not is_repaired else "#2d8293",width=7 if seg_alert else 4),showlegend=False,hoverinfo="skip"))
    colors=["#b6f36b" if s not in ("Alert",) else "#ff6f61" for s in nodes.status]
    figmap.add_trace(go.Scatter(x=nodes.x,y=nodes.y,mode="markers+text",text=nodes.Node,textposition="top center",marker=dict(size=[24,20,24,24,20],color=colors,line=dict(color="#e8f3eb",width=1.5)),customdata=nodes[["role","status"]],hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>",showlegend=False))
    figmap.update_layout(height=390,paper_bgcolor="#0b1c13",plot_bgcolor="#0b1c13",font_color="#e8f3eb",margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(visible=False),yaxis=dict(visible=False),title=f"Suspected zone: Segment {segment}")
    st.plotly_chart(figmap,use_container_width=True)
    st.info(f"Suggested inspection zone: Segment {segment}. This scenario selects a segment; precise field localization requires synchronized measurements and site validation.")
    st.dataframe(nodes[["Node","role","status"]],use_container_width=True,hide_index=True)

if page == "Repair operations":
    st.markdown("### Incident response / digital work order")
    st.markdown(f"<div class='as-card'><div class='as-eyebrow'>CURRENT INCIDENT</div><div style='font-size:1.35rem;font-weight:800;margin:6px 0'>{status}</div><div class='as-muted'>Segment {segment} • Severity {severity_label} • Crew: {st.session_state.crew}</div></div>",unsafe_allow_html=True)
    st.markdown("### Underground network explorer")
    st.caption("Explore a street basemap with an underground pipe overlay. Zoom in to inspect pipe bends, junctions and sensor locations. Routes and coordinates are illustrative, not a verified municipal asset map.")
    active_segment = segment if leak_scenario and not is_repaired else ""
    map_html = r"""<div id="as-map-wrap" style="border:1px solid #284735;border-radius:16px;overflow:hidden;background:#102319;color:#e8f3eb;font-family:Arial,sans-serif">
 <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 14px;background:#102319;border-bottom:1px solid #284735">
  <div><b style="font-size:15px">AquaSentinel · Field view</b><div style="font-size:12px;color:#a3b9aa;margin-top:3px">Street basemap + underground pipe overlay</div></div>
  <div style="font-size:11px;border:1px solid #d7a74c;color:#f1d38c;border-radius:99px;padding:6px 9px">ILLUSTRATIVE NETWORK</div>
 </div>
 <div id="as-leaflet-map" style="height:510px;width:100%;background:#e8e8e8"></div>
 <div style="display:flex;gap:14px;flex-wrap:wrap;padding:10px 14px;font-size:12px;color:#c7d8cc;background:#0b1c13">
  <span><b style="color:#1689b1">━━</b> Water main</span><span><b style="color:#ff6f61">━━</b> Suspected segment</span><span>◉ Pressure sensor</span><span>◆ Flow meter</span><span style="color:#a3b9aa">Tap markers for details · use +/− to zoom</span>
 </div>
</div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function(){
 const el=document.getElementById('as-leaflet-map');
 if(!window.L){el.innerHTML='<div style="padding:24px;color:#17251d">Map library could not load. Check internet access and reload the page.</div>';return;}
 const map=L.map(el,{zoomControl:true,scrollWheelZoom:true}).setView([12.9718,77.5945],16);
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:20,attribution:'© OpenStreetMap contributors'}).addTo(map);
 const pts={reservoir:[12.97235,77.59265],A:[12.97205,77.59325],B:[12.97178,77.59405],C:[12.97120,77.59448],D:[12.97080,77.59520],E:[12.97030,77.59555],F:[12.97005,77.59625]};
 const routes=[['reservoir','A'],['A','B'],['B','C'],['C','D'],['D','E'],['E','F']];
 const active='__ACTIVE_SEGMENT__'; const repaired=__REPAIRED__;
 routes.forEach(r=>{const key=(r[0]==='B'&&r[1]==='C')?'B–C':(r[0]==='C'&&r[1]==='D')?'C–D':'';const hot=!repaired&&active===key;const line=L.polyline([pts[r[0]],pts[r[1]]],{color:hot?'#e44f4f':'#1689b1',weight:8,opacity:.95,lineCap:'round',lineJoin:'round'}).addTo(map);line.bindPopup('<b>Pipe segment '+r[0]+'–'+r[1]+'</b><br>'+(hot?'Suspected inspection zone':'Distribution main')+'<br><small>Illustrative route · verify in field</small>');});
 function icon(html){return L.divIcon({className:'',html:html,iconSize:[30,30],iconAnchor:[15,15]});}
 const ss='display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:#143d2a;border:3px solid #b6f36b;color:white;font:bold 11px Arial;box-shadow:0 1px 7px #0008';
 [['A','Pressure sensor',pts.A],['B','Pressure + flow node',pts.B],['C','Pressure + acoustic node',pts.C],['D','Downstream check',pts.D]].forEach(x=>L.marker(x[2],{icon:icon('<div style="'+ss+'">'+x[0]+'</div>')}).addTo(map).bindPopup('<b>Node '+x[0]+'</b><br>'+x[1]+'<br><small>Illustrative sensor placement</small>'));
 const ms='display:flex;align-items:center;justify-content:center;width:25px;height:25px;border-radius:6px;background:#f3c65e;border:2px solid #fff;color:#17251d;font:bold 12px Arial;box-shadow:0 1px 7px #0008';
 [['IN · flow meter',pts.A],['OUT · flow meter',pts.D]].forEach(x=>L.marker(x[1],{icon:icon('<div style="'+ms+'">F</div>')}).addTo(map).bindPopup('<b>'+x[0]+'</b><br>Conceptual meter location<br><small>Actual installation requires hydraulic design</small>'));
 if(active){const lp=pts[active==='C–D'?'D':'C'];L.circleMarker(lp,{radius:10,color:'#fff',weight:2,fillColor:'#ff4f4f',fillOpacity:1}).addTo(map).bindPopup('<b>Suspected incident area</b><br>Scenario highlight, not a confirmed real leak.');}
 L.control.scale({imperial:false}).addTo(map);setTimeout(()=>map.invalidateSize(),250);
})();
</script>"""
    map_html = map_html.replace("__ACTIVE_SEGMENT__", active_segment).replace("__REPAIRED__", "true" if is_repaired else "false")
    components.html(map_html, height=625, scrolling=False)
    stages=["Open","Assigned","Repaired","Verified"]
    current=st.session_state.repair_state
    st.markdown("**Workflow:** " + "  →  ".join([f"**[{s}]**" if s==current else s for s in stages]))
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button("1 • Assign crew",use_container_width=True):
            st.session_state.repair_state="Assigned"
            st.session_state.events.append({"Time":datetime.now().strftime("%H:%M:%S"),"Event":"Work order assigned","System response":st.session_state.crew})
            st.rerun()
    with c2:
        if st.button("2 • Mark repaired",use_container_width=True):
            st.session_state.repair_state="Repaired"
            st.session_state.events.append({"Time":datetime.now().strftime("%H:%M:%S"),"Event":"Crew marked repair complete","System response":"Awaiting verification"})
            st.rerun()
    with c3:
        if st.button("3 • Verify baseline",type="primary",use_container_width=True):
            st.session_state.repair_state="Verified"
            st.session_state.events.append({"Time":datetime.now().strftime("%H:%M:%S"),"Event":"Post-repair check completed","System response":"Simulated baseline restored"})
            st.rerun()
    if current=="Verified":
        st.success("Incident closed in the simulated workflow. For field use, require stable pressure/flow and crew confirmation before closing.")
    elif current=="Assigned":
        st.info("Crew assigned. Next: mark the repair completed after the simulated intervention.")
    elif current=="Repaired":
        st.warning("Repair marked complete. Run baseline verification before closing the ticket.")
    else:
        st.caption("Start by assigning a crew. This demo logs each workflow transition.")
    if st.session_state.events:
        st.markdown("#### Audit trail")
        st.dataframe(pd.DataFrame(st.session_state.events[::-1]),use_container_width=True,hide_index=True)
    st.markdown("#### Response playbook")
    st.markdown("- **Suspected leak:** inspect the indicated segment and confirm with field measurements.\n- **Pipe burst:** prioritize isolation and urgent crew dispatch.\n- **Sensor fault:** restore telemetry before deciding whether leakage exists.\n- **Demand surge:** compare operational schedule and inlet/outlet balance before classifying as a leak.")

if page == "Detection engine":
    st.markdown("### Explainable detection engine")
    st.caption("A transparent, configurable rule engine operating on synthetic telemetry. The test bench below generates labelled synthetic cases and evaluates the same classifier; these are simulation metrics, not field-performance claims.")

    st.markdown("""
    <div class="as-card">
      <div class="as-eyebrow">DECISION PIPELINE</div>
      <div style="font-size:1.05rem;font-weight:800;margin:8px 0;color:#b6f36b">Data quality gate → event severity → leak evidence fusion → classification → action recommendation</div>
      <div class="as-muted">Missing/stale readings are handled before leak classification. A demand surge is separated from a leak when inlet and outlet flow rise together without persistent imbalance. Burst classification requires a stronger pressure collapse and flow mismatch.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        th_pressure = st.slider("Pressure drop threshold (bar)", 0.10, 1.50, 0.35, 0.05, key="eng_pressure")
        th_flow = st.slider("Flow imbalance threshold (L/s)", 0.50, 8.00, 2.00, 0.25, key="eng_flow")
    with c2:
        th_acoustic = st.slider("Acoustic anomaly threshold", 0.20, 1.50, 0.55, 0.05, key="eng_acoustic")
        th_burst_pressure = st.slider("Burst pressure drop (bar)", 0.50, 2.50, 1.00, 0.05, key="eng_burst_pressure")
    with c3:
        th_burst_flow = st.slider("Burst flow imbalance (L/s)", 2.00, 12.00, 5.00, 0.25, key="eng_burst_flow")
        th_demand = st.slider("High-flow demand threshold (L/s)", 25.0, 45.0, 28.0, 0.5, key="eng_demand")

    def classify_case(row):
        if row["telemetry_missing"] or row["sensor_health"] < 0.5:
            return "Sensor fault"
        if row["pressure_drop_bar"] >= th_burst_pressure and row["flow_imbalance_lps"] >= th_burst_flow:
            return "Pipe burst"
        if (row["pressure_drop_bar"] >= th_pressure and
            row["flow_imbalance_lps"] >= th_flow and
            row["acoustic_index"] >= th_acoustic):
            return "Leak suspected"
        if row["mean_flow_lps"] >= th_demand and row["flow_imbalance_lps"] < th_flow:
            return "Demand anomaly"
        return "Normal"

    st.markdown("#### Live decision trace for the selected scenario")
    pressure_drop = max(0.0, 3.15 - float(np.nanmean(p[-10:]))) if np.any(np.isfinite(p[-10:])) else 0.0
    acoustic_latest = float(np.nanmean(acoustic[-10:])) if np.any(np.isfinite(acoustic[-10:])) else 0.0
    mean_flow = float(np.nanmean(qin[-10:])) if np.any(np.isfinite(qin[-10:])) else 0.0
    trace_row = {
        "pressure_drop_bar": pressure_drop,
        "flow_imbalance_lps": float(imbalance) if np.isfinite(imbalance) else 0.0,
        "acoustic_index": acoustic_latest,
        "telemetry_missing": bool(fault),
        "sensor_health": 0.0 if fault else 1.0,
        "mean_flow_lps": mean_flow
    }
    engine_class = classify_case(trace_row)
    trace = pd.DataFrame([
        {"Signal / gate": "Telemetry integrity", "Observed value": "MISSING" if fault else "Available", "Rule / threshold": "Missing data → Sensor fault", "Result": "TRIGGERED" if fault else "PASS"},
        {"Signal / gate": "Pressure drop", "Observed value": f"{pressure_drop:.2f} bar", "Rule / threshold": f"≥ {th_pressure:.2f} bar (leak) / ≥ {th_burst_pressure:.2f} bar (burst)", "Result": "TRIGGERED" if pressure_drop >= th_pressure else "CLEAR"},
        {"Signal / gate": "Flow imbalance", "Observed value": f"{trace_row['flow_imbalance_lps']:.2f} L/s", "Rule / threshold": f"≥ {th_flow:.2f} L/s (leak)", "Result": "TRIGGERED" if trace_row['flow_imbalance_lps'] >= th_flow else "CLEAR"},
        {"Signal / gate": "Acoustic indicator", "Observed value": f"{acoustic_latest:.2f} (simulated)", "Rule / threshold": f"≥ {th_acoustic:.2f}", "Result": "TRIGGERED" if acoustic_latest >= th_acoustic else "CLEAR"},
        {"Signal / gate": "Combined engine output", "Observed value": engine_class, "Rule / threshold": "Priority: sensor fault → burst → leak → demand → normal", "Result": "CLASSIFIED"},
    ])
    st.dataframe(trace, use_container_width=True, hide_index=True)
    st.info(f"Explainable output: **{engine_class}**. This result comes from the configurable rules above. It is not a trained machine-learning prediction.")

    st.markdown("#### Repeatable synthetic test bench")
    st.write("Generate a reproducible set of synthetic labelled cases. Adjusting thresholds changes the classifier and the reported results.")
    n_each = st.slider("Cases per scenario class", 25, 500, 100, 25, key="eng_cases")
    seed = st.number_input("Random seed", min_value=1, max_value=999999, value=42, step=1, key="eng_seed")
    if st.button("▶ Run synthetic evaluation", type="primary", key="eng_run"):
        rr = np.random.default_rng(int(seed))
        rows = []
        classes = ["Normal", "Leak suspected", "Pipe burst", "Demand anomaly", "Sensor fault"]
        for truth in classes:
            for _ in range(int(n_each)):
                if truth == "Normal":
                    pdp, imb, ac, flow, missing, health = max(0, rr.normal(0.08, 0.07)), max(0, rr.normal(0.55, 0.30)), max(0, rr.normal(0.16, 0.08)), rr.normal(23.5, 2.0), False, 1.0
                elif truth == "Leak suspected":
                    pdp, imb, ac, flow, missing, health = max(0, rr.normal(0.55, 0.18)), max(0, rr.normal(3.2, 0.9)), max(0, rr.normal(0.88, 0.20)), rr.normal(26.5, 2.5), False, 1.0
                elif truth == "Pipe burst":
                    pdp, imb, ac, flow, missing, health = max(0, rr.normal(1.45, 0.25)), max(0, rr.normal(7.0, 1.4)), max(0, rr.normal(1.20, 0.25)), rr.normal(32.0, 4.0), False, 1.0
                elif truth == "Demand anomaly":
                    pdp, imb, ac, flow, missing, health = max(0, rr.normal(0.35, 0.15)), max(0, rr.normal(0.65, 0.35)), max(0, rr.normal(0.25, 0.12)), rr.normal(33.0, 3.5), False, 1.0
                else:
                    pdp, imb, ac, flow, missing, health = max(0, rr.normal(0.2, 0.2)), max(0, rr.normal(0.8, 0.6)), max(0, rr.normal(0.2, 0.15)), rr.normal(24.0, 3.0), bool(rr.random() < 0.85), 0.0 if rr.random() < 0.9 else 1.0
                rows.append({"truth": truth, "pressure_drop_bar": pdp, "flow_imbalance_lps": imb, "acoustic_index": ac, "mean_flow_lps": flow, "telemetry_missing": missing, "sensor_health": health})
        eval_df = pd.DataFrame(rows)
        eval_df["predicted"] = eval_df.apply(classify_case, axis=1)
        class_rows = []
        for cls in classes:
            tp = int(((eval_df.truth == cls) & (eval_df.predicted == cls)).sum())
            fp = int(((eval_df.truth != cls) & (eval_df.predicted == cls)).sum())
            fn = int(((eval_df.truth == cls) & (eval_df.predicted != cls)).sum())
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            class_rows.append({"Class": cls, "Precision": precision, "Recall": recall, "F1": f1, "Correct / total": f"{tp}/{int((eval_df.truth == cls).sum())}"})
        accuracy = float((eval_df.truth == eval_df.predicted).mean())
        incident_truth = eval_df.truth.isin(["Leak suspected", "Pipe burst"])
        incident_pred = eval_df.predicted.isin(["Leak suspected", "Pipe burst"])
        tp_i = int((incident_truth & incident_pred).sum())
        fp_i = int((~incident_truth & incident_pred).sum())
        fn_i = int((incident_truth & ~incident_pred).sum())
        tn_i = int((~incident_truth & ~incident_pred).sum())
        precision_i = tp_i / (tp_i + fp_i) if tp_i + fp_i else 0.0
        recall_i = tp_i / (tp_i + fn_i) if tp_i + fn_i else 0.0
        false_alarm_rate = fp_i / (fp_i + tn_i) if fp_i + tn_i else 0.0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Synthetic accuracy", f"{accuracy*100:.1f}%")
        k2.metric("Leak/burst precision", f"{precision_i*100:.1f}%")
        k3.metric("Leak/burst recall", f"{recall_i*100:.1f}%")
        k4.metric("False-alarm rate", f"{false_alarm_rate*100:.1f}%")
        st.dataframe(pd.DataFrame(class_rows).style.format({"Precision":"{:.2%}", "Recall":"{:.2%}", "F1":"{:.2%}"}), use_container_width=True, hide_index=True)
        conf = pd.crosstab(eval_df["truth"], eval_df["predicted"], rownames=["Ground truth"], colnames=["Engine output"], dropna=False)
        st.markdown("#### Confusion matrix")
        st.dataframe(conf, use_container_width=True)
        st.caption(f"Reproducible synthetic run: {len(eval_df):,} cases • seed {int(seed)}. These metrics describe only the generated distributions and current rule thresholds. They are not evidence of real-world performance, and must not be presented as field accuracy.")
        st.session_state["last_eval_summary"] = {"cases": len(eval_df), "accuracy": accuracy, "precision": precision_i, "recall": recall_i, "false_alarm_rate": false_alarm_rate}

    st.markdown("#### Engineering safeguards and next validation gate")
    st.markdown("""
    - **Data-quality gate:** missing telemetry is classified as a sensor fault before leak logic runs.
    - **False-alarm challenge:** demand surges are represented separately and must not be automatically treated as leaks.
    - **Threshold transparency:** all decision thresholds are visible and adjustable; they are provisional, not calibrated operating limits.
    - **No fake ML claim:** the engine is rule-based. The percentage metrics above come only from generated synthetic cases.
    - **Field validation gate:** before deployment, calibrate sensors, synchronize timestamps, collect labelled controlled tests, evaluate on held-out sites and document pressure/flow operating ranges.
    - **Safety gate:** automated shutoff is not enabled. Any real isolation/valve actuation requires engineering review, fail-safe design and authorized operator confirmation.
    """)


if page == "Leak localization":
    st.markdown("### Multi-node leak localization lab")
    st.caption("A transparent, synthetic demonstration of how synchronized pressure/flow evidence can rank candidate pipe segments. It does not represent field-validated localization accuracy.")
    st.markdown("""
    <div class="as-card">
      <div class="as-eyebrow">LOCALIZATION METHOD</div>
      <div style="font-size:1.02rem;font-weight:800;margin:8px 0;color:#b6f36b">1. Check sensor health → 2. Compare segment residuals → 3. Rank candidates → 4. Request field confirmation</div>
      <div class="as-muted">Each candidate score is an illustrative evidence score based on deviation from a synthetic baseline. Real deployment needs synchronized sensors, calibrated baselines, hydraulic context and labelled leak trials.</div>
    </div>
    """, unsafe_allow_html=True)

    loc_col1, loc_col2 = st.columns([1, 1])
    with loc_col1:
        injected_segment = st.selectbox("Inject simulated leak into", ["A–B", "B–C", "C–D", "D–E"], index=1, key="loc_segment")
        loc_severity = st.slider("Injected event strength", 1, 10, 7, key="loc_severity")
        loc_noise = st.slider("Localization measurement noise", 0.0, 1.0, 0.20, 0.05, key="loc_noise")
    with loc_col2:
        sensor_dropout = st.multiselect("Simulate unavailable nodes", ["Node A", "Node B", "Node C", "Node D", "Node E"], default=[], key="loc_dropout")
        st.write("**Topology**")
        st.markdown("Reservoir → **A** ─ A–B ─ **B** ─ B–C ─ **C** ─ C–D ─ **D** ─ D–E ─ **E** → District")

    loc_rng = np.random.default_rng(20261023 + ["A–B", "B–C", "C–D", "D–E"].index(injected_segment) * 31 + loc_severity)
    segs = ["A–B", "B–C", "C–D", "D–E"]
    base_residual = np.array([0.12, 0.16, 0.11, 0.14], dtype=float)
    event_index = segs.index(injected_segment)
    residuals = base_residual + loc_rng.normal(0, loc_noise, 4)
    residuals[event_index] += 0.18 + 0.11 * loc_severity
    # Adjacent segments can also show weaker effects, reflecting uncertainty rather than perfect localization.
    if event_index > 0:
        residuals[event_index - 1] += 0.025 * loc_severity
    if event_index < 3:
        residuals[event_index + 1] += 0.025 * loc_severity
    residuals = np.maximum(residuals, 0)
    node_pairs = [("Node A", "Node B"), ("Node B", "Node C"), ("Node C", "Node D"), ("Node D", "Node E")]
    segment_rows = []
    for i, seg in enumerate(segs):
        left_node, right_node = node_pairs[i]
        missing = left_node in sensor_dropout or right_node in sensor_dropout
        score = None if missing else float(min(0.99, residuals[i] / max(0.45, 0.18 + 0.11 * loc_severity)))
        segment_rows.append({
            "Candidate segment": seg,
            "Endpoint telemetry": "DEGRADED" if missing else "AVAILABLE",
            "Normalized residual (simulated)": None if missing else round(float(residuals[i]), 3),
            "Evidence score (illustrative)": None if missing else round(score, 3),
            "Disposition": "INSUFFICIENT DATA" if missing else "TOP CANDIDATE" if score == max([r["Evidence score (illustrative)"] for r in segment_rows if r["Evidence score (illustrative)"] is not None] + [score]) else "Monitor"
        })
    loc_df = pd.DataFrame(segment_rows)
    available_scores = loc_df.dropna(subset=["Evidence score (illustrative)"])
    if not available_scores.empty:
        loc_df["Disposition"] = loc_df.apply(
            lambda r: "INSUFFICIENT DATA" if pd.isna(r["Evidence score (illustrative)"]) else
            ("TOP CANDIDATE" if r["Evidence score (illustrative)"] == available_scores["Evidence score (illustrative)"].max() else "Monitor"),
            axis=1
        )
        ranked = available_scores.sort_values("Evidence score (illustrative)", ascending=False)
        top_segment = str(ranked.iloc[0]["Candidate segment"])
        top_score = float(ranked.iloc[0]["Evidence score (illustrative)"])
        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("Top-ranked segment", top_segment)
        lc2.metric("Evidence score", f"{top_score:.2f}")
        lc3.metric("Node availability", f"{5-len(sensor_dropout)}/5")
        if len(sensor_dropout) >= 2:
            st.warning("Multiple nodes are unavailable. Treat localization as low-confidence and dispatch for sensor recovery / field inspection before acting.")
        elif top_segment == injected_segment:
            st.success("In this synthetic run, the top-ranked segment matches the injected segment. This is a demonstration outcome, not a measured accuracy claim.")
        else:
            st.warning("The top-ranked segment differs from the injected segment in this noisy run. This is useful: localization can be uncertain and should be confirmed in the field.")
    else:
        st.error("No segment has enough endpoint telemetry to rank. The safe output is 'localization unavailable'—not a guessed location.")
    st.dataframe(loc_df, use_container_width=True, hide_index=True)
    fig_loc = go.Figure()
    fig_loc.add_trace(go.Bar(x=loc_df["Candidate segment"], y=loc_df["Evidence score (illustrative)"], marker_color=["#b6f36b" if s == top_segment else "#5ee7ed" for s in loc_df["Candidate segment"]] if not available_scores.empty else "#5ee7ed"))
    fig_loc.update_layout(title="Candidate ranking • synthetic residual evidence", height=300, paper_bgcolor="#0c1b15", plot_bgcolor="#0c1b15", font_color="#e4f1e7", margin=dict(l=18,r=18,t=82,b=24), yaxis=dict(range=[0,1], title="Illustrative score", gridcolor="#284735"))
    st.plotly_chart(fig_loc, use_container_width=True)
    st.markdown("#### What a field-grade localization test must report")
    st.markdown("- Segment-level accuracy and confusion matrix across many injection points.\n- Median and 95th-percentile localization error (metres), with pipe lengths and topology recorded.\n- Performance with one or more missing sensors, clock drift, changing demand and noisy readings.\n- A safe abstain state when evidence is insufficient; never invent a precise location from missing data.")

if page == "Real-world water loss & research":
    st.markdown("# Real-world water loss & research")
    st.caption("Evidence library · India · reported figures are kept separate from physical leakage unless the source explicitly measures it.")
    st.markdown("""
    <div class="as-card" style="margin-bottom:14px">
      <div class="as-eyebrow">RESEARCH NOTE</div>
      <div style="font-size:1.04rem;font-weight:800;margin:6px 0">Water that is not billed is not automatically water that leaked.</div>
      <div class="as-muted">Non-revenue water (NRW) can include physical leakage, apparent/commercial losses, meter inaccuracies and authorized unbilled consumption. The evidence below labels each metric and does not convert NRW into underground leakage.</div>
    </div>
    """, unsafe_allow_html=True)

    cag_url = "https://www.cag.gov.in/en/audit-report/details/124748"
    cag_pdf = "https://www.cag.gov.in/uploads/download_audit_report/2025/Delhi_PA-Report-on-3_DJB_English-069c2836793c603.23213132.pdf"
    # Primary-source annual table: CAG Table 3.5, source says data supplied by DJB.
    djb = pd.DataFrame([
        {"Year": "2017–18", "Treated water supplied (MGD)": 883.00, "Billed water (MGD)": 421.00, "NRW (MGD)": 462.00, "NRW (% of supplied)": 52.32},
        {"Year": "2018–19", "Treated water supplied (MGD)": 896.00, "Billed water (MGD)": 419.92, "NRW (MGD)": 476.08, "NRW (% of supplied)": 53.13},
        {"Year": "2019–20", "Treated water supplied (MGD)": 923.00, "Billed water (MGD)": 524.91, "NRW (MGD)": 398.09, "NRW (% of supplied)": 43.13},
        {"Year": "2020–21", "Treated water supplied (MGD)": 928.00, "Billed water (MGD)": 457.07, "NRW (MGD)": 470.93, "NRW (% of supplied)": 50.75},
        {"Year": "2021–22", "Treated water supplied (MGD)": 935.00, "Billed water (MGD)": 450.39, "NRW (MGD)": 484.61, "NRW (% of supplied)": 51.83},
    ])
    # Evidence library intentionally separates unlike metrics. Only Delhi's same-year billed-vs-NRW split is charted as a pie.
    records = [
      {"Geography":"Delhi · Delhi Jal Board", "Metric":"Non-revenue water", "Value":484.61, "Unit":"MGD", "Period":"2021–22", "Evidence type":"CAG performance audit; Table 3.5", "Publication date":"23 Mar 2026", "Scope label":"NRW — not physical leakage alone", "Source":"CAG Report No. 3 of 2025", "URL":cag_url},
      {"Geography":"Delhi · Delhi Jal Board", "Metric":"Billed water", "Value":450.39, "Unit":"MGD", "Period":"2021–22", "Evidence type":"CAG performance audit; Table 3.5", "Publication date":"23 Mar 2026", "Scope label":"Billed volume comparator", "Source":"CAG Report No. 3 of 2025", "URL":cag_url},
      {"Geography":"Delhi · Delhi Jal Board", "Metric":"Transmission loss", "Value":"16 → 21", "Unit":"%", "Period":"2017–18 to 2021–22", "Evidence type":"CAG press release / audit summary", "Publication date":"24 Mar 2026", "Scope label":"Transmission loss; distinct from NRW", "Source":"CAG press release on Report No. 3 of 2025", "URL":"https://cag.gov.in/uploads/PressRelease/PR-Press-Release-on-Report-No-3-of-2025-069c383c1c5b4d3-75064279.pdf"},
      {"Geography":"Bengaluru · BWSSB (reported by TOI)", "Metric":"Unaccounted water / pilferage", "Value":435, "Unit":"MLD", "Period":"Reported Mar 2024; current estimate in article", "Evidence type":"News report quoting utility context", "Publication date":"9 Mar 2024", "Scope label":"Unaccounted flow; not pure physical leakage", "Source":"The Times of India", "URL":"https://timesofindia.indiatimes.com/city/bengaluru/300ml-of-every-1l-of-cauvery-water-is-lost-to-pilferage/articleshow/108338898.cms"},
      {"Geography":"Ahmedabad · AMC (reported by TOI)", "Metric":"Daily loss attributed to theft and leaks", "Value":300, "Unit":"MLD", "Period":"Reported Mar 2023; daily estimate", "Evidence type":"News report quoting municipal/utility context", "Publication date":"21 Mar 2023", "Scope label":"Combined theft + leaks; not leakage-only", "Source":"The Times of India", "URL":"https://timesofindia.indiatimes.com/city/ahmedabad/ahmedabad-loses-300-million-litres-of-water-to-theft-and-leaks-every-day/articleshow/98846722.cms"},
      {"Geography":"Mumbai · BMC (reported by Mid-day)", "Metric":"Leakage complaints", "Value":5934, "Unit":"complaints", "Period":"FY 2023–24 through 22 Dec 2023", "Evidence type":"News report citing BMC complaint counts", "Publication date":"24 Dec 2023", "Scope label":"Complaints, not measured water volume", "Source":"Mid-day", "URL":"https://www.mid-day.com/mumbai/mumbai-news/article/mumbai-water-leakage-complaints-rise-by-30-per-cent-in-23-24-23326414"},
      {"Geography":"India · urban systems (historical national reference)", "Metric":"Average NRW in 28-city pilot", "Value":39, "Unit":"%", "Period":"2008–09", "Evidence type":"PIB release summarising MoUD pilot", "Publication date":"17 May 2012", "Scope label":"Historical NRW; outside five-year window", "Source":"Press Information Bureau / Ministry of Water Resources", "URL":"https://www.pib.gov.in/newsite/PrintRelease.aspx?lang=2&reg=48&relid=84072"},
    ]
    evidence_df = pd.DataFrame(records)

    f1, f2, f3 = st.columns([1.2, 1.1, 1.5])
    with f1:
        geography_filter = st.selectbox("Geography", ["All geographies"] + sorted(evidence_df["Geography"].unique().tolist()), key="research_geo")
    with f2:
        type_filter = st.selectbox("Evidence type", ["All types"] + sorted(evidence_df["Evidence type"].unique().tolist()), key="research_type")
    with f3:
        search_term = st.text_input("Search reports, metrics or sources", placeholder="e.g. transmission loss, Bengaluru", key="research_search")
    filtered = evidence_df.copy()
    if geography_filter != "All geographies": filtered = filtered[filtered["Geography"] == geography_filter]
    if type_filter != "All types": filtered = filtered[filtered["Evidence type"] == type_filter]
    if search_term.strip():
        mask = filtered.astype(str).apply(lambda col: col.str.contains(search_term.strip(), case=False, regex=False)).any(axis=1)
        filtered = filtered[mask]

    st.markdown("## Comparable volume split · Delhi Jal Board")
    st.caption("One year, one utility, one source table. This pie compares billed volume with NRW for 2021–22; it does not claim that all NRW is physical leakage.")
    selected_year = st.selectbox("Audit year", djb["Year"].tolist(), index=4, key="djb_pie_year")
    row = djb[djb["Year"] == selected_year].iloc[0]
    pie = go.Figure(data=[go.Pie(labels=["Billed water", "Non-revenue water (NRW)"], values=[row["Billed water (MGD)"], row["NRW (MGD)"],], hole=.58, sort=False, textinfo="label+percent", hovertemplate="%{label}<br>%{value:.2f} MGD<extra></extra>")])
    pie.update_layout(height=380, margin=dict(l=20,r=20,t=48,b=18), title=dict(text=f"DJB water balance · {selected_year}", x=.02), paper_bgcolor="#0b1c13", plot_bgcolor="#0b1c13", font_color="#e8f3eb", legend=dict(orientation="h",yanchor="bottom",y=-.05,xanchor="center",x=.5))
    pc1, pc2 = st.columns([1.05, 1])
    with pc1: st.plotly_chart(pie, use_container_width=True)
    with pc2:
        st.metric("Treated water supplied", f"{row['Treated water supplied (MGD)']:.2f} MGD")
        st.metric("NRW", f"{row['NRW (MGD)']:.2f} MGD", f"{row['NRW (% of supplied)']:.2f}% of supplied")
        st.metric("Billed water", f"{row['Billed water (MGD)']:.2f} MGD")
        st.markdown(f"**Source:** [CAG Performance Audit on Functioning of Delhi Jal Board, Report No. 3 of 2025]({cag_url}) · **Audit coverage:** FY 2017–18 to FY 2021–22 · **Report tabled:** 23 March 2026.")
    st.markdown("### Five-year audit table · Delhi Jal Board")
    st.caption("The reporting years are FY 2017–18 through FY 2021–22. The report was sent to government on 3 Dec 2025 and tabled on 23 Mar 2026; Report No. 3 of 2025 is the report number, not the tabled date.")
    st.dataframe(djb, use_container_width=True, hide_index=True)
    st.info("CAG Table 3.5 reports NRW calculated as treated water supplied minus billed quantity. This is a water-balance measure, not a direct measurement of underground leakage. The same audit summary separately reports transmission losses rising from 16% in 2017–18 to 21% in 2021–22. Revenue not realised is a financial measure and is not plotted as water volume.")

    st.markdown("## Research evidence register")
    display_cols = ["Geography", "Metric", "Value", "Unit", "Period", "Evidence type", "Publication date", "Scope label", "Source", "URL"]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True, column_config={"URL": st.column_config.LinkColumn("Original source", display_text="Open source"), "Value": st.column_config.TextColumn("Reported value")})
    st.caption(f"Showing {len(filtered)} of {len(evidence_df)} records. Search/filter affects the evidence register and case library. Figures are reported values unless explicitly labelled otherwise.")

    st.markdown("## Case study library")
    cases = [
      {"title":"Delhi Jal Board — audit of water supply and distribution", "date":"Audit coverage: FY 2017–18 to FY 2021–22 · tabled 23 Mar 2026", "geo":"Delhi · official audit", "type":"Official audit", "summary":"CAG reported NRW of 43.13%–53.13% across the five annual rows in Table 3.5, with 2021–22 at 51.83%. The audit summary separately reports transmission loss increasing from 16% to 21%.", "impact":"The audit gives treated water, billed water and NRW in MGD, and reports ₹4,988 crore potential revenue loss associated with NRW beyond the 20% benchmark over the audit period.", "limits":"NRW is not equivalent to physical leakage. Revenue not realised is not the monetary value of water physically leaking underground. The audit coverage predates its 2026 publication.", "relevance":"Highlights why inlet/outlet metering, persistent pressure/flow anomalies and segment-level incident triage can be useful; it does not prove AquaSentinel performance.", "url":cag_url},
      {"title":"Bengaluru — unaccounted Cauvery water", "date":"Published 9 Mar 2024", "geo":"Bengaluru · news report", "type":"News report", "summary":"The Times of India reported approximately 1,450 MLD supplied and about 435 MLD described as unaccounted flow/pilferage, around 30% in the article.", "impact":"435 MLD reported as a daily estimate in the article.", "limits":"This is unaccounted/pilferage water, not a direct audited measurement of underground physical leakage. The report includes commercial pilferage and aging infrastructure context.", "relevance":"Shows the operational value of distinguishing physical leaks from unmetered or unauthorized use and of monitoring water balance.", "url":"https://timesofindia.indiatimes.com/city/bengaluru/300ml-of-every-1l-of-cauvery-water-is-lost-to-pilferage/articleshow/108338898.cms"},
      {"title":"Ahmedabad — reported theft and pipeline leaks", "date":"Published 21 Mar 2023", "geo":"Ahmedabad · news report", "type":"News report", "summary":"The Times of India reported 300 MLD daily attributed jointly to theft and leaks.", "impact":"300 MLD combined estimate reported by the newspaper.", "limits":"The figure combines theft and leakage; the article does not provide a verified physical-leakage-only split. It is not comparable to Delhi's NRW table.", "relevance":"Illustrates why the system should preserve metric definitions and avoid treating all unaccounted water as pipe leakage.", "url":"https://timesofindia.indiatimes.com/city/ahmedabad/ahmedabad-loses-300-million-litres-of-water-to-theft-and-leaks-every-day/articleshow/98846722.cms"},
      {"title":"Mumbai — leakage complaint workload", "date":"Published 24 Dec 2023; count through 22 Dec 2023", "geo":"Mumbai · news report citing BMC", "type":"News report", "summary":"Mid-day reported 5,934 leakage-related complaints received through 22 December, versus 6,228 complaints during FY 2022–23. The article says complaint categories also included connections, valves, contamination and shortage.", "impact":"Complaint volume, not a measured water-loss quantity.", "limits":"Complaints are not unique confirmed leaks, and the article's reported categories are broader than underground pipe failures. No litres lost can be calculated from these counts.", "relevance":"Supports a repair operations workflow with triage, crew assignment, timestamps and closure tracking.", "url":"https://www.mid-day.com/mumbai/mumbai-news/article/mumbai-water-leakage-complaints-rise-by-30-per-cent-in-23-24-23326414"},
    ]
    for case in cases:
        if geography_filter != "All geographies" and geography_filter.split(" · ")[0].lower() not in case["geo"].lower():
            continue
        if type_filter != "All types" and not ((case["type"] == "Official audit" and "audit" in type_filter.lower()) or (case["type"] == "News report" and "news report" in type_filter.lower())):
            continue
        if search_term.strip() and search_term.lower() not in (case["title"]+case["summary"]+case["limits"]+case["geo"]).lower():
            continue
        with st.expander(case["title"] + "  ·  " + case["date"]):
            st.markdown(f"**Location / evidence:** {case['geo']}\n\n**Incident / finding:** {case['summary']}\n\n**Reported impact:** {case['impact']}\n\n**Evidence limitations:** {case['limits']}\n\n**Relevance to early detection:** {case['relevance']}\n\n**Original source:** [Open report]({case['url']})")

    with st.expander("Methodology, definitions and conversion policy"):
        st.markdown("""
        - **Source hierarchy:** original CAG report and official CAG press release first; news reports are included as reported context and explicitly labelled as such.
        - **Publication date vs reporting period:** shown separately in every register row. CAG Report No. 3 of 2025 covers FY 2017–18 to FY 2021–22; it was sent to government on 3 Dec 2025 and tabled on 23 Mar 2026.
        - **Comparability:** only the Delhi annual figures from CAG Table 3.5 are shown together in the five-year table. The pie chart compares billed quantity and NRW for the same utility and year, both in MGD.
        - **NRW definition:** includes more than physical leakage; no percentage or volume here is presented as underground leakage unless the cited source specifically says so.
        - **Units:** MGD means million gallons per day; MLD means million litres per day. No conversion is applied between these units in the charts. No unreported litres or costs are inferred.
        - **Limitations:** comparable, audited, state-wise physical leakage volumes for every Indian state over the most recent five-year reporting window were not found in the reviewed sources. The section therefore displays the verified available records and flags heterogeneous news estimates rather than filling gaps with zeros.
        """)

if page == "Components guide":
    st.markdown("### System architecture & component guide")
    st.caption("A plain-language walkthrough of the proposed system—from the pipe-side instruments to the decision engine and repair workflow.")
    st.markdown("#### How each component contributes")
    component_guide = pd.DataFrame([
        {"Component / layer":"Pressure transducer", "What it does":"Measures water pressure in the pipe and reports changes over time.", "Why AquaSentinel uses it":"A sustained pressure drop can be one signal of a leak or burst.", "Design consideration":"Choose a pressure range and output interface that match the pipe and electronics; calibrate against a reference."},
        {"Component / layer":"Flow meter", "What it does":"Measures how much water passes a point per unit time.", "Why AquaSentinel uses it":"Comparing upstream and downstream flow can reveal a persistent imbalance.", "Design consideration":"Select a suitable pipe size, flow range and pulse or Modbus interface."},
        {"Component / layer":"Optional acoustic / vibration sensor", "What it does":"Captures sound or vibration patterns around a pipe.", "Why AquaSentinel uses it":"It can provide an additional clue to help distinguish a leak from ordinary demand changes.", "Design consideration":"Noise varies by pipe material, mounting, pumps and surroundings; it needs controlled testing."},
        {"Component / layer":"ESP32 edge controller", "What it does":"Reads local sensor signals, checks data quality and packages measurements.", "Why AquaSentinel uses it":"Provides a low-cost starting point for a connected sensor node.", "Design consideration":"Use appropriate signal conditioning, protection, ADC validation and a robust enclosure."},
        {"Component / layer":"LoRa radio / gateway", "What it does":"Sends small sensor messages over a long-range, low-power wireless link.", "Why AquaSentinel uses it":"Can connect distributed monitoring points where Wi-Fi is impractical.", "Design consideration":"Confirm regional frequency rules, antenna, link budget, coverage and packet-loss handling."},
        {"Component / layer":"Detection engine", "What it does":"Checks pressure, flow balance, acoustic indicator and sensor health against transparent rules.", "Why AquaSentinel uses it":"Produces an explainable classification instead of an unexplained alert.", "Design consideration":"Thresholds must be calibrated and evaluated on labelled trials; the current prototype uses configurable rules."},
        {"Component / layer":"Network localization", "What it does":"Ranks candidate pipe segments using simulated residual evidence from connected nodes.", "Why AquaSentinel uses it":"Helps an operator prioritize where to inspect first.", "Design consideration":"Real localization requires a surveyed topology, synchronized calibrated sensors and ground-truth leak trials."},
        {"Component / layer":"Dashboard, event log and repair workflow", "What it does":"Shows status, evidence, event history, crew assignment and post-repair verification.", "Why AquaSentinel uses it":"Connects detection to an operational response rather than stopping at an alarm.", "Design consideration":"A production deployment needs authenticated users, audit retention and operational integration."},
    ])
    st.dataframe(component_guide, use_container_width=True, hide_index=True)
    st.markdown("#### End-to-end information flow")
    st.markdown("**Pipe → pressure / flow / optional acoustic sensing → ESP32 edge node → LoRa or wired network → gateway / MQTT → time-series storage → explainable detection engine → segment triage → operator-confirmed repair → post-repair verification.**")
    st.caption("The current app demonstrates the detection logic, scenario generation, localization workflow and response interface in software. Sensor acquisition, external connectivity, field accuracy and physical valve control are separate integration and validation stages.")
    st.markdown("#### 1 · Capability and evidence register")
    evidence = pd.DataFrame([
        {"Claim / capability":"Live-looking telemetry and animated leak","Evidence in this build":"Scenario-driven simulator and browser animation","Status":"Demonstrated in software"},
        {"Claim / capability":"Rule-based leak/burst/demand/fault classification","Evidence in this build":"Inspectable thresholds + synthetic test bench","Status":"Demonstrated on synthetic inputs"},
        {"Claim / capability":"Repeatable metrics","Evidence in this build":"Seeded synthetic scenarios + confusion matrix","Status":"Synthetic only; not field validation"},
        {"Claim / capability":"Pipe-segment ranking","Evidence in this build":"Synthetic multi-node residual ranking","Status":"Concept demonstration"},
        {"Claim / capability":"Physical sensor acquisition","Evidence in this build":"Hardware architecture / candidate BOM only","Status":"Integration stage"},
        {"Claim / capability":"Trained machine-learning model","Evidence in this build":"None; current engine is explicit rules","Status":"Future model-validation stage"},
        {"Claim / capability":"Municipal network / GIS integration","Evidence in this build":"Illustrative schematic topology","Status":"Integration stage"},
        {"Claim / capability":"Automatic valve actuation","Evidence in this build":"No control path enabled","Status":"Safety-gated; disabled in demo"},
    ])
    st.dataframe(evidence, use_container_width=True, hide_index=True)

    st.markdown("#### 2 · Candidate hardware and interface review")
    bom = pd.DataFrame([
        {"Layer":"Edge controller","Candidate":"ESP32 DevKit V1","Interface / design check":"3.3 V GPIO; verify ADC range, isolation and input conditioning","Decision gate":"Bench test with calibrated source"},
        {"Layer":"Pressure","Candidate":"Industrial 0–10 bar transducer, 0.5–4.5 V output","Interface / design check":"Output may exceed ESP32 ADC range; use suitable signal conditioning and protection","Decision gate":"Confirm exact datasheet + calibration"},
        {"Layer":"Flow","Candidate":"Pulse-output or Modbus flow meter","Interface / design check":"Pulse counting / UART-RS485 transceiver as required; document units and sampling","Decision gate":"Verify meter protocol and flow range"},
        {"Layer":"Long-range radio","Candidate":"SX1276 / RA-02 LoRa module","Interface / design check":"Regional frequency compliance, antenna, power budget and link testing","Decision gate":"Choose region-compliant module and gateway"},
        {"Layer":"Backend","Candidate":"MQTT + time-series store","Interface / design check":"Timestamp, sequence number, device identity, offline buffer and retry policy","Decision gate":"Test packet loss and reconnection"},
    ])
    st.dataframe(bom, use_container_width=True, hide_index=True)
    st.info("Integration checklist: finalize manufacturer part numbers and datasheets, verify voltage levels and signal conditioning, confirm sensor protocols, then bench-test calibration, radio reliability and enclosure protection before a field pilot.")

    st.markdown("#### 3 · Proposed acceptance gates before a real pilot")
    gates = pd.DataFrame([
        {"Gate":"G0 — Instrument sanity","Pass condition":"All sensors calibrated against a reference; timestamp and units validated"},
        {"Gate":"G1 — Baseline characterization","Pass condition":"Normal pressure/flow envelopes measured across demand and pump states"},
        {"Gate":"G2 — Controlled leak trials","Pass condition":"Pre-registered leak sizes and locations; repeated runs; labelled ground truth"},
        {"Gate":"G3 — Blind evaluation","Pass condition":"Held-out runs/sites; report precision, recall, false-alarm rate and detection delay"},
        {"Gate":"G4 — Localization","Pass condition":"Segment accuracy + distance error with missing/noisy sensors included"},
        {"Gate":"G5 — Safety & operations","Pass condition":"Human confirmation, fail-safe state, audit log, access control and rollback tested"},
    ])
    st.dataframe(gates, use_container_width=True, hide_index=True)

    st.markdown("#### 4 · Live demo checklist")
    checklist = [
        "Show normal operation first; explain baseline pressure and flow balance.",
        "Trigger a leak and point to the three signals used by the rule engine.",
        "Switch to demand surge and show that it is not automatically labelled a leak.",
        "Switch to sensor failure and show the data-quality gate abstaining from leak diagnosis.",
        "Open the detection engine; run the seeded synthetic evaluation and inspect the confusion matrix.",
        "Open localization lab; disable a node and show how the system reports degraded evidence.",
        "Assign a crew, mark repair complete, then verify simulated baseline recovery.",
        "State clearly which outputs are simulated and what field test comes next.",
    ]
    for item in checklist:
        st.checkbox(item, key="evidence_check_" + str(checklist.index(item)))
    st.markdown("#### 5 · Threat model and operational safeguards")
    st.markdown("- **False positives:** separate demand changes from persistent leak evidence; require persistence/hysteresis in a production implementation.\n- **False negatives:** small leaks may not cross fixed thresholds; evaluate across leak size, pipe material, pressure and demand ranges.\n- **Sensor drift / fouling:** include plausibility checks, calibration schedule and cross-sensor disagreement alerts.\n- **Network loss:** buffer readings locally, timestamp at source and flag stale telemetry instead of treating it as normal.\n- **Cybersecurity:** unique device credentials, encrypted transport, signed firmware/update process and least-privilege access.\n- **Unsafe actuation:** no automatic valve commands in this prototype; any future actuation needs hazard analysis, interlocks and authorized operator approval.\n- **Privacy / governance:** minimize stored operational data and define ownership, retention and incident audit policy.")
    st.info("Engineering status: the software workflow and explainable rule engine are demonstrable now. The next formal gate is a controlled sensor-bench study followed by blind field evaluation before operational deployment.")
