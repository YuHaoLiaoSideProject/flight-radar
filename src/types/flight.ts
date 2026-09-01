export interface WeekItem {
  weekIndex: number
  departureDate: string
  returnDate: string
  label: string
  tag: string | null
  isHoliday: boolean
  price: number | null
  previousPrice: number | null
  priceDiff: number | null
  history: { queryDate: string; price: number }[]
}

export interface TopDealItem {
  weekIndex: number
  departureDate: string
  returnDate: string
  label: string
  tag: string | null
  price: number
}

export interface RouteSummary {
  id: string
  name: string
  origin: string
  destination: string
  airline: string
  airlineName: string
  color: string
  minPrice: number
  path: string
}

// Alias kept for backward compat if needed
export type RouteInfo = RouteSummary

export interface AirlineSummary {
  code: string
  name: string
  routesCount: number
  path: string
}

export interface RootIndex {
  title: string
  version: string
  generatedAt: string
  weeksCount: number
  config: {
    defaultAirline: string
    defaultRoute: string
    tripDays: number
    currency: string
  }
  airlines: AirlineSummary[]
  routes: RouteSummary[]
}

// meta.json 結構
export interface RouteMeta {
  id: string
  name: string
  origin: string
  destination: string
  airline: string
  airlineName: string
  color: string
  stayDays: number
  generatedAt: string
  latestQueryDate: string
  totalSnapshotsRecorded: number
  weeksCount: number
  stats: {
    minPrice: number
    avgPrice: number
  }
  topDeals: TopDealItem[]
}

// 完整航線資料 (meta + 已載入的週資料)
export interface RouteDetail extends RouteMeta {
  weeklyData: WeekItem[]
  loadedWeeks: number
  totalWeeks: number
  isLoadingWeeks: boolean
  loadProgress: number
}
