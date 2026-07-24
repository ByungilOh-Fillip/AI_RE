# WebSocket Chat Protocol Handoff

- 문서 상태: Current Backend Contract
- 대상: Backend 담당, UE 연동 담당, Web 담당
- 범위: WebSocket endpoint, 인증, Chat Frame과 연결 운영

## 1. 목적

WebSocket Chat은 기존 `POST /api/v1/chat`과 동일한 Chat Request/Response 의미를
지속 연결 위에서 제공합니다. HTTP endpoint는 마이그레이션과 명시적 fallback을
위해 유지합니다.

권위 있는 Payload 정의는 `Backend/app/application/models/chat.py`와
`Contracts/`입니다.

## 2. Endpoint와 인증

| Endpoint | 대상 | 인증 |
|---|---|---|
| `/api/v1/game/chat` | UE 등 Native GameClient | Handshake `Authorization` Header |
| `/api/v1/mobile/chat` | Browser/WebView WebClient | 연결 후 첫 Auth Frame |

Production에서는 `wss://`를 사용합니다. 두 endpoint는 인증 전달 방식만 다르고
Chat Frame, 오류와 처리 순서는 같습니다.

### 2.1 GameClient

```text
Authorization: Bearer <device-token>
```

서버는 연결을 수립하기 전에 Token을 검증합니다. 실패한 연결은 열리지 않습니다.

### 2.2 WebClient

연결 직후 첫 Frame으로 다음 JSON을 전송합니다.

```json
{
  "type": "auth",
  "token": "<device-token>"
}
```

- Auth 이전의 다른 Frame은 즉시 연결 종료 대상입니다.
- `WS_AUTH_TIMEOUT_SECONDS` 기본값인 10초 안에 인증해야 합니다.
- 인증 성공 응답은 없습니다. Client는 Auth Frame 전송 후 Chat Frame을 보냅니다.
- 인증 실패는 `1008 Policy Violation`으로 종료됩니다.
- `1008`은 동일 Token 재시도보다 Token 갱신·재발급이 필요한 신호입니다.

## 3. Message Envelope

모든 Application Message는 UTF-8 JSON Text Frame이며 `type`과 `payload`를
사용합니다.

### Client Chat

```json
{
  "type": "chat",
  "payload": {
    "schema_version": 1,
    "request_id": "request-ingame-001",
    "save_slot_id": "save-01",
    "companion_id": "MAKO",
    "session_id": "session-ingame-001",
    "interaction_mode": "InGame",
    "message_id": "message-user-002",
    "user_message": "여기서 기다려",
    "time_context": {
      "source": "GameWorld",
      "day": 18,
      "hour": 14.5,
      "period": "Afternoon"
    },
    "recent_event_ids": [],
    "game_context": {},
    "allowed_commands": []
  }
}
```

### Server Success

```json
{
  "type": "chat_response",
  "payload": {
    "schema_version": 1,
    "request_id": "request-ingame-001",
    "save_slot_id": "save-01",
    "companion_id": "MAKO",
    "session_id": "session-ingame-001",
    "interaction_mode": "InGame",
    "response_id": "response-001",
    "display_text": "알겠어. 여기서 기다릴게.",
    "command_candidates": [],
    "memory_candidates": [],
    "ai_metadata": {
      "provider": "mock",
      "model_version": "mock-v1",
      "prompt_version": "mock-v1"
    }
  }
}
```

### Server Error

```json
{
  "type": "error",
  "payload": {
    "schema_version": 1,
    "request_id": "request-ingame-001",
    "error": {
      "code": "AIServiceUnavailable",
      "message": "AI service is currently unavailable.",
      "retryable": true,
      "details": {}
    }
  }
}
```

알 수 없는 `type`은 오류나 연결 종료로 처리하지 않고 조용히 무시합니다. Phase 2의
`chat_delta`와 `chat_commit` 추가 시 기존 Client가 연결을 유지하기 위한
호환성 규칙입니다.

## 4. Chat Payload 규칙

- 정의되지 않은 필드는 `InvalidRequest`로 거부합니다.
- 모든 안정 ID는 `^[A-Za-z0-9][A-Za-z0-9._:-]*$`, 최대 128자입니다.
- `user_message`는 1~2000자입니다.
- `InGame`은 `GameWorld`, `Offline`은 `RealWorld` Time Context만 사용합니다.
- Offline의 `game_context`와 `allowed_commands`는 비어 있어야 합니다.
- GameClient Token은 InGame, WebClient Token은 Offline 요청에만 사용할 수 있습니다.
- `game_context`는 최대 32개 Key이며 민감 정보 Key를 포함할 수 없습니다.
- `request_id`는 멱등성 Key입니다. 같은 ID와 같은 Body는 저장 응답을 재사용하고,
  같은 ID와 다른 Body는 `DuplicateRequest`입니다.
- `message_id`는 Profile 범위에서 새 발화마다 유일해야 합니다. 재시도는 기존
  `request_id`, `message_id`와 동일 Body를 그대로 사용합니다.
- WebSocket Frame에는 `X-Request-ID`가 없으며 Payload `request_id`로 상관관계를
  유지합니다.

## 5. Response와 Candidate

- Client는 Response `request_id`가 활성 Request와 일치하는지 확인합니다.
- `display_text`는 비어 있지 않은 1~4000자 문자열입니다.
- `command_candidates`는 현재 0개 또는 1개이며 Schema 상한은 4개입니다.
- Candidate는 요청의 `allowed_commands`에 포함된 Type만 반환됩니다.
- 현재 MAKO Backend 출력 범위는 `Command.Follow`, `Command.HoldPosition`,
  `Command.CancelCurrent`입니다.
- Command는 `expires_at` 이후 폐기해야 합니다.
- `memory_candidates`는 현재 빈 배열입니다.
- UE의 1차 `display_text` 수직 슬라이스는 Candidate를 실행하거나 저장하지 않습니다.

## 6. 오류와 연결 유지

인증 이후 Chat 처리 오류는 연결을 종료하지 않습니다. Client는 Error Frame을 처리한
뒤 같은 연결에서 다음 요청을 전송할 수 있습니다.

| Code | Retryable | 의미 |
|---|---|---|
| `InvalidRequest` | false | Envelope 또는 Payload 검증 실패 |
| `RequestTooLarge` | false | 기본 256KB 상한 초과 |
| `DuplicateRequest` | false | Request/Message ID 재사용 충돌 |
| `IdentityClaimMismatch` | false | Token Identity와 Client Claim 불일치 |
| `UnauthorizedDevice` | false | Device 역할과 Interaction Mode 불일치 |
| `AIServiceUnavailable` | true | AI 일시 장애 |
| `AIServiceTimeout` | true | AI 처리 Timeout |
| `RequestTimeout` | true | Message 처리 Timeout, 기본 30초 |
| `InternalError` | true | Backend 내부 오류 |

`retryable=true`인 요청은 직렬화된 동일 Body와 동일 `request_id`, `message_id`로
재전송합니다.

## 7. 연결 운영

- 연결당 Message는 순차 처리되며 Response도 요청 순서대로 반환됩니다.
- Client는 Response를 확인한 후 다음 Chat을 보내는 방식을 사용합니다.
- 연결이 끊기면 Client가 재연결합니다.
- 응답을 확인하지 못한 Request는 동일 ID와 Body로 재전송할 수 있습니다.
- 현재 Streaming과 Server Push는 지원하지 않습니다.
- Token, Auth Frame과 실제 사용자 발화는 일반 로그에 기록하지 않습니다.

## 8. UE 구현 인계 기준

- [ ] `/api/v1/game/chat` Handshake에 Bearer Device Token을 전달한다.
- [ ] `chat` Envelope 안에 기존 InGame Chat Request를 넣는다.
- [ ] `chat_response`와 `error`를 구분하고 알 수 없는 Type은 무시한다.
- [ ] 같은 연결에서 한 번에 하나의 Chat Request만 처리한다.
- [ ] Retry는 동일 Request/Message ID와 직렬화 Body를 재사용한다.
- [ ] `1008`과 일반 연결 장애를 구분한다.
- [ ] Chat Error가 MAKO의 로컬 StateTree·GAS 동작을 중단시키지 않는다.
- [ ] Token과 사용자 발화가 로그·Config·Fixture에 남지 않는다.
- [ ] HTTP Chat은 명시적 설정으로만 선택하고 자동 fallback하지 않는다.

