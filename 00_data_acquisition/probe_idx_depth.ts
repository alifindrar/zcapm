// Step 00 probe: how far back does idx.co.id serve the per-date stock summary, and does it include dead codes?
//
// Read-only: one request per date, nothing is written to the idx-api DB. Needs a fresh browser session in
// 00_data_acquisition/.idx_session.json (same file as sync_idx_history.ts). Run from the zcapm folder:
//   deno run -A 00_data_acquisition/probe_idx_depth.ts                      # default dates, newest first
//   deno run -A 00_data_acquisition/probe_idx_depth.ts 20260630 20081112    # first date = baseline of listed codes
//
// Per date: HTTP status, rows, rows with volume, and codes that are not in the baseline date (delisted or renamed
// since - the survivor-free part). Rows are saved to 00_data_acquisition/batches/probe_depth.json.
const DELAY_MS = 2500
const DEFAULT_DATES = ['20260630', '20191113', '20170111', '20151111', '20121114', '20101110', '20081112', '20051116',
  '20021113', '20001115', '19971112', '19951115']

const s = JSON.parse(await Deno.readTextFile(new URL('./.idx_session.json', import.meta.url)))
const headers: Record<string, string> = {
  Accept: 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
  Referer: 'https://www.idx.co.id/',
  'User-Agent': s.userAgent,
  'X-Requested-With': 'XMLHttpRequest',
  Cookie: s.cookie
}
type Row = { StockCode: string; Close: number; Previous: number; Volume: number; ListedShares: number; DelistingDate: string; Remarks: string }

const dates = Deno.args.length ? Deno.args : DEFAULT_DATES
const out: Record<string, unknown> = {}
let baseline: Set<string> | null = null
for (const d of dates) {
  const r = await fetch(`https://www.idx.co.id/primary/TradingSummary/GetStockSummary?date=${d}`, { headers })
  const type = r.headers.get('content-type') ?? ''
  const text = await r.text()
  if (!r.ok || !type.includes('json')) {
    console.log(`${d}: HTTP ${r.status} (${type || 'no content-type'}) - Cloudflare challenge, refresh .idx_session.json`)
    out[d] = { status: r.status, type }
    break
  }
  const rows: Row[] = JSON.parse(text).data ?? []
  const common = rows.filter((x) => /^[A-Z]{4}$/.test(x.StockCode))
  const codes = new Set(common.map((x) => x.StockCode))
  baseline ??= codes
  const dead = [...codes].filter((c) => !baseline!.has(c)).sort()
  console.log(`${d}: rows ${rows.length}, common stocks ${common.length}, with volume ${common.filter((x) => x.Volume > 0).length}, ` +
    `not in baseline ${dead.length}${dead.length ? ` (${dead.slice(0, 12).join(' ')}${dead.length > 12 ? ' ...' : ''})` : ''}`)
  out[d] = rows.map((x) => ({ code: x.StockCode, close: x.Close, previous: x.Previous, volume: x.Volume, listed_shares: x.ListedShares,
    delisting_date: x.DelistingDate, remarks: x.Remarks }))
  await new Promise((res) => setTimeout(res, DELAY_MS))
}
await Deno.mkdir(new URL('./batches/', import.meta.url), { recursive: true })
await Deno.writeTextFile(new URL('./batches/probe_depth.json', import.meta.url), JSON.stringify(out))
