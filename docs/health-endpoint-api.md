# Health Endpoint API Documentation

## Summary

The health endpoint provides real-time status information about the CrackDSA API and its database connectivity. It is designed for use by monitoring systems, load balancers, and CI/CD pipelines.

**Endpoint**: `GET /health`  
**Authentication**: Not required (public)  
**Response Time**: < 500ms (typical)  

## Responses

### Success (HTTP 200)

Database is connected and operational.

```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2025-03-29T10:15:30Z"
}
```

**Fields**:
- `status` (string): Application status - `"ok"` indicates healthy
- `database` (string): Database connectivity - `"connected"` indicates Supabase is reachable
- `timestamp` (string): UTC ISO 8601 format when check was performed

### Degraded (HTTP 503)

Database connection is unavailable but application is still running.

```json
{
  "status": "degraded",
  "database": "disconnected",
  "timestamp": "2025-03-29T10:15:32Z"
}
```

### Error (HTTP 503)

Unexpected error during health check.

```json
{
  "status": "error",
  "database": "disconnected",
  "error": "Connection timeout to Supabase",
  "timestamp": "2025-03-29T10:15:35Z"
}
```

**Note**: Error messages are included for debugging. In production, consider hiding specific error details.

## Usage Examples

### cURL

```bash
# Basic health check
curl http://localhost:8000/health

# With pretty JSON output
curl -s http://localhost:8000/health | jq .

# Check status code only
curl -o /dev/null -w "%{http_code}" http://localhost:8000/health
```

### Python

```python
import requests

response = requests.get("http://localhost:8000/health")
if response.status_code == 200:
    health = response.json()
    print(f"App Status: {health['status']}")
    print(f"Database: {health['database']}")
else:
    print(f"Health check failed: {response.status_code}")
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/health');
const health = await response.json();

if (response.status === 200) {
  console.log(`Status: ${health.status}, DB: ${health.database}`);
} else {
  console.log('Health check failed');
}
```

### Bash Script (Monitoring)

```bash
#!/bin/bash
# Check health every 30 seconds and log failures

HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/var/log/crackdsa-health.log"

while true; do
  response=$(curl -s -w "\n%{http_code}" "$HEALTH_URL")
  body=$(echo "$response" | head -n -1)
  status_code=$(echo "$response" | tail -n 1)
  
  if [ "$status_code" != "200" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: Health check failed (HTTP $status_code)" >> "$LOG_FILE"
    # Send alert to monitoring system
  fi
  
  sleep 30
done
```

## Monitoring Integrations

### Kubernetes Liveness Probe

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: crackdsa-api
spec:
  containers:
  - name: api
    image: crackdsa-api:1.0
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 30
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 10
```

### AWS Load Balancer (Target Group)

```json
{
  "HealthCheckPath": "/health",
  "HealthCheckProtocol": "HTTP",
  "HealthCheckPort": "8000",
  "HealthCheckIntervalSeconds": 30,
  "HealthCheckTimeoutSeconds": 5,
  "HealthyThresholdCount": 2,
  "UnhealthyThresholdCount": 2
}
```

### Datadog Monitor

```python
from datadog import initialize, api

options = {
  'api_key': 'YOUR_API_KEY',
  'app_key': 'YOUR_APP_KEY'
}

initialize(**options)

api.Monitor.create(
    type="http_check",
    query="http_check.status{url:http://localhost:8000/health}.last(1) != 1",
    name="CrackDSA API Health",
    message="CrackDSA API health check failed @slack-alerts",
    tags=["service:crackdsa", "env:production"]
)
```

### Grafana Dashboard Alert

In Grafana, set up an HTTP check alert:
1. Create new probe: `GET http://your-api.com/health`
2. Assert response status code = 200
3. Check interval: 30 seconds
4. Alert on failure: 2 consecutive failures

## Interpreting Results

### When Status = "ok" & Database = "connected"
✅ Everything is working normally. API is ready to serve requests.

**Action**: None required.

### When Status = "degraded" & Database = "disconnected"
⚠️ API is running but database is unavailable. Requests depending on database will fail.

**Likely Causes**:
- Supabase project paused
- Network connectivity issue
- Supabase maintenance window
- Database credentials expired

**Actions**:
1. Check Supabase dashboard for project status
2. Verify network connectivity to Supabase
3. Review API logs for specific error messages
4. If persistent, restart API process

### When Status = "error"
❌ Unexpected error during health check. Review error message for details.

**Actions**:
1. Check application logs
2. Verify environment variables are set correctly
3. Ensure Supabase project exists and is accessible
4. Restart API service

## Performance Metrics

### Response Time
- Typical: 50-200ms
- Database check adds majority of latency

### Database Load
- Single query per health check
- Minimal impact on database performance
- Safe to call every 5-10 seconds from monitoring

## Rate Limiting

The health endpoint is **not rate-limited** by default. It's intended for frequent monitoring calls.

**Recommendation**: Call every 10-30 seconds for production monitoring.

## HTTP Status Codes

| Code | Meaning | Database | Recommendation |
|------|---------|----------|-----------------|
| 200 | Healthy | Connected | Accept traffic |
| 503 | Service Unavailable | Disconnected | Drain traffic, investigate |
| 500 | Internal Error | Unknown | Restart service |

## Timestamp Format

All timestamps use UTC ISO 8601 format:
```
2025-03-29T10:15:30Z
```

Parsed as: `YYYY-MM-DDTHH:MM:SSZ`

Example parsing in different languages:

**Python**:
```python
from datetime import datetime
ts = datetime.fromisoformat(health['timestamp'].replace('Z', '+00:00'))
```

**JavaScript**:
```javascript
const ts = new Date(health.timestamp);
```

**Go**:
```go
t, _ := time.Parse(time.RFC3339, health.Timestamp)
```

## Debugging

### Enable Verbose Logging

Set log level to DEBUG:
```bash
PYTHONUNBUFFERED=1 uvicorn app.main:app --log-level debug
```

### Manual Database Connection Test

```python
from app.database import check_database_connection

result = check_database_connection()
print(f"Database connected: {result}")
```

### Check Configuration

```python
from app.config import settings

print(f"Supabase URL: {settings.SUPABASE_URL}")
print(f"Supabase Key configured: {bool(settings.SUPABASE_KEY)}")
```

## FAQ

**Q: Why is the database check taking so long?**  
A: Network latency to Supabase or large database. Consider adding caching or monitoring from closer region.

**Q: Can I customize the health check response?**  
A: Yes, edit `app/main.py` `/health` endpoint handler to add additional fields.

**Q: Is the health endpoint cached?**  
A: No, it performs a fresh database check on every call. Add caching if aggressive monitoring is needed.

**Q: Should I expose `/health` publicly?**  
A: Yes, health endpoints are typically public for monitoring. It contains no sensitive data.

**Q: What if Supabase is down but I still want /health to respond?**  
A: Modify `health_check()` to return degraded status with HTTP 200 instead of 503. See `app/main.py` for implementation.

## See Also

- [Supabase Integration Guide](supabase-integration.md)
- [API Root Documentation](roadmap-generation-api.md)
- [Authentication Guide](../MIGRATION_GUIDE.md#phase-2-authentication-integration-optional)
