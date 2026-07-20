# AIService Handoff Guide

## 1. 목적

AI 개발자가 FastAPI Router와 데이터베이스 코드를 수정하지 않고 `AIService`
구현체를 교체하여 Local LLM Runtime 연동을 시작할 수 있도록 현재 계약, 책임
경계와 검증 Gate를 정리합니다.

이 문서는 실제 모델이나 Runtime을 고정하지 않습니다. 외부 API와 Application
Port는 공급자에 독립적으로 유지하며, AI 파트가 선택한 Runtime은 Infrastructure
Adapter 안에서만 연결합니다.

저장소를 처음 접하는 AI 개발자는 계약 세부사항을 읽기 전에
[`AI Developer Quickstart`](AI_DEVELOPER_QUICKSTART.md)의 clean 환경 준비와 검증
순서를 먼저 수행합니다.

## 2. 현재 기준선

현재 저장소에는 다음 기반이 있습니다.

- AIService Request Schema v2와 strict `AIServiceResult` Pydantic 모델
- `AIService.generate_chat()` Protocol
- `normal`, `command`, `memory`, `timeout`, `unavailable`, `invalid_output` Mock
- 일반 대화, Command Candidate와 Memory Candidate 공용 fixture
- `AI_MODE=mock|local` 설정 분리
- Chat Application Service의 AI timeout과 표준 오류 변환
- Prompt, Model, Provider 버전 Metadata
- HTTP Local Runtime Adapter와 Fake Runtime 테스트

`AI_MODE=local`은 설정된 Runtime의 `/v1/generate-chat` 경계에 연결됩니다. 최종
Runtime, 모델, Prompt와 공급자별 요청 매핑은 AI 파트 결정 범위입니다.

## 3. 계약 기준 파일

- `Contracts/schemas/ai-service-request.schema.json`
- `Contracts/schemas/ai-service-result.schema.json`
- `Contracts/fixtures/ai-service/request.valid.json`
- `Contracts/fixtures/ai-service/result.valid.json`
- `Backend/app/application/models/ai.py`
- `Backend/app/application/ports/ai_service.py`
- `Backend/app/infrastructure/ai/mock.py`
- `Backend/app/infrastructure/ai/local_runtime.py`
- `Backend/tests/test_mock_ai_service.py`
- `Backend/tests/test_local_runtime_ai_service.py`

공유 계약 변경은 JSON Schema와 fixture를 먼저 변경한 뒤 Backend 모델과 Adapter에
반영합니다. 지원하지 않는 필수 `schema_version`과 정의되지 않은 출력 필드는
명시적으로 거부합니다.

## 4. 책임 경계

### Backend 담당

- 인증과 Profile, Device, Save, Companion 범위 검증
- Message와 Event Source ID의 존재 및 소유 범위 검증
- AIService 입력 Context 구성과 크기 제한
- AI 결과의 Schema, Command allowlist와 Memory Source 재검증
- timeout과 표준 오류 변환
- Conversation, Event와 Memory 영속화

### AI 담당

- Local LLM Runtime Adapter
- Prompt Template과 구조화 출력 생성
- `display_text`, Command Candidate와 Memory Candidate 후보 생성
- Provider, Model과 Prompt version Metadata
- 모델별 지연, VRAM, Context/Token 예산과 권장 timeout 측정
- Runtime 장애와 잘못된 출력의 명시적 반환

### UE 담당

- InGame Context와 안정 ID 제공
- 외부 Command 후보의 대상, 거리, 상태, 만료와 중복 최종 검증
- 승인된 Command만 StateTree 또는 GAS로 전달
- Backend와 LLM 장애 중 로컬 Companion 행동 유지

## 5. 이번 Handoff Task에서 확정할 항목

1. AIService가 참조할 현재 Message ID와 허용된 Event ID 전달 규칙
2. AI가 임의 Source ID를 생성하지 못하도록 하는 Backend 검증 규칙
3. `allowed_commands`, `game_context`, `retrieved_memories`의 MVP 입력 규칙
4. 일반 대화, Command Candidate와 Memory Candidate Mock 시나리오
5. Local Runtime Base URL, 모델명과 Prompt version 설정 경계
6. 공급자 원본 JSON의 strict `AIServiceResult` 검증
7. unavailable, timeout, malformed JSON과 schema mismatch 오류 매핑
8. Fake Runtime으로 검증 가능한 Local Adapter 교체 지점

### 5.1 Source ID 규칙

AIService Request Schema v2는 `current_message_id`와
`allowed_event_ids`를 명시적으로 전달합니다. Memory Candidate의 모든
`source_ids`는 두 필드의 합집합 안에 있어야 하며, Backend는 범위를 벗어난 후보
전체를 `AIServiceInvalidOutput`으로 거부합니다. AI는 Source ID를 생성하거나
변형하지 않습니다.

현재 Chat 요청의 `message_id`는 인증된 요청 범위에 묶인 현재 Source로 즉시
허용합니다. `recent_event_ids`는 Client 주장값입니다. `POST /api/v1/events`와
GameEvent 저장소가 구현되어 Profile, Save, Companion 범위를 확인하기 전까지
Backend는 이를 `allowed_event_ids`로 승격하지 않으며 AIService에는 빈 배열을
전달합니다.

### 5.2 MVP Context 규칙

- `allowed_commands`: 인증된 InGame 요청이 공통 allowlist 안에서 제공한 현재
  허용 Command만 전달합니다. Offline에서는 빈 배열만 허용합니다.
- `game_context`: InGame Chat 목적에 필요한 최대 32개 속성의 정제된 JSON만
  전달합니다. Offline에서는 빈 객체만 허용합니다.
- `retrieved_memories`: Memory 검색이 구현되기 전까지 Backend가 빈 배열을
  전달합니다. Client가 검색 결과를 직접 주입하지 않습니다.

Backend는 결과의 Command type이 `allowed_commands`에 포함되는지, Command와
Result의 `request_id`가 현재 요청과 같은지, Memory의 `source_mode`가 현재
Interaction Mode와 같은지를 AIService 호출 뒤 다시 검증합니다.

### 5.3 Local Runtime Adapter 경계

기본 Local Adapter는 `POST {AI_RUNTIME_BASE_URL}/v1/generate-chat`에 공급자 독립
Envelope를 전송합니다. Envelope는 `model`, `prompt_version`, `input`을 가지며
`input`은 AIService Request Schema v2입니다. Runtime 응답은 공급자 원본 형식을
Router나 Domain에 노출하지 않고 Adapter 안에서 strict `AIServiceResult`로
검증합니다.

`AI_RUNTIME_BASE_URL`, `AI_MODEL_NAME`, `AI_PROMPT_VERSION`은
`AI_MODE=local`에서만 필수입니다. `AI_MODE=mock`은 세 설정 없이 동작합니다.
Runtime별 Prompt와 원본 응답 매핑은 `infrastructure/ai` 내부 구현만 교체하며
Application Port, Router와 DB를 변경하지 않습니다.

## 6. 보안 규칙

다음 값은 AIService 입력, Prompt와 일반 로그에 포함하지 않습니다.

- Device Token과 Pairing Code
- `profile_id`, `device_id`와 DB 내부 Primary Key
- 데이터베이스 접속정보와 Runtime 비밀정보
- 현재 응답에 불필요한 전체 현실 대화 원문

AI 결과는 후보 데이터입니다. AI 파트가 생성한 Command는 UE Command Gateway가
최종 검증하며, Memory Candidate는 Backend가 실제 Message/Event Source와 범위를
확인한 뒤에만 저장합니다.

## 7. 로컬 검증

Backend 기본 검증은 실제 Runtime 없이 Mock 모드로 실행합니다.

```powershell
uv --directory Backend run pytest
```

실제 Local Adapter 테스트는 Fake Runtime 또는 Stub HTTP 응답을 사용하여 다음을
검증합니다.

- 정상 구조화 결과
- Runtime 연결 실패
- timeout과 취소
- JSON 파싱 실패
- 필수 필드 누락과 지원하지 않는 Schema
- 허용되지 않은 Command와 근거 없는 Memory Candidate 거부

실제 Runtime과 모델을 사용하는 성능·품질 검증은 별도 AI 파트 Task에서
수행합니다.

## 8. Handoff Gate

- AI 개발자가 문서와 fixture만으로 입력·출력 의미를 설명할 수 있습니다.
- AI 개발자가 Router와 DB를 수정하지 않고 최소 대체 AIService를 연결합니다.
- Mock과 Local 구현이 동일한 `AIServiceResult`와 표준 오류를 사용합니다.
- 정상·timeout·unavailable·invalid output 계약 테스트가 독립 환경에서 통과합니다.
- AI 출력 오류가 실행 가능한 Command나 사실 Memory로 통과하지 않습니다.
- Runtime, 모델, Prompt 미결정 사항과 담당자가 기록됩니다.

미결정 항목의 담당자는 다음과 같습니다.

- 최종 Runtime, 모델, 양자화와 Prompt: AI 개발자
- Runtime별 권장 timeout과 Context/Token 예산: AI 개발자 측정 후 제안
- Event Source 허용: Backend의 Event 저장 Task 완료 후 Backend 담당자가 연결
- Memory 검색 입력: Memory 검색 Task 완료 후 Backend 담당자가 연결

## 9. 제외 범위

- 최종 Local LLM Runtime과 모델 선택
- GPU/VRAM 벤치마크 수행
- Memory 저장·검색·삭제 구현
- GameEvent 저장 API
- Unreal HTTP Client와 Command 실행
- 음성, 멀티모달과 외부 인터넷 공개
