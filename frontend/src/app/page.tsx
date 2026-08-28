"use client";

import { useEffect, useState, useRef } from "react";
import { XAxis, YAxis, CartesianGrid, ReferenceLine, ResponsiveContainer, Area, AreaChart, Tooltip } from "recharts";
import { AlertTriangle, Play, Pause, Activity, ShieldCheck, Database, Info, TrendingUp, AlertCircle, ShieldAlert, Cpu } from "lucide-react";
import Image from "next/image";

// Types
interface StatusResponse {
  status: string;
  dataset: string;
  model: string;
  threshold: number;
  total_windows: number;
}

interface MetricsResponse {
  metrics: {
    precision: number;
    recall: number;
    f1: number;
    tn: number;
    fp: number;
    fn: number;
    tp: number;
    total_cost: number;
  };
}

interface Reason {
  signal: string;
  contribution_level: string;
}

interface Alert {
  step: number;
  score: number;
  is_synthetic_spike: boolean;
  reasons: Reason[];
}

interface StreamInfo {
  start_step: number;
  end_step: number;
}

interface ChartPoint {
  window_start: number;
  score: number;
  is_alert: boolean;
}

const API_BASE = "http://127.0.0.1:8000/api";

export default function Home() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const [statusRes, metricsRes, streamRes] = await Promise.all([
          fetch(`${API_BASE}/status`).then(r => r.json()),
          fetch(`${API_BASE}/metrics`).then(r => r.json()),
          fetch(`${API_BASE}/stream/info`).then(r => r.json())
        ]);
        
        setStatus(statusRes);
        setMetrics(metricsRes);
        setStreamInfo(streamRes);
        setCurrentStep(streamRes.start_step);
        setIsLoading(false);
      } catch (err) {
        console.error("Failed to fetch initial data", err);
      }
    }
    init();
  }, []);

  useEffect(() => {
    async function fetchStepData() {
      if (currentStep === 0) return;
      try {
        const res = await fetch(`${API_BASE}/stream/historical/${currentStep}`);
        const data = await res.json();
        setChartData(data.chart_data);
        setAlerts(data.alerts);
      } catch (err) {
        console.error("Failed to fetch historical data", err);
      }
    }
    
    // Throttle the fetch to avoid overwhelming the server during rapid slider changes
    const timeoutId = setTimeout(fetchStepData, 50);
    return () => clearTimeout(timeoutId);
  }, [currentStep]);

  useEffect(() => {
    if (isPlaying && streamInfo) {
      intervalRef.current = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= streamInfo.end_step) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 500 / playbackSpeed);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, playbackSpeed, streamInfo]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 text-gray-800 dark:text-gray-200">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
          <div className="text-sm font-medium tracking-wide">INITIALIZING SYSTEM...</div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-zinc-950 text-gray-900 dark:text-gray-100 p-4 md:p-8 font-sans selection:bg-indigo-500/30">
      
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400">PaySim Risk Monitor</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium mt-1">Real-time anomaly detection system</p>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="bento-card flex items-center gap-3 px-4 py-2">
              <Cpu className="text-gray-400" size={16} />
              <div className="flex flex-col">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Model</span>
                <span className="text-sm font-medium">{status?.model || "Unknown"}</span>
              </div>
            </div>
            <div className="bento-card flex items-center gap-3 px-4 py-2">
              <Database className="text-gray-400" size={16} />
              <div className="flex flex-col">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Dataset</span>
                <span className="text-sm font-medium">{status?.dataset || "Unknown"}</span>
              </div>
            </div>
            <div className="bento-card flex items-center gap-3 px-4 py-2">
              <div className="relative flex h-3 w-3">
                {status?.status === "OPERATIONAL" && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${status?.status === "OPERATIONAL" ? "bg-emerald-500" : "bg-red-500"}`}></span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">System Status</span>
                <span className="text-sm font-medium">{status?.status || "ERROR"}</span>
              </div>
            </div>
          </div>
        </header>

        {/* BENTO GRID */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          {/* MAIN CHART AREA */}
          <div className="md:col-span-8 bento-card p-6 flex flex-col gap-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <Activity size={16} /> Anomaly Score Over Time
                </h3>
                <div className="text-4xl font-bold mt-2 tabular-nums">
                  Step {currentStep} <span className="text-sm text-gray-400 font-normal">/ {streamInfo?.end_step}</span>
                </div>
              </div>

              {/* STREAM CONTROLS */}
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-zinc-800/50 p-1.5 rounded-2xl">
                <button 
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={`p-2.5 rounded-xl transition-all ${isPlaying ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' : 'hover:bg-gray-200 dark:hover:bg-zinc-700'}`}
                >
                  {isPlaying ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
                </button>
                <button 
                  onClick={() => setPlaybackSpeed(s => s === 1 ? 5 : s === 5 ? 10 : 1)}
                  className="px-3 py-2 rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors w-12 text-center"
                >
                  {playbackSpeed}x
                </button>
              </div>
            </div>

            <div className="w-full">
              <input
                type="range"
                min={streamInfo?.start_step}
                max={streamInfo?.end_step}
                value={currentStep}
                onChange={(e) => setCurrentStep(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div className="h-[280px] w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-zinc-800" opacity={0.5} />
                  <XAxis 
                    dataKey="window_start" 
                    tick={{fontSize: 12, fill: 'currentColor'}}
                    className="text-gray-500 dark:text-gray-400"
                    axisLine={false}
                    tickLine={false}
                    tickMargin={10}
                  />
                  <YAxis 
                    domain={[0, 1]} 
                    tick={{fontSize: 12, fill: 'currentColor'}}
                    className="text-gray-500 dark:text-gray-400"
                    axisLine={false}
                    tickLine={false}
                    tickMargin={10}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    itemStyle={{ color: '#6366f1', fontWeight: 600 }}
                    labelStyle={{ color: '#6b7280', marginBottom: '4px' }}
                  />
                  <ReferenceLine 
                    y={status?.threshold} 
                    stroke="#ef4444" 
                    strokeDasharray="4 4" 
                    label={{ position: 'insideTopLeft', value: 'ALERT THRESHOLD', fill: '#ef4444', fontSize: 10, fontWeight: 600 }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="score" 
                    stroke="#6366f1" 
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorScore)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* METRICS WIDGETS */}
          <div className="md:col-span-4 flex flex-col gap-6">
            <div className="bento-card p-6 bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-none shadow-indigo-500/20 shadow-xl">
              <h3 className="text-indigo-100 text-sm font-medium mb-1 flex items-center gap-2">
                <TrendingUp size={16} /> Total Expected Cost
              </h3>
              <div className="text-4xl font-bold tracking-tight mb-4">
                ₹{metrics?.metrics.total_cost.toLocaleString()}
              </div>
              <div className="grid grid-cols-2 gap-4 mt-auto">
                <div className="bg-white/10 rounded-xl p-3 backdrop-blur-sm">
                  <div className="text-indigo-100 text-xs mb-1">Precision</div>
                  <div className="text-xl font-semibold">{metrics?.metrics.precision.toFixed(3)}</div>
                </div>
                <div className="bg-white/10 rounded-xl p-3 backdrop-blur-sm">
                  <div className="text-indigo-100 text-xs mb-1">Recall</div>
                  <div className="text-xl font-semibold">{metrics?.metrics.recall.toFixed(3)}</div>
                </div>
              </div>
            </div>

            <div className="bento-card p-6 grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-xs text-gray-500 font-medium">F1 Score</span>
                <span className="text-2xl font-bold">{metrics?.metrics.f1.toFixed(3)}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-gray-500 font-medium">True Positives</span>
                <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{metrics?.metrics.tp}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-gray-500 font-medium">False Positives</span>
                <span className="text-2xl font-bold text-amber-500">{metrics?.metrics.fp}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-gray-500 font-medium">False Negatives</span>
                <span className="text-2xl font-bold text-red-500">{metrics?.metrics.fn}</span>
              </div>
            </div>
          </div>

          {/* ACTIVE ALERTS */}
          <div className="md:col-span-8 bento-card p-6 flex flex-col h-[500px]">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 flex items-center gap-2">
              <ShieldAlert size={16} /> Active Alerts Log
            </h3>
            
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar flex flex-col gap-4">
              {alerts.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                  <ShieldCheck size={48} className="mb-4 opacity-50 text-emerald-500" />
                  <div className="text-lg font-medium text-gray-600 dark:text-gray-300">System Secure</div>
                  <div className="text-sm">No recent anomalies detected.</div>
                </div>
              ) : (
                alerts.map((alert, idx) => (
                  <div key={idx} className="bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/50 rounded-2xl p-4 md:p-5 relative overflow-hidden transition-all hover:shadow-md">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500"></div>
                    
                    <div className="flex flex-wrap justify-between items-start gap-4 mb-4">
                      <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-bold">
                        <AlertTriangle size={18} />
                        Anomaly Detected
                      </div>
                      
                      <div className="flex gap-3">
                        <div className="bg-white dark:bg-zinc-900 px-3 py-1 rounded-lg border border-gray-100 dark:border-zinc-800 text-xs flex flex-col">
                          <span className="text-gray-400 text-[10px] font-medium uppercase">Step</span>
                          <span className="font-bold">{alert.step}</span>
                        </div>
                        <div className="bg-white dark:bg-zinc-900 px-3 py-1 rounded-lg border border-gray-100 dark:border-zinc-800 text-xs flex flex-col">
                          <span className="text-gray-400 text-[10px] font-medium uppercase">Score</span>
                          <span className="font-bold text-red-600 dark:text-red-400">{alert.score.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>

                    {alert.is_synthetic_spike && (
                      <div className="inline-flex items-center gap-1.5 bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 text-xs font-semibold px-2.5 py-1 rounded-md mb-4">
                        <Info size={12} /> Confirmed Synthetic Spike
                      </div>
                    )}

                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Contributing Factors</h4>
                      <div className="grid gap-2">
                        {alert.reasons.map((r, r_idx) => (
                          <div key={r_idx} className="flex justify-between items-center bg-white/60 dark:bg-zinc-900/60 p-2.5 rounded-xl border border-gray-100 dark:border-zinc-800/50">
                            <span className="text-sm font-medium">{r.signal}</span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              r.contribution_level === 'High' 
                                ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' 
                                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'
                            }`}>
                              {r.contribution_level}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* SIDE WIDGETS */}
          <div className="md:col-span-4 flex flex-col gap-6">
            <div className="bento-card p-6">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 flex items-center gap-2">
                <AlertCircle size={16} /> Cost Assumptions
              </h3>
              <ul className="space-y-3">
                <li className="flex justify-between items-center p-3 bg-gray-50 dark:bg-zinc-900/50 rounded-xl">
                  <span className="text-sm font-medium">False Positive (FP)</span>
                  <span className="font-mono text-sm font-semibold text-gray-600 dark:text-gray-300">₹500</span>
                </li>
                <li className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-100 dark:border-red-900/20">
                  <span className="text-sm font-medium">False Negative (FN)</span>
                  <span className="font-mono text-sm font-bold text-red-600 dark:text-red-400">₹10,000</span>
                </li>
                <li className="flex justify-between items-center p-3 bg-emerald-50 dark:bg-emerald-900/10 rounded-xl border border-emerald-100 dark:border-emerald-900/20">
                  <span className="text-sm font-medium">True Positive (TP)</span>
                  <span className="font-mono text-sm font-bold text-emerald-600 dark:text-emerald-400">₹100</span>
                </li>
              </ul>
            </div>

            <div className="bento-card p-6 flex-1">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 flex items-center gap-2">
                <TrendingUp size={16} /> Validation Analysis
              </h3>
              <div className="space-y-4">
                <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-2xl p-3 border border-gray-100 dark:border-zinc-800">
                  <div className="text-xs font-semibold text-gray-500 mb-2 px-1">Precision-Recall Curve</div>
                  <div className="rounded-xl overflow-hidden bg-white dark:bg-zinc-800/80 p-2 relative h-48 w-full">
                     <Image src="/validation_pr_curve.png" alt="PR Curve" fill className="object-contain dark:opacity-90 dark:mix-blend-screen" />
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-2xl p-3 border border-gray-100 dark:border-zinc-800">
                  <div className="text-xs font-semibold text-gray-500 mb-2 px-1">Cost vs Threshold Analysis</div>
                  <div className="rounded-xl overflow-hidden bg-white dark:bg-zinc-800/80 p-2 relative h-48 w-full">
                     <Image src="/validation_cost_vs_threshold.png" alt="Cost Curve" fill className="object-contain dark:opacity-90 dark:mix-blend-screen" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </main>
  );
}
