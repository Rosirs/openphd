import type { AgentContract } from '../api/types';
import fixturesRaw from '../../../docs/superpowers/specs/fixtures/pipelines.json';

interface FixturesShape {
  agents: AgentContract[];
  pipelines: Record<string, string[]>;
}

export const FIXTURES: FixturesShape = fixturesRaw as FixturesShape;
