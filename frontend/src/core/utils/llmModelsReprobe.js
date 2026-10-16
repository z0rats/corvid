// Window event asking useAppSettings to re-probe the backend's model registry right away (no
// throttle) - for screens where a stale list matters, e.g. Settings -> AI Settings on open. The
// probe and its out-of-order guard stay in one place; callers only ask.
export const LLM_MODELS_REPROBE_EVENT = 'corvid:llm-models-reprobe';

export function requestLlmModelsReprobe() {
  window.dispatchEvent(new Event(LLM_MODELS_REPROBE_EVENT));
}
