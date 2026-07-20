# Contract Fixtures

| Fixture | Expected result |
|---|---|
| `chat/offline-request.valid.json` | Valid Offline Chat request using RealWorld time |
| `chat/ingame-request.valid.json` | Valid InGame Chat request using GameWorld time |
| `chat/response.valid.json` | Valid normalized response with no direct game execution |
| `chat/request.invalid-missing-time-context.json` | Invalid because `time_context` is required |
| `commands/follow.valid.json` | Valid Follow command candidate |
| `events/combat-started.valid.json` | Valid meaningful game event |
| `memory/user-shared-event.valid.json` | Valid source-backed memory candidate |
| `errors/ai-service-unavailable.valid.json` | Valid stable unavailable error |
| `ai-service/request.valid.json` | Valid provider-independent AIService input without authentication data |
| `ai-service/result.valid.json` | Valid normalized AIService output |

Semantic checks such as command expiry, duplicate IDs, target validity, and source existence are application validations in addition to JSON Schema validation.
