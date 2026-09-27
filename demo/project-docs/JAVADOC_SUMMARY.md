# Javadoc Summary — Extracted Business Intent

This document summarises the business intent extracted from Javadoc comments in the codebase.
It is used by the Architecture and Migration Agents to ensure migrated code preserves intent.

---

## UserService

**Class intent:** Manages the full user lifecycle for the platform. Acts as the single source of
truth for user state. All user mutations (create, activate, delete) MUST go through this service —
never modify the User model directly from outside.

| Method | Business Intent |
|--------|----------------|
| `createUser(username, email)` | Onboards a new user. Normalises input (trim, lowercase) before persisting. Validates domain rules. This is the ONLY permitted way to create users. |
| `getUserById(id)` | Safe read — returns empty/None for invalid IDs instead of throwing. Callers must handle the absent case. |
| `getActiveUsers()` | Returns only users with active=true. Used by billing and reporting pipelines. |
| `activateUser(id)` | Transitions a user from inactive to active. Throws if user not found — this is intentional (activation of non-existent user is a hard error, not a soft one). |
| `deleteUser(id)` | Idempotent delete. Silently no-ops if user not found — callers should not need to check existence first. |
| `getUserCount()` | Used by the admin dashboard for capacity planning. Must be fast (no filtering). |

---

## OrderProcessor

**Class intent:** Stateless processor for order financial calculations. Applies business rules for
discounts and tax. Designed to be called per-order or in bulk. Has no side effects beyond returning
the mutated order object — it does NOT persist to database.

| Method | Business Intent |
|--------|----------------|
| `processOrder(order)` | Core pipeline: validate → discount → tax → total. Returns the same order object mutated. Throws on invalid input — invalid orders must never silently produce a $0 total. |
| `validateOrder(order)` | Guard method. Checks structural integrity: non-null, non-empty items, non-negative prices, positive quantities. Private — only called from processOrder. |
| `calculateSubtotal(items)` | Pure arithmetic: sum of price*quantity. No rounding at this stage. |
| `calculateDiscount(subtotal)` | Applies the enterprise bulk discount contract. See ADR-002. |
| `processBatch(orders)` | Fault-tolerant batch runner. See ADR-004. Logs skipped orders to stderr. |

---

## Key Business Rules Summary (for Migration Agents)

1. User email is ALWAYS stored lowercase — normalise on input, not on read.
2. Username is ALWAYS trimmed of whitespace before storage.
3. Bulk discount threshold ($500) and rate (10%) are contractual — never change values.
4. Tax rate (8%) is a configurable business parameter — use a named constant, not a magic number.
5. activateUser throws on missing user — this is a hard business rule, not a bug.
6. deleteUser is silent on missing user — this is intentional idempotency.
7. processBatch never throws — per-item errors are logged and skipped.
