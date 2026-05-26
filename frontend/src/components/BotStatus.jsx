import React from 'react'
import { Activity, Power, CircleDot, XOctagon } from 'lucide-react'
import useStore from '../store/useStore'

const BotStatus = ({ botStatus, onPause, onResume }) => {
  const { closeAllPositions } = useStore()
  const isActive = !botStatus?.paused

  return (
    <div className="glass-container p-3 md:p-4 mb-4 md:mb-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-surface-container border border-border-glass">
            <Activity size={12} className={isActive ? 'text-secondary md:w-[14px] md:h-[14px]' : 'text-tertiary md:w-[14px] md:h-[14px]'} />
            <span className="text-[10px] md:text-xs font-semibold uppercase tracking-wider text-on-surface-variant">System</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isActive ? 'bg-secondary' : 'bg-tertiary'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isActive ? 'bg-secondary' : 'bg-tertiary'}`}></span>
            </div>
            <span className="text-[11px] md:text-xs font-mono font-bold">
              {isActive ? 'ACTIVE' : 'PAUSED'}
            </span>
            <span className="text-[9px] md:text-[10px] text-on-surface-variant font-mono flex items-center gap-1 ml-1 md:ml-2">
              <CircleDot size={8} className="md:w-[10px] md:h-[10px]" />
              {botStatus?.open_positions || 0} POSITIONS
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-2 md:gap-3 w-full sm:w-auto">
          <button
            onClick={() => {
              if (window.confirm('WARNING: Close all active positions immediately?')) {
                closeAllPositions()
              }
            }}
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 md:px-4 py-1.5 rounded-lg bg-tertiary/10 text-tertiary border border-tertiary/20 hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 text-[9px] md:text-[10px] font-bold"
          >
            <XOctagon size={12} className="md:w-[14px] md:h-[14px]" />
            CLOSE ALL
          </button>
          
          {isActive ? (
            <button
              onClick={onPause}
              className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 md:px-4 py-1.5 rounded-lg bg-surface-container-high text-on-surface-variant border border-border-glass hover:bg-tertiary/10 hover:text-tertiary transition-all duration-300 text-[9px] md:text-[10px] font-bold"
            >
              <Power size={12} className="md:w-[14px] md:h-[14px]" />
              PAUSE
            </button>
          ) : (
            <button
              onClick={onResume}
              className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 md:px-4 py-1.5 rounded-lg bg-secondary/10 text-secondary border border-secondary/20 hover:bg-secondary hover:text-on-secondary transition-all duration-300 text-[9px] md:text-[10px] font-bold"
            >
              <Power size={12} className="md:w-[14px] md:h-[14px]" />
              RESUME
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default BotStatus
