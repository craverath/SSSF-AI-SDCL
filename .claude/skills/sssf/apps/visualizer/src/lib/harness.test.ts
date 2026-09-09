/**
 * The lane's harness label, against the ids sssf.config.yaml can hold.
 *
 * Run with: bun test
 */
import { describe, expect, test } from 'bun:test'
import { harnessLabel, harnessTitle } from './harness'

describe('harnessLabel', () => {
  test('maps every harness the roster can name to its CLI', () => {
    expect(harnessLabel('kiro_cli')).toBe('kiro-cli')
    expect(harnessLabel('antigravity')).toBe('agy')
    expect(harnessLabel('claude_code')).toBe('claude')
    expect(harnessLabel('codex')).toBe('codex')
    expect(harnessLabel('pi')).toBe('pi')
  })

  test('falls back to the dash-cased id for a harness it does not know', () => {
    expect(harnessLabel('some_new_cli')).toBe('some-new-cli')
  })

  test('renders nothing when the db has no harness recorded', () => {
    expect(harnessLabel(null)).toBe('')
    expect(harnessLabel(undefined)).toBe('')
    expect(harnessLabel('  ')).toBe('')
  })
})

describe('harnessTitle', () => {
  test('names the configured id and the CLI when they differ', () => {
    expect(harnessTitle('kiro_cli')).toBe('harness kiro_cli · cli kiro-cli')
  })

  test('does not repeat itself when the id already is the CLI', () => {
    expect(harnessTitle('codex')).toBe('harness codex')
  })
})
