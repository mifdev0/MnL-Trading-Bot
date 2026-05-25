import { create } from 'zustand'
import axios from 'axios'

const useStore = create((set, get) => ({
  // State
  balance: { total: 0, free: 0, used: 0 },
  positions: [],
  trades: [],
  performance: {},
  news: [],
  signals: [],
  botStatus: { paused: false, status: 'active', open_positions: 0 },
  loading: false,
  error: null,

  // Actions
  fetchBalance: async () => {
    try {
      const response = await axios.get('/api/balance')
      if (response.data && response.data.data) {
        set({ balance: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching balance:', error)
      set({ error: error.message })
    }
  },

  fetchPositions: async () => {
    try {
      const response = await axios.get('/api/positions')
      if (response.data && response.data.data) {
        set({ positions: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching positions:', error)
      set({ error: error.message })
    }
  },

  fetchTrades: async () => {
    try {
      const response = await axios.get('/api/trades')
      if (response.data && response.data.data) {
        set({ trades: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching trades:', error)
      set({ error: error.message })
    }
  },

  fetchPerformance: async () => {
    try {
      const response = await axios.get('/api/performance')
      if (response.data && response.data.data) {
        set({ performance: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching performance:', error)
      set({ error: error.message })
    }
  },

  fetchNews: async () => {
    try {
      const response = await axios.get('/api/news')
      if (response.data && response.data.data) {
        set({ news: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching news:', error)
      set({ error: error.message })
    }
  },

  fetchSignals: async () => {
    try {
      const response = await axios.get('/api/signals')
      if (response.data && response.data.data) {
        set({ signals: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching signals:', error)
      set({ error: error.message })
    }
  },

  fetchBotStatus: async () => {
    try {
      const response = await axios.get('/api/bot/status')
      if (response.data && response.data.data) {
        set({ botStatus: response.data.data })
      }
    } catch (error) {
      console.error('Error fetching bot status:', error)
      set({ error: error.message })
    }
  },

  pauseBot: async () => {
    try {
      await axios.post('/api/bot/pause')
      await get().fetchBotStatus()
    } catch (error) {
      set({ error: error.message })
    }
  },

  resumeBot: async () => {
    try {
      await axios.post('/api/bot/resume')
      await get().fetchBotStatus()
    } catch (error) {
      set({ error: error.message })
    }
  },

  fetchAll: async () => {
    set({ loading: true })
    await Promise.all([
      get().fetchBalance(),
      get().fetchPositions(),
      get().fetchTrades(),
      get().fetchPerformance(),
      get().fetchNews(),
      get().fetchSignals(),
      get().fetchBotStatus()
    ])
    set({ loading: false })
  }
}))

export default useStore
