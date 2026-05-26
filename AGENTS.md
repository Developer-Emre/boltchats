# boltchats — Agent & Handover Context

Bu dosya; projeyi ilk kez gören bir geliştirici, AI agent veya yeni bir oturum için
tüm mimari kararları ve "neden böyle yaptık" sorularının cevabını içerir.

---

## Proje Özeti

boltchats, gerçek zamanlı bir chat platformudur. 4 servisten oluşur:

| Servis | Görev | Port |
|--------|-------|------|
| `boltchats-api` | REST API — auth, kullanıcılar, odalar, mesaj geçmişi | 8000 |
| `boltchats-ws` | WebSocket — gerçek zamanlı mesajlaşma | 8001 |
| `boltchats-storage` | Async mesaj kalıcılık worker'ı | — |
| `boltchats-web` | Next.js 14 frontend | 3000 |

---

## Temel Mimari Kararlar

### Neden `shared/` klasörü yok?
Her servis bağımsız deploy edilebilir olmalı. Ortak kütüphane olsaydı
bir servisi güncellemek diğerlerini etkileyebilirdi.
Servisler arası contract: `docs/api/openapi.yaml` üzerinden.
Her servis kendi `core/security.py` ile JWT doğrular.
→ Bkz: `docs/architecture/decision-records/ADR-003-no-shared-library.md`

---

## Redis Kullanım Kararları

Redis bu projede **iki farklı pattern** ile kullanılır — karıştırılmamalı:

### Pattern 1 — Queue (LPUSH / BRPOP) — Mesaj Kalıcılığı
```
boltchats-ws  →  LPUSH  →  Redis Queue  →  BRPOP  →  boltchats-storage  →  MongoDB
```
- Dosya: `boltchats-ws/app/utils/message_queue.py` (yazar)
- Dosya: `boltchats-storage/app/consumer.py` (okur)
- Mesaj **kaybolmamalı** — kalıcı kayıt için kullanılır

### Pattern 2 — Pub/Sub (PUBLISH / SUBSCRIBE) — Gerçek Zamanlı Broadcast
```
boltchats-ws instance 1  →  PUBLISH  →  Redis channel  →  SUBSCRIBE  →  boltchats-ws instance 2
```
- Dosya: `boltchats-ws/app/managers/broadcast_manager.py`
- Mesaj kaybolabilir — o an bağlı olmayan kullanıcı göremez
- Hız kritik, kalıcılık gerekmez

### Neden İkisi Birden?
Sadece Queue kullansaydık: farklı pod'daki kullanıcıya mesaj iletilemezdi.
Sadece Pub/Sub kullansaydık: storage servisi mesajı göremezdi.

### Write-Behind Pattern
Kullanıcı mesajı gönderir → WS aynı anda hem Pub/Sub hem Queue'ya yazar.
Kullanıcı B mesajı **MongoDB'ye yazılmadan önce** görür.
MongoDB yazma işlemi **kullanıcıyı bekletmez**, arka planda gerçekleşir.

### Redis'in Diğer Kullanımları
- **Rate limit sayacı**: `middlewares/rate_limit.py` — IP başına istek sayısı
- **Refresh token saklama**: `utils/constants.py` → `REDIS_PREFIX_REFRESH_TOKEN`
- **Presence (online kullanıcı listesi)**: `managers/presence_manager.py` → Redis Set

---

## Kubernetes Config Stratejisi

```
infrastructure/kubernetes/
├── base/configmap.yaml          ← Tüm ortamlarda ortak env var'lar
├── overlays/dev/patch.yaml      ← Dev override (replica=1, debug)
├── overlays/staging/patch.yaml  ← Staging override (replica=2)
└── overlays/prod/patch.yaml     ← Prod override (replica=3+, limits)
```

Servisler env var'ları `core/config.py` (Pydantic Settings) ile okur.
Kubernetes bu env var'ları ConfigMap aracılığıyla pod'a inject eder.
Servis kodunda hardcode URL veya config değeri **kesinlikle olmaz**.

---

## Sağlık İzleme

- `GET /health` → Her FastAPI servisinde var, Kubernetes liveness probe olarak kullanılır
- `components/service-monitor.yaml` → Prometheus'a "şu servisleri scrape et" der
- `monitoring/dashboards/api-latency.json` → API gecikme grafikleri
- `monitoring/dashboards/ws-connections.json` → Aktif WebSocket sayısı
- `monitoring/dashboards/boltschats-overview.json` → Genel bakış

---

## Test Stratejisi

Her 3 Python servisi aynı yapıyı kullanır:
```
tests/
├── unit/         ← Dış bağımlılık mock'lanır (MongoDB, Redis yok)
├── integration/  ← Gerçek MongoDB ve Redis ile test
└── conftest.py   ← Ortak fixture'lar
```

Her test dosyası: happy path + error case + edge case içermeli.
Magic number/string yasak — sabitler `utils/constants.py` veya enum'da tanımlanır.

---

## Deployment Akışı

```
PR açıldı → CI (lint + test + build) → merge to main → CD staging (otomatik)
git tag v1.x.x → CD prod (manual approval)
```

Her servis için ayrı CD workflow'u var:
- `.github/workflows/cd-api.yml`
- `.github/workflows/cd-ws.yml`
- `.github/workflows/cd-storage.yml`
- `.github/workflows/cd-web.yml`

---

## Geliştirici Notları

- Tek geliştirici projesi — `CODEOWNERS` tek kişiye atanmış
- `make up` → tüm servisleri local'de başlatır
- `make test` → tüm testleri çalıştırır
- `make lint` → tüm servisleri lint eder
- `.env.example` dosyaları dolu, `.env` dosyaları `.gitignore`'da
- `boltchats-web` `npx create-next-app` ile oluşturuldu — nested `.git` kaldırıldı

---

## Henüz Doldurulmamış (Boş) Kritik Dosyalar

Aşağıdaki dosyalar yapıya eklenmiş ama içi henüz yazılmamış:

```
infrastructure/kubernetes/base/configmap.yaml
infrastructure/kubernetes/base/namespace.yaml
infrastructure/kubernetes/components/api-deployment.yaml
infrastructure/kubernetes/components/service-monitor.yaml
infrastructure/kubernetes/overlays/*/kustomization.yaml
infrastructure/kubernetes/overlays/*/patch.yaml
services/*/Dockerfile
services/*/requirements.txt
```
