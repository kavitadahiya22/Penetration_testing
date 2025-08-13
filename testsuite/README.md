# Cybrty-Pentest Test Suite

Comprehensive automated test harness for the CrewAI multi-agent pentesting service with dynamic planning, dual LLM providers, FastAPI APIs, and OpenSearch logging.

## Overview

This test suite validates:
- **All agents**: Recon (Amass/Nmap), Web (ZAP/sqlmap/Nikto), Exploit (Metasploit RPC), Creds (Hydra/CME), Lateral (BloodHound/CME), Priv-Esc (BloodHound)
- **Dynamic planning**: Planner generates tasks based on inputs & features, respecting policy gates
- **OpenSearch logging**: Every planner decision, agent action, and run summary is written to cybrty-planner, cybrty-actions, cybrty-runs
- **Safety**: Dummy data scenarios with realistic but safe payloads; simulate tools when needed
- **Negative cases**: Edge cases and performance checks
- **Dual deployment**: Works locally (Docker Compose) and against AKS endpoints

## Quick Start

### Local Testing (Docker Compose)

```bash
# Copy environment template
cp .env.example .env

# Start test environment
make up

# Run all tests
make test

# Run specific test categories
make smoke      # Quick smoke tests
make recon      # Recon agent tests only
make web        # Web agent tests only

# Performance testing
make perf

# Cleanup
make down
```

### Remote Testing (AKS/Production)

```bash
# Configure for remote endpoint
cp .env.example .env
# Edit .env with your AKS/production settings:
# API_BASE=https://your-aks-api.example.com/api/v1
# OS_SCHEME=https
# OS_HOST=your-opensearch.example.com
# OS_USERNAME=your-user
# OS_PASSWORD=your-pass

# Run tests against remote
pytest -q
```

## Test Categories

### Agent-Specific Tests
```bash
pytest -m recon          # Recon agent (Amass/Nmap)
pytest -m web            # Web agent (ZAP/sqlmap/Nikto)
pytest -m exploit        # Exploit agent (Metasploit RPC)
pytest -m creds          # Credentials agent (Hydra/CME)
pytest -m lateral        # Lateral movement (BloodHound/CME)
pytest -m privesc        # Privilege escalation (BloodHound)
```

### Functional Tests
```bash
pytest -m planner        # Dynamic planning tests
pytest -m logging        # OpenSearch logging validation
pytest -m policy         # Policy gates and safety rails
pytest -m negative       # Negative and edge cases
```

### Specific Test Files
```bash
pytest e2e/test_planner_end_to_end.py
pytest e2e/test_run_multiagent_happy.py
pytest e2e/test_agent_recon.py::test_recon_nmap_scan
pytest e2e/test_logging_fields.py::test_opensearch_schema_validation
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_BASE` | FastAPI service base URL | `http://localhost:8080/api/v1` |
| `MODEL_PROVIDER` | LLM provider (ollama/openai) | `ollama` |
| `OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11434` |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI) | `sk-xxx...` |
| `OS_SCHEME` | OpenSearch scheme | `http` |
| `OS_HOST` | OpenSearch host | `localhost` |
| `OS_PORT` | OpenSearch port | `9200` |
| `OS_USERNAME` | OpenSearch username | `` |
| `OS_PASSWORD` | OpenSearch password | `` |

### OpenSearch Indices
- `OS_IDX_PLANNER` - Planner decisions (default: cybrty-planner)
- `OS_IDX_ACTIONS` - Agent actions (default: cybrty-actions)  
- `OS_IDX_RUNS` - Run summaries (default: cybrty-runs)

### Policy Configuration
- `POLICY_ALLOW_NETS` - Allowed network ranges (default: 10.0.0.0/8,192.168.0.0/16)

## Test Data

### Fixtures
- `fixtures/sample_inputs.json` - Realistic test scenarios for all agent types
- `fixtures/planner_expectations.json` - Expected plan shapes by feature/depth

### Sample Data
- `data/urls.txt` - Sample web targets for testing
- `data/creds.csv` - Sample credential wordlists
- `data/bloodhound/` - Small SharpHound JSON samples for offline testing

## Architecture

```
testsuite/
├── README.md                    # This file
├── .env.example                 # Environment template
├── Makefile                     # Test automation
├── conftest.py                  # Pytest configuration
├── docker/
│   └── docker-compose.tests.yml # Test environment
├── data/                        # Sample test data
├── fixtures/                    # Test fixtures and expectations
├── src/                         # Test utilities and helpers
├── e2e/                         # End-to-end tests
├── perf/                        # Performance tests
├── postman/                     # Postman collections (optional)
└── ci/                          # CI/CD configurations
```

## Key Features

### Dynamic Planning Validation
- Tests planner with mixed inputs (IPs, domains, URLs)
- Validates plan generation based on depth and features
- Ensures policy compliance and safety gates

### Agent Testing
- **Recon**: Validates Amass domain enum and Nmap port scanning
- **Web**: Tests ZAP baseline, sqlmap injection detection, Nikto scanning
- **Exploit**: Validates Metasploit RPC integration with simulation mode
- **Creds**: Tests Hydra brute force and CME enumeration
- **Lateral**: Validates BloodHound analysis and CME lateral movement
- **Priv-Esc**: Tests privilege escalation path discovery

### OpenSearch Logging
- Validates all actions are logged with correct schema
- Tests planner decision logging with metadata
- Ensures run summaries contain required fields
- Validates timestamps and duration tracking

### Safety & Policy
- Tests network allowlist enforcement
- Validates simulation mode compliance
- Tests destructive action blocking
- Ensures rate limiting and resource controls

## Mock Services

The test environment includes mock services for external tools:
- **ZAP Mock**: Simulates OWASP ZAP baseline scans
- **MSF Mock**: Simulates Metasploit RPC calls
- **Tool Mocks**: Safe simulation of pentesting tools

## Troubleshooting

### Common Issues

1. **OpenSearch not ready**
   ```bash
   # Wait for OpenSearch to be ready
   make wait-os
   ```

2. **API 404 errors**
   - Check `API_BASE` URL in `.env`
   - Ensure API service is running

3. **Planner failures**
   - Switch model provider in `.env`
   - Check model availability with `make check-models`

4. **Permission denied**
   - Check OpenSearch credentials
   - Verify network allowlist settings

### Logs and Debugging

```bash
# View service logs
docker-compose -f docker/docker-compose.tests.yml logs api
docker-compose -f docker/docker-compose.tests.yml logs opensearch

# Reset OpenSearch indices
make reset-os

# Run tests with verbose output
pytest -v -s
```

### OpenSearch Dashboard

Access the OpenSearch Dashboard at http://localhost:5601 to view:
- Test execution logs
- Agent action timelines
- Performance metrics

## CI/CD Integration

The test suite includes GitHub Actions configuration for:
- Matrix testing with different model providers
- Automated testing on push/PR
- Performance regression detection
- Security scanning

```bash
# Local CI simulation
make ci-test
```

## Performance Testing

Light performance testing with Locust:

```bash
# Run performance tests
make perf

# Custom performance test
locust -f perf/locustfile.py --headless -u 50 -r 10 -t 5m --html report.html
```

## Contributing

1. Add new test cases to appropriate category in `e2e/`
2. Update fixtures in `fixtures/` for new scenarios
3. Add utilities to `src/` for reusable test helpers
4. Update this README for new features

## License

This test suite is part of the cybrty-pentest project and follows the same licensing terms.
