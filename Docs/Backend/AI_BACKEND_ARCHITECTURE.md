# AI Backend Architecture

- 문서 상태: Team Review
- 대상: Backend 담당, AI 담당, UE 연동 담당, Web 담당
- 1차 범위: 동일 LAN 기반 스탠드얼론 솔로 플레이
- Backend 기준: Python/FastAPI 모듈러 모놀리스

## 1. 목적

AI_RE의 Backend 기반과 AI 파트의 구현 경계를 정의합니다.

Backend 담당자는 LLM 모델과 C PC GPU 사양이 확정되지 않아도 API, DB, Mock AIService, 기기 페어링과 Web 연동 기반을 개발할 수 있어야 합니다. AI 담당자는 이후 동일한 `AIService` 계약을 구현해 Local LLM Runtime과 모델을 연결합니다.

## 2. 시스템 구성

| 구분 | 실행 위치 | 책임 |
|---|---|---|
| A PC | UE5 Game Client | 동료 StateTree/GAS, 현재 게임 상태, Command 최종 검증과 실행 |
| B 휴대폰 | Web Browser | 오프라인 대화 입력, 기억 조회·삭제 요청 |
| C PC | Backend Host | FastAPI, Local LLM Runtime, DB, WebApp 호스팅 |

```text
┌─────────────────────┐
│ A PC: UE5 Game      │
│ Local Companion AI  │
└──────────┬──────────┘
           │ HTTP REST
           ▼
┌──────────────────────────────────────────┐
│ C PC                                     │
│ Reverse Proxy                            │
│ ├─ WebApp                                │
│ ├─ FastAPI Backend                       │
│ │  ├─ Domain/Application Services        │
│ │  ├─ Persistence                        │
│ │  └─ AIService Interface                │
│ ├─ Local LLM Runtime                     │
│ └─ SQLite (MVP)                          │
└──────────┬───────────────────────────────┘
           │ HTTPS
           ▼
┌─────────────────────┐
│ B Phone: WebApp     │
│ Offline Conversation│
└─────────────────────┘
```

### 권위 경계

- A PC는 이동, 전투, 대상 유효성, Ability와 현재 월드 상태의 권위자입니다.
- C PC는 대화, 관계 기억, 기기 페어링과 오프라인 데이터의 권위자입니다.
- B 휴대폰은 사용자 입력 UI이며 UE5 게임 상태를 직접 변경하지 않습니다.
- LLM은 Command 실행자가 아니라 표시 대사, Command 후보와 Memory 후보 생성자입니다.

## 3. 확정 범위와 AI 파트 결정 범위

### Backend에서 먼저 확정할 범위

- FastAPI 애플리케이션 구조
- API Request/Response와 오류 Envelope
- SQLite와 Migration. pgvector가 확정되면 PostgreSQL로 승격
- Profile/Device/Save/Companion 데이터 범위
- Conversation, Message, Event와 Memory 영속화
- A/B 기기 인증과 페어링
- Mock AIService
- timeout, 중복 요청과 장애 처리
- 로그 마스킹과 기억 삭제 정책

### AI 파트에서 결정할 범위

- Local LLM Runtime
- 최초 LLM 모델과 양자화 방식
- Prompt Template과 System Prompt
- 구조화 출력 생성 방식
- Memory Candidate 추출 기준
- 기억 검색 관련성 판단
- 모델별 timeout 권장값
- Context/Token 예산
- 모델·Prompt 품질 평가 기준

AI 파트의 결정은 Backend API를 변경하지 않고 `AIService` 구현과 설정으로 교체할 수 있어야 합니다.

## 4. 저장소 목표 구조

```text
AI_RE/
├── UEProject/
├── Backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   ├── dependencies/
│   │   │   └── errors/
│   │   ├── application/
│   │   │   ├── models/
│   │   │   │   └── ai.py
│   │   │   ├── ports/
│   │   │   │   └── ai_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── event_service.py
│   │   │   ├── memory_service.py
│   │   │   └── pairing_service.py
│   │   ├── domain/
│   │   │   ├── chat.py
│   │   │   ├── command.py
│   │   │   ├── event.py
│   │   │   ├── memory.py
│   │   │   └── identity.py
│   │   ├── infrastructure/
│   │   │   ├── ai/
│   │   │   │   ├── mock.py
│   │   │   │   └── local_runtime.py
│   │   │   ├── database/
│   │   │   └── security/
│   │   ├── settings.py
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── WebApp/
├── Contracts/
│   ├── openapi.yaml
│   ├── schemas/
│   └── fixtures/
└── Docs/
```

의존성 방향은 `api → application → domain`으로 유지합니다. `infrastructure`는 application/domain이 정의한 포트를 구현하며 domain이 FastAPI, DB ORM 또는 특정 LLM SDK를 직접 참조하지 않습니다.

## 5. Backend 모듈 책임

### API Layer

- HTTP Request 인증과 Schema 검증
- Application Service 호출
- 표준 Response/Error 변환
- 공급자별 LLM 응답을 Client에 직접 노출하지 않음

### Application Layer

- Chat, Event, Memory와 Pairing 유스케이스 조정
- Transaction 경계
- AIService 호출 전 Context 구성
- AI 결과를 저장 정책과 Command 정책으로 재검증

### Domain Layer

- 안정적인 ID와 상태 모델
- Command allowlist와 상태
- Memory 출처와 생명주기 규칙
- InGame/Offline 시간 의미
- 외부 프레임워크와 무관한 도메인 오류

### Infrastructure Layer

- SQLAlchemy Repository와 SQLite MVP Adapter
- 기기 Token Hash와 검증
- Mock/Local AIService
- Local LLM Runtime HTTP Client
- 구조화 로그와 외부 서비스 Adapter

## 6. AIService 계약

Backend와 AI 파트의 핵심 경계입니다.

```python
from typing import Protocol


class AIService(Protocol):
    async def generate_chat(
        self,
        request: AIServiceRequest,
    ) -> AIServiceResult:
        ...
```

M01의 최소 경계는 `generate_chat` 하나로 고정합니다. 실제 모델 내부에서 대사와 Memory Candidate를 한 번에 생성할지 별도 단계로 추출할지는 AI 파트 구현 세부사항이며, 외부 API와 Application Port를 변경하지 않습니다.

### AIServiceRequest

- `interaction_mode`: `InGame` 또는 `Offline`
- 정제된 사용자 발화
- 현재 모드에 맞는 Time Context
- 제한된 Game/Offline Context
- Backend가 검색한 관련 기억
- 허용된 Command 목록
- 동료의 관계 의미 상태

다음 값은 AI 입력에서 제외합니다.

- 기기 인증 Token
- DB 접속 정보
- `device_id`
- `profile_id`
- 내부 Primary Key
- 불필요한 현실 대화 원문 전체

### AIServiceResult

```json
{
  "schema_version": 1,
  "request_id": "request-ingame-001",
  "display_text": "좋아, 내가 시선을 끌게.",
  "command_candidates": [],
  "memory_candidates": [],
  "metadata": {
    "provider": "AI_PART_DEFINED",
    "model_version": "AI_PART_DEFINED",
    "prompt_version": "AI_PART_DEFINED"
  }
}
```

### Backend의 AI 결과 검증

AI 결과를 그대로 Client에 전달하거나 DB에 저장하지 않습니다.

- `display_text` 길이와 빈 값 검사
- Command allowlist와 필드 검사
- Memory Candidate의 Source 존재 여부 검사
- 지원하지 않는 출력 필드 제거 또는 거부
- Schema 불일치 시 명시적인 AI Output 오류 반환
- 모델 실패 시 Command를 생성하지 않음

## 7. Mock 우선 개발

Backend 기본 개발은 실제 모델 없이 `AI_MODE=mock`으로 진행합니다.

```text
AI_MODE=mock
→ 고정 display_text
→ 선택적 고정 Command Candidate
→ 선택적 고정 Memory Candidate
```

Mock은 최소 다음 시나리오를 제공합니다.

- 정상 InGame Chat
- 정상 Offline Chat
- Command가 없는 일반 대화
- 허용된 Command 후보
- Memory Candidate 후보
- timeout
- Runtime unavailable
- invalid structured output

실제 모델 연결 시 `AI_MODE=local`로 Adapter만 교체합니다.

## 8. 핵심 API

### System

```text
GET /health
GET /api/v1/system/capabilities
```

### Device Pairing

```text
POST   /api/v1/devices/register-game
POST   /api/v1/devices/pairing-codes
POST   /api/v1/devices/pair
GET    /api/v1/devices/me
DELETE /api/v1/devices/me
GET    /api/v1/devices
DELETE /api/v1/devices/{device_id}
```

### Chat and Events

```text
POST /api/v1/chat
POST /api/v1/events
```

InGame과 Offline 대화는 별도 Endpoint가 아니라 `interaction_mode`로 구분합니다.

### Memories

```text
GET    /api/v1/memories
POST   /api/v1/memories/search
DELETE /api/v1/memories/{memory_id}
POST   /api/v1/memories/reset
GET    /api/v1/companion/state
```

API의 실행 가능한 상세 계약은 `Contracts/openapi.yaml`에서 관리할 예정입니다.

## 9. Profile과 Device Pairing

회원 계정 대신 C PC가 단일 플레이어 `profile_id`를 발급합니다.

### Bootstrap 및 영속 Device 인증

- `user_id`는 두지 않습니다.
- `.env`의 GameClient 개발 Token은 최초 `register-game` Bootstrap에만 사용합니다.
- Backend가 영속 Device Token에서 `profile_id`, `device_id`, Device 역할을 결정합니다.
- Client Body의 동일 ID는 선택적 주장값이며 인증 결과와 다르면 거부합니다.
- Device Token과 8자리 Pairing Code는 환경 Pepper 기반 HMAC-SHA256 Hash만 SQLite에 저장합니다.
- Pairing Code는 기본 5분 만료와 1회 사용 제한을 적용합니다.
- Bootstrap Token, Device Token, Pairing Code 원문은 Commit, DB, Fixture, URL과 로그에 포함하지 않습니다.

```text
A Game 최초 연결
→ C가 profile_id + GameClient device_id + Token 발급
→ A가 1회 Pairing Code 요청
→ B WebApp이 Pairing Code 제출
→ C가 WebClient device_id + Token 발급
```

- Pairing Code는 짧은 만료 시간과 1회 사용 제한을 가집니다.
- 장기 Token 원문은 최초 응답과 동일 요청의 멱등 재응답에서만 반환합니다.
- Device 역할은 `GameClient`와 `WebClient`로 분리합니다.
- WebClient는 게임 Command를 직접 실행할 권한을 갖지 않습니다.
- 인증 결과로 확인한 `profile_id/device_id`가 Client Body보다 우선합니다.

### WebClient Pairing UX 결정

- 사용자가 8자리 Pairing Code를 매번 직접 입력하는 흐름은 개발·Swagger 검증용으로만 사용합니다.
- 실제 B 휴대폰은 A 게임 또는 C 관리 화면에 표시된 QR을 스캔해 WebApp Pairing 화면을 엽니다.
- QR에는 장기 Device Token을 넣지 않고 5분 만료·1회 사용 Pairing 정보만 포함합니다.
- Pairing 정보는 URL query보다 브라우저가 서버로 전송하지 않는 URL fragment로 전달합니다.
- WebApp은 Pairing 성공 응답의 WebClient Device Token을 브라우저 자격 증명 저장소에 보관합니다.
- 이후 접속과 Backend 재시작 시 저장된 Token으로 자동 연결하며 Code를 다시 요구하지 않습니다.
- Device 폐기, Token 거부 또는 브라우저 데이터 삭제 시에만 새 QR Pairing을 요구합니다.
- WebClient는 `/devices/me`로 자기 인증 상태만 확인하고 자기 Device만 폐기합니다.
- 다른 Device 목록과 경로 기반 폐기는 계속 GameClient 권한으로 제한합니다.
- 같은 LAN이라는 이유만으로 승인 없이 기기를 자동 등록하지 않습니다.

## 10. 데이터 모델

### 1차 테이블

```text
profiles
devices
save_slots
companions
conversations
messages
game_events
memories
relationship_states
```

### 주요 범위 키

모든 Conversation, Event, Memory와 관계 상태는 최소 다음 범위를 가집니다.

```text
profile_id
save_slot_id
companion_id
```

### Memory 원칙

- 현실 사건은 사용자가 대화에서 직접 공유한 내용만 저장 후보가 됩니다.
- Memory는 원본 Message/Event의 `source_ids`를 가집니다.
- LLM이 추론한 감정과 사용자가 말한 사실을 분리합니다.
- 삭제된 Memory는 검색, Prompt와 캐시에서 제외합니다.
- 관계 상태는 사용자 UI에 숫자로 노출하지 않습니다.

## 11. 시간 Context

### InGame

```json
{
  "interaction_mode": "InGame",
  "time_context": {
    "source": "GameWorld",
    "day": 18,
    "hour": 14.5,
    "period": "Afternoon"
  }
}
```

### Offline

```json
{
  "interaction_mode": "Offline",
  "time_context": {
    "source": "RealWorld",
    "observed_at": "2026-07-15T23:30:00+09:00",
    "timezone": "Asia/Seoul"
  }
}
```

서버의 수신 시각은 감사와 정렬에 사용하며 사용자의 현지 시간으로 가장하지 않습니다. Offline 기억을 InGame에서 회상할 때 원래 `source`와 `occurred_at`을 유지합니다.

## 12. 요청 흐름

### A PC InGame Chat

```text
A UE Context(GameWorld Time)
→ C FastAPI
→ Backend Memory Search
→ AIService
→ display_text + Command Candidate
→ Backend Schema Validation
→ A UE Command Gateway
→ UE 최종 검증 및 StateTree/GAS 실행
→ Command Result Event를 C에 보고
```

### B Phone Offline Chat

```text
B WebApp Context(RealWorld Time)
→ C FastAPI
→ Backend Memory Search
→ AIService
→ display_text + Memory Candidate
→ Backend Source/Policy Validation
→ Message와 Memory 저장
```

## 13. 설정 계약

Backend 기본 설정은 모델 사양과 분리합니다.

```text
APP_ENV
BACKEND_HOST
BACKEND_PORT
DATABASE_URL
AI_MODE=mock|local
AI_RUNTIME_BASE_URL
AI_MODEL_NAME
AI_REQUEST_TIMEOUT_SECONDS
LOG_LEVEL
```

- `AI_MODE=mock`에서는 Runtime/Model 설정이 없어도 Backend가 실행되어야 합니다.
- `AI_MODE=local`에서 필요한 설정은 AI 파트가 제공합니다.
- 모델명과 Runtime URL은 코드에 하드코딩하지 않습니다.
- `.env`는 Git에 포함하지 않고 `.env.example`에는 비밀이 아닌 변수명과 설명만 기록합니다.

## 14. 장애 처리

| 장애 | Backend 동작 | Client 기대 동작 |
|---|---|---|
| LLM Runtime 미실행 | 표준 `AIServiceUnavailable` 오류 | A 로컬 AI 유지, B 재시도 표시 |
| LLM timeout | 요청 취소 및 `AIServiceTimeout` | Command 실행 안 함 |
| Structured Output 오류 | `AIServiceInvalidOutput` | 잘못된 Command 폐기 |
| DB 쓰기 실패 | 성공으로 가장하지 않음 | 저장 실패 표시 |
| 중복 Event | `event_id` 기준 멱등 처리 | 정상 Ack 허용 |
| Backend 미접속 | 응답 없음 | A 로컬 AI 유지 |

## 15. 테스트와 Handoff 기준

### Backend 담당 제공물

- Mock 모드로 실행 가능한 FastAPI
- OpenAPI/Schema와 정상·오류 Fixture
- SQLite Migration과 PostgreSQL 승격 기준
- AIService Interface와 Mock 구현
- Backend 실행 가이드와 `.env.example`
- AI Runtime unavailable/timeout/invalid output 테스트

### AI 담당 제공물

- 실제 Local AIService 구현
- Runtime 실행 방법과 필요한 설정 변수
- Prompt/Model 버전 Metadata
- 구조화 출력 계약 테스트
- Memory Candidate와 회상 평가 Fixture
- 모델별 측정값과 권장 timeout

### Handoff 완료 조건

- AI 담당이 Backend Router와 DB 코드를 수정하지 않고 AIService를 연결할 수 있습니다.
- Mock과 Local 모드가 동일한 API Response Schema를 반환합니다.
- 실제 Runtime이 없어도 A/B 통합 개발을 계속할 수 있습니다.
- AI 출력 오류가 게임 Command나 사실 Memory로 통과하지 않습니다.

## 16. 구현 순서

1. `Contracts` Schema와 Fixture
2. FastAPI 프로젝트와 `/health`
3. 표준 오류, 설정과 로그
4. SQLite와 Migration
5. Mock AIService
6. Mock `/chat`과 `/events`
7. Profile/Device Pairing
8. Conversation/Event 영속화
9. AI 파트에 AIService Handoff
10. Local LLM Adapter 연결
11. Memory Candidate 저장·검색·삭제
12. A/B/C 통합 검증

MVP는 C PC의 단일 사용자·단일 Backend worker를 전제로 SQLite를 사용합니다.
SQLAlchemy 모델과 Alembic migration은 PostgreSQL 호환 타입과 명명 규칙을
유지합니다. AI 파트가 첫 Memory MVP에 pgvector를 필수로 확정하거나 동시
쓰기 부하가 단일 writer 범위를 넘으면 PostgreSQL 승격과 데이터 이관을 별도
Task로 수행합니다.

## 17. 1차 제외 범위

- LLM 모델과 Runtime 확정
- Vector DB
- Redis와 다중 Worker
- WebSocket Push
- 음성 STT/TTS
- 멀티모달 이미지
- 오프라인 자원 정산
- 인터넷 공개와 다중 사용자 서비스

## 18. 팀 검토 필요 항목

- AIService 세부 Request/Result 필드
- AI 파트가 담당할 Memory 검색 범위와 Backend 정책 범위
- Prompt/Model 버전 규칙
- C PC에서 Runtime 실행 방식
- 최초 모델 측정 기준
- 기억 보존 기간
- LAN 이후 외부 접속 필요 여부
