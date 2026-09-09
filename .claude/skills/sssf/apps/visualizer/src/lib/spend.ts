/**
 * Per-agent spend, derived from the `agent_end` events the trace already has.
 *
 * Nothing here is stored or served. agents.py writes each phase's total spend
 * onto that phase's `agent_end` event, and the session's own totals are a sum
 * over exactly those rows — so the split is recoverable from any db, including
 * runs recorded before this view existed. No migration, no re-run.
 *
 * The unit is the whole point. A mixed roster bills in different currencies in
 * the same session: Kiro CLI reports credits and no tokens at all, Antigravity
 * reports tokens and no dollars, pi and Claude Code report dollars. Adding
 * those into one headline is arithmetic on incompatible units, which is how a
 * run that cost 20 credits ends up reading as "$0.0000". Each agent therefore
 * carries the unit it actually reported, and nothing is ever summed across two
 * different units.
 */
import type { AgentEndPayload, EventRow } from './types'
import { parsePayload } from './events'
import { fmtCost, fmtCredits, fmtTokens } from './format'

/** What a harness actually billed in, inferred from what it reported. */
export type BillingUnit = 'credit' | 'dollar' | 'token' | 'none'

export interface AgentSpend {
  agent: string
  /** Completed agent phases — one `agent_end` each. Retries are inside them. */
  calls: number
  credits: number
  costUsd: number
  /**
   * Billed tokens as the harness defines them, which is NOT the same
   * definition everywhere: pi and Claude Code count cached re-reads in it,
   * codex and Antigravity do not. Compare it across agents on the same
   * harness, never across harnesses.
   */
  billedTokens: number
  inputTokens: number
  outputTokens: number
  cacheReadTokens: number
  reasoningTokens: number
  unit: BillingUnit
}

function blank(agent: string): AgentSpend {
  return {
    agent,
    calls: 0,
    credits: 0,
    costUsd: 0,
    billedTokens: 0,
    inputTokens: 0,
    outputTokens: 0,
    cacheReadTokens: 0,
    reasoningTokens: 0,
    unit: 'none',
  }
}

/**
 * The unit this agent's spend is denominated in.
 *
 * Credits win over dollars because only a credit-billed harness reports them,
 * and dollars win over tokens because a harness that prices its own tokens has
 * already answered the cost question. `none` means the harness reported no
 * billing signal at all, which is a real answer and not a zero.
 */
function unitOf(row: AgentSpend): BillingUnit {
  if (row.credits > 0) return 'credit'
  if (row.costUsd > 0) return 'dollar'
  if (row.billedTokens > 0) return 'token'
  return 'none'
}

/**
 * Spend per agent for one session, in the order the agents first finished.
 *
 * `agent_end.name` is the agent's own name (agents.py writes it), so no phase
 * lookup is needed. A phase that retried already had every attempt merged into
 * its event by the time it was written, so summing events never double counts.
 */
export function agentSpend(events: EventRow[]): AgentSpend[] {
  const byAgent = new Map<string, AgentSpend>()
  for (const e of events) {
    if (e.type !== 'agent_end' || !e.name) continue
    const payload = parsePayload(e.payload_json) as AgentEndPayload | null
    const usage = payload?.usage
    const row = byAgent.get(e.name) ?? blank(e.name)
    row.calls += 1
    // `credits` sits at the top of the payload and again inside `usage`; either
    // one is the same number, and a pre-credits run has neither.
    row.credits += payload?.credits ?? usage?.credits ?? 0
    row.costUsd += payload?.cost ?? usage?.total_cost ?? 0
    // events.tokens carries the same total for runs written before the
    // breakdown existed, which is all a legacy row can offer.
    row.billedTokens += usage?.total_tokens ?? e.tokens ?? 0
    row.inputTokens += usage?.input_tokens ?? 0
    row.outputTokens += usage?.output_tokens ?? 0
    row.cacheReadTokens += usage?.cache_read_tokens ?? 0
    row.reasoningTokens += usage?.reasoning_tokens ?? 0
    byAgent.set(e.name, row)
  }
  const rows = [...byAgent.values()]
  for (const row of rows) row.unit = unitOf(row)
  return rows
}

/** This agent's spend, or null when it has not finished a phase yet. */
export function spendFor(rows: AgentSpend[], agent: string | null): AgentSpend | null {
  if (!agent) return null
  return rows.find((r) => r.agent === agent) ?? null
}

/** Session total in one unit. Only ever called per unit, never across units. */
export function totalOf(rows: AgentSpend[], field: 'credits' | 'costUsd' | 'billedTokens'): number {
  return rows.reduce((sum, r) => sum + r[field], 0)
}

/** This agent's share of the session, 0–100. Zero total means no share to give. */
export function shareOf(value: number, total: number): number {
  if (!total || value <= 0) return 0
  return Math.min(100, (value / total) * 100)
}

/** The headline figure for an agent, in its own unit. `—` when nothing billed. */
export function spendLabel(row: AgentSpend): string {
  if (row.unit === 'credit') return fmtCredits(row.credits)
  if (row.unit === 'dollar') return fmtCost(row.costUsd)
  if (row.unit === 'token') return `${fmtTokens(row.billedTokens)} tok`
  return '—'
}

/** Why that figure is in that unit — the chip's tooltip. */
export function spendTitle(row: AgentSpend): string {
  const phases = `${row.calls} agent phase${row.calls === 1 ? '' : 's'}`
  if (row.unit === 'credit') {
    return (
      `${fmtCredits(row.credits)} billed over ${phases}. This harness bills in credits ` +
      `and reports no per-session token count, so credits are its only cost signal.`
    )
  }
  if (row.unit === 'dollar') {
    return `${fmtCost(row.costUsd)} billed over ${phases}, ${fmtTokens(row.billedTokens)} tokens exchanged.`
  }
  if (row.unit === 'token') {
    return (
      `${fmtTokens(row.billedTokens)} tokens over ${phases} — ${fmtTokens(row.inputTokens)} in, ` +
      `${fmtTokens(row.outputTokens)} out. This harness reports no dollars and no credits.`
    )
  }
  return `${phases}, no billing reported by this harness.`
}
