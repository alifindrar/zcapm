// Orchestrator: runs sync_idx_history.ts for batches 2025-2026 down to 2020.
//
// Usage:
//   deno run -A --config ../_arcip/idx-api/deno.json 00_data_acquisition/run_sync_until_2020.ts

const BATCHES = ['2025-2026', '2024', '2023', '2022', '2021', '2020']
const BATCH_DIR = new URL('./batches/', import.meta.url)

async function getBatchState(batch: string): Promise<any> {
  try {
    return JSON.parse(await Deno.readTextFile(new URL(`${batch}.json`, BATCH_DIR)))
  } catch {
    return null
  }
}

console.log('=== ZCAPM Data Acquisition: Syncing from 2026 back to 2020 ===')
console.log(`Target batches: ${BATCHES.join(', ')}\n`)

for (const batch of BATCHES) {
  let state = await getBatchState(batch)
  if (state?.status === 'done') {
    console.log(`[Batch ${batch}] Already marked DONE. Skipping.`)
    continue
  }

  // If another process is currently running this batch, wait for it to complete
  if (state?.status === 'running') {
    console.log(`[Batch ${batch}] Active sync in progress. Monitoring until complete...`)
    while (true) {
      await new Promise((r) => setTimeout(r, 10000))
      state = await getBatchState(batch)
      if (!state || state.status !== 'running') {
        break
      }
      const daysCount = Object.keys(state.days ?? {}).length
      console.log(`[Batch ${batch}] Progress: ${daysCount} days recorded...`)
    }
    if (state?.status === 'done') {
      console.log(`[Batch ${batch}] Finished successfully!`)
      continue
    }
  }

  console.log(`\n============================================================`)
  console.log(`[Batch ${batch}] Starting synchronization...`)
  console.log(`============================================================\n`)

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

  if (!status.success) {
    console.error(`\n[Batch ${batch}] Process exited with code ${status.code}.`)
    console.error(`If blocked by Cloudflare, refresh cookies in .idx_session.json and re-run.`)
    Deno.exit(status.code)
  }

  console.log(`\n[Batch ${batch}] Finished successfully!`)
}

console.log('\n============================================================')
console.log('All batches from January 2020 to June 2026 are COMPLETE!')
console.log('Now run: python 00_data_acquisition/run.py')
console.log('============================================================')
