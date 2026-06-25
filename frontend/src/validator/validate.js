const DEFAULT_BOOTSTRAP = new Set(['user_id', 'user_background']);
export function validatePipeline(pipeline, contracts, bootstrap) {
    const provided = new Set(bootstrap ?? DEFAULT_BOOTSTRAP);
    const steps = [];
    for (let idx = 0; idx < pipeline.length; idx++) {
        const agentId = pipeline[idx];
        const c = contracts.get(agentId);
        if (!c)
            throw new Error(`Unknown agent: ${agentId}`);
        const required = new Set(c.required_fields);
        const missing = [...required].filter(f => !provided.has(f));
        steps.push({
            step: idx,
            agent_id: agentId,
            required: [...required],
            provided_at_step: [...provided],
            missing,
            ok: missing.length === 0,
        });
        if (missing.length > 0) {
            return { valid: false, failed_at: idx, steps };
        }
        c.output_fields.forEach(f => provided.add(f));
    }
    return { valid: true, failed_at: null, steps };
}
