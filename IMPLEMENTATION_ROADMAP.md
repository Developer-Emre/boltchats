# Implementation Roadmap — Next Steps

**Current Status**: Backend 83% complete | All critical features done ✅  
**Recommended Effort**: 2-3 weeks to reach 100%

---

## Phase 10: Error Recovery (CRITICAL - 1 week)

### 1.1 WebSocket Connection Recovery
**File**: `services/boltchats-ws/app/handlers/reconnect_handler.py`

```python
async def handle_reconnect(
    event: ReconnectEvent,
    user_id: str,
    connection_manager: ConnectionManager,
) -> None:
    """
    Handle user reconnection after network drop.
    
    Tasks:
    1. Verify user is authenticated
    2. Get last known message ID from Redis
    3. Replay undelivered messages
    4. Resubscribe to previous rooms
    5. Confirm reconnection
    """
```

**Requirements**:
- [ ] Sequence number tracking (each message gets seq#)
- [ ] Undelivered queue (Redis list: user:{id}:undelivered)
- [ ] Replay mechanism (resend messages seq# > last_acked)
- [ ] Graceful downgrade if queue too large

**Tests**:
- [ ] User disconnects for 1 second, reconnects
- [ ] User receives 100+ messages during disconnect
- [ ] User disconnects forever (timeout after 5 min)
- [ ] Partial disconnect (network latency, not full drop)

---

### 1.2 Storage Worker Recovery
**File**: `services/boltchats-storage/app/worker/recovery.py`

```python
class RecoveryManager:
    """Handle storage worker failure scenarios"""
    
    async def recover_from_crash(self):
        """
        When storage worker restarts:
        1. Check for messages in queue
        2. Check for messages in DLQ
        3. Verify last processed message ID
        4. Resume from last checkpoint
        """
    
    async def handle_db_unavailable(self):
        """If MongoDB is down, queue messages until recovered"""
    
    async def handle_redis_unavailable(self):
        """If Redis is down, retry with backoff"""
```

**Requirements**:
- [ ] Checkpoint tracking (last processed message ID)
- [ ] Crash recovery (resume from checkpoint)
- [ ] Retry budget (max 3 retries before DLQ)
- [ ] Exponential backoff (100ms, 500ms, 2s)

---

### 1.3 Message Resync
**File**: `services/boltchats-api/app/schemas/resync.py`

```python
class ResyncRequest(BaseModel):
    """Request to resync messages after gap"""
    conversation_id: str
    last_received_at: datetime  # User's last timestamp

class ResyncResponse(BaseModel):
    """Messages user might have missed"""
    messages: list[MessageInDB]
    has_more: bool
```

**Endpoints**:
- [ ] `GET /conversations/{id}/resync?since=2024-08-01T12:00:00Z`
- [ ] Returns messages since timestamp
- [ ] Limits to last 100 messages (prevent huge downloads)

---

## Phase 11: Alerting & Notifications (HIGH - 3-4 days)

### 2.1 Alertmanager Deployment
**File**: `infrastructure/alerting/alertmanager.yml`

```yaml
global:
  slack_api_url: "https://hooks.slack.com/services/..."

route:
  receiver: 'default'
  group_wait: 10s
  group_interval: 1m
  repeat_interval: 4h
  
  routes:
    - match:
        severity: critical
      receiver: critical
      group_wait: 0s
      repeat_interval: 5m
    
    - match:
        severity: warning
      receiver: ops-team
```

**Requirements**:
- [ ] Slack webhook configuration
- [ ] Alert routing (critical → on-call, warning → Slack channel)
- [ ] Alert grouping (don't spam same alert)
- [ ] Inhibition rules (don't warn if service down)

**Notifications Setup**:
- [ ] Create Slack bot for boltchats
- [ ] Add bot to ops channel
- [ ] Test with manual alert

---

### 2.2 Runbook Creation
**Directory**: `infrastructure/runbooks/`

```
├── API_DOWN.md           ← What to do if API service down
├── HIGH_ERROR_RATE.md    ← Debugging 5xx errors
├── DATABASE_SLOW.md      ← MongoDB query investigation
├── WEBSOCKET_LAG.md      ← Message delivery delay
├── STORAGE_QUEUE_FULL.md ← Queue not draining
└── DISK_FULL.md          ← Out of space on node
```

**Each Runbook Should Include**:
1. Alert definition (what fires it)
2. Impact (what's broken)
3. Quick triage (3 things to check)
4. Resolution steps
5. Escalation procedure
6. Post-mortem checklist

---

## Phase 12: OpenTelemetry Tracing (HIGH - 2-3 days)

### 3.1 Instrument Services
**File**: `services/boltchats-api/app/core/tracing.py`

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def init_tracing(service_name: str):
    """Initialize Jaeger tracing"""
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

tracer = trace.get_tracer(__name__)
```

**Spans to Create**:
- [ ] HTTP request span (FastAPI middleware)
- [ ] Database query span (Motor)
- [ ] Redis operation span (aioredis)
- [ ] Message processing span (WS handler)
- [ ] Queue operation span (LPUSH/BRPOP)

**Example**:
```python
with tracer.start_as_current_span("send_message") as span:
    span.set_attribute("conversation_id", conv_id)
    span.set_attribute("content_length", len(content))
    await message_service.send_message(...)
```

---

### 3.2 Distributed Context
**Propagate trace ID across services**:
- [ ] Extract trace ID from HTTP headers
- [ ] Pass to async tasks
- [ ] Include in Redis queue messages
- [ ] Log trace ID in all logs

---

## Phase 13: Load Testing (HIGH - 2-3 days)

### 4.1 WebSocket Load Test
**File**: `tests/load/websocket_load.js` (k6)

```javascript
import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up
    { duration: '5m', target: 1000 },  // Stay at 1k
    { duration: '2m', target: 0 },     // Ramp down
  ],
};

export default function () {
  let res = ws.connect('ws://localhost:8001', function (socket) {
    socket.on('open', () => {
      for (let i = 0; i < 100; i++) {
        socket.send(JSON.stringify({
          type: 'message',
          content: `Load test message ${i}`,
        }));
      }
    });
    socket.on('close', () => {});
  });
  check(res, { 'status is 101': (r) => r && r.status === 101 });
}
```

**Scenarios**:
- [ ] 1000 concurrent users
- [ ] Each sends 100 messages
- [ ] Measure latency p50/p95/p99
- [ ] Measure message loss
- [ ] Measure CPU/memory usage

---

### 4.2 API Load Test
**File**: `tests/load/api_load.js` (k6)

```javascript
import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 100,
  duration: '5m',
};

export default function () {
  let res = http.post('http://localhost:8000/api/v1/messages', {
    conversation_id: `conv_${__VU}`,
    content: `Message from VU ${__VU}`,
  });
  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

**Report Deliverable**:
- Throughput (req/sec)
- Latency percentiles (p50/p95/p99)
- Error rate
- Bottleneck identification
- Capacity recommendations

---

## Phase 14: Security Audit (MEDIUM - 3-4 days)

### 5.1 Security Checklist
**File**: `SECURITY_AUDIT.md`

```markdown
## Authentication
- [ ] JWT validation on all endpoints
- [ ] Token expiry enforced (60 min)
- [ ] Refresh token rotation
- [ ] No tokens in logs

## Authorization
- [ ] Multi-tenant isolation verified
- [ ] org_id checked on all queries
- [ ] Permission cache invalidation
- [ ] RBAC enforced on sensitive operations

## Input Validation
- [ ] All user input sanitized
- [ ] Max length enforced (10KB messages)
- [ ] No SQL injection possible (MongoDB)
- [ ] No XSS in message content

## Secrets Management
- [ ] No hardcoded secrets in code
- [ ] Secrets in GitHub Secrets only
- [ ] .env files in .gitignore
- [ ] Secret rotation documented

## API Security
- [ ] Rate limiting on all endpoints
- [ ] CORS properly configured
- [ ] HTTPS enforced in production
- [ ] API keys for integrations

## Database
- [ ] MongoDB auth enabled
- [ ] Network ACL configured
- [ ] Backups encrypted
- [ ] Audit logging enabled
```

---

## Phase 15: Documentation (MEDIUM - 2-3 days)

### 6.1 API Documentation
**File**: `docs/api-reference.md`

Auto-generate from OpenAPI spec:
```bash
npm install redoc-cli
redoc-cli build openapi.yaml -o api-docs.html
```

### 6.2 Architecture Decision Records (ADRs)
**File**: `docs/adr/001-message-queue-architecture.md`

```markdown
# ADR-001: Redis Queue for Message Persistence

## Decision
Use Redis LPUSH/BRPOP queue for write-behind message persistence.

## Rationale
1. WebSocket doesn't wait for DB (fast response)
2. Storage worker persists asynchronously
3. No message loss (queue is persistent)
4. Scales better than synchronous writes

## Trade-offs
- Complexity: Need recovery mechanism if worker crashes
- Consistency: Eventual consistency, not immediate
- Infrastructure: Need Redis cluster in HA

## Alternatives Considered
- Synchronous writes to MongoDB: Too slow for WS
- Message broker (RabbitMQ/Kafka): More overhead
- In-memory queue: Would lose messages on crash

## Implementation
- messages:queue (Redis list)
- StorageWorker consumes with BRPOP
- DLQ for failures (messages:queue:dlq)
```

---

## Quick Wins (Can Do Today)

1. **Add message versioning** (10 min)
   - Track message version/revision
   - Support edit history

2. **Add user avatars** (20 min)
   - Store avatar URL in user model
   - Serve from CDN

3. **Add online indicators** (30 min)
   - Show "typing..." status
   - Show "user is online" in real-time

4. **Add message read receipts** (1 hour)
   - Track who read what
   - Show read status to sender

---

## Timeline Estimate

| Phase | Tasks | Est. Time | Impact |
|-------|-------|-----------|--------|
| **10** | Error Recovery | 1 week | Critical |
| **11** | Alerting | 3-4 days | High |
| **12** | Tracing | 2-3 days | High |
| **13** | Load Testing | 2-3 days | High |
| **14** | Security Audit | 3-4 days | Medium |
| **15** | Documentation | 2-3 days | Medium |
| **16** | Quick Wins | 2-3 hours | Low |

**Total**: 3-4 weeks to 100%

---

## Dependencies

```
Phase 10 (Error Recovery)
    ↓
Phase 11 (Alerting) - Run in parallel with 12-13
    ↓
Phase 12 (Tracing) - Run in parallel with 11, 13
    ↓
Phase 13 (Load Testing) - Run in parallel with 11, 12
    ↓
Phase 14 (Security Audit) - After load testing validates stability
    ↓
Phase 15 (Documentation) - Can happen anytime
    ↓
Phase 16 (Quick Wins) - Polish & features
```

---

## Success Criteria for Each Phase

### Phase 10
- [ ] Message resync works after 5-min disconnect
- [ ] Storage worker recovers after crash
- [ ] No message loss in any scenario
- [ ] E2E tests pass

### Phase 11
- [ ] Alert fires when error rate > 1%
- [ ] Slack notification received
- [ ] Runbook created for each alert
- [ ] On-call rotation set up

### Phase 12
- [ ] Trace visible in Jaeger UI
- [ ] End-to-end trace for message flow
- [ ] Trace ID in all logs
- [ ] Performance impact < 5%

### Phase 13
- [ ] 1000+ concurrent WS connections
- [ ] 500+ API req/sec
- [ ] P95 latency < 500ms
- [ ] Error rate < 0.1%

### Phase 14
- [ ] No security vulnerabilities found
- [ ] All OWASP top 10 covered
- [ ] Penetration test passed
- [ ] Security sign-off

### Phase 15
- [ ] OpenAPI spec generated
- [ ] API docs published
- [ ] 5+ ADRs written
- [ ] Deployment guide complete

---

## Getting Started (Next Monday)

1. **Pick ONE phase** (recommend Phase 10)
2. **Create feature branch**: `git checkout -b phase-10-error-recovery`
3. **Implement tasks** in order
4. **Write tests** for each feature
5. **Create PR** with comprehensive tests
6. **Merge** after review + all tests pass
7. **Deploy** to staging first

Good luck! 🚀
