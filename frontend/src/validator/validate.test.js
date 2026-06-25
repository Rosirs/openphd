import { describe, test, expect } from 'vitest';
import { validatePipeline } from './validate';
import { FIXTURES } from './fixtures';
const contracts = new Map(FIXTURES.agents.map(a => [a.agent_id, a]));
describe('validatePipeline', () => {
    test('happy path mock_echo -> mock_logger with bootstrap', () => {
        const r = validatePipeline(['mock_echo', 'mock_logger'], contracts, new Set(['dynamic_storage.echo_input']));
        expect(r.valid).toBe(true);
        expect(r.failed_at).toBeNull();
        expect(r.steps.every(s => s.ok)).toBe(true);
    });
    test('missing field fails at first step', () => {
        const r = validatePipeline(['mock_logger'], contracts, new Set(['dynamic_storage.echo_input']));
        expect(r.valid).toBe(false);
        expect(r.failed_at).toBe(0);
        expect(r.steps[0].missing).toContain('dynamic_storage.echo_output');
    });
    test('chain broken when order wrong', () => {
        const r = validatePipeline(['mock_logger', 'mock_echo'], contracts, new Set(['dynamic_storage.echo_input']));
        expect(r.valid).toBe(false);
    });
    test('empty pipeline is valid', () => {
        const r = validatePipeline([], contracts);
        expect(r.valid).toBe(true);
    });
    test('unknown agent throws', () => {
        expect(() => validatePipeline(['ghost'], contracts)).toThrow();
    });
});
