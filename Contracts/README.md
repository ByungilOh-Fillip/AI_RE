# AI_RE Contracts

This directory is the executable source of truth for data exchanged between the Backend, WebApp, Unreal Engine, and AIService.

## Layout

- `openapi.yaml`: HTTP API contract.
- `schemas/`: reusable JSON Schema definitions.
- `fixtures/`: normal and failure examples used by every implementation.

## Rules

- Breaking semantic changes increment `schema_version`.
- Unknown optional fields may be ignored, but unsupported required schema versions must be rejected.
- Display names, Unreal class names, and array indexes are not stable protocol identifiers.
- `InGame` uses `GameWorld` time and `Offline` uses `RealWorld` time.
- Command and Memory candidates are untrusted until validated by the owning system.
- Fixtures must not contain credentials or real user conversation data.

## Identity and development authentication

- There is no multi-user `user_id`. C owns one local `profile_id` and scopes data by `save_slot_id` and `companion_id`.
- C resolves `profile_id`, `device_id`, and the Device role from the bearer token.
- Client-provided `profile_id` and `device_id` are optional claims. When present, C compares them with the authenticated identity and rejects a mismatch.
- The local GameClient development token is accepted only by `register-game` as a bootstrap credential.
- Registered GameClient and paired WebClient tokens are validated from persisted HMAC-SHA256 hashes. Raw tokens and Pairing Codes are never stored.
- Tokens never appear in Contracts fixtures, logs, URLs, or committed configuration.

## Request correlation and idempotency

- Clients may send `X-Request-ID`; when a body also has `request_id`, the values must match.
- When the header is absent, a body `request_id` becomes the effective correlation ID; requests without either receive a Backend UUID.
- The effective value is returned in `X-Request-ID`, error envelopes and structured request logs.
- Repeating the same authenticated Profile plus `request_id` and identical content returns the stored Chat response.
- Reusing that key with different content returns `DuplicateRequest` without creating messages.

## Initial scope

The contract covers health, capabilities, persistent Device Pairing, Chat, Event, Command candidates, Memory candidates, the AIService boundary, and the shared error envelope.
