# boltschats — Final Project Structure

```
boltschats/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                        # Test + lint + build (her PR)
│   │   ├── cd-api.yml                    # API deploy (main → staging, tag → prod)
│   │   ├── cd-ws.yml                     # WS deploy (main → staging, tag → prod)
│   │   ├── cd-storage.yml                # Storage deploy
│   │   ├── security-scan.yml             # Trivy + Snyk (scheduled + PR)
│   │   ├── load-test.yml                 # Scheduled k6 (her gece)
│   │   └── dependabot.yml                # Otomatik dep güncelleme
│   ├── CODEOWNERS                        # Kim neyi review eder
│   └── pull_request_template.md          # PR açıkken kontrol listesi
│
├── services/
│   │
│   ├── boltschats-api/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py             # Pydantic Settings
│   │   │   │   ├── security.py           # JWT encode/decode + password hash
│   │   │   │   ├── database.py           # MongoDB bağlantısı
│   │   │   │   └── redis.py              # Redis bağlantısı
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── room.py
│   │   │   │   ├── message.py
│   │   │   │   └── feedback.py
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_schema.py
│   │   │   │   ├── user_schema.py
│   │   │   │   ├── room_schema.py
│   │   │   │   ├── message_schema.py
│   │   │   │   └── feedback_schema.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py               # /login /register /refresh
│   │   │   │   ├── users.py
│   │   │   │   ├── rooms.py
│   │   │   │   ├── messages.py           # /messages/history
│   │   │   │   └── feedback.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── user_service.py
│   │   │   │   ├── room_service.py
│   │   │   │   └── message_service.py
│   │   │   ├── middlewares/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_middleware.py
│   │   │   │   ├── rate_limit.py
│   │   │   │   ├── logging.py
│   │   │   │   └── cors.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── validators.py
│   │   │   │   ├── helpers.py
│   │   │   │   └── constants.py
│   │   │   └── exceptions/
│   │   │       ├── __init__.py
│   │   │       ├── http_exceptions.py
│   │   │       └── handlers.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_auth.py
│   │   │   │   ├── test_users.py
│   │   │   │   └── test_rooms.py
│   │   │   ├── integration/
│   │   │   │   ├── test_api_auth.py
│   │   │   │   └── test_api_rooms.py
│   │   │   └── conftest.py
│   │   ├── scripts/                      # Sadece API'ye ait script'ler
│   │   │   ├── create_admin.py
│   │   │   ├── seed_data.py
│   │   │   └── migrate.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   ├── .env.example
│   │   ├── .dockerignore
│   │   └── Makefile
│   │
│   ├── boltschats-ws/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py           # JWT verify — kendi kopyası
│   │   │   │   └── redis.py
│   │   │   ├── managers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection_manager.py
│   │   │   │   ├── room_manager.py
│   │   │   │   └── broadcast_manager.py
│   │   │   ├── handlers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── message_handler.py
│   │   │   │   ├── room_handler.py
│   │   │   │   └── ping_handler.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ws_message.py
│   │   │   │   └── ws_event.py
│   │   │   ├── middlewares/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_websocket.py
│   │   │   │   └── rate_limit_ws.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── message_queue.py
│   │   │   │   └── metrics.py            # Prometheus: aktif conn, msg/s
│   │   │   └── constants/
│   │   │       ├── __init__.py
│   │   │       └── ws_codes.py
│   │   ├── tests/
│   │   │   ├── unit/                     # API ile tutarlı: unit/integration ayrımı
│   │   │   │   ├── test_connection_manager.py
│   │   │   │   ├── test_room_manager.py
│   │   │   │   └── test_broadcast_manager.py
│   │   │   ├── integration/
│   │   │   │   ├── test_ws_connection.py
│   │   │   │   ├── test_ws_broadcast.py
│   │   │   │   └── test_ws_auth.py
│   │   │   └── conftest.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   ├── .env.example
│   │   ├── .dockerignore
│   │   └── Makefile
│   │
│   └── boltschats-storage/               # API ve WS ile eşit iskelet
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── core/
│       │   │   ├── __init__.py
│       │   │   ├── config.py
│       │   │   └── database.py
│       │   ├── consumer.py               # Redis queue consumer
│       │   ├── storage.py                # MongoDB write logic
│       │   └── utils/
│       │       ├── __init__.py
│       │       └── metrics.py
│       ├── tests/
│       │   ├── unit/
│       │   │   └── test_storage.py
│       │   ├── integration/
│       │   │   └── test_consumer.py
│       │   └── conftest.py
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── .env.example
│       ├── .dockerignore
│       └── Makefile
│
├── infrastructure/
│   │
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── namespace.yaml
│   │   │   └── configmap.yaml
│   │   │   # NOT: secrets.yaml burada YOK — secrets/ klasöründe şifreli
│   │   ├── components/                   # Sadece uygulama servisleri
│   │   │   ├── api-deployment.yaml
│   │   │   ├── api-service.yaml
│   │   │   ├── ws-deployment.yaml
│   │   │   ├── ws-service.yaml
│   │   │   ├── storage-deployment.yaml
│   │   │   ├── storage-service.yaml
│   │   │   ├── network-policy.yaml
│   │   │   └── service-monitor.yaml
│   │   ├── databases/                    # DB manifestleri ayrı — farklı lifecycle
│   │   │   ├── mongodb-statefulset.yaml
│   │   │   ├── mongodb-service.yaml
│   │   │   ├── redis-deployment.yaml
│   │   │   └── redis-service.yaml
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   │   ├── kustomization.yaml
│   │   │   │   └── patch.yaml
│   │   │   ├── staging/
│   │   │   │   ├── kustomization.yaml
│   │   │   │   ├── hpa.yaml
│   │   │   │   └── pdb.yaml
│   │   │   └── prod/
│   │   │       ├── kustomization.yaml
│   │   │       ├── hpa.yaml
│   │   │       ├── pdb.yaml
│   │   │       └── ingress.yaml
│   │   └── secrets/
│   │       ├── sealed-secret.yaml        # kubeseal ile şifrelenmiş
│   │       └── external-secret.yaml      # Vault/AWS SSM entegrasyonu
│   │
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── eks/
│   │   │   │   ├── main.tf
│   │   │   │   ├── variables.tf
│   │   │   │   └── outputs.tf
│   │   │   ├── vpc/
│   │   │   │   ├── main.tf
│   │   │   │   └── variables.tf
│   │   │   └── mongodb-atlas/
│   │   │       ├── main.tf
│   │   │       └── variables.tf
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   │   ├── main.tf
│   │   │   │   ├── provider.tf           # Her env kendi provider'ı taşır
│   │   │   │   ├── variables.tf
│   │   │   │   ├── terraform.tfvars
│   │   │   │   └── backend.tf            # Remote state: S3 + DynamoDB lock
│   │   │   ├── staging/
│   │   │   │   ├── main.tf
│   │   │   │   ├── provider.tf
│   │   │   │   ├── variables.tf
│   │   │   │   ├── terraform.tfvars
│   │   │   │   └── backend.tf
│   │   │   └── prod/
│   │   │       ├── main.tf
│   │   │       ├── provider.tf
│   │   │       ├── variables.tf
│   │   │       ├── terraform.tfvars
│   │   │       └── backend.tf
│   │   └── global/
│   │       └── iam.tf                    # Sadece IAM — provider buradan kalktı
│   │
│   ├── monitoring/                       # Helm values + dashboard JSON'ları
│   │   ├── prometheus-values.yaml
│   │   ├── grafana-values.yaml
│   │   ├── loki-values.yaml
│   │   ├── tempo-values.yaml
│   │   └── dashboards/
│   │       ├── boltschats-overview.json
│   │       ├── ws-connections.json       # Aktif WS + room metrikleri
│   │       └── api-latency.json
│   │
│   ├── configs/                          # Tüm config dosyaları burada — root'ta değil
│   │   ├── nginx.conf
│   │   ├── prometheus.yml
│   │   ├── loki-config.yaml
│   │   ├── alertmanager.yaml
│   │   └── opentelemetry-collector.yaml
│   │
│   ├── logging/
│   │   ├── fluentbit-values.yaml
│   │   └── vector-config.yaml
│   │
│   └── service-mesh/
│       ├── istio-values.yaml
│       └── virtual-service.yaml
│
├── load-test/                            # k6 scriptleri — scripts/'taki .sh buraya işaret eder
│   ├── smoke.js                          # Hızlı sağlık kontrolü
│   ├── stress.js                         # Kademeli yük artışı
│   ├── spike.js                          # Ani trafik patlaması
│   ├── ws-load.js                        # WebSocket bağlantı testi
│   └── config/
│       ├── thresholds.js                 # SLO eşikleri
│       └── scenarios.js                  # Senaryo tanımları
│
├── scripts/                              # Sadece infra/ops script'leri
│   ├── deploy.sh                         # K8s deploy wrapper
│   ├── backup-mongodb.sh
│   ├── load-test.sh                      # k6 çağrır → load-test/*.js
│   ├── cert-renew.sh
│   └── seed-test-data.sh
│
├── docs/                                 # TEK docs/ — iki ayrı dizin birleştirildi
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── postman-collection.json
│   ├── websocket/
│   │   └── protocol.md
│   ├── architecture/
│   │   ├── c4-model.md
│   │   └── decision-records/
│   │       ├── ADR-001-ws-redis-pubsub.md
│   │       ├── ADR-002-kustomize-over-helm.md
│   │       └── ADR-003-no-shared-library.md
│   └── operations/
│       ├── runbook.md
│       └── on-call-guide.md
│
├── docker-compose.yml                    # Local dev: api + ws + storage + mongo + redis
├── docker-compose.test.yml               # CI: test ortamı
├── docker-compose.monitoring.yml         # Local: prometheus + grafana + loki
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile                              # make up / test / deploy-staging / lint
├── README.md
└── LICENSE
```

---

## Yapısal kurallar (değişmez)

### Servis bağımsızlığı
Her servis kendi `core/security.py` ile JWT doğrular. `shared/` klasörü yoktur.
Servisler arası contract: OpenAPI spec (`docs/api/openapi.yaml`) üzerinden.

### Script sorumluluğu
| Nerede | Ne tür script |
|--------|---------------|
| `services/*/scripts/` | O servise ait: migrate, seed, admin oluştur |
| `scripts/` (root) | İnfra/ops: deploy, backup, load-test çağrısı |

### Test tutarlılığı
Her 3 servis aynı test yapısını kullanır: `tests/unit/` + `tests/integration/` + `conftest.py`

### Terraform provider kuralı
`provider.tf` her `environments/*/` altında ayrı durur.
`global/` sadece cross-env IAM resource'larını taşır.

### Kubernetes ayrımı
`components/` → uygulama servisleri (deployment + service)
`databases/` → MongoDB, Redis (farklı lifecycle, farklı owner)
`secrets/` → sadece şifreli Sealed Secret veya External Secret referansı

### Docs tekliği
Tek `docs/` dizini, root'ta. Mimari kararlar ADR formatında `docs/architecture/decision-records/` altında.
```
