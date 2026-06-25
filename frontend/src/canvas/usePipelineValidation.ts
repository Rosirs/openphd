import { useMemo } from 'react';
import type { AgentContract, ValidationResult } from '../api/types';
import { validatePipeline } from '../validator/validate';

export function usePipelineValidation(
  pipeline: string[],
  contracts: Map<string, AgentContract>,
  bootstrap?: Set<string>,
): ValidationResult {
  return useMemo(
    () => validatePipeline(pipeline, contracts, bootstrap),
    [pipeline, contracts, bootstrap],
  );
}
