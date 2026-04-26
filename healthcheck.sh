#!/usr/bin/env sh
python -c 'import nexus_agent; print(nexus_agent.__version__)' >/dev/null 2>&1

# Warmup ping to avoid cold-start latency on first approval request
if [ "$ENV" = "staging" ] && [ -n "$AGENT_WEBHOOK_URL" ]; then
  curl -s -X POST "$AGENT_WEBHOOK_URL/warmup" --max-time 2 || true
fi
