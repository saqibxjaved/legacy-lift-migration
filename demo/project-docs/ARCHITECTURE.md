# Architecture Decision Records — Legacy Monolith

## ADR-001: Keep UserService and OrderProcessor Decoupled
**Date:** 2022-03-15  
**Status:** ACCEPTED

### Context
UserService manages user lifecycle. OrderProcessor handles order business logic.
These two classes MUST remain independent with no direct method calls between them.
An OrderProcessor should only receive a userId (Long), never a User object — to avoid
coupling the order domain to the user domain.

### Decision
OrderProcessor MUST NOT import or instantiate UserService.
Communication is allowed only via userId (primitive). Any migration MUST preserve this boundary.

### Consequences
Each service can be deployed independently. Cross-service data fetching must go through a REST API.

---

## ADR-002: Bulk Discount Logic is Business-Critical — Do Not Simplify
**Date:** 2022-06-01  
**Status:** ACCEPTED

### Context
The 10% bulk discount threshold of $500 in OrderProcessor is contractually agreed with enterprise
customers. It must not be changed, approximated, or simplified during migration.

### Decision
The exact values TAX_RATE=0.08, BULK_DISCOUNT_THRESHOLD=500.00, BULK_DISCOUNT_RATE=0.10
must be preserved as named constants in the migrated code. Using magic numbers is FORBIDDEN.

### Consequences
Any migration that inlines these values instead of naming them must be rejected and retried.

---

## ADR-003: Username Validation Rules are Regulatory Requirements
**Date:** 2022-09-10  
**Status:** ACCEPTED

### Context
Username max length (50 chars) and email format validation in UserService are required by
GDPR data minimization and our Terms of Service. They are NOT arbitrary — they cannot be relaxed.

### Decision
These validations MUST be present in migrated code with identical semantics:
- username.strip() before saving (trim whitespace)
- email.lower() before saving (case-insensitive storage)
- max 50 characters for username
- email must contain "@"

---

## ADR-004: OrderProcessor.processBatch Must Be Non-Blocking on Errors
**Date:** 2023-01-20  
**Status:** ACCEPTED

### Context
When processing a batch of orders, a single invalid order must NOT stop processing of remaining orders.
The original Java implementation uses try/catch per order. This pattern must be preserved.

### Decision
processBatch (or equivalent) MUST catch exceptions per item and continue.
Failing fast on the first error is FORBIDDEN in batch context.

---

## ADR-005: Target Microservice Boundaries
**Date:** 2023-04-05  
**Status:** PROPOSED

### Context
Migration target is Python microservices on FastAPI. Two services are proposed:

### Decision
- **user-service**: owns UserService, User model, UserRepository
  - Exposes: POST /users, GET /users/{id}, DELETE /users/{id}, PUT /users/{id}/activate
  - Port: 8001
- **order-service**: owns OrderProcessor, Order model, OrderItem model
  - Exposes: POST /orders/process, POST /orders/batch
  - Port: 8002

Services communicate via HTTP, not shared database.
