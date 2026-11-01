import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, BarChart3, Bell, Bot, CheckCircle2, Cpu, Database, Filter, BrainCircuit, Cloud, Server, Workflow, SlidersHorizontal, CircleGauge, MessageCircle, Building2, BookOpen, CalendarDays,
  ChevronDown, ChevronRight, Clock3, Droplets, Gauge, Info, Leaf, Menu, MessageSquare,
  Moon, Radio, RefreshCw, Settings, ShieldCheck, Sparkles, Sun, Thermometer,
  Waves, X, Zap, ArrowUpRight
} from "lucide-react";
import {
  AreaChart, Area, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
  LineChart, Line, BarChart, Bar
} from "recharts";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

const readings = [
  { label: "pH", value: "7.18", unit: "", status: "Within range", icon: Activity },
  { label: "Turbidity", value: "2.4", unit: "NTU", status: "Low", icon: Waves },
  { label: "TDS", value: "318", unit: "mg/L", status: "Normal", icon: Droplets },
  { label: "Temperature", value: "26.4", unit: "°C", status: "Normal", icon: Thermometer }
];

const trendData = [
  { time: "08:00", ph: 7.12, turbidity: 2.1, tds: 304 },
  { time: "10:00", ph: 7.16, turbidity: 2.2, tds: 309 },
  { time: "12:00", ph: 7.18, turbidity: 2.4, tds: 318 },
  { time: "14:00", ph: 7.21, turbidity: 2.7, tds: 321 },
  { time: "16:00", ph: 7.17, turbidity: 2.3, tds: 315 },
  { time: "18:00", ph: 7.15, turbidity: 2.2, tds: 312 }
];

const weeklyData = [
  { day: "Mon", score: 86 }, { day: "Tue", score: 88 }, { day: "Wed", score: 84 },
  { day: "Thu", score: 90 }, { day: "Fri", score: 87 }, { day: "Sat", score: 89 },
  { day: "Sun", score: 91 }
];

const alerts = [
  { title: "Turbidity rose above the usual baseline", time: "Today, 14:12", severity: "Watch", text: "A short increase was detected. Current value is back within the normal operating band." },
  { title: "Monitoring connection restored", time: "Today, 11:42", severity: "Resolved", text: "The monitoring gateway reconnected to the MQTT broker after a 42-second interruption." },
  { title: "Daily water quality check completed", time: "Today, 08:00", severity: "Info", text: "All four monitored parameters were received successfully." }
];

function Shell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const location = useLocation();

  return (
    <div className={dark ? "app dark" : "app"}>
      <header className="topbar">
        <Link to="/" className="brand" onClick={() => setMobileOpen(false)}>
          <span className="brand-mark"><Droplets size={20} strokeWidth={2.2} /></span>
          <span>
            <strong>ClearWater</strong>
            <small>quality intelligence</small>
          </span>
        </Link>

        <nav className={mobileOpen ? "nav open" : "nav"}>
          <NavLink to="/" end onClick={() => setMobileOpen(false)}>Home</NavLink>
          <NavLink to="/dashboard" onClick={() => setMobileOpen(false)}>Sensor Readings</NavLink>
          <NavLink to="/analytics" onClick={() => setMobileOpen(false)}>Analysis</NavLink>
          <NavLink to="/history" onClick={() => setMobileOpen(false)}>10-Day History</NavLink>
          <NavLink to="/agentic-ai" onClick={() => setMobileOpen(false)}>Agentic AI</NavLink>
          <NavLink to="/alerts" onClick={() => setMobileOpen(false)}>Alerts</NavLink>
                    <NavLink to="/feedback" onClick={() => setMobileOpen(false)}>Feedback</NavLink>
        </nav>

        <div className="top-actions">
          <button className="icon-btn" onClick={() => setDark(!dark)} title="Toggle theme">
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link className="status-pill" to="/dashboard">
            <span className="live-dot"></span> Live
          </Link>
          {localStorage.getItem("clearwater_current_user") ? (
            <button className="icon-btn" title="Sign out" onClick={() => { localStorage.removeItem("clearwater_current_user"); window.location.href = "/"; }}>↪</button>
          ) : (
            <Link className="status-pill" to="/login">Sign in</Link>
          )}
          <button className="mobile-menu icon-btn" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {location.pathname !== "/" && <div className="page-strip"><span>Monitoring network</span><span>•</span><span>Live monitoring</span><span>•</span><span>Updated just now</span></div>}
      <main>{children}</main>
    </div>
  );
}

function Home() {
  const [live, setLive] = useState({ph:7.18,turbidity:2.4,tds:318,temperature:26.4,condition:"Safe",confidence:94.2,qualityScore:87,wqi:{value:34.8,band:"Good"}});
  useEffect(() => {
    fetch("/api/readings").then(r => r.ok ? r.json() : null).then(d => d && setLive(d)).catch(() => {});
  }, []);
  const conditionSafe = live.condition === "Safe";
  return (
    <div className="cw-home">
      <style>{`\
        .cw-home{--cw-ink:#153b38;--cw-muted:#637875;--cw-teal:#167c73;--cw-teal-dark:#0f625b;--cw-mint:#dff2ed;--cw-cream:#f7f5ee;--cw-line:#dbe7e3;background:var(--cw-cream);color:var(--cw-ink);min-height:calc(100vh - 70px);overflow:hidden}\
        .cw-home *{box-sizing:border-box}.cw-container{width:min(1160px,calc(100% - 40px));margin:auto}\
        .cw-hero{position:relative;padding:76px 0 82px;background:radial-gradient(circle at 83% 28%,rgba(104,184,171,.25),transparent 28%),linear-gradient(135deg,#f7f5ee 0%,#edf6f2 52%,#dff1ec 100%)}\
        .cw-hero-grid{display:grid;grid-template-columns:1.03fr .97fr;align-items:center;gap:65px;position:relative;z-index:1}.cw-kicker{display:inline-flex;align-items:center;gap:9px;font-size:12px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--cw-teal);margin-bottom:18px}.cw-kicker:before{content:"";width:30px;height:2px;background:currentColor}\
        .cw-hero h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(46px,6vw,76px);line-height:.99;letter-spacing:-.045em;margin:0 0 24px;max-width:680px;font-weight:600}.cw-hero h1 em{color:var(--cw-teal);font-weight:500;font-style:italic}.cw-lead{font-size:18px;line-height:1.7;color:#5f716e;max-width:600px;margin:0 0 30px}.cw-actions{display:flex;align-items:center;gap:13px;flex-wrap:wrap}.cw-btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:999px;padding:13px 19px;text-decoration:none;font-weight:750;font-size:14px;transition:.2s}.cw-btn:hover{transform:translateY(-2px)}.cw-btn-main{background:var(--cw-teal);color:white;box-shadow:0 12px 28px rgba(22,124,115,.2)}.cw-btn-main:hover{background:var(--cw-teal-dark)}.cw-btn-quiet{color:var(--cw-ink);border:1px solid #cbdad5;background:rgba(255,255,255,.55)}.cw-note{display:flex;align-items:center;gap:8px;margin-top:20px;font-size:12px;color:#71827f}\
        .cw-live-card{position:relative;max-width:500px;margin-left:auto}.cw-card-shadow{position:absolute;z-index:1;inset:28px -22px -18px 24px;background:rgba(22,124,115,.12);border-radius:34px;transform:rotate(3deg)}.cw-monitor{position:relative;z-index:2;background:rgba(255,255,255,.9);border:1px solid rgba(255,255,255,.9);border-radius:30px;padding:22px;box-shadow:0 25px 70px rgba(28,76,70,.14);backdrop-filter:blur(14px)}.cw-monitor-top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e4ece9;padding-bottom:17px;margin-bottom:18px}.cw-station{display:flex;gap:11px;align-items:center}.cw-station-mark{width:40px;height:40px;border-radius:14px;background:#e3f3ef;display:grid;place-items:center;color:var(--cw-teal)}.cw-station strong{display:block;font-size:14px}.cw-station small{display:block;color:#82918e;margin-top:3px}.cw-online{font-size:11px;color:#257d62;font-weight:800;background:#e8f7ef;padding:7px 10px;border-radius:999px}.cw-online i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#35a76d;margin-right:6px}.cw-score-row{display:grid;grid-template-columns:1fr 170px;gap:18px;align-items:center}.cw-condition-label{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#84918f;font-weight:800}.cw-score{font-size:64px;line-height:1;margin:8px 0 3px;font-weight:800;letter-spacing:-.05em}.cw-score span{font-size:17px;color:#94a29f;font-weight:600}.cw-safe{display:inline-flex;align-items:center;gap:6px;color:#227558;font-size:13px;font-weight:800}.cw-ring{width:150px;height:150px;border-radius:50%;background:conic-gradient(var(--cw-teal) 0 87%,#e8efed 87% 100%);display:grid;place-items:center;margin:auto;position:relative}.cw-ring:after{content:"";position:absolute;width:118px;height:118px;border-radius:50%;background:white}.cw-ring div{position:relative;z-index:1;text-align:center}.cw-ring strong{display:block;font-size:25px}.cw-ring small{font-size:10px;color:#83928f}.cw-reading-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:20px}.cw-reading{background:#f5f8f7;border:1px solid #e4ece9;border-radius:14px;padding:12px}.cw-reading small{display:block;color:#82908e;font-size:10px;margin-bottom:4px}.cw-reading strong{font-size:17px}.cw-reading em{font-style:normal;color:#7a8986;font-size:10px;margin-left:2px}\
        .cw-hero-photo{position:absolute;inset:-54px -46px 70px 74px;border-radius:34px;overflow:hidden;z-index:0;box-shadow:0 28px 80px rgba(16,74,68,.18);border:7px solid rgba(255,255,255,.72)}.cw-hero-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,47,44,.03) 35%,rgba(5,47,44,.48) 100%)}.cw-hero-photo img{width:100%;height:100%;object-fit:cover;display:block}        .cw-water-drops{position:absolute;inset:0;pointer-events:none;z-index:0;overflow:hidden}.cw-drop{position:absolute;top:-80px;width:24px;height:32px;object-fit:contain;opacity:0;filter:drop-shadow(0 8px 12px rgba(18,117,108,.22));animation:cwDropFall 7.2s cubic-bezier(.22,.61,.36,1) infinite}.cw-drop-1{left:7%;width:17px;animation-delay:-1.2s}.cw-drop-2{left:21%;width:12px;animation-delay:-4.8s}.cw-drop-3{left:39%;width:21px;animation-delay:-2.8s}.cw-drop-4{left:58%;width:15px;animation-delay:-5.7s}.cw-drop-5{left:72%;width:24px;animation-delay:-3.4s}.cw-drop-6{left:84%;width:13px;animation-delay:-6.3s}.cw-drop-7{left:94%;width:18px;animation-delay:-1.9s}@keyframes cwDropFall{0%{top:-80px;opacity:0;transform:translate3d(0,0,0) rotate(-7deg)}10%{opacity:.72}38%{transform:translate3d(10px,24vh,0) rotate(4deg);opacity:.6}68%{transform:translate3d(-7px,58vh,0) rotate(-3deg);opacity:.48}100%{top:110%;transform:translate3d(5px,0,0) rotate(5deg);opacity:0}}.cw-hero:after{content:"";position:absolute;width:520px;height:520px;right:-210px;top:-170px;border-radius:50%;border:1px solid rgba(34,145,133,.12);box-shadow:0 0 0 24px rgba(34,145,133,.035),0 0 0 52px rgba(34,145,133,.02);pointer-events:none}        .cw-live-card{filter:drop-shadow(0 18px 30px rgba(22,124,115,.06))}        .cw-hero-photo{background:linear-gradient(145deg,#dcefeb,#b7d8d2)}        .cw-hero-photo img{padding:0;mix-blend-mode:normal;filter:saturate(.92) contrast(1.03)}        .cw-hero-photo-label{box-shadow:0 12px 30px rgba(20,75,69,.12)}.cw-hero-photo-label{position:absolute;z-index:2;left:18px;bottom:18px;display:flex;gap:9px;align-items:center;padding:10px 12px;background:rgba(255,255,255,.9);backdrop-filter:blur(14px);border-radius:14px}.cw-hero-photo-label span{width:8px;height:8px;border-radius:50%;background:#35a76d;box-shadow:0 0 0 5px rgba(53,167,109,.12)}.cw-hero-photo-label strong{display:block;font-size:11px}.cw-hero-photo-label small{display:block;color:#73827f;font-size:9px;margin-top:2px}.cw-real-gallery{padding:92px 0;background:#f5f8f7}.cw-gallery-head{display:grid;grid-template-columns:1fr 420px;gap:40px;align-items:end;margin-bottom:30px}.cw-gallery-head h2{font-family:Georgia,serif;font-size:48px;line-height:1.02;letter-spacing:-.04em;margin:0}.cw-gallery-head p{margin:0;color:#687975;line-height:1.7;font-size:14px}.cw-gallery-grid{display:grid;grid-template-columns:1.35fr .85fr .85fr;gap:16px}.cw-gallery-grid figure{margin:0;background:#fff;border:1px solid #e0eae7;border-radius:24px;overflow:hidden;box-shadow:0 15px 35px rgba(26,73,68,.06)}.cw-gallery-grid figure img{width:100%;height:280px;object-fit:cover;display:block}.cw-gallery-grid .cw-gallery-main img{height:420px}.cw-gallery-grid figcaption{padding:15px 16px 17px}.cw-gallery-grid figcaption strong{display:block;font-size:13px}.cw-gallery-grid figcaption span{display:block;color:#7a8986;font-size:10px;margin-top:4px}.cw-image-source-note{margin-top:14px;color:#91a09d;font-size:9px;line-height:1.5}@media(max-width:900px){.cw-hero-photo{position:relative;inset:auto;height:300px;margin-bottom:-12px}.cw-live-card{padding-top:0}.cw-gallery-head{grid-template-columns:1fr}.cw-gallery-grid{grid-template-columns:1fr 1fr}.cw-gallery-grid .cw-gallery-main{grid-column:1/-1}.cw-gallery-grid .cw-gallery-main img{height:340px}}@media(max-width:560px){.cw-hero-photo{height:240px;margin-bottom:12px}.cw-gallery-grid{grid-template-columns:1fr}.cw-gallery-grid .cw-gallery-main{grid-column:auto}.cw-gallery-grid figure img,.cw-gallery-grid .cw-gallery-main img{height:260px}.cw-gallery-head h2{font-size:35px}}
        .cw-home-actions{padding:38px 0 70px}.cw-action-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.cw-action-card{display:flex;align-items:center;gap:13px;padding:18px;background:white;border:1px solid #e1ebe8;border-radius:18px;text-decoration:none;color:var(--cw-ink);box-shadow:0 10px 25px rgba(28,76,70,.05);transition:.2s}.cw-action-card:hover{transform:translateY(-3px);border-color:#bcd8d1}.cw-action-icon{width:40px;height:40px;border-radius:13px;background:#e7f4f0;color:var(--cw-teal);display:grid;place-items:center;flex:none}.cw-action-card strong{display:block;font-size:14px}.cw-action-card span{display:block;color:#7a8986;font-size:11px;margin-top:3px}.cw-footer{padding:28px 0;border-top:1px solid var(--cw-line);color:#7a8986;font-size:12px}.cw-footer-inner{display:flex;justify-content:space-between;gap:20px}.cw-footer strong{color:var(--cw-ink);font-size:14px;margin-right:9px}\

        .cw-drop{object-fit:contain;mix-blend-mode:multiply}
        .cw-floating-drop{position:absolute;z-index:4;right:5%;top:-34px;width:72px;height:92px;animation:cwFloatDrop 4.8s ease-in-out infinite;filter:drop-shadow(0 10px 14px rgba(17,116,108,.2));pointer-events:none}.cw-floating-drop img{width:100%;height:100%;object-fit:contain}.cw-floating-drop{mix-blend-mode:multiply}@keyframes cwFloatDrop{0%,100%{transform:translateY(0) rotate(-3deg);opacity:.9}50%{transform:translateY(16px) rotate(4deg);opacity:1}}
        @media(max-width:900px){.cw-hero-grid{grid-template-columns:1fr;gap:45px}.cw-live-card{margin:auto}.cw-action-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.cw-container{width:min(100% - 28px,1160px)}.cw-hero{padding:50px 0 60px}.cw-hero h1{font-size:45px}.cw-score-row{grid-template-columns:1fr}.cw-ring{width:125px;height:125px}.cw-ring:after{width:98px;height:98px}.cw-action-grid{grid-template-columns:1fr}.cw-footer-inner{flex-direction:column}}\
        .cw-visual-story{padding:90px 0;background:#fff}.cw-visual-grid{display:grid;grid-template-columns:1.02fr .98fr;gap:72px;align-items:center}.cw-visual-photo{position:relative;min-height:470px;border-radius:36px;overflow:hidden;background:#d9ebe7;box-shadow:0 30px 80px rgba(20,75,69,.13)}.cw-visual-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 50%,rgba(7,49,46,.34));pointer-events:none}.cw-visual-photo img{width:100%;height:100%;min-height:470px;object-fit:cover;display:block;transform:scale(1.04)}.cw-photo-badge{position:absolute;left:22px;bottom:22px;z-index:2;display:flex;align-items:center;gap:10px;padding:12px 15px;border-radius:16px;background:rgba(255,255,255,.92);backdrop-filter:blur(14px);box-shadow:0 15px 35px rgba(0,0,0,.12)}.cw-photo-dot{width:9px;height:9px;border-radius:50%;background:#35a76d;box-shadow:0 0 0 5px rgba(53,167,109,.12)}.cw-photo-badge strong{display:block;font-size:12px}.cw-photo-badge small{display:block;color:#72827f;font-size:10px;margin-top:3px}.cw-visual-copy h2{font-family:Georgia,"Times New Roman",serif;font-size:48px;line-height:1.02;letter-spacing:-.04em;margin:0 0 20px;max-width:600px}.cw-visual-copy>p{color:#657774;font-size:16px;line-height:1.75;max-width:560px}.cw-visual-points{display:grid;gap:0;margin-top:30px;border-top:1px solid #dbe7e3}.cw-visual-points>div{display:grid;grid-template-columns:40px 1fr;gap:14px;padding:17px 0;border-bottom:1px solid #dbe7e3}.cw-visual-points>div>span{font-size:11px;color:#167c73;font-weight:800;padding-top:2px}.cw-visual-points strong{display:block;font-size:14px}.cw-visual-points small{display:block;color:#788985;font-size:11px;line-height:1.5;margin-top:4px}.cw-showcase-band{padding:42px 0;background:linear-gradient(135deg,#075d57,#11948a);color:white}.cw-showcase-grid{display:grid;grid-template-columns:1fr auto;align-items:center;gap:40px}.cw-showcase-kicker{text-transform:uppercase;letter-spacing:.14em;font-size:10px;font-weight:800;color:#a7ddd4}.cw-showcase-band h2{font-family:Georgia,serif;font-size:32px;margin:8px 0 0;letter-spacing:-.025em}.cw-showcase-stats{display:flex;gap:38px}.cw-showcase-stats div{min-width:90px}.cw-showcase-stats strong{display:block;font-size:29px}.cw-showcase-stats span{display:block;color:#b9d9d5;font-size:10px;margin-top:3px}@media(max-width:900px){.cw-visual-grid{grid-template-columns:1fr;gap:38px}.cw-visual-photo,.cw-visual-photo img{min-height:380px}.cw-visual-copy h2{font-size:40px}.cw-showcase-grid{grid-template-columns:1fr}.cw-showcase-stats{justify-content:space-between}}@media(max-width:560px){.cw-visual-story{padding:65px 0}.cw-visual-photo,.cw-visual-photo img{min-height:300px}.cw-visual-copy h2{font-size:35px}.cw-showcase-stats{gap:18px;flex-wrap:wrap}.cw-showcase-stats div{min-width:70px}}\
      `}</style>
      <section className="cw-hero">
        <div className="cw-water-drops" aria-hidden="true"><img className="cw-drop cw-drop-1" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-2" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-3" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-4" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-5" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-6" src="/images/realistic-water-drop-user.png" alt="" /><img className="cw-drop cw-drop-7" src="/images/realistic-water-drop-user.png" alt="" /></div>
        <div className="cw-container cw-hero-grid">
          <div>
            <div className="cw-kicker">Live water monitoring</div>
            <h1>Know your water <em>in real time.</em></h1>
            <p className="cw-lead">ClearWater monitors pH, turbidity, TDS and temperature, turns the latest readings into a water-quality result, and lets you ask Agentic AI what the numbers mean.</p>
            <div className="cw-actions"><Link to="/dashboard" className="cw-btn cw-btn-main">Open dashboard <ArrowRight size={16}/></Link><Link to="/agentic-ai" className="cw-btn cw-btn-quiet"><Bot size={16}/> Ask Agentic AI</Link></div>
            <div className="cw-note"><ShieldCheck size={15}/> 4 parameters monitored · WQI included</div>
          </div>
          <div className="cw-live-card"><div className="cw-hero-photo"><img src="https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/USGS_opticalsensor_fixedmonitoring.jpg" onError={(e)=>{e.currentTarget.src="/images/field-water-monitoring.png";}} alt="USGS water quality monitoring station" /><div className="cw-hero-photo-label"><span></span><div><strong>Real-time water station</strong><small>IoT sensor deployment</small></div></div><div className="cw-floating-drop" aria-hidden="true"><img src="/images/realistic-water-drop-user.png" alt="" /></div></div><div className="cw-card-shadow"></div><div className="cw-monitor">
            <div className="cw-monitor-top"><div className="cw-station"><span className="cw-station-mark"><Droplets size={19}/></span><div><strong>Live monitoring</strong><small>Water quality station</small></div></div><span className="cw-online"><i></i> LIVE</span></div>
            <div className="cw-score-row"><div><div className="cw-condition-label">Water Quality Index</div><div className="cw-score">{live.wqi?.value ?? live.qualityScore}<span>/100</span></div><div className="cw-safe" style={{color:conditionSafe?"#227558":"#a04c42"}}>{conditionSafe?<CheckCircle2 size={15}/>:<AlertTriangle size={15}/>} {live.wqi?.band || live.condition}</div></div><div className="cw-ring" style={{background:`conic-gradient(var(--cw-teal) 0 ${Math.min(100,Math.max(0,Number(live.wqi?.value ?? live.qualityScore ?? 0)))}%,#e8efed ${Math.min(100,Math.max(0,Number(live.wqi?.value ?? live.qualityScore ?? 0)))}% 100%)`}}><div><strong>{Number(live.wqi?.value ?? live.qualityScore ?? 0).toFixed(0)}</strong><small>WQI / 100</small></div></div></div>
            <div className="cw-reading-grid"><div className="cw-reading"><small>pH</small><strong>{live.ph}</strong></div><div className="cw-reading"><small>Turbidity</small><strong>{live.turbidity}</strong><em>NTU</em></div><div className="cw-reading"><small>TDS</small><strong>{live.tds}</strong><em>mg/L</em></div><div className="cw-reading"><small>Temp.</small><strong>{live.temperature}</strong><em>°C</em></div></div>
          </div></div>
        </div>
      </section>
      <section className="cw-home-actions"><div className="cw-container"><div className="cw-action-grid">
        <Link to="/dashboard" className="cw-action-card"><span className="cw-action-icon"><Gauge size={18}/></span><div><strong>Live readings</strong><span>See all sensor values</span></div></Link>
        <Link to="/analytics" className="cw-action-card"><span className="cw-action-icon"><BarChart3 size={18}/></span><div><strong>Analysis</strong><span>View trends and scores</span></div></Link>
        <Link to="/agentic-ai" className="cw-action-card"><span className="cw-action-icon"><Bot size={18}/></span><div><strong>Agentic AI</strong><span>Ask about the current data</span></div></Link>
        <Link to="/alerts" className="cw-action-card"><span className="cw-action-icon"><Bell size={18}/></span><div><strong>Alerts</strong><span>Check warnings and events</span></div></Link>
      </div></div></section>
      <section className="cw-visual-story">
        <div className="cw-container cw-visual-grid">
          <div className="cw-visual-photo">
            <img src="https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/sensor_101_0628.JPG" onError={(e)=>{e.currentTarget.src="/images/industrial-monitoring.png";}} alt="Real water quality sensor equipment" />
            <div className="cw-photo-badge"><span className="cw-photo-dot"></span><div><strong>Monitoring online</strong><small>Sensor station connected</small></div></div>
          </div>
          <div className="cw-visual-copy">
            <div className="cw-kicker">Built around the water, not the dashboard</div>
            <h2>See the environment. Then understand the numbers.</h2>
            <p>ClearWater combines a calm visual experience with live sensor context, trend analysis and AI explanations so the important information is easy to find.</p>
            <div className="cw-visual-points">
              <div><span>01</span><div><strong>Live sensor context</strong><small>pH, turbidity, TDS and temperature in one view.</small></div></div>
              <div><span>02</span><div><strong>Visual trends</strong><small>Follow changes over time instead of isolated readings.</small></div></div>
              <div><span>03</span><div><strong>Human-friendly AI</strong><small>Ask why a value changed and what to check next.</small></div></div>
            </div>
          </div>
        </div>
      </section>
      <section className="cw-real-gallery">
        <div className="cw-container">
          <div className="cw-gallery-head"><div><div className="cw-kicker">Real monitoring in the field</div><h2>Designed around real water-quality hardware.</h2></div><p>Real-world sensor installations and laboratory testing inspire the visual language of this monitoring experience.</p></div>
          <div className="cw-gallery-grid">
            <figure className="cw-gallery-main"><img src="https://upload.wikimedia.org/wikipedia/commons/a/a4/Water_Quality_Testing_%2848366433581%29.jpg" onError={(e)=>{e.currentTarget.src="/images/water-landscape-real.png";}} alt="Real water quality field testing" /><figcaption><strong>Field monitoring</strong><span>Multi-probe water quality station</span></figcaption></figure>
            <figure><img src="https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/sensor_101_0628.JPG" onError={(e)=>{e.currentTarget.src="/images/industrial-monitoring.png";}} alt="Real water quality sensor equipment" /><figcaption><strong>Industrial monitoring</strong><span>Sensor data and live trends</span></figcaption></figure>
            <figure><img src="https://upload.wikimedia.org/wikipedia/commons/a/a4/Water_Quality_Testing_%2848366433581%29.jpg" onError={(e)=>{e.currentTarget.src="/images/water-testing-lab.png";}} alt="Real water quality testing" /><figcaption><strong>Sensor testing</strong><span>Probe-based measurement</span></figcaption></figure>
          </div>
          <div className="cw-image-source-note">Visual references are packaged locally so the page remains reliable without external image loading.</div>
        </div>
      </section>
      <section className="cw-showcase-band">
        <div className="cw-container cw-showcase-grid">
          <div><span className="cw-showcase-kicker">One connected workflow</span><h2>Sense · Analyze · Explain · Improve</h2></div>
          <div className="cw-showcase-stats"><div><strong>4</strong><span>sensor inputs</span></div><div><strong>10</strong><span>day history</span></div><div><strong>AI</strong><span>decision support</span></div></div>
        </div>
      </section>
      <footer className="cw-footer"><div className="cw-container cw-footer-inner"><div><strong>ClearWater</strong> IoT water quality monitoring</div><div>Academic project · 2026–27</div></div></footer>
    </div>
  );
}

function getUsers() {
  try { return JSON.parse(localStorage.getItem("clearwater_users") || "[]"); }
  catch { return []; }
}

function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth-page">
      <style>{`
        .auth-page{min-height:100vh;background:radial-gradient(circle at 15% 15%,rgba(84,176,160,.18),transparent 28%),linear-gradient(135deg,#f7f5ee,#e5f3ef);display:grid;place-items:center;padding:28px;color:#153b38}
        .auth-wrap{width:min(100%,980px);display:grid;grid-template-columns:1fr 1fr;background:rgba(255,255,255,.82);border:1px solid rgba(255,255,255,.9);border-radius:30px;overflow:hidden;box-shadow:0 30px 90px rgba(24,73,67,.15);backdrop-filter:blur(16px)}
        .auth-story{padding:48px;background:#103f3b;color:white;position:relative;overflow:hidden}.auth-story:after{content:"";position:absolute;width:360px;height:360px;border:1px solid rgba(255,255,255,.12);border-radius:50%;right:-170px;bottom:-160px;box-shadow:0 0 0 50px rgba(255,255,255,.025),0 0 0 100px rgba(255,255,255,.02)}
        .auth-brand{display:flex;align-items:center;gap:11px;font-size:18px;font-weight:800}.auth-brand span{width:40px;height:40px;border-radius:14px;background:#dff2ed;color:#167c73;display:grid;place-items:center}.auth-story h1{font-family:Georgia,serif;font-size:45px;line-height:1.02;margin:75px 0 18px;letter-spacing:-.04em}.auth-story p{color:#b6cfca;line-height:1.7;max-width:390px}.auth-points{margin-top:35px;display:grid;gap:14px}.auth-point{display:flex;gap:10px;align-items:center;color:#d8e8e5;font-size:13px}.auth-point svg{color:#8fd0c3}
        .auth-form{padding:48px}.auth-kicker{font-size:11px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:#167c73;margin-bottom:10px}.auth-form h2{font-family:Georgia,serif;font-size:36px;margin:0 0 8px}.auth-form>p{color:#70817e;font-size:14px;line-height:1.6;margin:0 0 27px}.auth-field{display:grid;gap:7px;margin-bottom:15px}.auth-field label{font-size:12px;font-weight:800;color:#45635e}.auth-field input{width:100%;border:1px solid #d7e4e0;background:#fbfdfc;border-radius:13px;padding:12px 13px;font:inherit;outline:none;transition:.2s}.auth-field input:focus{border-color:#167c73;box-shadow:0 0 0 3px rgba(22,124,115,.1)}.auth-error{background:#fff0ee;border:1px solid #f2c9c3;color:#a34e43;border-radius:12px;padding:10px 12px;font-size:12px;margin-bottom:15px}.auth-success{background:#edf9f2;border:1px solid #cce8d7;color:#2a7653;border-radius:12px;padding:10px 12px;font-size:12px;margin-bottom:15px}.auth-submit{width:100%;border:0;border-radius:13px;padding:13px;background:#167c73;color:white;font-weight:800;cursor:pointer;box-shadow:0 12px 25px rgba(22,124,115,.18);transition:.2s}.auth-submit:hover{background:#0f625b;transform:translateY(-1px)}.auth-switch{text-align:center;color:#788985;font-size:12px;margin-top:19px}.auth-switch a{color:#167c73;font-weight:800;text-decoration:none}.auth-back{display:inline-flex;align-items:center;gap:6px;color:#71817e;text-decoration:none;font-size:12px;margin-bottom:24px}.auth-check{display:flex;gap:8px;align-items:flex-start;font-size:11px;color:#788985;margin:5px 0 17px}.auth-check input{margin-top:2px}.auth-logged{margin-top:18px;text-align:center;color:#71817e;font-size:12px}.auth-logged button{border:0;background:none;color:#167c73;font-weight:800;cursor:pointer}
        @media(max-width:760px){.auth-wrap{grid-template-columns:1fr}.auth-story{display:none}.auth-form{padding:34px 25px}}
      `}</style>
      <div className="auth-wrap">
        <div className="auth-story">
          <div className="auth-brand"><span><Droplets size={21}/></span>ClearWater</div>
          <h1>Water intelligence made easier to understand.</h1>
          <p>Create your account and keep your monitoring dashboard, analysis and AI decision support in one place.</p>
          <div className="auth-points"><div className="auth-point"><CheckCircle2 size={16}/> Live sensor readings</div><div className="auth-point"><CheckCircle2 size={16}/> CNN-LSTM analysis</div><div className="auth-point"><CheckCircle2 size={16}/> Agentic AI explanations</div><div className="auth-point"><CheckCircle2 size={16}/> Human feedback loop</div></div>
        </div>
        <div className="auth-form">
          <Link to="/" className="auth-back"><ArrowRight size={14} style={{transform:"rotate(180deg)"}}/> Back to home</Link>
          {children}
          {footer}
        </div>
      </div>
    </div>
  );
}

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({name:"", email:"", password:"", confirm:""});
  const [error, setError] = useState("");
  const submit = (e) => {
    e.preventDefault(); setError("");
    if (!form.name.trim() || !form.email.trim() || !form.password) return setError("Please complete all required fields.");
    if (form.password.length < 6) return setError("Password must contain at least 6 characters.");
    if (form.password !== form.confirm) return setError("Passwords do not match.");
    const users = getUsers();
    if (users.some(u => u.email.toLowerCase() === form.email.trim().toLowerCase())) return setError("An account with this email already exists.");
    const user = {name:form.name.trim(), email:form.email.trim().toLowerCase(), password:form.password};
    localStorage.setItem("clearwater_users", JSON.stringify([...users, user]));
    localStorage.setItem("clearwater_current_user", JSON.stringify({name:user.name,email:user.email}));
    navigate("/dashboard");
  };
  return <AuthShell title="Create account" subtitle="Start using ClearWater to explore your monitoring system." footer={<div className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></div>}>
    <div className="auth-kicker">Welcome to ClearWater</div><h2>Create your account</h2><p>It only takes a minute. Your account is stored locally for this frontend demo.</p>
    <form onSubmit={submit}>
      {error && <div className="auth-error">{error}</div>}
      <div className="auth-field"><label>Full name</label><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Your name" /></div>
      <div className="auth-field"><label>Email address</label><input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com" /></div>
      <div className="auth-field"><label>Password</label><input type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="Minimum 6 characters" /></div>
      <div className="auth-field"><label>Confirm password</label><input type="password" value={form.confirm} onChange={e=>setForm({...form,confirm:e.target.value})} placeholder="Repeat your password" /></div>
      <label className="auth-check"><input type="checkbox" required /> I agree to use this demo account for monitoring and project testing.</label>
      <button className="auth-submit">Create account <ArrowRight size={15} style={{verticalAlign:"middle",marginLeft:5}}/></button>
    </form>
  </AuthShell>;
}

function Login() {
  const navigate = useNavigate();
  const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState("");
  const submit=(e)=>{e.preventDefault();setError("");const user=getUsers().find(u=>u.email===email.trim().toLowerCase()&&u.password===password);if(!user)return setError("Email or password is incorrect.");localStorage.setItem("clearwater_current_user",JSON.stringify({name:user.name,email:user.email}));navigate("/dashboard")};
  return <AuthShell title="Welcome back" subtitle="Sign in to continue to your water monitoring workspace." footer={<div className="auth-switch">New to ClearWater? <Link to="/register">Create an account</Link></div>}>
    <div className="auth-kicker">ClearWater account</div><h2>Sign in</h2><p>Access your sensor readings, analysis and AI decision support.</p>
    <form onSubmit={submit}>
      {error && <div className="auth-error">{error}</div>}
      <div className="auth-field"><label>Email address</label><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" required /></div>
      <div className="auth-field"><label>Password</label><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Your password" required /></div>
      <button className="auth-submit">Sign in <ArrowRight size={15} style={{verticalAlign:"middle",marginLeft:5}}/></button>
    </form>
  </AuthShell>;
}

function ProtectedRoute({ children }) {
  const location = useLocation();
  const user = localStorage.getItem("clearwater_current_user");
  if (!user) return <Navigate to="/login" state={{from:location.pathname}} replace />;
  return children;
}

function PageHeader({ eyebrow, title, text, action }) {
  return (
    <div className="container page-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        {text && <p>{text}</p>}
      </div>
      {action}
    </div>
  );
}

function MetricCard({ item }) {
  const Icon = item.icon;
  return (
    <div className="metric-card">
      <div className="metric-top"><span>{item.label}</span><span className="metric-icon"><Icon size={18}/></span></div>
      <div className="metric-value">{item.value}<small>{item.unit}</small></div>
      <div className="metric-bottom"><span className="status-dot"></span>{item.status}</div>
    </div>
  );
}

function Dashboard() {
  const [refreshing, setRefreshing] = useState(false);
  const [liveReadings, setLiveReadings] = useState(readings);
  const [condition, setCondition] = useState("Safe");
  const [confidence, setConfidence] = useState(94.2);
  const [qualityScore, setQualityScore] = useState(87);
  const [wqi, setWqi] = useState({value:34.8,band:"Good",weights:{pH:0,turbidity:0,tds:0}});
  const [form, setForm] = useState({ph:7.18,turbidity:2.4,tds:318,temperature:26.4});
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");

  // Keep the hero parameter values in sync with the live metric cards.
  const live = {
    ph: liveReadings.find((item) => item.label === "pH")?.value ?? form.ph,
    turbidity: liveReadings.find((item) => item.label === "Turbidity")?.value ?? form.turbidity,
    tds: liveReadings.find((item) => item.label === "TDS")?.value ?? form.tds,
    temperature: liveReadings.find((item) => item.label === "Temperature")?.value ?? form.temperature,
  };

  const applyReading = (d) => {
    setLiveReadings([
      {label:"pH",value:String(d.ph),unit:"",status:Number(d.ph)>=6.5&&Number(d.ph)<=8.5?"Within range":"Outside range",icon:Activity},
      {label:"Turbidity",value:String(d.turbidity),unit:"NTU",status:Number(d.turbidity)<=5?"Normal":"High",icon:Waves},
      {label:"TDS",value:String(d.tds),unit:"mg/L",status:Number(d.tds)<=500?"Normal":"High",icon:Droplets},
      {label:"Temperature",value:String(d.temperature),unit:"°C",status:Number(d.temperature)>=0&&Number(d.temperature)<=40?"Normal":"Outside range",icon:Thermometer}
    ]);
    setCondition(d.condition || "Safe");
    setConfidence(Number(d.confidence || 0));
    setQualityScore(Number(d.qualityScore || 0));
    setWqi(d.wqi || {value:Number(d.qualityScore || 0),band:"Monitoring index",weights:{pH:0,turbidity:0,tds:0}});
    setForm({ph:d.ph,turbidity:d.turbidity,tds:d.tds,temperature:d.temperature});
  };

  const refresh = async () => {
    setRefreshing(true);
    try {
      const res = await fetch("/api/readings");
      if (!res.ok) throw new Error("Backend unavailable");
      applyReading(await res.json());
    } catch(e) {}
    finally { setTimeout(() => setRefreshing(false), 450); }
  };

  const sendReading = async () => {
    setSending(true); setMessage("");
    try {
      const payload={ph:Number(form.ph),turbidity:Number(form.turbidity),tds:Number(form.tds),temperature:Number(form.temperature)};
      const r=await fetch("/api/readings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      const d=await r.json();
      if(!r.ok) throw new Error(d.error || "Could not update reading");
      applyReading(d);
      setMessage(`Reading updated. ${d.condition || "Current condition"}. Open Agentic AI and ask a question about it.`);
    } catch(e) {
      setMessage("Backend is not running. Start the project with npm run dev.");
    } finally { setSending(false); }
  };

  useEffect(() => { refresh(); }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-intro">
        <div className="container dashboard-intro-inner">
          <div className="dashboard-breadcrumb"><span>Monitoring</span><ChevronRight size={13}/><b>Water quality</b><span className="intro-live"><i></i> Live</span></div>
          <div className="dashboard-intro-grid">
            <div>
              <div className="eyebrow"><span className="eyebrow-line"></span> Live water intelligence</div>
              <h1>Water quality <em>at a glance.</em></h1>
              <p>One clear view of the latest sensor state, recent trends and the AI-ready context behind your water-quality monitoring.</p>
            </div>
            <div className="dashboard-intro-actions">
              <div className="last-sync"><span>Last sync</span><strong>Just now</strong></div>
              <button className="btn primary dashboard-refresh" onClick={refresh}><RefreshCw size={16} className={refreshing ? "spin" : ""}/> {refreshing ? "Refreshing" : "Refresh data"}</button>
            </div>
          </div>
        </div>
      </div>

      <section className="container dashboard-shell">
        <div className="station-hero">
          <div className="station-hero-glow"></div>
          <div className="station-copy">
            <div className="station-status"><span className="live-dot"></span> Live water monitoring</div>
            <div className="station-title-row"><div><span className="station-kicker">Current water quality</span><h2>Water quality <em>at a glance.</em></h2></div><span className={condition === "Safe" ? "badge good large" : "badge warning large"}>{condition}</span></div>
            <p>Real-time sensor intelligence, recent trends and prediction context in one clear monitoring view.</p>
            <div className="station-meta"><span><span className="meta-dot"></span> All sensors active</span><span><Clock3 size={14}/> Updated just now</span><span><ShieldCheck size={14}/> {confidence.toFixed(1)}% confidence</span></div>
            <div className="hero-parameter-pills"><span>pH <b>{live.ph}</b></span><span>Turbidity <b>{live.turbidity} NTU</b></span><span>TDS <b>{live.tds} mg/L</b></span><span>Temperature <b>{live.temperature}°C</b></span></div>
          </div>
          <div className="station-score"><div className="score-label">Water Quality Index</div><div className="score-big">{wqi.value}<small>/100</small></div><div className="score-track"><i style={{width:`${Math.min(100,Math.max(0,wqi.value))}%`}}></i></div><span>{wqi.band}</span></div>
        </div>

        <div className="dashboard-section-label"><span>Live parameters</span><small>Latest values from the four monitored parameters</small></div>
        <div className="metric-grid dashboard-metrics">
          {liveReadings.map((item, index) => <MetricCard key={item.label} item={item} />)}
        </div>
        <div className="dashboard-wqi-card">
          <div className="wqi-card-icon"><CircleGauge size={22}/></div>
          <div className="wqi-card-copy">
            <span>WATER QUALITY INDEX</span>
            <strong>{wqi.value}<small>/100</small></strong>
            <em>{wqi.band}</em>
          </div>
          <div className="wqi-card-detail">
            <span>pH <b>30%</b></span>
            <span>Turbidity <b>30%</b></span>
            <span>TDS <b>25%</b></span>
            <span>Temperature <b>15%</b></span>
          </div>
        </div>

        <div className="dashboard-grid dashboard-main-grid">
          <div className="panel chart-panel dashboard-chart-card">
            <div className="panel-head dashboard-card-head"><div><span className="panel-kicker">Sensor history</span><h3>Recent readings</h3><p>Live trend across the latest monitoring window</p></div><select><option>Last 12 hours</option><option>Last 24 hours</option><option>Last 7 days</option></select></div>
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height={310}>
                <LineChart data={trendData} margin={{top:8,right:8,left:-8,bottom:0}}>
                  <CartesianGrid strokeDasharray="3 6" vertical={false} stroke="#dce9e6"/>
                  <XAxis dataKey="time" tick={{fontSize:12,fill:"#718481"}} axisLine={false} tickLine={false}/>
                  <YAxis yAxisId="left" domain={[6.8,7.4]} tick={{fontSize:12,fill:"#718481"}} axisLine={false} tickLine={false}/>
                  <YAxis yAxisId="right" orientation="right" domain={[0,400]} tick={{fontSize:12,fill:"#718481"}} axisLine={false} tickLine={false}/>
                  <Tooltip contentStyle={{borderRadius:14,border:"1px solid #dce7e4",boxShadow:"0 12px 30px rgba(21,67,62,.10)"}} />
                  <Line yAxisId="left" type="monotone" dataKey="ph" stroke="#16756e" strokeWidth={3} dot={false} name="pH"/>
                  <Line yAxisId="right" type="monotone" dataKey="tds" stroke="#a46c25" strokeWidth={2.5} dot={false} name="TDS"/>
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-footer"><div className="chart-legend"><span><i className="legend-ph"></i> pH</span><span><i className="legend-tds"></i> TDS</span></div><span className="chart-note">Values update with the latest sensor readings</span></div>
          </div>

          <div className="panel quality-panel dashboard-quality-card">
            <div className="quality-topline"><div><span className="panel-kicker">Current result</span><h3>Water condition</h3></div><span className={condition === "Safe" ? "badge good" : "badge warning"}>{condition}</span></div>
            <div className="quality-visual"><div className="quality-ring"><div><strong>{qualityScore}</strong><span>/ 100</span></div></div><div className="quality-copy"><strong>{condition === "Safe" ? "Monitoring looks stable" : "Attention is required"}</strong><p>The current result is based on the latest sensor context and prediction output.</p></div></div>
            <div className="confidence-box"><div><span>Prediction confidence</span><strong>{confidence.toFixed(1)}%</strong></div><div className="meter"><i style={{width:`${Math.min(100,Math.max(0,confidence))}%`}}></i></div></div>
            <Link to="/agentic-ai" className="ai-link"><span><Sparkles size={16}/> Ask Agentic AI about this result</span><ArrowUpRight size={17}/></Link>
          </div>
        </div>

        <div className="dashboard-section-label lower-label"><span>Take action</span><small>Update the live context or ask the AI for an explanation</small></div>
        <div className="dashboard-grid lower dashboard-action-grid">
          <div className="panel controls-card">
            <div className="panel-head dashboard-card-head"><div><span className="panel-kicker">Sensor controls</span><h3>Update current reading</h3><p>Test the same data flow without physical hardware.</p></div><span className="control-chip"><SlidersHorizontal size={14}/> Manual</span></div>
            <div className="sensor-input-grid modern-inputs">
              {[['ph','pH'],['turbidity','Turbidity (NTU)'],['tds','TDS (mg/L)'],['temperature','Temperature (°C)']].map(([key,label])=><label key={key}><span>{label}</span><input type="number" step="0.1" value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}/></label>)}
            </div>
            <div className="control-footer"><button className="cw-btn cw-btn-main" onClick={sendReading} disabled={sending}><RefreshCw size={15}/> {sending?"Updating…":"Update sensor reading"}</button>{message&&<div className="inline-success">{message}</div>}</div>
          </div>
          <div className="panel quick-card">
            <div className="panel-head dashboard-card-head"><div><span className="panel-kicker">Quick actions</span><h3>What do you want to know?</h3><p>Jump directly into an AI explanation.</p></div><span className="question-mark">?</span></div>
            <div className="quick-action-grid">
              <Link to="/agentic-ai"><span>Is the water safe right now?</span><ArrowUpRight size={16}/></Link>
              <Link to="/agentic-ai"><span>Why is the water unsafe?</span><ArrowUpRight size={16}/></Link>
              <Link to="/agentic-ai"><span>What is the current pH?</span><ArrowUpRight size={16}/></Link>
              <Link to="/agentic-ai"><span>What should I do next?</span><ArrowUpRight size={16}/></Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function Analytics() {
  const [range, setRange] = useState("7 days");
  return (
    <>
      <PageHeader eyebrow="WATER INTELLIGENCE / ANALYSIS" title="See the story behind the data." text="Explore quality trends, compare parameters, and understand the changes that matter." />
      <section className="container analytics-editorial">
        <div className="analytics-toolbar">
          <div><span className="analytics-overline">ANALYSIS PERIOD</span><strong>{range === "7 days" ? "Last seven days" : range === "30 days" ? "Last 30 days" : "Selected period"}</strong></div>
          <div className="range-switch" role="group" aria-label="Analysis period">
            {["7 days", "30 days", "Custom"].map(item => <button key={item} className={range === item ? "active" : ""} onClick={() => setRange(item)}>{item}</button>)}
          </div>
        </div>
        <section className="analytics-feature">
          <div className="analytics-feature-head"><div><span className="analytics-overline">WATER QUALITY INDEX</span><h2>WQI trend</h2><p>Daily Water Quality Index across the selected monitoring period.</p></div><div className="analytics-average"><span>Period WQI</span><strong>33.6 <small>/100</small></strong><em>WAWQI average across this period</em></div></div>
          <div className="analytics-main-chart"><ResponsiveContainer width="100%" height={330}><AreaChart data={weeklyData} margin={{top:12,right:12,left:0,bottom:0}}><defs><linearGradient id="analyticsFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#197b74" stopOpacity={0.24}/><stop offset="100%" stopColor="#197b74" stopOpacity={0.01}/></linearGradient></defs><CartesianGrid strokeDasharray="3 6" vertical={false} stroke="#dce9e6"/><XAxis dataKey="day" tick={{fontSize:12,fill:"#647a76"}} axisLine={false} tickLine={false}/><YAxis domain={[70,100]} tick={{fontSize:12,fill:"#647a76"}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{borderRadius:12,border:"1px solid #dce7e4",boxShadow:"0 12px 30px rgba(21,67,62,.10)"}}/><Area type="monotone" dataKey="score" name="Water Quality Index" stroke="#147f75" fill="url(#analyticsFill)" strokeWidth={3} activeDot={{r:5,strokeWidth:0}}/></AreaChart></ResponsiveContainer></div>
        </section>
        <div className="analytics-lower">
          <section className="parameter-story"><div className="analytics-section-head"><div><span className="analytics-overline">PARAMETER PROFILE</span><h2>Compare the readings</h2></div><span className="section-aside">Latest sensor values</span></div><div className="parameter-list">{readings.map((item,index)=><div className="parameter-row" key={item.label}><div className="parameter-name"><span className={`parameter-dot dot-${index}`}></span><strong>{item.label}</strong></div><div className="parameter-track"><i style={{width:`${Math.min(100,Math.max(4,Number(item.value)/([14,10,500,50][index]||100)*100))}%`}}></i></div><strong className="parameter-value">{item.value}<small>{item.unit}</small></strong></div>)}</div><p className="parameter-note">Values use different units and scales. Compare each parameter with its own acceptable range rather than comparing bar lengths directly.</p></section>
          <section className="insight-report"><span className="analytics-overline">INTERPRETATION</span><h2>What the trend suggests</h2><div className="report-item"><span>01</span><div><strong>pH remains steady</strong><p>Recent readings stay close to neutral, with only small movement.</p></div></div><div className="report-item"><span>02</span><div><strong>Watch parameter variation</strong><p>Review changes in turbidity and TDS alongside their timestamps.</p></div></div><div className="report-item"><span>03</span><div><strong>Use context before conclusions</strong><p>Interpret the combined readings with the model output and sensor conditions.</p></div></div></section>
        </div>
      </section>
    </>
  );
}

const historyFallback = Array.from({ length: 10 }, (_, dayIndex) => {
  const base = [
    { time: "08:00", ph: 7.12, turbidity: 2.1, tds: 304, temperature: 25.8 },
    { time: "10:00", ph: 7.16, turbidity: 2.2, tds: 309, temperature: 26.0 },
    { time: "12:00", ph: 7.18, turbidity: 2.4, tds: 318, temperature: 26.4 },
    { time: "14:00", ph: 7.21, turbidity: 2.7, tds: 321, temperature: 26.8 },
    { time: "16:00", ph: 7.17, turbidity: 2.3, tds: 315, temperature: 26.6 },
    { time: "18:00", ph: 7.15, turbidity: 2.2, tds: 312, temperature: 26.2 },
    { time: "18:30", ph: 7.18, turbidity: 2.4, tds: 318, temperature: 26.4 }
  ];
  return {
    day: dayIndex + 1,
    date: new Date(Date.now() - dayIndex * 86400000).toISOString().slice(0, 10),
    readings: base.map((r, i) => ({
      ...r,
      ph: +(r.ph + Math.sin(dayIndex * 0.9 + i) * 0.03).toFixed(2),
      turbidity: +(r.turbidity + Math.cos(dayIndex * 0.7 + i) * 0.18).toFixed(1),
      tds: Math.round(r.tds + Math.sin(dayIndex * 0.55 + i * 0.8) * 8),
      temperature: +(r.temperature + Math.cos(dayIndex * 0.45 + i) * 0.5).toFixed(1)
    }))
  };
});

function History() {
  const [days, setDays] = useState(historyFallback);
  const [selectedDay, setSelectedDay] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetch("/api/readings/history")
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!active || !Array.isArray(data) || !data.length) return;
        const normalized = data.slice(-10).map((d, index) => ({
          day: index + 1,
          date: d.date || new Date(Date.now() - (data.length - 1 - index) * 86400000).toISOString().slice(0, 10),
          readings: Array.isArray(d.readings) ? d.readings : []
        }));
        if (normalized.some(d => d.readings.length)) setDays(normalized);
      })
      .catch(() => {})
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const selected = days.find(d => d.day === selectedDay) || days[0];
  const chartData = selected?.readings?.length ? selected.readings : historyFallback[0].readings;

  return (
    <>
      <PageHeader
        eyebrow="10-day history"
        title="Daily water-quality history"
        text="Review readings collected across the monitoring period. Select a day to inspect the sensor trend for that date."
        action={<span className="history-source"><span className="live-dot"></span>{loading ? "Loading readings…" : "Firebase readings"}</span>}
      />
      <section className="container history-page">
        <div className="history-panel panel">
          <div className="history-head">
            <div>
              <span className="panel-kicker">10-day history</span>
              <h3>Daily water-quality history</h3>
            </div>
            <span className="history-source desktop-source">Firebase readings</span>
          </div>

          <div className="day-tabs" role="tablist" aria-label="Select history day">
            {days.map(d => (
              <button
                key={d.day}
                className={selectedDay === d.day ? "day-tab active" : "day-tab"}
                onClick={() => setSelectedDay(d.day)}
                role="tab"
                aria-selected={selectedDay === d.day}
              >Day {String(d.day).padStart(2, "0")}</button>
            ))}
          </div>

          <div className="history-chart-meta">
            <div><strong>Day {String(selected?.day || 1).padStart(2, "0")}</strong><span>{selected?.date}</span><span>{chartData.length} readings</span></div>
          </div>

          <div className="history-chart">
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={chartData} margin={{ top: 10, right: 12, left: 2, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 6" vertical={false} stroke="#dce9e6" />
                <XAxis dataKey="time" tick={{ fontSize: 15, fill: "#526864", fontWeight: 600 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="ph" domain={[0, 14]} ticks={[0, 4, 8, 14]} tick={{ fontSize: 15, fill: "#526864", fontWeight: 600 }} axisLine={false} tickLine={false} width={34} />
                <YAxis yAxisId="scale" orientation="right" domain={[0, 340]} ticks={[0, 85, 170, 255, 340]} tick={{ fontSize: 15, fill: "#8a6a43", fontWeight: 600 }} axisLine={false} tickLine={false} width={38} />
                <Tooltip formatter={(value, name) => [value, name]} contentStyle={{ borderRadius: 10, border: "1px solid #dce9e6", fontSize: 14, fontWeight: 600 }} />
                <Line yAxisId="scale" type="monotone" dataKey="tds" stroke="#a56d25" strokeWidth={2.4} dot={false} name="TDS (mg/L)" />
                <Line yAxisId="ph" type="monotone" dataKey="ph" stroke="#147d75" strokeWidth={2.4} dot={false} name="pH" />
                <Line yAxisId="ph" type="monotone" dataKey="turbidity" stroke="#c45e5e" strokeWidth={2.1} dot={false} name="Turbidity (NTU)" />
                <Line yAxisId="ph" type="monotone" dataKey="temperature" stroke="#7b9a8f" strokeWidth={2.1} dot={false} name="Temperature (°C)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="history-legend">
            <span><i className="history-dot tds"></i>TDS</span>
            <span><i className="history-dot ph"></i>pH</span>
            <span><i className="history-dot turbidity"></i>Turbidity</span>
            <span><i className="history-dot temperature"></i>Temperature</span>
          </div>
        </div>
      </section>
    </>
  );
}

function Alerts() {
  const [filter, setFilter] = useState("All");
  const filtered = useMemo(() => filter === "All" ? alerts : alerts.filter(a => a.severity === filter), [filter]);
  return (
    <>
      <PageHeader eyebrow="Notifications" title="Alerts & events" text="A simple event history for contamination warnings, connection issues and routine monitoring events." />
      <section className="container">
        <div className="filter-row">
          {["All","Watch","Resolved","Info"].map(x => <button key={x} className={filter===x ? "filter active":"filter"} onClick={()=>setFilter(x)}>{x}</button>)}
        </div>
        <div className="alert-list">
          {filtered.map((a,i) => (
            <div className="alert-card" key={i}>
              <div className={"alert-symbol " + (a.severity==="Watch" ? "amber" : a.severity==="Resolved" ? "green" : "blue")}>
                {a.severity==="Watch" ? <AlertTriangle size={19}/> : a.severity==="Resolved" ? <CheckCircle2 size={19}/> : <Info size={19}/>}
              </div>
              <div className="alert-content"><div className="alert-title"><strong>{a.title}</strong><span>{a.severity}</span></div><p>{a.text}</p><small>{a.time}</small></div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}


function Feedback() {
  const [rating,setRating]=useState(0);
  const [category,setCategory]=useState("Water quality result");
  const [message,setMessage]=useState("");
  const [submitted,setSubmitted]=useState(false);
  const categories=["Water quality result","Water Quality Index","Alert","Agentic AI response"];
  const quick=["Very clear","Helpful recommendation","Easy to understand","Needs improvement"];

  const submit=async()=>{
    if(!rating && !message.trim()) return;
    try{
      await fetch("/api/feedback",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({rating,category,message})});
    }catch(e){}
    setSubmitted(true);
  };

  return (
    <div className="feedback-page">
      <PageHeader
        eyebrow="Feedback integration"
        title="Help make ClearWater better."
        text="Rate the result or AI explanation in a few seconds. Your feedback becomes structured input for improving recommendations."
      />
      <section className="container feedback-interactive">
        {!submitted ? (
          <div className="feedback-focus-card">
            <div className="feedback-focus-head">
              <div>
                <span className="feedback-mini-label">QUICK FEEDBACK</span>
                <h3>How useful was this result?</h3>
                <p>Choose a rating, tell us what you are reviewing, and optionally add one short note.</p>
              </div>
              <div className="feedback-orb"><Sparkles size={21}/></div>
            </div>

            <div className="feedback-big-rating">
              {[1,2,3,4,5].map(n=>(
                <button key={n} type="button" className={n<=rating?"feedback-star selected":"feedback-star"} onClick={()=>setRating(n)} aria-label={`${n} out of 5`}>
                  ★
                </button>
              ))}
              <span>{rating ? ["","Not useful","Needs work","Okay","Helpful","Excellent"][rating] : "Tap a star"}</span>
            </div>

            <div className="feedback-section">
              <span className="feedback-label">WHAT ARE YOU REVIEWING?</span>
              <div className="feedback-pills">
                {categories.map(item=><button key={item} type="button" className={category===item?"feedback-pill active":"feedback-pill"} onClick={()=>setCategory(item)}>{item}</button>)}
              </div>
            </div>

            <div className="feedback-section">
              <span className="feedback-label">QUICK TAGS</span>
              <div className="feedback-pills">
                {quick.map(item=><button key={item} type="button" className="feedback-pill soft" onClick={()=>setMessage(v=>v ? `${v} ${item}.` : `${item}.`)}>{item}</button>)}
              </div>
            </div>

            <div className="feedback-section">
              <div className="feedback-label-row"><span className="feedback-label">OPTIONAL NOTE</span><span className="feedback-count">{message.length}/240</span></div>
              <textarea maxLength={240} value={message} onChange={e=>setMessage(e.target.value)} placeholder="What was clear, useful, confusing, or missing?" />
            </div>

            <div className="feedback-bottom">
              <div className="feedback-private"><ShieldCheck size={16}/><span>No personal information needed</span></div>
              <button className="feedback-submit" onClick={submit} disabled={!rating && !message.trim()}>Send feedback <ArrowRight size={16}/></button>
            </div>
          </div>
        ) : (
          <div className="feedback-success-card feedback-success-modern">
            <div className="success-orbit"><CheckCircle2 size={34}/></div>
            <span className="feedback-mini-label">THANK YOU</span>
            <h3>Feedback received.</h3>
            <p>Your response was saved for <b>{category}</b>. It can be used as structured feedback when improving ClearWater recommendations and Agentic AI explanations.</p>
            <div className="success-summary"><span>{rating ? `${rating}/5 rating` : "Written feedback"}</span><span>{category}</span></div>
            <button className="feedback-submit secondary" onClick={()=>{setSubmitted(false);setMessage("");setRating(0)}}>Send another response</button>
          </div>
        )}
      </section>
    </div>
  );
}

function CornerAssistantRobot() {
  const goToChat = () => {
    const chat = document.querySelector(".agent-chat");
    if (chat) chat.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <button className="corner-assistant" type="button" onClick={goToChat} aria-label="Hello, open the Agentic AI chat" title="Talk to ClearWater AI">
      <span className="corner-assistant-bubble">Hello! <span>👋</span></span>
      <span className="corner-assistant-viewport" aria-hidden="true">
        <span className="corner-assistant-robot">
          <span className="robot-antenna"><i /></span>
          <span className="robot-head">
            <span className="robot-ear left" /><span className="robot-ear right" />
            <span className="robot-face"><i /><i /></span><span className="robot-smile" />
          </span>
          <span className="robot-neck" />
          <span className="robot-body"><span className="robot-emblem"><Droplets size={16} /></span><span className="robot-body-light" /></span>
          <span className="robot-arm left" />
          <span className="robot-arm right" />
        </span>
      </span>
    </button>
  );
}

function AgenticAI() {
  const initial = {
    intent: "safety",
    risk: "Low",
    answer: "I’m ready to check the latest sensor reading. Ask a question and I’ll first read the current pH, turbidity, TDS and temperature, then run the decision and knowledge agents before generating the response.",
    recommendation: "Try: “What is the current WQI?”, “Is the water safe right now?”, “Is pH normal?”, or “What should I check next?”",
    evidence: ["Water Quality Index", "4 live sensor parameters", "Current decision context"],
    stages: [
      ["1", "Intent agent", "Waiting for your question"],
      ["2", "Monitoring agent", "Reads the latest sensor packet"],
      ["3", "Knowledge agent", "Retrieves relevant project knowledge"],
      ["4", "Decision agent", "Checks the sensor values and prediction context"],
      ["5", "Recommendation agent", "Generates the next-step response"]
    ]
  };
  const [messages, setMessages] = useState([{from:"agent", text:initial.answer, result:initial}]);
  const [input,setInput]=useState("");
  const [busy,setBusy]=useState(false);
  const [lastResult,setLastResult]=useState(initial);
  const [live,setLive]=useState({ph:7.18,turbidity:2.4,tds:318,temperature:26.4,condition:"Safe",confidence:94.2,qualityScore:87,wqi:{value:34.8,band:"Good"}});

  const loadLive = async () => {
    try { const res=await fetch("/api/readings"); if(res.ok) setLive(await res.json()); } catch(e) {}
  };
  useEffect(() => { loadLive(); const timer=setInterval(loadLive, 5000); return () => clearInterval(timer); }, []);

  const ask = async (value) => {
    const q=value.trim();
    if(!q || busy) return;
    setInput("");
    setMessages(m=>[...m,{from:"user",text:q}]);
    setBusy(true);
    try {
      const res=await fetch("/api/agentic/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q})});
      const data=await res.json();
      if(!res.ok) throw new Error(data.error || "Agentic AI request failed");
      setLastResult(data);
      await loadLive();
      setMessages(m=>[...m,{from:"agent",text:data.answer,result:data}]);
    } catch(err) {
      const fallback={...initial,answer:"The Agentic AI service is not reachable. Start the backend with npm run dev, then try again. If you want live LLM answers, also configure the LLM variables in backend/.env."};
      setLastResult(fallback);
      setMessages(m=>[...m,{from:"agent",text:fallback.answer,result:fallback}]);
    } finally { setBusy(false); }
  };

  return (
    <>
      <CornerAssistantRobot />
      <section className="container agent-workspace">
        <div className="agent-chat-wrap">
          <div className="panel agent-chat">
          <div className="agent-chat-head">
            <div><strong>ClearWater Agentic AI</strong><small>Water insights, explained clearly</small></div>
            <span className="online-text"><span className="live-dot"></span>{busy?"thinking":"ready"}</span>
          </div>
          <div className="agent-messages">
            {messages.map((m,i)=><div className={m.from==="user"?"agent-message user":"agent-message"} key={i}>
              <div className="agent-message-label">{m.from==="user"?"You":"Agentic AI"}</div>
              <div className="agent-message-text">{m.text}</div>
              {m.result && <div className="response-evidence"><div><b>Recommendation</b><span>{m.result.recommendation}</span></div><div className="evidence-list">{(m.result.evidence||[]).map(x=><span key={x}>{x}</span>)}</div>{m.result.source && <small className="response-source">Response source: {m.result.source}</small>}</div>}
            </div>)}
            {busy&&<div className="agent-thinking"><span className="thinking-dot"></span><span>Checking current sensor data…</span></div>}
          </div>
          <div className="agent-suggestions">{["What is the current WQI?","Is the water safe right now?","Is the pH normal?","Is turbidity high?","What should I check next?"].map(q=><button key={q} onClick={()=>ask(q)}>{q}</button>)}</div>
          <div className="agent-input"><input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&ask(input)} placeholder="Ask anything about the monitored water quality..." disabled={busy}/><button onClick={()=>ask(input)} disabled={busy||!input.trim()}><ArrowRight size={18}/></button></div>
          
          </div>
        </div>
        <aside className="agent-side-stack">
          <div className="panel"><div className="panel-kicker">Ask about the current reading</div><h3>Try a question</h3><div className="quick-action-list"><button onClick={()=>ask("What is the current WQI?")}>What is the current WQI? <ArrowRight size={15}/></button><button onClick={()=>ask("Is the water safe right now?")}>Is the water safe right now? <ArrowRight size={15}/></button><button onClick={()=>ask("What is the current pH?")}>What is the current pH? <ArrowRight size={15}/></button><button onClick={()=>ask("What should I check next?")}>What should I check next? <ArrowRight size={15}/></button></div></div>
        </aside>
      </section>
    </>
  );
}

function App() {
  const protectedElement = (element) => <ProtectedRoute>{element}</ProtectedRoute>;
  return (
    <Routes>
      <Route path="/" element={<Shell><Home /></Shell>} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={protectedElement(<Shell><Dashboard /></Shell>)} />
      <Route path="/analytics" element={protectedElement(<Shell><Analytics /></Shell>)} />
      <Route path="/history" element={protectedElement(<Shell><History /></Shell>)} />
      <Route path="/alerts" element={protectedElement(<Shell><Alerts /></Shell>)} />
      <Route path="/agentic-ai" element={protectedElement(<Shell><AgenticAI /></Shell>)} />
      <Route path="/feedback" element={protectedElement(<Shell><Feedback /></Shell>)} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
