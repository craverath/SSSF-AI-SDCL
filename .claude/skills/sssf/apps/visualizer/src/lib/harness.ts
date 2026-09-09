/**
 * coding_agent → the CLI that actually ran the turn.
 *
 * `sssf.config.yaml` names harnesses in snake_case (`kiro_cli`, `claude_code`),
 * but the thing on your PATH has its own name (`kiro-cli`, `claude`, `agy`).
 * The lane shows the CLI, because that is what you reach for when a harness
 * misbehaves — its version, its login, its process.
 */

const HARNESS_CLI: Record<string, string> = {
  pi: 'pi',
  claude_code: 'claude',
  codex: 'codex',
  kiro_cli: 'kiro-cli',
  antigravity: 'agy',
}

/** Unknown harnesses render their configured id dash-cased, never blank. */
export function harnessLabel(codingAgent: string | null | undefined): string {
  if (!codingAgent) return ''
  const key = codingAgent.trim().toLowerCase()
  if (!key) return ''
  return HARNESS_CLI[key] ?? key.replace(/_/g, '-')
}

/** Hover text: the configured id, plus the CLI when the two differ. */
export function harnessTitle(codingAgent: string | null | undefined): string {
  if (!codingAgent) return ''
  const cli = harnessLabel(codingAgent)
  const id = codingAgent.trim()
  return cli === id ? `harness ${id}` : `harness ${id} · cli ${cli}`
}
