/**
 * 產生 Google Flights 搜尋 URL
 * @param origin 出發機場代碼（如 TPE）
 * @param dest 目的地機場代碼（如 NRT）
 * @param dep 出發日期（YYYY-MM-DD）
 * @param ret 回程日期（YYYY-MM-DD）
 * @returns Google Flights URL
 */
export function getGoogleFlightsUrl(
  origin: string,
  dest: string,
  dep: string,
  ret: string
): string {
  const q = `flights from ${origin} to ${dest} on ${dep} returning ${ret}`
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(q)}`
}
