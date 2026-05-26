import React, { useState, useEffect } from 'react'
import { Newspaper, TrendingUp, TrendingDown, Minus, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const NewsFeed = ({ news }) => {
  // Force re-render every minute to update relative time
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (isoString) => {
    if (!isoString) return ''
    try {
      const date = new Date(isoString)
      // Use date-fns for accurate relative time
      return formatDistanceToNow(date, { addSuffix: true })
    } catch (e) {
      return ''
    }
  }

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'bullish':
        return <TrendingUp size={12} className="text-secondary" />
      case 'bearish':
        return <TrendingDown size={12} className="text-tertiary" />
      default:
        return <Minus size={12} className="text-on-surface-variant" />
    }
  }

  return (
    <div className="glass-container p-4">
      <div className="flex items-center gap-2 mb-4 border-b border-border-glass pb-3">
        < Newspaper size={16} className="text-primary" />
        <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface">Intelligence Feed</h2>
      </div>
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {news && news.length > 0 ? (
          news.map((item) => (
            <div 
              key={item.id} 
              className="p-2.5 rounded-lg bg-surface-container/30 border border-border-glass/30 hover:bg-surface-container/50 transition-all group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="bg-surface-container-high p-1 rounded">
                    {getSentimentIcon(item.sentiment)}
                  </div>
                  <span className={`text-[9px] font-bold uppercase tracking-tighter ${
                    item.sentiment === 'bullish' ? 'text-secondary' : 
                    item.sentiment === 'bearish' ? 'text-tertiary' : 'text-on-surface-variant'
                  }`}>
                    {item.sentiment}
                  </span>
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-[8px] font-mono text-primary font-bold">
                    {formatTime(item.published_at)}
                  </span>
                  <span className="text-[7px] font-mono text-on-surface-variant opacity-40">
                    {item.source}
                  </span>
                </div>
              </div>
              
              <h3 className="text-[11px] leading-relaxed font-medium text-on-surface line-clamp-2 group-hover:text-primary transition-colors">
                {item.title}
              </h3>
              
              {item.coins && item.coins.length > 0 && (
                <div className="flex gap-1 flex-wrap mt-2">
                  {item.coins.slice(0, 3).map((coin, idx) => (
                    <span 
                      key={idx} 
                      className="text-[8px] font-mono bg-primary/10 text-primary px-1.5 py-0.5 rounded border border-primary/20"
                    >
                      ${coin}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-on-surface-variant text-center py-6 text-xs font-mono italic opacity-50">
            Scanning frequencies...
          </div>
        )}
      </div>
    </div>
  )
}

export default NewsFeed
