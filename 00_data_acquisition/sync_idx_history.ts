// Step 00: fill the idx-api SQLite DB with history from idx.co.id, ONE BATCH PER RUN.
//
// Batches (run in this order, newest first):
//   2025-2026  -> 2025-01-01 .. 2026-06-30
//   2024, 2023, ..., 1995  -> one calendar year each
//
// Run from the zcapm folder, using idx-api's import map (@app/, @data/):
//   deno run -A --config ../_arcip/idx-api/deno.json 00_data_acquisition/sync_idx_history.ts          # next pending batch
//   deno run -A --config ../_arcip/idx-api/deno.json 00_data_acquisition/sync_idx_history.ts 2019     # a specific batch
//
// Daily:   stock_summary (OHLC, previous, volume, listed shares - survivor-free), index_summary (IHSG)
// Monthly: dividends, delistings, splits, rights issues, financial ratios (pbv for HML)
//
// Each batch keeps its own state in 00_data_acquisition/batches/<batch>.json (resumable; per-day
// row counts, failures, final status). A Cloudflare block / non-JSON reply aborts the batch
// instead of being recorded as an empty day.
import { sql } from 'drizzle-orm'
import * as schemas from '@app/Backend/Schemas/index.ts'
import * as sync from '@app/Backend/Sync/index.ts'
import BaseClient from '@app/Client.ts'
import Database from '@app/Database.ts'

const DELAY_MS = 2500
const DIR = new URL('./batches/', import.meta.url)

// Optional browser session for Cloudflare: 00_data_acquisition/.idx_session.json = {"cookie": "...", "userAgent": "..."}
// (copy both from the browser that has idx.co.id open; cf_clearance is tied to that User-Agent and IP)
try {
  const s = JSON.parse(await Deno.readTextFile(new URL('./.idx_session.json', import.meta.url)))
  if (s.cookie) Deno.env.set('IDX_COOKIE', s.cookie)
  if (s.userAgent) Deno.env.set('IDX_USER_AGENT', s.userAgent)
  console.log('using browser session from .idx_session.json')
} catch {
  // no session file: idx-api fetches its own cookies
}

// explicit order: object keys like "2024" would otherwise enumerate ascending, before "2025-2026"
const ORDER = ['2025-2026']
const BATCHES: Record<string, [string, string]> = { '2025-2026': ['2025-01-01', '2026-06-30'] }
for (let y = 2024; y >= 1995; y--) {
  ORDER.push(String(y))
  BATCHES[String(y)] = [`${y}-01-01`, `${y}-12-31`]
}

type DayRec = { stock: number; index: number }
type State = {
  batch: string
  range: [string, string]
  status: 'running' | 'done' | 'incomplete' | 'blocked'
  months: Record<string, 'ok' | 'failed'>
  days: Record<string, DayRec | 'failed'>
  summary?: Record<string, number | string>
  updated?: string
}

const stateFile = (b: string) => new URL(`${b}.json`, DIR)
async function loadState(b: string): Promise<State | null> {
  try {
    return JSON.parse(await Deno.readTextFile(stateFile(b)))
  } catch {
    return null
  }
}
const saveState = (s: State) => {
  s.updated = new Date().toISOString()
  return Deno.writeTextFile(stateFile(s.batch), JSON.stringify(s, null, 1))
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))
const ymd = (d: Date) => d.toISOString().slice(0, 10).replaceAll('-', '')

class BlockedError extends Error {}

/** Probe the stock summary endpoint directly: throws BlockedError when IDX answers with a non-JSON page (Cloudflare challenge). */
class Probe extends BaseClient {
  async check(date: string): Promise<void> {
    await this.ensureSession()
    const r = await this.fetcherUrl(`https://www.idx.co.id/primary/TradingSummary/GetStockSummary?date=${date}`)
    const type = r.headers.get('content-type') ?? ''
    await r.body?.cancel()
    if (!r.ok || !type.includes('json')) {
      throw new BlockedError(`IDX returned HTTP ${r.status} (${type || 'no content-type'}) - likely a Cloudflare challenge`)
    }
  }
}
const probe = new Probe()

async function count(table: 'stock' | 'index'): Promise<number> {
  const t = table === 'stock' ? schemas.stockSummary : schemas.indexSummary
  const [row] = await Database.select({ n: sql<number>`count(*)` }).from(t)
  return Number(row?.n ?? 0)
}

async function attempt(label: string, fn: () => Promise<void>): Promise<boolean> {
  for (let i = 1; i <= 3; i++) {
    try {
      await fn()
      return true
    } catch (err) {
      console.error(`[${label}] attempt ${i} failed:`, err instanceof Error ? err.message : err)
      await sleep(2000 * i)
    }
  }
  return false
}

// ---- pick the batch
const arg = Deno.args[0]
let batch = arg
if (!batch) {
  for (const b of ORDER) {
    if ((await loadState(b))?.status !== 'done') {
      batch = b
      break
    }
  }
  if (!batch) {
    console.log('all batches done - now run: python 00_data_acquisition/run.py')
    Deno.exit(0)
  }
}
if (!BATCHES[batch]) {
  console.error(`unknown batch "${batch}". Valid: ${ORDER.join(', ')}`)
  Deno.exit(2)
}
const range = BATCHES[batch]!
await Deno.mkdir(DIR, { recursive: true })
const state: State = (await loadState(batch)) ?? { batch, range, status: 'running', months: {}, days: {} }
state.status = 'running'
const start = new Date(range[0])
const end = new Date(range[1])
console.log(`=== batch ${batch}: ${range[0]} .. ${range[1]} ===`)

try {
  // preflight: a normal trading-day request must come back as JSON
  await probe.check(ymd(start.getDay() % 6 === 0 ? new Date(start.getTime() + 2 * 864e5) : new Date(start.getTime() + 864e5)))

  // monthly corporate-action / ratio tables
  for (let d = new Date(start.getFullYear(), start.getMonth(), 1); d <= end; d.setMonth(d.getMonth() + 1)) {
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    if (state.months[key] === 'ok') continue
    const [y, m] = [d.getFullYear(), d.getMonth() + 1]
    const ok = [
      await attempt(`dividend ${key}`, () => sync.syncCompanyDividend(y, m)),
      await attempt(`delisting ${key}`, () => sync.syncCompanyDelisting(y, m)),
      await attempt(`split ${key}`, () => sync.syncStockSplit(y, m)),
      await attempt(`rights ${key}`, () => sync.syncRightOffering(y, m)),
      await attempt(`ratio ${key}`, () => sync.syncFinancialRatio(y, m))
    ].every(Boolean)
    state.months[key] = ok ? 'ok' : 'failed'
    await saveState(state)
    await sleep(DELAY_MS)
  }

  // daily prices (weekdays; holidays return no data - verified by a probe so blocks are not mistaken for holidays)
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    if (d.getDay() === 0 || d.getDay() === 6) continue
    const key = ymd(d)
    const prev = state.days[key]
    if (prev && prev !== 'failed') continue
    const [s0, i0] = [await count('stock'), await count('index')]
    const ok = (await attempt(`stock ${key}`, () => sync.syncStockSummary(key))) &&
      (await attempt(`index ${key}`, () => sync.syncIndexSummary(key)))
    const rec = { stock: (await count('stock')) - s0, index: (await count('index')) - i0 }
    if (ok && rec.stock === 0) {
      await probe.check(key)
      console.log(`[no trades / holiday] ${key}`)
    }
    state.days[key] = ok ? rec : 'failed'
    await saveState(state)
    await sleep(DELAY_MS)
  }

  const days = Object.values(state.days)
  const traded = days.filter((r) => r !== 'failed' && r.stock > 0) as DayRec[]
  const failed = days.filter((r) => r === 'failed').length + Object.values(state.months).filter((m) => m === 'failed').length
  state.summary = {
    weekdays: days.length,
    trading_days: traded.length,
    stock_rows: traded.reduce((a, r) => a + r.stock, 0),
    index_rows: traded.reduce((a, r) => a + r.index, 0),
    failed_items: failed
  }
  state.status = failed === 0 ? 'done' : 'incomplete'
  await saveState(state)
  console.log(`=== batch ${batch} ${state.status}:`, state.summary)
  const next = ORDER[ORDER.indexOf(batch) + 1]
  if (state.status === 'done') console.log(next ? `next batch: ${next}` : 'all batches done - now run: python 00_data_acquisition/run.py')
  else console.log(`rerun batch ${batch} to retry the failed items`)
} catch (err) {
  state.status = err instanceof BlockedError ? 'blocked' : 'incomplete'
  await saveState(state)
  console.error(`=== batch ${batch} ${state.status}: ${err instanceof Error ? err.message : err}`)
  Deno.exit(1)
}
