import React from 'react'
import { Briefcase, ArrowUpRight, ArrowDownRight, Info, XCircle } from 'lucide-react'
import useStore from '../store/useStore'

const PositionsTable = ({ positions }) => {
  const { closePosition } = useStore()
  const getStatusStyle = (status) => {
    switch(status) {
      case 'BE':
        return 'bg-primary/20 text-primary border-primary/30'
      case 'TRAILING':
        return 'bg-secondary/20 text-secondary border-secondary/30'
      case 'OPEN':
        return 'bg-surface-container-high text-on-surface border-border-glass'
      default:
        return 'bg-surface-container text-on-surface-variant'
    }
  }

  if (!positions || positions.length === 0) {
    return (
      <div className="glass-container p-4">
        <div className="flex items-center gap-2 mb-4 border-b border-border-glass pb-3">
          <Briefcase size={16} className="text-secondary" />
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface">Active Positions</h2>
        </div>
        <div className="text-on-surface-variant text-center py-6 text-xs font-mono italic opacity-50">
          No active positions detected
        </div>
      </div>
    )
  }

  return (
    <div className="glass-container p-3 md:p-4 overflow-hidden">
      <div className="flex items-center gap-2 mb-4 border-b border-border-glass pb-3">
        <Briefcase size={16} className="text-secondary" />
        <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface">Active Positions</h2>
      </div>
      <div className="overflow-x-auto -mx-3 px-3 md:-mx-4 md:px-4">
        <table className="w-full text-left min-w-[600px] md:min-w-0">
          <thead>
            <tr className="text-[9px] md:text-[10px] uppercase tracking-wider text-on-surface-variant font-bold border-b border-border-glass/50">
              <th className="pb-2">Pair</th>
              <th className="pb-2">Side</th>
              <th className="pb-2 text-right">Entry</th>
              <th className="pb-2 text-right">Price Now</th>
              <th className="pb-2 text-right">PnL</th>
              <th className="pb-2 text-center">Status</th>
              <th className="pb-2 text-right">Analysis</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-glass/30">
            {positions.map((position) => {
              const pnlValue = position?.pnl || 0
              const isPositive = pnlValue >= 0
              const side = position?.side === 'LONG'
              
              return (
                <tr key={position?.id} className="group hover:bg-surface-glass transition-colors">
                  <td className="py-2 md:py-2.5 font-mono text-[11px] md:text-xs font-bold">
                    {position?.pair?.replace('/USDT:USDT', '')}
                  </td>
                  <td className="py-2 md:py-2.5">
                    <span className={`flex items-center gap-1 text-[9px] md:text-[10px] font-bold ${side ? 'text-secondary' : 'text-tertiary'}`}>
                      {side ? <ArrowUpRight size={10} className="md:w-3 md:h-3" /> : <ArrowDownRight size={10} className="md:w-3 md:h-3" />}
                      {position?.side}
                    </span>
                  </td>
                  <td className="py-2 md:py-2.5 text-right font-mono text-[11px] md:text-xs text-on-surface-variant">
                    ${position?.entry_price?.toFixed(4)}
                  </td>
                  <td className="py-2 md:py-2.5 text-right font-mono text-[11px] md:text-xs font-bold text-on-surface">
                    ${position?.current_price?.toFixed(4) || '0.0000'}
                  </td>
                  <td className={`py-2 md:py-2.5 text-right font-mono text-[11px] md:text-xs font-bold ${isPositive ? 'text-secondary' : 'text-tertiary'}`}>
                    {isPositive ? '+' : ''}${pnlValue.toFixed(2)}
                  </td>
                  <td className="py-2 md:py-2.5 text-center">
                    <span className={`px-1.5 md:px-2 py-0.5 rounded text-[8px] md:text-[9px] font-bold border ${getStatusStyle(position?.status)}`}>
                      {position?.status}
                    </span>
                  </td>
                  <td className="py-2 md:py-2.5 text-right">
                    <div className="flex items-center justify-end gap-2 md:gap-3">
                      <div className="group/info relative inline-block">
                        <Info size={12} className="md:w-[14px] md:h-[14px] text-on-surface-variant cursor-help opacity-40 hover:opacity-100 transition-opacity" />
                        <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-surface-container border border-border-glass rounded text-[10px] text-on-surface-variant opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible transition-all z-50 shadow-xl backdrop-blur-md text-left">
                          {position?.ai_reason}
                        </div>
                      </div>
                      <button 
                        onClick={() => {
                          if (window.confirm(`Close ${position.pair} manually?`)) {
                            closePosition(position.id)
                          }
                        }}
                        className="text-tertiary opacity-40 hover:opacity-100 transition-opacity"
                        title="Close Position"
                      >
                        <XCircle size={12} className="md:w-[14px] md:h-[14px]" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PositionsTable
