# AI Developer Quickstart

- 대상: AI_RE 저장소와 Backend 구조를 처음 접하는 AI 개발자
- 목표: 실제 모델을 선택하기 전에 계약과 교체 경계를 독립 환경에서 검증하고,
  Runtime·모델·Prompt 개발 계획을 작성할 수 있도록 합니다.
- 기준 계약: AIService Request Schema v2, AIService Result Schema v1

## 1. 이 문서로 완료해야 하는 일

AI 개발자는 다음 결과를 남깁니다.

1. 전달받은 Branch와 Commit을 별도 환경에서 재현합니다.
2. 계약, Mock, Fake Runtime과 Backend 전체 테스트를 실행합니다.
3. `AIServiceRequest`와 `AIServiceResult`의 의미와 보안 제한을 확인합니다.
4. Router와 DB를 수정하지 않는 최소 대체 `AIService` 경계를 확인합니다.
5. Runtime·모델·양자화·Prompt 후보의 평가 계획을 작성합니다.
6. 실행 환경, 명령, 결과와 미결정 사항을 Handoff 보고서로 전달합니다.

실제 Runtime과 최종 모델 선택, GPU 벤치마크 완료, Memory 영속화와 GameEvent
저장은 이 검증의 완료 조건이 아닙니다.

## 2. Backend 담당자에게 받아야 할 정보

작업을 시작하기 전에 다음 네 값을 요청합니다.

| 항목 | 예시 | 용도 |
|---|---|---|
| Repository URL | `https://github.com/OWNER/REPOSITORY.git` | 저장소 복제 |
| Handoff Branch | `21-feat-aiservice-handoff-...` | 검증할 변경 선택 |
| Commit SHA | 40자리 Git SHA | 양쪽이 같은 코드를 검증했는지 확인 |
| Issue/PR URL | GitHub Issue 또는 Draft PR | 결과와 결정 기록 |

Branch 이름만 전달받지 말고 Commit SHA도 받습니다. Branch가 갱신되면 같은 이름이
다른 코드를 가리킬 수 있기 때문입니다.

## 3. 사전 준비

필수 도구는 다음과 같습니다.

- Git
- PowerShell 7 또는 Windows PowerShell
- `uv`
- 저장소를 내려받을 디스크 공간

Python은 `Backend/pyproject.toml`의 범위인 3.12 이상 3.14 미만을 사용합니다.
`uv`가 호환 Python과 프로젝트 가상환경을 관리할 수 있습니다. Unreal Engine,
PostgreSQL, 실제 LLM Runtime과 GPU는 계약 테스트 단계에 필요하지 않습니다.

## 4. Clean 환경 준비

기존 개발 폴더를 재사용하지 않는 것을 권장합니다. 아래 값은 전달받은 실제 값으로
바꿉니다.

```powershell
git clone https://github.com/OWNER/REPOSITORY.git AI_RE_AI_HANDOFF
Set-Location AI_RE_AI_HANDOFF
git fetch origin
git switch --track origin/HANDOFF_BRANCH
git rev-parse HEAD
git status --short --branch
```

판정 기준은 다음과 같습니다.

- `git rev-parse HEAD`가 전달받은 Commit SHA와 같습니다.
- `git status --short --branch`에 수정되거나 추적되지 않은 파일이 없습니다.
- 다른 Branch에서 테스트한 결과를 Handoff 결과로 제출하지 않습니다.

의존성을 준비합니다.

```powershell
uv --directory Backend sync --dev
```

이 단계에서 실제 Runtime SDK를 임의로 추가하지 않습니다. Runtime 후보가 결정되지
않은 상태에서 SDK를 먼저 추가하면 Adapter가 특정 공급자에 불필요하게 결합됩니다.

## 5. 저장소 구조를 5분 안에 이해하기

| 위치 | 의미 | AI 개발자 행동 |
|---|---|---|
| `Contracts/schemas/ai-service-request.schema.json` | AI 입력 실행 계약 | 읽고 fixture를 검증 |
| `Contracts/schemas/ai-service-result.schema.json` | AI 출력 실행 계약 | 출력 생성의 최종 기준으로 사용 |
| `Contracts/fixtures/ai-service/` | 정상 예제 | Prompt와 Adapter 평가 입력으로 재사용 |
| `Backend/app/application/models/ai.py` | strict Pydantic 모델 | Schema와 의미가 같은지 확인 |
| `Backend/app/application/ports/ai_service.py` | 교체 불변 Port | `generate_chat()` 서명을 유지 |
| `Backend/app/infrastructure/ai/mock.py` | 모델 없는 기준 구현 | 정상 시나리오 의미 확인 |
| `Backend/app/infrastructure/ai/local_runtime.py` | Local Runtime HTTP 경계 | Runtime별 매핑을 구현할 위치 |
| `Backend/app/api/dependencies/ai.py` | Mock/Local 선택 지점 | 설정에 따른 구현 선택만 유지 |
| `Backend/tests/test_local_runtime_ai_service.py` | Fake Runtime 검증 | Adapter 변경 후 반드시 통과 |

의존 방향은 `API → Application → Domain`입니다. Infrastructure가 Application의
Port를 구현합니다. Runtime 공급자 형식은 Infrastructure 밖으로 나가면 안 됩니다.

## 6. 첫 번째 검증: 계약과 Fixture

```powershell
uv --directory Backend run pytest tests/test_contracts.py
```

성공하면 다음을 확인한 것입니다.

- JSON Schema와 정상 fixture가 일치합니다.
- OpenAPI가 참조하는 외부 Schema 파일이 존재합니다.
- AIService fixture에 인증 Token, `profile_id`, `device_id`, DB 연결정보가 없습니다.
- 지원하지 않는 필수 Schema와 누락 필드가 검증에서 거부됩니다.

실패하면 모델 작업을 시작하지 않습니다. 먼저 실패한 Schema, fixture 또는 Backend
모델의 불일치를 Backend 담당자에게 공유합니다.

## 7. 두 번째 검증: Mock의 세 정상 시나리오

```powershell
uv --directory Backend run pytest tests/test_mock_ai_service.py
```

| 시나리오 | 입력 | 기대 출력 |
|---|---|---|
| `normal` | 일반 Offline 발화 | 대사, 빈 Command, 빈 Memory |
| `command` | InGame 발화와 허용 Command | 허용 목록 안의 Command Candidate |
| `memory` | 사용자가 직접 공유한 내용 | 현재 Message ID를 근거로 한 Memory Candidate |

Mock 출력은 같은 이름의 공용 fixture와 정확히 일치해야 합니다. 실제 모델의 품질이
아니라 계약을 검증하는 기준선입니다.

## 8. 세 번째 검증: Local Adapter와 표준 오류

```powershell
uv --directory Backend run pytest tests/test_local_runtime_ai_service.py
```

이 테스트는 실제 서버 대신 `httpx.MockTransport`를 사용합니다.

| Fake Runtime 동작 | 기대 Backend 오류/결과 |
|---|---|
| 정상 JSON | strict `AIServiceResult` |
| 연결 실패 또는 일반 HTTP 오류 | `AIServiceUnavailable` |
| Transport timeout, HTTP 408 또는 504 | `AIServiceTimeout` |
| JSON이 아닌 응답 | `AIServiceInvalidOutput` |
| 누락 필드, 추가 필드, 지원하지 않는 Schema | `AIServiceInvalidOutput` |

예외에 Runtime 원본 응답, Prompt 원문, Token 또는 접속 비밀정보를 추가하지
않습니다. 오류 코드는 Client API가 이해하는 안정 코드이고 공급자 오류 문자열은
아닙니다.

## 9. 네 번째 검증: Backend 정책과 전체 회귀

```powershell
uv --directory Backend run pytest tests/test_chat_api.py
uv --directory Backend run pytest
git diff --check
```

현재 Handoff 기준선의 전체 결과는 `68 passed`입니다. 이후 테스트가 추가되면 개수는
늘 수 있으므로, 최종 판정은 개수보다 실패가 0개인지로 합니다.

다음 정책이 통과해야 합니다.

- 현재 `message_id`가 `current_message_id`로 전달됩니다.
- GameEvent 저장 전에는 Client의 `recent_event_ids`를 허용 Source로 전달하지
  않습니다.
- `retrieved_memories`는 Memory 검색 구현 전까지 Backend가 빈 배열로 공급합니다.
- Offline 요청은 `game_context`와 `allowed_commands`를 제공할 수 없습니다.
- 허용되지 않은 Command와 임의 Memory Source ID는
  `AIServiceInvalidOutput`으로 거부됩니다.
- 민감한 Context 키, 인증 값과 대화 원문이 AI 입력 또는 일반 로그로 새지 않습니다.

Starlette의 `httpx` 사용 방식에 대한 deprecation warning 1건은 현재 알려진
비차단 경고입니다. 테스트 실패나 새 warning은 별도로 보고합니다.

## 10. Mock Backend 수동 실행

자동 테스트가 모두 통과한 뒤 실행 상태를 확인합니다.

```powershell
Copy-Item Backend\.env.example Backend\.env
uv --directory Backend run alembic upgrade head
$env:AI_MODE = "mock"
$env:MOCK_AI_SCENARIO = "normal"
uv --directory Backend run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

서버를 실행한 터미널은 그대로 두고 새 PowerShell에서 확인합니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/capabilities
```

`/health`의 `status`는 `ok`, `ai_mode`는 `mock`이어야 합니다. Capabilities에는
`Health`, `MockChat`, `SQLitePersistence`가 포함되어야 합니다. 종료는 서버
터미널에서 `Ctrl+C`를 사용합니다.

`.env`는 Commit하지 않습니다. Mock 검증에는 Runtime URL, 모델명과 Runtime
비밀정보가 필요하지 않습니다.

## 11. AIService Request v2 해석

AI가 직접 사용해야 하는 주요 필드는 다음과 같습니다.

| 필드 | 의미 | 규칙 |
|---|---|---|
| `schema_version` | AI 입력 계약 버전 | 현재 값은 `2` |
| `request_id` | 요청과 결과 상관관계 | Result에 같은 값을 반환 |
| `current_message_id` | 현재 사용자 Message 근거 | Memory Source로 그대로 재사용 가능 |
| `allowed_event_ids` | Backend가 검증한 Event 근거 | 목록에 없는 ID를 생성하지 않음 |
| `interaction_mode` | `InGame` 또는 `Offline` | `time_context.source`와 일치 |
| `companion_id` | 안정적인 동료 식별자 | 표시 이름이나 UObject명이 아님 |
| `user_message` | 정제된 현재 발화 | 로그에 원문을 남기지 않음 |
| `time_context` | GameWorld 또는 RealWorld 시간 | 두 시간 의미를 혼합하지 않음 |
| `game_context` | 목적 제한 게임 상태 | Offline에서는 빈 객체 |
| `retrieved_memories` | Backend 검색 결과 | Client 입력으로 만들지 않음 |
| `allowed_commands` | 현재 생성 가능한 Command | 목록 밖 Command 생성 금지 |

AI는 `profile_id`, `device_id`, Token, Pairing Code, DB 연결정보와 내부 Primary Key를
요청하거나 추론해 출력하지 않습니다.

## 12. AIService Result v1 생성 규칙

Result는 다음 필드를 모두 가집니다.

- `schema_version=1`
- 입력과 같은 `request_id`
- 비어 있지 않은 `display_text`
- `command_candidates` 배열
- `memory_candidates` 배열
- `provider`, `model_version`, `prompt_version` Metadata

Command와 Memory는 실행·저장 결과가 아니라 후보입니다.

### Command Candidate

- `type`은 입력의 `allowed_commands` 안에 있어야 합니다.
- `request_id`는 현재 요청과 같아야 합니다.
- `expires_at`은 `issued_at`보다 나중이어야 합니다.
- UObject 이름, 함수명과 자유 형식 실행 코드를 반환하지 않습니다.
- UE Command Gateway가 대상, 거리, 상태, 만료와 중복을 최종 검증합니다.

### Memory Candidate

- `source_ids`는 `current_message_id`와 `allowed_event_ids`의 합집합 안에서만
  선택합니다.
- Source ID를 새로 만들거나 요약문에서 추측하지 않습니다.
- `source_mode`는 요청의 `interaction_mode`와 같아야 합니다.
- 후보는 Backend Source/정책 검증 전까지 사실 Memory가 아닙니다.

## 13. 실제 Runtime을 연결할 때의 수정 경계

### 자유롭게 수정 가능한 영역

- `Backend/app/infrastructure/ai/` 아래 Runtime Adapter
- Runtime Adapter 전용 테스트
- Prompt Template과 구조화 출력 파서
- 비밀이 아닌 설정 예제와 AI 파트 실행 문서

### Backend 담당자와 계약 변경 합의가 필요한 영역

- `Contracts/schemas/ai-service-*.schema.json`
- `Contracts/fixtures/ai-service/`
- `Backend/app/application/models/ai.py`
- `Backend/app/application/ports/ai_service.py`
- 공용 오류 코드와 Metadata 의미

### AI 파트가 단독으로 수정하면 안 되는 영역

- `Backend/app/api/routes/`
- `Backend/app/infrastructure/database/`
- Migration과 데이터 모델
- Device 인증, Pairing과 Profile 범위 검증
- Client API Response를 공급자 원본 형식으로 바꾸는 코드

Runtime의 네이티브 API가 `/v1/generate-chat`과 다르면 Infrastructure Adapter
내부에서 요청과 응답을 변환합니다. Runtime API에 맞추기 위해 Router, Port 또는
DB를 바꾸지 않습니다.

## 14. Local 모드 설정

`AI_MODE=local`에는 다음 값이 필요합니다.

```dotenv
AI_MODE=local
AI_RUNTIME_BASE_URL=http://127.0.0.1:PORT
AI_MODEL_NAME=MODEL_IDENTIFIER
AI_PROMPT_VERSION=prompt-v1
AI_REQUEST_TIMEOUT_SECONDS=10
```

- 실제 Token과 비밀정보는 `.env`에만 저장하고 Commit하지 않습니다.
- 모델명과 URL을 코드에 하드코딩하지 않습니다.
- Base URL은 C PC 내부 또는 허용된 Local Runtime을 가리킵니다.
- 데이터베이스와 Runtime을 A/B Client에 직접 노출하지 않습니다.
- 설정을 바꾼 뒤에는 Backend 프로세스를 다시 시작합니다.

설정 누락만 확인하려면 다음 테스트를 사용합니다.

```powershell
uv --directory Backend run pytest tests/test_local_runtime_ai_service.py -k settings
```

## 15. 최소 대체 AIService 검증 방법

최소 대체 구현의 목적은 모델 품질 검증이 아니라 Port 독립성 검증입니다.

1. `AIService.generate_chat(request)` 서명을 그대로 구현합니다.
2. 입력을 `AIServiceRequest`로만 받습니다.
3. 출력은 `AIServiceResult`로 생성하거나 외부 JSON을 해당 모델로 검증합니다.
4. Router와 DB 파일을 수정하지 않습니다.
5. 테스트에서는 `get_ai_service` Dependency만 대체합니다.
6. 일반·Command·Memory 입력을 각각 실행합니다.
7. 잘못된 Command와 Source ID가 Backend에서 거부되는지 확인합니다.

기존 `test_chat_builds_policy_limited_ai_service_request`가 최소 대체 구현을 주입하는
예제이고, `test_chat_rejects_candidates_outside_backend_allowlists`가 잘못된 후보의
거부 예제입니다.

```powershell
uv --directory Backend run pytest tests/test_chat_api.py -k "policy_limited or outside_backend_allowlists"
```

이 명령이 독립 환경에서 통과하고 Router/DB diff가 없다면 최소 대체 경계 검증은
통과입니다.

## 16. Runtime·모델 개발 계획 작성

계약 테스트 후 다음 순서로 AI 파트 계획을 작성합니다.

### Phase 1. Runtime 후보 측정

- 후보별 설치·실행 방법
- 구조화 JSON 출력 지원 방식
- timeout과 취소 처리 방식
- C PC GPU/CPU/RAM/VRAM 요구량
- Local API 접근 범위와 인증 필요 여부

### Phase 2. 모델·양자화 후보 측정

- 모델 식별자와 버전
- 양자화 형식
- VRAM/RAM 사용량
- 첫 Token 지연과 전체 응답 지연
- 최대 Context와 권장 입력 예산
- 한국어 대화 자연스러움

### Phase 3. 구조화 출력과 Prompt

- Prompt version 규칙
- 일반 대화, Command와 Memory 출력 성공률
- 허용 목록 밖 Command 발생률
- 근거 없는 Source ID 발생률
- malformed JSON과 Schema mismatch 발생률
- 재시도 없이 실패를 명시적으로 반환하는 방식

### Phase 4. 품질 평가

최소 평가 세트는 공용 fixture의 일반·Command·Memory 시나리오를 포함합니다.
추가 평가 데이터에는 실제 개인 대화, Token과 내부 ID를 사용하지 않습니다.

| 측정 항목 | 기록 단위 |
|---|---|
| 첫 응답 지연 | ms |
| 전체 응답 지연 | ms, p50/p95 |
| timeout 비율 | 실패 수 / 전체 요청 수 |
| strict Schema 성공률 | 성공 수 / 전체 요청 수 |
| 허용 Command 준수율 | 유효 후보 수 / 전체 후보 수 |
| Memory Source 준수율 | 허용 Source 후보 수 / 전체 후보 수 |
| VRAM/RAM 사용량 | MiB 또는 GiB |
| Prompt/Model version | 안정 문자열 |

Runtime과 모델을 한 번에 여러 개 바꾸지 않습니다. Runtime, 모델, 양자화, Prompt 중
하나만 바꾸고 같은 fixture와 측정 조건으로 비교합니다.

## 17. 실패 판정과 담당자

| 실패 | 먼저 확인할 담당 |
|---|---|
| Schema와 Pydantic 모델 불일치 | Backend 담당 |
| Router나 DB 수정 없이는 연결 불가 | Backend 담당과 계약 재검토 |
| Runtime 연결·HTTP 형식 오류 | AI 담당 |
| 모델이 strict JSON을 반복적으로 생성하지 못함 | AI 담당 |
| 허용되지 않은 Command 후보 | AI Prompt/Adapter 확인 후 Backend 재검증 |
| 존재하지 않는 Memory Source | AI Prompt/Adapter 확인 후 Backend 거부 유지 |
| Event Source 목록이 항상 비어 있음 | 후속 GameEvent 저장 Task 담당 |
| Retrieved Memory가 항상 비어 있음 | 후속 Memory 검색 Task 담당 |

실패를 임의 fallback 성공으로 바꾸지 않습니다. 재현 명령, 입력 fixture, 기대 결과와
실제 오류 코드를 기록합니다.

## 18. Handoff 결과 보고 템플릿

다음 양식을 Issue 또는 Draft PR에 붙여 넣습니다.

```markdown
## AIService 독립 환경 검증 결과

- Repository:
- Branch:
- Commit SHA:
- OS:
- Python:
- uv:
- 검증 일시:

### 실행 결과

- 계약 테스트: Pass / Fail
- Mock 일반 대화: Pass / Fail
- Mock Command Candidate: Pass / Fail
- Mock Memory Candidate: Pass / Fail
- Local Adapter 정상 응답: Pass / Fail
- Local Adapter timeout: Pass / Fail
- Local Adapter unavailable: Pass / Fail
- malformed JSON: Pass / Fail
- schema mismatch: Pass / Fail
- Backend 전체 테스트: N passed / N failed
- Router 변경: 없음 / 있음
- DB·Migration 변경: 없음 / 있음

### Runtime·모델 계획

- Runtime 후보:
- 모델 후보:
- 양자화 후보:
- Prompt version 초안:
- 측정할 timeout/지연/VRAM/Context 항목:
- 예상 일정:

### 미결정 또는 차단 사항

- 항목:
- 재현 방법:
- 필요한 결정 담당자:
```

## 19. 최종 Handoff Gate

다음 항목이 모두 충족되어야 AIService Handoff를 완료 처리합니다.

- 전달받은 Commit SHA를 clean 환경에서 검증했습니다.
- 계약, Mock, Fake Runtime과 Backend 전체 테스트가 통과했습니다.
- 최소 대체 `AIService`가 Router와 DB 수정 없이 동작했습니다.
- 민감정보가 입력, fixture와 로그에 포함되지 않았습니다.
- Runtime·모델·양자화·Prompt 후보 및 평가 계획이 기록되었습니다.
- 미결정 항목과 담당자가 기록되었습니다.
- 검증 결과가 GitHub Issue/PR, M01 Task와 Notion `MVP-BE-05`에 동기화되었습니다.

하나라도 증빙이 없으면 상태는 `In Progress` 또는 `AI Handoff Verification
Pending`으로 유지합니다.

## 20. 문제 해결

### `uv` 또는 Python 실행 권한 오류

- PowerShell을 새로 열고 저장소 경로를 다시 확인합니다.
- 다른 프로세스가 `Backend/.venv`를 사용 중인지 확인합니다.
- 회사 보안 정책이 Python 또는 `uv` 실행을 차단하는지 담당자에게 확인합니다.
- 우회로 테스트를 성공으로 기록하지 말고 실제 오류 전문을 첨부합니다.

### 포트 8000 사용 중

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

기존 Backend를 종료하거나 검증용 포트를 변경합니다. 포트를 변경했다면 Health 요청
주소도 같은 값으로 바꿉니다.

### Local 모드가 시작되지 않음

- `AI_MODE=local`인지 확인합니다.
- `AI_RUNTIME_BASE_URL`, `AI_MODEL_NAME`, `AI_PROMPT_VERSION`이 모두 있는지
  확인합니다.
- Runtime이 먼저 실행 중인지 확인합니다.
- Runtime 네이티브 API와 Adapter 경로가 다르면 Infrastructure 매핑을 확인합니다.

### HTTP는 성공하지만 Chat이 `AIServiceInvalidOutput`

- Runtime 응답이 JSON인지 확인합니다.
- `AIServiceResult` 필수 필드와 Schema version을 확인합니다.
- 추가 필드가 있는지 확인합니다.
- `request_id`, Command allowlist와 Memory Source 범위를 확인합니다.
- 원본 응답을 일반 로그에 그대로 남기지 않습니다.

