import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import mqtt from "mqtt";

dotenv.config({ path: path.join(path.dirname(fileURLToPath(import.meta.url)), ".env") });
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = Number(process.env.PORT || 5000);
const readingsFile = path.join(__dirname, "data", "readings.json");
const feedbackFile = path.join(__dirname, "data", "feedback.json");
const knowledge = JSON.parse(await fs.readFile(path.join(__dirname, "knowledge", "water-quality.json"), "utf8"));

app.use(cors({ origin: process.env.FRONTEND_ORIGIN?.split(",") || "*" }));
app.use(express.json({ limit: "1mb" }));

const demoTrend = [
  {time:"08:00",ph:7.12,turbidity:2.1,tds:304,temperature:25.8},
  {time:"10:00",ph:7.16,turbidity:2.2,tds:309,temperature:26.0},
  {time:"12:00",ph:7.18,turbidity:2.4,tds:318,temperature:26.4},
  {time:"14:00",ph:7.21,turbidity:2.7,tds:321,temperature:26.8},
  {time:"16:00",ph:7.17,turbidity:2.3,tds:315,temperature:26.6},
  {time:"18:00",ph:7.15,turbidity:2.2,tds:312,temperature:26.2}
];

async function getReading(){ return JSON.parse(await fs.readFile(readingsFile,"utf8")); }
async function getHistory(){
  try {
    const data=JSON.parse(await fs.readFile(readingsFile,"utf8"));
    return Array.isArray(data.history) ? data.history : demoTrend;
  } catch { return demoTrend; }
}
async function saveReading(data){ await fs.writeFile(readingsFile, JSON.stringify(data,null,2)); }
function withHistory(reading, history){
  return {...reading, history: history.slice(-50)};
}
function retrieveKnowledge(q){
  const text=q.toLowerCase();
  const words=text.split(/[^a-z0-9]+/).filter(Boolean);
  return knowledge.map(k=>({k,score:k.keywords.reduce((sum,key)=>sum+(words.includes(key)?3:(text.includes(key)?1:0)),0)}))
    .filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,4).map(x=>x.k);
}
function detectIntent(q){
  const s=q.toLowerCase();
  if(/wqi|water quality index|water-quality index/.test(s)) return "wqi";
  if(/safe|drink|potable|contaminat|quality|good|bad|usable|okay|ok|normal|status|condition/.test(s)) return "safety";
  if(/turbid|cloud|muddy|clarity/.test(s)) return "turbidity";
  if(/\bph\b|acid|alkaline/.test(s)) return "ph";
  if(/\btds\b|dissolved|solid/.test(s)) return "tds";
  if(/temperature|\btemp\b|hot|cold/.test(s)) return "temperature";
  if(/trend|change|increase|decrease|history|recent|pattern|yesterday|over time/.test(s)) return "trend";
  if(/cnn|lstm|model|predict|prediction|confidence|classif/.test(s)) return "prediction";
  if(/mqtt|esp32|sensor|hardware|node|iot|wifi|connection|communication/.test(s)) return "system";
  if(/alert|warning|notify|risk|danger|action|check next|what should|recommend|recommendation/.test(s)) return "action";
  return "general";
}

function calculateWQI(reading){
  // Weighted Arithmetic Water Quality Index (WAWQI).
  // Standards used for this project: pH 8.5, turbidity 5 NTU, TDS 500 mg/L.
  // Temperature is monitored separately and is NOT included in WQI because
  // this selected WAWQI implementation does not define a temperature standard.
  const standards={pH:8.5,turbidity:5,tds:500};
  const ideal={pH:7,turbidity:0,tds:0};
  const K=1/((1/standards.pH)+(1/standards.turbidity)+(1/standards.tds));
  const weights={pH:K/standards.pH,turbidity:K/standards.turbidity,tds:K/standards.tds};

  const ph=Number(reading.ph), turbidity=Number(reading.turbidity), tds=Number(reading.tds);
  const components={
    pH:100*(ph-ideal.pH)/(standards.pH-ideal.pH),
    turbidity:100*(turbidity-ideal.turbidity)/(standards.turbidity-ideal.turbidity),
    tds:100*(tds-ideal.tds)/(standards.tds-ideal.tds)
  };
  const denominator=weights.pH+weights.turbidity+weights.tds;
  const value=Number(((components.pH*weights.pH+components.turbidity*weights.turbidity+components.tds*weights.tds)/denominator).toFixed(1));
  const band=value<=25?"Excellent":value<=50?"Good":value<=75?"Poor":value<=100?"Very Poor":"Unsuitable for drinking";
  return {
    value, band,
    method:"Weighted Arithmetic WQI (WAWQI)",
    parameters:["pH","Turbidity","TDS"],
    standards,
    idealValues:ideal,
    K:Number(K.toFixed(6)),
    weights:{pH:Number(weights.pH.toFixed(6)),turbidity:Number(weights.turbidity.toFixed(6)),tds:Number(weights.tds.toFixed(6))},
    components:{pH:Number(components.pH.toFixed(1)),turbidity:Number(components.turbidity.toFixed(1)),tds:Number(components.tds.toFixed(1))},
    temperatureExcluded:true
  };
}
function parameterStatus(reading){
  return {
    ph: reading.ph>=6.5 && reading.ph<=8.5 ? "Normal" : "Outside configured range",
    turbidity: reading.turbidity<=5 ? "Normal" : "High",
    tds: reading.tds<=500 ? "Normal" : "High",
    temperature: reading.temperature>=0 && reading.temperature<=40 ? "Normal" : "Outside configured range"
  };
}
async function getModelPrediction(reading){
  const url=process.env.ML_SERVICE_URL;
  if(!url) return null;
  try{
    const r=await fetch(`${url.replace(/\/$/,"")}/predict`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ph:reading.ph,turbidity:reading.turbidity,tds:reading.tds,temperature:reading.temperature})});
    if(!r.ok) return null;
    return await r.json();
  }catch(e){
    return null;
  }
}

function decision(reading, trend, modelPrediction=null){
  // Demo project thresholds; replace with validated standards/configuration before deployment.
  const phOk=reading.ph>=6.5&&reading.ph<=8.5;
  const turbidityOk=reading.turbidity<=5;
  const tdsOk=reading.tds<=500;
  const tempOk=reading.temperature>=0&&reading.temperature<=40;
  const safe=phOk&&turbidityOk&&tdsOk&&tempOk;
  const predicted=modelPrediction?.prediction;
  const condition=predicted || (safe?"Safe":"Contaminated");
  const confidence=Number(modelPrediction?.confidence ?? reading.confidence ?? (safe?94.2:72.0));
  const wqi=calculateWQI(reading); return {condition,confidence,qualityScore:Number(reading.qualityScore ?? (condition==="Safe"?87:45)),wqi,checks:{phOk,turbidityOk,tdsOk,tempOk},modelSource:modelPrediction?.source||"demo threshold fallback"};
}
function trendSummary(history){
  const rows=(history||[]).filter(x=>Number.isFinite(Number(x.ph))).slice(-8);
  if(rows.length<2) return "Only the latest sensor reading is available, so a time trend cannot yet be established.";
  const first=rows[0], last=rows.at(-1);
  const delta=(key)=>Number(last[key])-Number(first[key]);
  return `Across the latest ${rows.length} readings, pH changed ${delta("ph").toFixed(2)}, turbidity changed ${delta("turbidity").toFixed(2)} NTU, TDS changed ${delta("tds").toFixed(0)} mg/L and temperature changed ${delta("temperature").toFixed(1)} °C.`;
}
function localAnswer(question, reading, retrieved, result, intent, history){
  const status=parameterStatus(reading);
  const knowledgeText=retrieved.map(x=>x.content).join(" ");
  const current=`Current sensor reading: pH ${reading.ph}, turbidity ${reading.turbidity} NTU, TDS ${reading.tds} mg/L, temperature ${reading.temperature} °C.`;
  let answer, recommendation;
  if(intent==="wqi"){
    answer=`The current Water Quality Index (WQI) is ${result.wqi.value}/100, rated ${result.wqi.band}, using the Weighted Arithmetic WQI (WAWQI) method. It is calculated from pH, turbidity and TDS using their permissible standard values of 8.5, 5 NTU and 500 mg/L. Component quality ratings are pH ${result.wqi.components.pH}, turbidity ${result.wqi.components.turbidity} and TDS ${result.wqi.components.tds}. Temperature is monitored separately and is not included in this WQI calculation. This WQI follows the selected project methodology and is not a laboratory or regulatory certification.`;
    recommendation=result.wqi.value>=75?"Continue monitoring the four parameters and watch for sustained WQI changes.":"Review the parameters contributing most to the lower WQI, verify sensor calibration, and follow the alert workflow if the condition persists.";
  } else if(intent==="safety"){
    answer=`${current} The decision layer classifies the current reading as ${result.condition} with ${result.confidence}% model confidence and a Water Quality Index (WQI) of ${result.wqi.value}/100, rated ${result.wqi.band}. pH is ${status.ph.toLowerCase()}, turbidity is ${status.turbidity.toLowerCase()}, TDS is ${status.tds.toLowerCase()}, and temperature is ${status.temperature.toLowerCase()}. These are the project's configured demo checks, not a laboratory certification. ${knowledgeText}`;
    recommendation=result.condition==="Safe"?"Continue monitoring consecutive readings. If any parameter moves outside the configured range, verify the sensor and review the alert decision.":"Treat this as a warning from the monitoring system. Verify the sensor reading, inspect the source, and follow the configured alert/escalation procedure.";
  } else if(intent==="trend"){
    answer=`${trendSummary(history)} The latest reading is pH ${reading.ph}, turbidity ${reading.turbidity} NTU, TDS ${reading.tds} mg/L and temperature ${reading.temperature} °C. ${knowledgeText}`;
    recommendation="Use consecutive readings rather than one isolated value to decide whether a change is persistent. A sudden jump should also trigger sensor/calibration checks.";
  } else if(intent==="turbidity"){
    answer=`The current turbidity sensor value is ${reading.turbidity} NTU, which is ${status.turbidity.toLowerCase()} under the project's configured demo threshold of 5 NTU. ${knowledgeText}`;
    recommendation=reading.turbidity<=5?"Keep monitoring for a persistent rise and inspect the sensor if the value changes suddenly.":"Verify the sensor and sample, inspect the water source, and review the contamination alert logic.";
  } else if(intent==="ph"){
    answer=`The current pH sensor value is ${reading.ph}. The configured project range is 6.5–8.5, so this reading is ${status.ph.toLowerCase()}. ${knowledgeText}`;
    recommendation=status.ph==="Normal"?"Continue monitoring pH over time.":"Verify pH sensor calibration and inspect the water source before drawing conclusions.";
  } else if(intent==="tds"){
    answer=`The current TDS sensor value is ${reading.tds} mg/L. The configured project threshold is 500 mg/L, so this reading is ${status.tds.toLowerCase()}. ${knowledgeText}`;
    recommendation=reading.tds<=500?"Continue monitoring TDS and compare it with the other sensor parameters.":"Verify the TDS probe and investigate the source of elevated dissolved solids.";
  } else if(intent==="temperature"){
    answer=`The current temperature sensor value is ${reading.temperature} °C. The project's demo operating check is 0–40 °C, so this reading is ${status.temperature.toLowerCase()}. ${knowledgeText}`;
    recommendation="Continue monitoring temperature because it helps interpret changes in other water-quality parameters.";
  } else if(intent==="prediction"){
    answer=`The latest sensor values are pH ${reading.ph}, turbidity ${reading.turbidity} NTU, TDS ${reading.tds} mg/L and temperature ${reading.temperature} °C. The current prediction is ${result.condition} with ${result.confidence}% confidence. The CNN-LSTM is intended to learn multi-parameter patterns and temporal behaviour; this demo backend applies the configured decision checks until a trained model API is connected. ${knowledgeText}`;
    recommendation="When the trained CNN-LSTM API is connected, compare its prediction and confidence with the sensor-level checks before taking action.";
  } else if(intent==="system"){
    answer=`The latest sensor packet contains pH ${reading.ph}, turbidity ${reading.turbidity} NTU, TDS ${reading.tds} mg/L and temperature ${reading.temperature} °C. The intended flow is ESP32 → Wi-Fi/MQTT → processing → CNN-LSTM → Agentic AI → dashboard/alerts. ${knowledgeText}`;
    recommendation="Connect the ESP32 to the MQTT topic and keep the backend as the single context source for the Agentic AI response.";
  } else if(intent==="action"){
    const failed=Object.entries(result.checks).filter(([,ok])=>!ok).map(([k])=>k).join(", ");
    answer=`The Agentic AI checked the latest sensor packet before answering. Current condition: ${result.condition}; confidence: ${result.confidence}%. ${failed?`The parameters outside the configured checks are: ${failed}.` : "All four configured parameter checks currently pass."} ${knowledgeText}`;
    recommendation=failed?"Verify the flagged parameter(s), check calibration/sample conditions, and follow the alert workflow if the abnormal reading persists.":"No immediate threshold action is indicated by the current demo rules; continue monitoring consecutive readings.";
  } else {
    answer=`I checked the latest sensor reading before answering: pH ${reading.ph}, turbidity ${reading.turbidity} NTU, TDS ${reading.tds} mg/L and temperature ${reading.temperature} °C. I can explain the current condition, WQI, any individual parameter, trends, the prediction, alerts, or the IoT/Agentic AI workflow. ${knowledgeText}`;
    recommendation="Ask a specific question such as “Is the water safe right now?”, “Is the pH normal?”, or “What should I check next?”";
  }
  return {answer,recommendation};
}
async function llmAnswer(question, reading, retrieved, result){
  if(!process.env.LLM_API_KEY || !process.env.LLM_MODEL) return null;
  const base=process.env.LLM_BASE_URL || "https://api.openai.com/v1/chat/completions";
  const system=`You are ClearWater Agentic AI for an academic IoT water-quality monitoring system. Answer the user's question using ONLY the supplied monitoring context and retrieved project knowledge. Do not claim laboratory certification or guarantee drinking-water safety. Explain reasoning clearly, mention uncertainty when appropriate, and give a practical recommendation. Current context: ${JSON.stringify(reading)}. Decision: ${JSON.stringify(result)}. Retrieved knowledge: ${retrieved.map(x=>x.content).join(" ")}`;
  const response=await fetch(base,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${process.env.LLM_API_KEY}`},body:JSON.stringify({model:process.env.LLM_MODEL,messages:[{role:"system",content:system},{role:"user",content:question}],temperature:0.2})});
  if(!response.ok) throw new Error(`LLM request failed: ${response.status}`);
  const data=await response.json();
  return data.choices?.[0]?.message?.content || null;
}

app.get("/api/health",(req,res)=>res.json({ok:true,service:"ClearWater Agentic AI",llmConfigured:Boolean(process.env.LLM_API_KEY&&process.env.LLM_MODEL)}));
app.get("/api/readings",async(req,res)=>{ const reading=await getReading(); const history=await getHistory(); const wqi=calculateWQI(reading); res.json({...reading,wqi,history}); });
app.get("/api/readings/history",async(req,res)=>res.json(await getHistory()));
app.get("/api/wqi",async(req,res)=>{ const reading=await getReading(); res.json(calculateWQI(reading)); });
app.post("/api/readings",async(req,res)=>{
  const allowed=["nodeId","timestamp","ph","turbidity","tds","temperature","condition","confidence","qualityScore"];
  const body=req.body||{};
  for(const key of ["ph","turbidity","tds","temperature"]) if(typeof body[key]!=="number" || !Number.isFinite(body[key])) return res.status(400).json({error:`${key} must be a finite number`});
  const old=await getReading();
  const history=await getHistory();
  const reading=Object.fromEntries(allowed.filter(k=>body[k]!==undefined).map(k=>[k,body[k]]));
  const merged={...old,...reading,nodeId:body.nodeId||old.nodeId||"WQM-01",timestamp:body.timestamp||new Date().toISOString()};
  const d=decision(merged,history); Object.assign(merged,{condition:d.condition,confidence:d.confidence,qualityScore:d.qualityScore,wqi:d.wqi});
  const point={time:new Date(merged.timestamp).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}),ph:merged.ph,turbidity:merged.turbidity,tds:merged.tds,temperature:merged.temperature,timestamp:merged.timestamp};
  const nextHistory=[...history,point].slice(-50);
  await saveReading(withHistory(merged,nextHistory));
  res.json({...merged,history:nextHistory});
});
app.post("/api/agentic/ask",async(req,res)=>{
  try{
    const question=String(req.body?.question||"").trim();
    if(!question) return res.status(400).json({error:"Question is required"});
    const reading=await getReading();
    const history=await getHistory();
    const intent=detectIntent(question);
    const retrieved=retrieveKnowledge(question);
    const modelPrediction=await getModelPrediction(reading);
    const result=decision(reading,history,modelPrediction);
    const local=localAnswer(question,reading,retrieved,result,intent,history);
    let answer=local.answer, source="Local agentic reasoning";
    try { const ai=await llmAnswer(question,reading,retrieved,result); if(ai){answer=ai;source="LLM + local agent orchestration";} } catch(e){ console.warn(e.message); }
    const evidence=[`Condition: ${result.condition}`,`Confidence: ${result.confidence}%`,`Water Quality Index: ${result.wqi.value}/100 (${result.wqi.band})`,`pH: ${reading.ph}`,`Turbidity: ${reading.turbidity} NTU`,`TDS: ${reading.tds} mg/L`,`Temperature: ${reading.temperature} °C`,`Prediction source: ${result.modelSource}`];
    return res.json({intent,risk:result.condition==="Contaminated"?"High":"Low",answer,recommendation:local.recommendation,evidence,source,stages:[["1","Intent agent",`Detected ${intent} question`],["2","Monitoring agent",`Read the latest sensor context (${result.condition})`],["3","Knowledge agent",`Retrieved ${retrieved.length} relevant knowledge item(s)`],["4","Decision agent",`Evaluated model prediction (${result.modelSource}) + confidence ${result.confidence}% + configured thresholds`],["5","Recommendation agent","Generated next-step guidance"]],model:{prediction:result.condition,confidence:result.confidence,source:result.modelSource},retrieved:retrieved.map(x=>x.title)});
  }catch(e){console.error(e);res.status(500).json({error:"Agentic AI service error"});}
});
app.post("/api/feedback",async(req,res)=>{
  const item={id:Date.now(),rating:Number(req.body?.rating||0),category:String(req.body?.category||"General"),message:String(req.body?.message||""),createdAt:new Date().toISOString()};
  const current=JSON.parse(await fs.readFile(feedbackFile,"utf8")); current.push(item); await fs.writeFile(feedbackFile,JSON.stringify(current,null,2)); res.json({ok:true,item});
});

const mqttUrl=process.env.MQTT_BROKER_URL;
if(mqttUrl){
  const client=mqtt.connect(mqttUrl,{username:process.env.MQTT_USERNAME,password:process.env.MQTT_PASSWORD});
  client.on("connect",()=>client.subscribe(process.env.MQTT_TOPIC||"water/wqm-01/readings"));
  client.on("message",async(topic,payload)=>{try{const data=JSON.parse(payload.toString()); if(["ph","turbidity","tds","temperature"].every(k=>typeof data[k]==="number")){const old=await getReading(); const merged={...old,...data,nodeId:data.nodeId||old.nodeId||"WQM-01",timestamp:data.timestamp||new Date().toISOString()}; const history=await getHistory(); const d=decision(merged,history); Object.assign(merged,{condition:d.condition,confidence:d.confidence,qualityScore:d.qualityScore,wqi:d.wqi}); const point={time:new Date(merged.timestamp).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}),ph:merged.ph,turbidity:merged.turbidity,tds:merged.tds,temperature:merged.temperature,timestamp:merged.timestamp}; await saveReading(withHistory(merged,[...history,point].slice(-50)));}}catch(e){console.error("MQTT payload error",e.message)}});
}

app.listen(PORT,()=>console.log(`ClearWater backend running on http://localhost:${PORT}`));
