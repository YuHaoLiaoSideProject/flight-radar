export interface WeekItem {
  weekIndex: number
  departureDate: string
  returnDate: string
  label: string
  tag: string | null
  isHoliday: boolean
  price: number | null
}

export interface RouteSummary {
  id: string
  name: string
  origin: string
  destination: string
  color: string
  minPrice: number
  path: string
}

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

export interface RouteDetail {
  id: string
  name: string
  origin: string
  destination: string
  airline: string
  airlineName: string
  color: string
  stayDays: number
  generatedAt: string
  rawFetchedAt: string
  weeksCount: number
  stats: {
    minPrice: number
    avgPrice: number
  }
  topDeals: WeekItem[]
  weeklyData: WeekItem[]
}
