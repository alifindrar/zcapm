// Orchestrator: runs sync_idx_history.ts for batches 2025-2026 down to 2005.
//
// Features:
//   - Loops in reverse chronological order (2025-2026, 2024, ..., 2005)
//   - Resumes seamlessly if interrupted
//   - If a Cloudflare block / expired cookie is encountered, auto-pauses and
//     waits for .idx_session.json to be updated with fresh cookies, then auto-resumes!
//   - Runs python 00_data_acquisition/run.py upon completion.
//
// Usage:
//   deno run -A --config ../_arcip/idx-api/deno.json 00_data_acquisition/run_sync.ts

const TARGET_YEAR = 2020
const BATCHES = ['2026-recent', '2025-2026']
for (let y = 2024; y >= TARGET_YEAR; y--) {
  BATCHES.push(String(y))
}

const BATCH_DIR = new URL('./batches/', import.meta.url)
const SESSION_FILE = new URL('./.idx_session.json', import.meta.url)

async function getBatchState(batch: string): Promise<any> {
  try {
    return JSON.parse(await Deno.readTextFile(new URL(`${batch}.json`, BATCH_DIR)))
  } catch {
    return null
  }
}

async function getSessionMtime(): Promise<number> {
  try {
    const info = await Deno.stat(SESSION_FILE)
    return info.mtime?.getTime() ?? 0
  } catch {
    return 0
  }
}

async function waitForFreshSession(oldMtime: number): Promise<void> {
  console.log('\n============================================================')
  console.log('[PAUSED] Cloudflare clearance expired.')
  console.log('Please refresh https://www.idx.co.id/primary/home/GetIndexList in your browser,')
  console.log('copy the new Cookie header, and update 00_data_acquisition/.idx_session.json.')
  console.log('The orchestrator is watching for updates and will auto-resume immediately...')
  console.log('============================================================\n')

  while (true) {
    await new Promise((r) => setTimeout(r, 4000))
    const currentMtime = await getSessionMtime()
    if (currentMtime > oldMtime) {
      console.log('Detected updated .idx_session.json! Resuming batch in 2 seconds...\n')
      await new Promise((r) => setTimeout(r, 2000))
      return
    }
  }
}

console.log('=== ZCAPM Data Acquisition: Syncing from 2026 back to ' + TARGET_YEAR + ' ===')
console.log(`Total Batches (${BATCHES.length}): ${BATCHES.join(', ')}\n`)

for (const batch of BATCHES) {
  while (true) {
    let state = await getBatchState(batch)
    if (state?.status === 'done') {
      console.log(`[Batch ${batch}] Already marked DONE. Skipping.`)
      break
    }

    console.log(`\n============================================================`)
    console.log(`[Batch ${batch}] Starting synchronization...`)
    console.log(`============================================================\n`)

    const sessionMtimeBefore = await getSessionMtime()

    const cmd = new Deno.Command(Deno.execPath(), {
      args: [
        'run',
        '-A',
        '--node-modules-dir=none',
        '--config',
        '../_arcip/idx-api/deno.json',
        '00_data_acquisition/sync_idx_history.ts',
        batch
      ],
      stdout: 'inherit',
      stderr: 'inherit'
    })

    const process = cmd.spawn()
    const status = await process.status

    if (status.success) {
      console.log(`\n[Batch ${batch}] Finished successfully!`)
      break
    } else {
      console.warn(`\n[Batch ${batch}] Exited with code ${status.code} (likely Cloudflare challenge).`)
      await waitForFreshSession(sessionMtimeBefore)
      // will loop and retry this batch
    }
  }
}

console.log('\n============================================================')
console.log(`All batches from ${TARGET_YEAR} to 2026 are COMPLETE!`)
console.log('Generating canonical raw CSVs via run.py...')
console.log('============================================================\n')

const pyCmd = new Deno.Command('python', {
  args: ['00_data_acquisition/run.py'],
  stdout: 'inherit',
  stderr: 'inherit'
})
await pyCmd.spawn().status

console.log('\nPipeline Step 00 (Data Acquisition) fully complete!')
