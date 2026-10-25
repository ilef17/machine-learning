"""Global look of the platform: one stylesheet injected once per run.

Colours of the page itself come from .streamlit/config.toml; this file adds the pieces Streamlit cannot theme
(cards, KPI tiles, result panel, sign-in screen). Its colours are CSS variables, switched in the browser
(see THEME_JS), so they follow the Settings menu (System / Light / Dark) instantly, without a server rerun.
"""

import streamlit as st

LIGHT = dict(sb_bg="#ffffff", card="#ffffff", rule="#e4e7ec", muted="#667085", accent="#2563eb", soft="#eff4ff",
             shadow="0 1px 2px rgba(16,24,40,.06)", track="#e4e7ec", head="#0b1220",
             panel="radial-gradient(120% 90% at 0% 0%, #dbeafe 0%, #f1f5f9 62%)", panel_text="#334155", panel_title="#0b1220", panel_foot="#64748b", panel_dot="#2563eb")
DARK = dict(sb_bg="#0a101d", card="#121a2c", rule="#243049", muted="#98a2b3", accent="#60a5fa", soft="rgba(96,165,250,.12)",
            shadow="0 1px 2px rgba(0,0,0,.35)", track="#243049", head="#f1f5f9",
            panel="radial-gradient(120% 90% at 0% 0%, #1e3a8a 0%, #0f172a 62%)", panel_text="#cbd5e1", panel_title="#ffffff", panel_foot="#94a3b8", panel_dot="#60a5fa")


def _vars(tokens):
    return " ".join(f"--{k.replace('_', '-')}: {v};" for k, v in tokens.items())


CSS = """
<style>
/* ---- theme variables */
:root { {LIGHT} }
@media (prefers-color-scheme: dark) { :root:not([data-app-theme]) { {DARK} } }
:root[data-app-theme="dark"] { {DARK} }
:root[data-app-theme="light"] { {LIGHT} }

/* ---- page */
[data-testid="stMainBlockContainer"] { max-width: 1240px; padding: 1.6rem 2.2rem 3rem; }
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
.stApp h1 { font-size: 1.75rem; font-weight: 650; letter-spacing: -.02em; line-height: 1.2; color: var(--head); padding: 0 0 .15rem; }
.stApp h2, .stApp h3 { font-weight: 600; letter-spacing: -.01em; color: var(--head); }
.stApp .crumb { font-size: .82rem; color: var(--muted); margin: 0 0 .35rem; }
.stApp .lede { font-size: .98rem; line-height: 1.55; max-width: 74ch; color: var(--muted); margin: 0 0 1.4rem; }

/* ---- cards */
div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"]:has(.home-card) {
    background: var(--card); border: 1px solid var(--rule); border-radius: 12px; box-shadow: var(--shadow); }
div[data-testid="stForm"] { padding: 1.3rem 1.4rem 1.5rem; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.home-card) { transition: border-color .15s, box-shadow .15s; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.home-card):hover { border-color: var(--accent); box-shadow: 0 4px 14px rgba(37,99,235,.10); }
[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--rule); border-radius: 10px; padding: .85rem 1.05rem; box-shadow: var(--shadow); }
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 650; letter-spacing: -.01em; }
div[data-testid="stFormSubmitButton"] button { font-weight: 600; min-height: 2.7rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--rule); border-radius: 10px; overflow: hidden; }
.stApp .form-section { font-size: .8rem; font-weight: 600; color: var(--muted); margin: 1.1rem 0 .15rem; padding-top: .9rem;
                       border-top: 1px solid var(--rule); }
.stApp .form-section.first { border-top: 0; padding-top: 0; margin-top: .2rem; }

/* ---- home cards */
.stApp .home-icon { width: 38px; height: 38px; border-radius: 10px; background: var(--soft); color: var(--accent); display: flex;
                    align-items: center; justify-content: center; font-size: 1.25rem; margin-bottom: .7rem; }
.stApp .home-card-title { font-size: 1.08rem; font-weight: 600; margin: 0 0 .25rem; color: var(--head); }
.stApp .home-card-model { font-size: .82rem; color: var(--muted); margin: .2rem 0 .65rem; }
.stApp .home-card-extra { display: inline-block; font-size: .78rem; color: var(--accent); background: var(--soft); font-weight: 500;
                          padding: .22rem .6rem; border-radius: 999px; margin: 0 0 .6rem; }

/* ---- home: hero banner */
.st-key-hero { position: relative; overflow: hidden; border-radius: 22px; padding: 2.6rem 2.8rem 1.6rem; margin-bottom: .6rem;
               background: radial-gradient(60% 90% at 88% 0%, rgba(56,189,248,.42) 0%, transparent 60%),
                           radial-gradient(50% 80% at 0% 100%, rgba(99,102,241,.45) 0%, transparent 60%),
                           linear-gradient(135deg, #0a1440 0%, #1e3a8a 55%, #1d4ed8 100%);
               box-shadow: 0 18px 40px -18px rgba(29,78,216,.55); }
.st-key-hero::before { content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
                       background-image: radial-gradient(rgba(255,255,255,.22) 1px, transparent 1.4px); background-size: 22px 22px;
                       -webkit-mask-image: linear-gradient(100deg, transparent 20%, #000 100%); mask-image: linear-gradient(100deg, transparent 20%, #000 100%); }
.st-key-hero > div { position: relative; }
.stApp .hero-pill { display: inline-flex; align-items: center; gap: .5rem; font-size: .8rem; font-weight: 500; color: #dbeafe;
                    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22); padding: .3rem .8rem; border-radius: 999px; }
.hero-pill i { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 0 4px rgba(74,222,128,.25); }
.stApp .hero-title { font-size: 2.45rem; line-height: 1.12; letter-spacing: -.03em; font-weight: 700; color: #fff; margin: 1.1rem 0 .9rem; padding: 0; }
.hero-title [data-heading-text] > span { background: linear-gradient(90deg, #7dd3fc, #c4b5fd); -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero-title [data-testid="stHeaderActionElements"] { display: none; }
.stApp .hero-sub { color: #cbd5e1; font-size: 1.02rem; line-height: 1.6; max-width: 56ch; margin: 0 0 1.5rem; }
.st-key-hero a[data-testid="stPageLink-NavLink"] { justify-content: center; border-radius: 10px; padding: .62rem 1rem; font-weight: 600;
                                                    transition: transform .15s, background .15s; }
.st-key-hero a[data-testid="stPageLink-NavLink"]:hover { transform: translateY(-1px); }
.st-key-hero-cta a[data-testid="stPageLink-NavLink"] { background: #fff; box-shadow: 0 6px 16px -6px rgba(0,0,0,.45); }
.st-key-hero-cta a[data-testid="stPageLink-NavLink"] * { color: #1e3a8a !important; }
.st-key-hero-ghost a[data-testid="stPageLink-NavLink"] { background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.3); }
.st-key-hero-ghost a[data-testid="stPageLink-NavLink"]:hover { background: rgba(255,255,255,.2); }
.st-key-hero-ghost a[data-testid="stPageLink-NavLink"] * { color: #fff !important; }
.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin-top: 1.9rem; padding-top: 1.2rem;
              border-top: 1px solid rgba(255,255,255,.16); }
.hero-stats b { display: block; font-size: 1.5rem; font-weight: 700; letter-spacing: -.02em; color: #fff; font-variant-numeric: tabular-nums; }
.hero-stats span { font-size: .8rem; color: #bfdbfe; }

/* hero illustration: three floating cards */
.hero-visual { position: relative; height: 395px; max-width: 460px; margin-left: auto; }
.hero-visual .fx { position: absolute; background: rgba(255,255,255,.95); border-radius: 14px; padding: .9rem 1.05rem; color: #0f172a;
                   box-shadow: 0 22px 40px -16px rgba(2,6,23,.55); }
.hero-visual .fx-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: .35rem; }
.hero-visual .fx-top em { font-style: normal; font-size: .72rem; font-weight: 700; color: #2563eb; background: #eff4ff; padding: .15rem .55rem; border-radius: 999px; }
.hero-visual .fx-top span { font-size: .7rem; color: #64748b; }
.hero-visual .fx-a { top: 0; left: 0; width: 66%; transform: rotate(-2deg); }
.hero-visual .fx-big { font-size: 1.7rem; font-weight: 700; letter-spacing: -.02em; margin: .2rem 0 .7rem; color: #0f172a; }
.hero-visual .fx-meter { height: 7px; border-radius: 4px; background: #e2e8f0; overflow: hidden; }
.hero-visual .fx-meter div { height: 100%; background: linear-gradient(90deg, #2563eb, #38bdf8); border-radius: 4px; }
.hero-visual .fx-meta { display: flex; justify-content: space-between; font-size: .72rem; color: #64748b; margin-top: .4rem; }
.hero-visual .fx-meta b { color: #0f172a; }
.hero-visual .fx-b { top: 152px; right: 0; width: 62%; transform: rotate(2deg); }
.hero-visual .fx-row { display: grid; grid-template-columns: 78px 1fr; align-items: center; gap: .5rem; font-size: .7rem; color: #475569; margin-top: .45rem; }
.hero-visual .fx-row i { display: block; height: 7px; border-radius: 4px; background: linear-gradient(90deg, #6366f1, #38bdf8); }
.hero-visual .fx-c { bottom: 0; left: 8%; width: 58%; transform: rotate(-1deg); }
.hero-visual .fx-people { display: flex; align-items: center; margin-top: .45rem; }
.hero-visual .fx-people b { width: 30px; height: 30px; border-radius: 50%; border: 2px solid #fff; margin-left: -8px; color: #fff; font-size: .75rem;
                            display: flex; align-items: center; justify-content: center; }
.hero-visual .fx-people b:first-child { margin-left: 0; }
.hero-visual .fx-people span { margin-left: .55rem; font-size: .75rem; color: #64748b; font-weight: 600; }
.hero-visual .orb { position: absolute; border-radius: 50%; filter: blur(2px); }
.hero-visual .o1 { width: 90px; height: 90px; right: 6%; bottom: 8px; background: radial-gradient(circle at 30% 30%, #7dd3fc, #6366f1); opacity: .85; }
.hero-visual .o2 { width: 26px; height: 26px; left: -6px; bottom: 120px; background: #c4b5fd; opacity: .8; }

/* home: model cards, charts, steps */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.home-card), [class*="st-key-card-"] { overflow: hidden; }
[class*="st-key-card-"] { height: 100%; background: var(--card); box-shadow: var(--shadow); transition: border-color .15s, box-shadow .15s, transform .15s; }
[class*="st-key-card-"]:hover { border-color: var(--accent); box-shadow: 0 10px 24px -10px rgba(37,99,235,.35); transform: translateY(-2px); }
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-card-"]) { height: 100%; }
.stApp .home-banner { position: relative; height: 112px; margin: -1rem -1rem .95rem; overflow: hidden; }
.home-banner::after { content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 20% 0%, rgba(255,255,255,.22), transparent 55%); }
.home-motif { position: absolute; inset: 0; width: 100%; height: 100%; }
.stApp .home-banner .home-icon { position: absolute; left: 1rem; bottom: .8rem; z-index: 1; width: 42px; height: 42px; margin: 0; color: #fff;
                                 background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.35); backdrop-filter: blur(6px); }
.stApp .home-chart-title { font-weight: 600; color: var(--head); margin: .1rem 0 0; }
.stApp .home-chart-sub { font-size: .82rem; color: var(--muted); margin: 0 0 .6rem; }
.stApp .home-session { display: flex; flex-wrap: wrap; align-items: center; gap: .55rem; margin: .8rem 0 0; }
.stApp .home-session-title { font-size: .8rem; font-weight: 600; color: var(--muted); margin-right: .2rem; }
.stApp .home-chip { display: inline-flex; flex-direction: column; background: var(--card); border: 1px solid var(--rule); border-radius: 10px;
                    padding: .3rem .75rem; box-shadow: var(--shadow); line-height: 1.25; }
.home-chip small { color: var(--muted); font-size: .7rem; }
.home-chip b { color: var(--head); font-size: .85rem; }
.how-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.how-step { position: relative; background: var(--card); border: 1px solid var(--rule); border-radius: 12px; padding: 1.2rem 1.3rem 1.25rem; box-shadow: var(--shadow); }
.stApp .how-n { position: absolute; top: 1rem; right: 1.1rem; font-size: 2.4rem; font-weight: 700; line-height: 1; color: var(--soft); }
.stApp .how-icon { width: 38px; height: 38px; border-radius: 10px; background: var(--soft); color: var(--accent); display: flex; align-items: center;
                   justify-content: center; font-size: 1.25rem; margin-bottom: .8rem; }
.stApp .how-title { font-weight: 600; margin: 0 0 .2rem; color: var(--head); }
.stApp .how-text { font-size: .88rem; color: var(--muted); margin: 0; line-height: 1.5; }

/* ---- prediction result */
.result-card { background: var(--card); border: 1px solid var(--rule); border-radius: 12px; box-shadow: var(--shadow); padding: 1.35rem 1.5rem 1.3rem; }
.stApp .result-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
.stApp .badge { font-size: .76rem; font-weight: 600; color: var(--accent); background: var(--soft); padding: .22rem .65rem; border-radius: 999px; }
.stApp .result-model { font-size: .8rem; color: var(--muted); }
.stApp .result-label { margin: 0 0 .4rem; font-size: 1.85rem; font-weight: 650; line-height: 1.2; letter-spacing: -.02em; color: var(--head); }
.stApp .result-desc { margin: 0 0 1.15rem; color: var(--muted); max-width: 62ch; line-height: 1.5; }
.stApp .meter-top { display: flex; justify-content: space-between; font-size: .82rem; margin-bottom: .4rem; color: var(--muted); }
.stApp .meter-top b { font-variant-numeric: tabular-nums; color: var(--head); }
.meter-track { height: 8px; border-radius: 4px; background: var(--track); overflow: hidden; }
.meter-fill { height: 100%; background: var(--accent); border-radius: 4px; }
.stApp .placeholder { background: var(--card); border: 1px dashed var(--rule); border-radius: 12px; padding: 2.6rem 1.8rem; color: var(--muted); line-height: 1.5; }
.stApp .placeholder b { display: block; font-size: 1rem; color: var(--head); margin-bottom: .3rem; }
.stApp .section-head { margin: 1.9rem 0 .15rem; font-size: 1.15rem; font-weight: 600; letter-spacing: -.01em; color: var(--head); }
.stApp .section-sub { color: var(--muted); margin: 0 0 1rem; font-size: .92rem; }

/* ---- sidebar */
/* light sidebar: swap the logo for a copy with dark text (assets/logo.svg has near-white text for the dark sidebar) */
:root[data-app-theme="light"] [data-testid="stSidebarLogo"] { content: url("data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20width=%22190%22%20height=%2236%22%20viewBox=%220%200%20190%2036%22%3E%20%3Crect%20x=%222%22%20y=%224%22%20width=%2228%22%20height=%2228%22%20rx=%227%22%20fill=%22%232563eb%22/%3E%20%3Crect%20x=%228%22%20y=%2219%22%20width=%224%22%20height=%228%22%20rx=%221%22%20fill=%22%23fff%22/%3E%20%3Crect%20x=%2214%22%20y=%2213%22%20width=%224%22%20height=%2214%22%20rx=%221%22%20fill=%22%23fff%22/%3E%20%3Crect%20x=%2220%22%20y=%229%22%20width=%224%22%20height=%2218%22%20rx=%221%22%20fill=%22%23fff%22/%3E%20%3Ctext%20x=%2240%22%20y=%2224%22%20font-family=%22Inter,%20Segoe%20UI,%20Arial,%20sans-serif%22%20font-size=%2217%22%20font-weight=%22600%22%20fill=%22%230f172a%22%3ECensus%20Insight%3C/text%3E%20%3C/svg%3E"); }
.user-chip { display: flex; align-items: center; gap: .65rem; padding: .2rem 0 .65rem; }
.user-info { min-width: 0; }

/* account block: last thing in the sidebar, pinned to the bottom */
[data-testid="stSidebarUserContent"] { display: flex; flex-direction: column; min-height: calc(100% - 4.5rem); }
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] { flex: 1; }
[data-testid="stSidebar"] .st-key-usercard { position: sticky; bottom: 0; margin-top: auto; padding: .9rem 0 1rem; z-index: 2;
                                              background: var(--sb-bg, inherit); border-top: 1px solid var(--rule); }
[data-testid="stSidebar"] .st-key-usercard button { border-radius: 8px; font-weight: 500; }

/* profile dashboard menu */
.stApp .side-title { font-size: 1.05rem; font-weight: 650; letter-spacing: -.01em; color: var(--head); margin: .2rem 0 .9rem; }
.stApp .side-label { font-size: .7rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: .9rem 0 .35rem; }
.stApp .side-note { font-size: .76rem; color: var(--muted); line-height: 1.4; margin-top: 1rem; padding-top: .8rem; border-top: 1px solid var(--rule); }
.st-key-profilenav [role="radiogroup"] { gap: .15rem; }
.st-key-profilenav label[data-baseweb="radio"] { width: 100%; margin: 0; padding: .5rem .7rem; border-radius: 8px; align-items: center;
                                                  border-left: 3px solid transparent; transition: background .12s, color .12s; cursor: pointer; }
.st-key-profilenav label[data-baseweb="radio"] > div:first-child { display: none; }  /* hide the round radio dot */
.st-key-profilenav label[data-baseweb="radio"] p { font-size: .92rem; font-weight: 500; color: var(--muted); display: flex; align-items: center; gap: .55rem; }
.st-key-profilenav label[data-baseweb="radio"]:hover { background: var(--soft); }
.st-key-profilenav label[data-baseweb="radio"]:hover p { color: var(--head); }
.st-key-profilenav label[data-baseweb="radio"]:has(input:checked) { background: var(--soft); border-left-color: var(--accent); }
.st-key-profilenav label[data-baseweb="radio"]:has(input:checked) p { color: var(--accent); font-weight: 600; }
.user-avatar { width: 34px; height: 34px; border-radius: 50%; background: #2563eb; color: #fff; display: flex;
               align-items: center; justify-content: center; font-weight: 600; font-size: .95rem; flex: none; }
.stApp .user-name { font-weight: 600; line-height: 1.2; }
.stApp .user-mail { font-size: .78rem; opacity: .65; line-height: 1.2; overflow-wrap: anywhere; }

/* ---- sign-in screen */
.auth-panel { min-height: 600px; border-radius: 16px; padding: 2.4rem 2.4rem 2rem; color: var(--panel-text); display: flex; flex-direction: column;
              background: var(--panel); border: 1px solid var(--rule); }
.auth-panel .brand { display: flex; align-items: center; gap: .6rem; font-weight: 650; font-size: 1.15rem; color: var(--panel-title); }
.auth-panel .mark { width: 30px; height: 30px; border-radius: 8px; background: #2563eb; display: flex; align-items: flex-end;
                    justify-content: center; gap: 3px; padding-bottom: 7px; }
.auth-panel .mark i { display: block; width: 4px; background: #fff; border-radius: 1px; }
.auth-panel .pitch { font-size: 1.9rem; font-weight: 650; line-height: 1.22; letter-spacing: -.02em; color: var(--panel-title); margin: 3.2rem 0 1.4rem; }
.auth-panel ul { list-style: none; padding: 0; margin: 0; display: grid; gap: .9rem; }
.auth-panel li { display: flex; gap: .7rem; line-height: 1.45; color: var(--panel-text); font-size: .95rem; }
.auth-panel li::before { content: ""; flex: none; width: 7px; height: 7px; margin-top: .5rem; border-radius: 50%; background: var(--panel-dot); }
.auth-panel .foot { margin-top: auto; padding-top: 2rem; font-size: .8rem; color: var(--panel-foot); }
.stApp .auth-title { font-size: 1.6rem; font-weight: 650; letter-spacing: -.02em; margin: 3rem 0 .2rem; color: var(--head); }
.stApp .auth-sub { color: var(--muted); margin-bottom: 1.2rem; }

@media (max-width: 900px) { .auth-panel { min-height: 0; } .auth-panel .pitch { margin-top: 1.6rem; font-size: 1.5rem; } }
@media (max-width: 900px) { .hero-visual, .st-key-hero [data-testid="stElementContainer"]:has(.hero-visual) { display: none; } .st-key-hero { padding: 1.8rem 1.4rem 1.2rem; } .stApp .hero-title { font-size: 1.8rem; }
                            .how-grid { grid-template-columns: 1fr; } }
@media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 2rem; } .result-label { font-size: 1.5rem; }
                            .hero-stats { grid-template-columns: repeat(2, 1fr); } }
</style>
"""
CSS = CSS.replace("{LIGHT}", _vars(LIGHT)).replace("{DARK}", _vars(DARK))

# Streamlit switches theme in the browser without rerunning the script, so Python cannot know the live theme.
# This script reads the real page background and tags <html data-app-theme="light|dark"> on every change.
THEME_JS = """
<script>
(function () {
  if (window.__appThemeWatch) return;
  window.__appThemeWatch = true;
  var root = document.documentElement;
  function lum(c) { var m = c.match(/\\d+(\\.\\d+)?/g); if (!m) return 1; return (0.299*m[0] + 0.587*m[1] + 0.114*m[2]) / 255; }
  function apply() {
    var el = document.querySelector('.stApp') || document.body;
    var t = lum(getComputedStyle(el).backgroundColor) < 0.5 ? 'dark' : 'light';
    if (root.getAttribute('data-app-theme') !== t) root.setAttribute('data-app-theme', t);
  }
  apply();
  new MutationObserver(apply).observe(document.documentElement, {attributes: true, childList: true, subtree: true, attributeFilter: ['class', 'style', 'data-theme']});
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () { setTimeout(apply, 150); });
  setInterval(apply, 1000);
})();
</script>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
    st.html(THEME_JS, unsafe_allow_javascript=True)
