import React, { useEffect, useState } from 'react'
import useStore from './store/useStore'
import MetricCards from './components/MetricCards'
import PositionsTable from './components/PositionsTable'
import NewsFeed from './components/NewsFeed'
import TradeHistory from './components/TradeHistory'
import BotStatus from './components/BotStatus'
import PnLChart from './components/PnLChart'
import { AlertCircle, RefreshCw, Cpu, Layers } from 'lucide-react'

function App() {
  const {
    balance,
    positions,
    trades,
    performance,
    performanceHistory,
    news,
    botStatus,
    loading,
    error,
    fetchAll,
    pauseBot,
    resumeBot
  } = useStore()

  const [pnlMode, setPnlMode] = useState('daily')

  useEffect(() => {
    // Initial fetch
    fetchAll()

    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      fetchAll()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchAll])

  if (loading && (!balance || balance.total === undefined)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background-deep">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-t-2 border-secondary animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center text-primary">
            <Cpu size={24} className="animate-pulse" />
          </div>
        </div>
        <div className="mt-6 text-[11px] font-bold uppercase tracking-[0.3em] text-on-surface-variant animate-pulse">
          Establishing Aetheric Link...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background-deep text-on-surface selection:bg-primary/30">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-primary/5 blur-[120px] rounded-full opacity-30"></div>
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-secondary/5 blur-[100px] rounded-full opacity-20"></div>
      </div>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className="bg-tertiary/20 text-tertiary px-4 py-3 rounded-lg border border-tertiary/30 backdrop-blur-xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-right fade-in duration-300">
            <AlertCircle size={18} />
            <div className="flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-wider">Sync Error</span>
              <span className="text-xs font-mono opacity-80">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-40 bg-surface-container-lowest/80 backdrop-blur-md border-b border-border-glass">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-1.5 rounded-lg border border-primary/30">
                <Layers size={18} className="text-primary" />
              </div>
              <div>
                <div className="text-lg font-bold tracking-tighter text-on-surface leading-none">
                  MnL<span className="text-primary">OS</span>
                </div>
                <div className="text-[9px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mt-0.5">
                  Aetheric Intelligence
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="hidden md:flex flex-col items-end">
                <div className="text-[10px] font-mono text-on-surface-variant leading-none">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
                <div className="text-[8px] font-bold text-secondary uppercase tracking-widest mt-1">
                  Live Node: 0.04ms
                </div>
              </div>
              <button 
                onClick={() => fetchAll()}
                className="p-2 rounded-lg bg-surface-container hover:bg-surface-container-high border border-border-glass text-on-surface-variant transition-colors group"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Viewport */}
          <div className="lg:col-span-8 space-y-6">
            <BotStatus
              botStatus={botStatus}
              onPause={pauseBot}
              onResume={resumeBot}
            />
            
            <MetricCards 
              balance={balance} 
              performance={performance} 
              pnlMode={pnlMode}
              setPnlMode={setPnlMode}
            />
            
            <PnLChart history={performanceHistory} mode={pnlMode} />

            <PositionsTable positions={positions} />
            
            <TradeHistory trades={trades} />
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-4">
            <NewsFeed news={news} />
            
            <div className="mt-6 glass-container p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Bot Version</span>
                <span className="text-[10px] font-mono text-primary">v4.2.0-Alpha</span>
              </div>
              <div className="h-px bg-border-glass mb-2"></div>
              <p className="text-[9px] text-on-surface-variant leading-relaxed opacity-60">
                AI Trading Engine is currently processing market cycles at 4ms. Risk parameters are strictly enforced by the Aetheric Core.
              </p>
            </div>
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-10 opacity-30">
        <div className="h-px bg-gradient-to-r from-transparent via-border-glass to-transparent mb-6"></div>
        <div className="flex flex-col items-center gap-2">
          <div className="text-[10px] font-mono tracking-tighter">
            MNL_TRADING_BOT // SECURE_CONNECTION_ACTIVE
          </div>
          <div className="text-[9px] text-center max-w-md uppercase tracking-[0.1em]">
            Trade responsibly. AI decisions are based on probabilistic models and historical data.
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
