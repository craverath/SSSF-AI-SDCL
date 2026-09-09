/**
 * Spend aggregation, against the payload shapes real harnesses actually write.
 *
 * The fixtures below are copied from a live `adw_simple_sdlc` trace: three Kiro
 * phases that billed credits and reported no tokens, and one Antigravity phase
 * that reported tokens and no money at all. The reconciliation assertion is the
 * point of the file — the per-agent split must add back up to what the session
 * row says, or the panel is inventing numbers.
 *
 * Run with: bun test
 */
import { describe, expect, test } from 'bun:test'
import type { EventRow } from './types'
import { agentSpend, spendFor, spendLabel } from './spend'

function agentEnd(
  name: string,
  tokens: number,
  payload: Record<string, unknown>,
  rowid = 1,
): EventRow {
  return {
    rowid,
    event_id: `evt_${rowid}`,
    adw_id: '0584f562',
    phase_id: `ph_${rowid}`,
    parent_id: null,
    type: 'agent_end',
    name,
    payload_json: JSON.stringify(payload),
    tokens,
    started_at: null,
    ended_at: null,
  }
}

/** A Kiro phase: credits billed, no tokens and no dollars reported anywhere. */
function kiroPhase(name: string, credits: number, rowid: number): EventRow {
  return agentEnd(
    name,
    0,
    {
      cost: 0,
      credits,
      usage: {
        input_tokens: 0,
        output_tokens: 0,
        cache_read_tokens: 0,
        cache_write_tokens: 0,
        reasoning_tokens: 0,
        total_tokens: 0,
        input_cost: 0,
        output_cost: 0,
        cache_read_cost: 0,
        cache_write_cost: 0,
        total_cost: 0,
        credits,
      },
      context_tokens: 7305,
      context_window: 1_000_000,
    },
    rowid,
  )
}

const SESSION: EventRow[] = [
  kiroPhase('planner', 9.370201368656716, 1),
  kiroPhase('builder', 6.821198249170812, 2),
  kiroPhase('reviewer', 4.730430005970149, 3),
  agentEnd(
    'documenter',
    93_110,
    {
      cost: 0,
      credits: 0,
      usage: {
        input_tokens: 86_198,
        output_tokens: 6912,
        cache_read_tokens: 384_545,
        cache_write_tokens: 0,
        reasoning_tokens: 4227,
        total_tokens: 93_110,
        input_cost: 0,
        output_cost: 0,
        cache_read_cost: 0,
        cache_write_cost: 0,
        total_cost: 0,
        credits: 0,
      },
      context_tokens: 0,
      context_window: 0,
    },
    4,
  ),
]

describe('agentSpend', () => {
  test('splits a mixed roster by agent and keeps each unit', () => {
    const rows = agentSpend(SESSION)
    expect(rows.map((r) => r.agent)).toEqual(['planner', 'builder', 'reviewer', 'documenter'])

    const planner = spendFor(rows, 'planner')
    expect(planner?.unit).toBe('credit')
    expect(planner?.credits).toBeCloseTo(9.3702, 4)
    expect(planner?.billedTokens).toBe(0)
    expect(spendLabel(planner!)).toBe('9.3702 cr')

    const documenter = spendFor(rows, 'documenter')
    expect(documenter?.unit).toBe('token')
    expect(documenter?.credits).toBe(0)
    expect(documenter?.billedTokens).toBe(93_110)
    expect(documenter?.inputTokens).toBe(86_198)
  })

  test('reconciles with the session totals the tracer recorded', () => {
    const rows = agentSpend(SESSION)
    const credits = rows.reduce((sum, r) => sum + r.credits, 0)
    const tokens = rows.reduce((sum, r) => sum + r.billedTokens, 0)
    // sessions.total_credits / total_tokens for this run.
    expect(credits).toBeCloseTo(20.9218, 4)
    expect(tokens).toBe(93_110)
  })

  test('sums every phase an agent ran, so a revise loop is not lost', () => {
    const rows = agentSpend([...SESSION, kiroPhase('builder', 2.5, 5)])
    const builder = spendFor(rows, 'builder')
    expect(builder?.calls).toBe(2)
    expect(builder?.credits).toBeCloseTo(9.3212, 4)
  })

  test('falls back to events.tokens on a run predating the breakdown', () => {
    const rows = agentSpend([agentEnd('planner', 1234, { cost: 0.5 }, 1)])
    const planner = spendFor(rows, 'planner')
    expect(planner?.billedTokens).toBe(1234)
    expect(planner?.costUsd).toBe(0.5)
    // Dollars outrank tokens: a harness that prices its own tokens has already
    // answered the cost question.
    expect(planner?.unit).toBe('dollar')
  })

  test('reports no unit when a harness billed nothing at all', () => {
    const rows = agentSpend([agentEnd('scout', 0, { cost: 0, credits: 0 }, 1)])
    expect(spendFor(rows, 'scout')?.unit).toBe('none')
    expect(spendLabel(spendFor(rows, 'scout')!)).toBe('—')
  })

  test('ignores every event type that is not agent_end', () => {
    const other: EventRow = { ...agentEnd('planner', 999, { credits: 99 }, 9), type: 'tool_call' }
    expect(agentSpend([other])).toEqual([])
  })
})
