import React from 'react'
import { TrendingUp, TrendingDown, DollarSign, Target, Zap } from 'lucide-react'

const MetricCard = ({ title, value, subtitle, trend, icon: Icon }) => {
  const isPositive = trend > 0
  const isNegative = trend < 0
  const trendColor = isPositive ? 'text-secondary' : isNegative ? 'text-tertiary' : 'text-on-surface-variant'
  
  return (
    <div className="glass-container p-4 relative overflow-hidden group hover:border-border-glass transition-all duration-300">
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface-variant flex items-center gap-1.5">
          <Icon size={12} className="text-primary" />
          {title}
        </div>
        {trend !== undefined && (
          <div className={`text-[10px] font-mono font-bold ${trendColor}`}>
            {isPositive ? '+' : ''}{trend.toFixed(2)}
          </div>
        )}
      </div>
      
      <div className="text-xl font-bold text-on-surface font-mono tracking-tight">
        {value}
      </div>
      
      {subtitle && (
        <div className="text-[10px] text-on-surface-variant font-mono mt-1 opacity-70">
          {subtitle}
        </div>
      )}
    </div>
  )
}

const MetricCards = ({ balance, performance }) => {
  const totalBalance = balance?.total || 0
  const unrealizedPnl = performance?.unrealized_pnl || 0
  const equity = totalBalance + unrealizedPnl

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="Balance"
        value={`$${totalBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        subtitle={`Unrealized: $${equity.toFixed(2)}`}
        icon={DollarSign}
      />
      <MetricCard
        title="Daily PnL"
        value={`$${performance?.today_pnl?.toFixed(2) || '0.00'}`}
        subtitle="Incl. Unrealized"
        trend={performance?.today_pnl}
        icon={TrendingUp}
      />
      <MetricCard
        title="Win Rate"
        value={`${performance?.win_rate?.toFixed(1) || '0.0'}%`}
        subtitle={`${performance?.winning_trades || 0}W / ${performance?.losing_trades || 0}L`}
        icon={Target}
      />
      <MetricCard
        title="Open"
        value={performance?.open_positions || 0}
        subtitle={`Total Trades: ${performance?.total_trades || 0}`}
        icon={Zap}
      />
    </div>
  )
}

export default MetricCards
