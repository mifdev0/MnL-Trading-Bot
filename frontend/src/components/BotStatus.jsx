import React from 'react'
import { Activity, Power, CircleDot } from 'lucide-react'

const BotStatus = ({ botStatus, onPause, onResume }) => {
  const isActive = !botStatus?.paused

  return (
    <div className="glass-container p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container border border-border-glass">
            <Activity size={14} className={isActive ? 'text-secondary' : 'text-tertiary'} />
            <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">System</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isActive ? 'bg-secondary' : 'bg-tertiary'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isActive ? 'bg-secondary' : 'bg-tertiary'}`}></span>
            </div>
            <span className="text-xs font-mono font-bold">
              {isActive ? 'ACTIVE' : 'PAUSED'}
            </span>
            <span className="text-[10px] text-on-surface-variant font-mono flex items-center gap-1 ml-2">
              <CircleDot size={10} />
              {botStatus?.open_positions || 0} POSITIONS
            </span>
          </div>
        </div>
        
        <div>
          {isActive ? (
            <button
              onClick={onPause}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-tertiary/10 text-tertiary border border-tertiary/20 hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 text-xs font-bold"
            >
              <Power size={14} />
              PAUSE SYSTEM
            </button>
          ) : (
            <button
              onClick={onResume}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-secondary/10 text-secondary border border-secondary/20 hover:bg-secondary hover:text-on-secondary transition-all duration-300 text-xs font-bold"
            >
              <Power size={14} />
              RESUME SYSTEM
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default BotStatus
