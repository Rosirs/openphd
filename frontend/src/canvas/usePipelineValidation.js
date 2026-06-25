import { useMemo } from 'react';
import { validatePipeline } from '../validator/validate';
export function usePipelineValidation(pipeline, contracts, bootstrap) {
    return useMemo(() => validatePipeline(pipeline, contracts, bootstrap), [pipeline, contracts, bootstrap]);
}
