import React from 'react'
import { History, CheckCircle, XCircle } from 'lucide-react'

const TradeHistory = ({ trades }) => {
  if (!trades || trades.length === 0) {
    return (
      <div className="glass-container p-4">
        <div className="flex items-center gap-2 mb-4 border-b border-border-glass pb-3">
          <History size={16} className="text-primary" />
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface">Execution History</h2>
        </div>
        <div className="text-on-surface-variant text-center py-6 text-xs font-mono italic opacity-50">
          No records found
        </div>
      </div>
    )
  }

  return (
    <div className="glass-container p-4">
      <div className="flex items-center gap-2 mb-4 border-b border-border-glass pb-3">
        <History size={16} className="text-primary" />
        <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface">Execution History</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-on-surface-variant font-bold border-b border-border-glass/50">
              <th className="pb-2">Pair</th>
              <th className="pb-2">Side</th>
              <th className="pb-2 text-right">PnL</th>
              <th className="pb-2 text-center">Conf</th>
              <th className="pb-2 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-glass/30">
            {trades.slice(0, 10).map((trade) => {
              const pnlValue = trade?.pnl || 0
              const isPositive = pnlValue >= 0
              
              return (
                <tr key={trade?.id} className="hover:bg-surface-glass transition-colors">
                  <td className="py-2 font-mono text-xs">
                    {trade?.pair?.replace('/USDT:USDT', '')}
                  </td>
                  <td className="py-2">
                    <span className={`text-[10px] font-bold ${trade?.side === 'LONG' ? 'text-secondary' : 'text-tertiary'}`}>
                      {trade?.side}
                    </span>
                  </td>
                  <td className={`py-2 text-right font-mono text-xs font-bold ${isPositive ? 'text-secondary' : 'text-tertiary'}`}>
                    <div className="flex items-center justify-end gap-1">
                      {isPositive ? <CheckCircle size={10} /> : <XCircle size={10} />}
                      {isPositive ? '+' : ''}${pnlValue.toFixed(2)}
                    </div>
                  </td>
                  <td className="py-2 text-center text-on-surface-variant font-mono text-[10px]">
                    {trade?.confidence}%
                  </td>
                  <td className="py-2 text-right text-on-surface-variant font-mono text-[9px] opacity-60">
                    {trade?.closed_at ? new Date(trade.closed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
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

export default TradeHistory
