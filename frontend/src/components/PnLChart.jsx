import React, { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  AreaChart,
  Area
} from 'recharts'
import { TrendingUp, Activity } from 'lucide-react'

const CustomTooltip = ({ active, payload, label, mode }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-surface-glass backdrop-blur-md border border-border-glass p-3 rounded-lg shadow-xl font-mono">
        <p className="text-[10px] text-on-surface-variant mb-1 font-bold">{label}</p>
        <p className={`text-xs font-bold ${data.pnl >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
          PnL: {data.pnl >= 0 ? '+' : ''}${data.pnl.toFixed(2)}
        </p>
        {data.trades !== undefined && (
          <p className="text-[9px] text-on-surface-variant mt-1 opacity-70">
            Trades: {data.trades}
          </p>
        )}
      </div>
    )
  }
  return null
}

const PnLChart = ({ history, mode = 'daily' }) => {
  const data = useMemo(() => {
    if (mode === 'daily') {
      return history?.daily || []
    }
    return (history?.monthly || []).map(item => ({
      ...item,
      date: item.month
    }))
  }, [history, mode])

  // Calculate Cumulative Equity
  const equityData = useMemo(() => {
    let cumulative = 0
    return data.map(item => {
      cumulative += item.pnl
      return {
        ...item,
        equity: cumulative
      }
    })
  }, [data])

  if (!data || data.length === 0) {
    return (
      <div className="glass-container p-6 flex flex-col items-center justify-center min-h-[300px]">
        <TrendingUp size={24} className="text-on-surface-variant opacity-20 mb-2" />
        <p className="text-xs text-on-surface-variant font-mono opacity-50">No performance data yet</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* PnL Distribution (Bars) */}
      <div className="glass-container p-4 h-[300px] relative group overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-border-glass pb-3">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface-variant flex items-center gap-2">
            <TrendingUp size={14} className="text-primary" />
            PnL {mode === 'daily' ? 'Daily' : 'Monthly'}
          </div>
        </div>

        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey={mode === 'daily' ? 'date' : 'month'} 
                axisLine={false} tickLine={false}
                tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 8, fontFamily: 'monospace' }}
                tickFormatter={(val) => mode === 'daily' ? val.split('-').slice(2).join('') : val.split('-').slice(1).join('')}
              />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 8, fontFamily: 'monospace' }} />
              <Tooltip content={<CustomTooltip mode={mode} />} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
              <Bar dataKey="pnl" radius={[2, 2, 0, 0]} animationDuration={1000}>
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.pnl >= 0 ? '#10b981' : '#ef4444'} 
                    fillOpacity={0.8} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Equity Curve (Area) */}
      <div className="glass-container p-4 h-[300px] relative group overflow-hidden">
        <div className="flex items-center justify-between mb-4 border-b border-border-glass pb-3">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface-variant flex items-center gap-2">
            <Activity size={14} className="text-primary" />
            Equity Progression
          </div>
        </div>

        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey={mode === 'daily' ? 'date' : 'month'} 
                axisLine={false} tickLine={false}
                tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 8, fontFamily: 'monospace' }}
                tickFormatter={(val) => mode === 'daily' ? val.split('-').slice(2).join('') : val.split('-').slice(1).join('')}
              />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 8, fontFamily: 'monospace' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(20, 20, 25, 0.9)', borderColor: 'rgba(255,255,255,0.1)', fontSize: '10px' }}
                itemStyle={{ color: '#a855f7' }}
              />
              <Area 
                type="monotone" 
                dataKey="equity" 
                stroke="#a855f7" 
                fillOpacity={1} 
                fill="url(#colorEquity)" 
                animationDuration={2000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default PnLChart

