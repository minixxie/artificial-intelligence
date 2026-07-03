# Naming Conventions

## Table of Contents

- [General Principles](#general-principles)
- [Java](#java)
- [Golang](#golang)
- [Node.js / TypeScript](#nodejs--typescript)
- [Python](#python)
- [MySQL](#mysql)

---

## General Principles

- Names must be **self-documenting** — a reader should infer purpose without comments.
- **Avoid abbreviations** unless universally understood (`id`, `db`, `http`, `html`, `io`).
- Use **US English** spelling (`color` not `colour`, `initialize` not `initialise`).
- Never encode type information in names (`nameStr`, `ageInt`, `userObj`) — use the type system.
- Boolean variables / parameters use positive prefixes: `isEnabled`, `hasAccess`, `canDelete`.

---

## Java

### Case Styles

| Element | Style | Example |
|---|---|---|
| Package | all lowercase, dot-separated, single word per segment | `com.company.orderservice` |
| Class / Enum | UpperCamelCase | `OrderService`, `OrderStatus` |
| Interface | UpperCamelCase (no prefix) | `OrderRepository`, `EmailSender` |
| Method | lowerCamelCase | `getOrderById()`, `sendNotification()` |
| Field / Variable | lowerCamelCase | `totalAmount`, `orderId` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Enum constant | UPPER_SNAKE_CASE | `PENDING`, `SHIPPED`, `DELIVERED` |
| Type Parameter | single uppercase letter | `T`, `R`, `K`, `V` |
| Record component | lowerCamelCase | `record Order(String orderId)` |
| Annotation | UpperCamelCase | `@Transactional`, `@RestController` |

### Conventions

- Acronyms in class/method names are Pascal-cased: `HttpClient`, `XmlParser`, `loadJson()`.
- Test classes: `{ClassUnderTest}Test` or `{ClassUnderTest}IT` for integration tests.
- Test methods: `{methodName}_{scenario}_{expectedOutcome}` e.g. `calculateTotal_whenNoItems_returnsZero`.
- Lombok / `@Builder` usage: builder method names match the field (no prefix).

---

## Golang

### Case Styles

| Element | Style | Example |
|---|---|---|
| Package | lowercase, single word, no underscores | `order`, `payment`, `httpclient` |
| Exported type | UpperCamelCase | `OrderService`, `PaymentGateway` |
| Unexported type | lowerCamelCase | `orderRepository`, `paymentClient` |
| Exported function | UpperCamelCase | `NewOrder()`, `ProcessPayment()` |
| Unexported function | lowerCamelCase | `validateOrder()`, `calculateTax()` |
| Exported field | UpperCamelCase | `OrderID`, `TotalAmount` |
| Unexported field | lowerCamelCase | `orderID`, `totalAmount` |
| Interface | UpperCamelCase, suffix `er` when single method | `Reader`, `Writer`, `Validator` |
| Constant | UpperCamelCase (Go convention) | `MaxRetryCount`, `DefaultTimeout` |
| Variable | lowerCamelCase | `totalAmount`, `err` |
| Acronym | all-uppercase or all-lowercase consistently | `HTTP`, `URL`, `ID`, `DB` |

### Conventions

- **Acronyms:** `HttpClient` → `HTTPClient`, `UrlParser` → `URLParser`. Entire acronym is uppercase (or lowercase if unexported).
- Keep package names short (1-2 words). No `_` in package names.
- `var` vs `:=`: use `:=` inside functions; `var` at package level or when zero-value is intentional.
- Error variables: `ErrNotFound`, `ErrInvalidInput`.
- Test helpers: prefix with `must` (e.g., `mustParseTime`, `mustCreateOrder`).
- No `get`/`set` prefix on field accessors — export the field directly or use `FieldName()`.

### File Naming

- `snake_case.go` — one primary type per file, named after the type.
- `{type}_test.go` for tests.
- `{type}_integration_test.go` for integration tests.

---

## Node.js / TypeScript

### Case Styles

| Element | Style | Example |
|---|---|---|
| File / directory | kebab-case | `order-service.ts`, `payment-handler.ts` |
| Class | UpperCamelCase | `OrderService`, `PaymentHandler` |
| Interface | UpperCamelCase, no `I` prefix | `OrderRepository`, `UserPayload` |
| Type alias | UpperCamelCase | `OrderStatus`, `ApiResponse` |
| Enum | UpperCamelCase (enum name), UPPER_SNAKE_CASE (members) | `OrderStatus { PENDING, SHIPPED }` |
| Function / Method | lowerCamelCase | `getOrderById()`, `processPayment()` |
| Variable | lowerCamelCase | `totalAmount`, `orderId` |
| Constant | lowerCamelCase (const) or UPPER_SNAKE_CASE (magic number) | `const maxRetries = 3` or `MAX_RETRIES` |
| Parameter | lowerCamelCase | `request`, `orderId` |
| Private member | lowerCamelCase, no `_` prefix | `#privateField` or `privateField` |
| React component | UpperCamelCase | `OrderList`, `PaymentForm` |
| React hook | `use` + UpperCamelCase | `useOrder`, `useAuth` |
| TypeScript file extension | `.ts` / `.tsx` | `order-service.ts` |
| Test file | `{name}.test.ts` or `{name}.spec.ts` | `order-service.test.ts` |

### Conventions

- **Imports:** Named imports for types, default imports for modules.
- Use `type` keyword for type-only imports: `import type { Order } from './order'`.
- Prefer `const` over `let` — `let` only when reassignment is required.
- No `any` — use `unknown` if type is truly indeterminate.
- Boolean props in React: `isLoading`, `hasError`, `canSubmit`.
- Event handlers: prefix with `handle` (`handleClick`, `handleSubmit`).

### Directory Structure

```
src/
  modules/
    order/
      order.service.ts
      order.controller.ts
      order.repository.ts
      order.model.ts
      order.test.ts
```

---

## Python

### Case Styles

| Element | Style | Example |
|---|---|---|
| Module / File | snake_case | `order_service.py`, `payment_handler.py` |
| Package | snake_case (no `__init__` magic) | `order_service`, `payment` |
| Class | UpperCamelCase | `OrderService`, `PaymentHandler` |
| Exception | UpperCamelCase + `Error` suffix | `OrderNotFoundError`, `InvalidInputError` |
| Function / Method | snake_case | `get_order_by_id()`, `process_payment()` |
| Variable | snake_case | `total_amount`, `order_id` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Private member | `_` prefix (single underscore) | `_validate_order()` |
| Name-mangled private | `__` prefix (double underscore) | `__internal_method()` |
| Type parameter | single uppercase letter | `T`, `R` |
| Enum member | UPPER_SNAKE_CASE | `PENDING`, `SHIPPED` |
| Test function | `test_` prefix | `test_calculate_total_with_no_items()` |
| Test class | `Test` prefix | `TestOrderService` |
| Fixture / pytest | snake_case | `order_factory`, `db_session` |

### Conventions

- Follow **PEP 8** strictly.
- Type hints are **required** for all public functions and methods.
- Return type annotation is always present: `def get_order(order_id: str) -> Order:`.
- No spacing around `=` for keyword arguments / defaults: `def func(arg: str = "default")`.
- Use `@dataclass` for data containers; `NamedTuple` for lightweight immutable records.
- Context managers for resource management (`with open(...)`).

---

## MySQL

### Database

| Element | Style | Example |
|---|---|---|
| Database name | `snake_case` | `order_service`, `payment_db` |
| Environment suffix | `_dev`, `_staging`, `_prod` | `order_service_dev` |

- Keep names short but descriptive.
- Use singular nouns for domain-oriented databases (`order_service`, not `orders_service`).

### Table

| Element | Style | Example |
|---|---|---|
| Table name | `snake_case` | `order`, `order_item`, `user_address` |
| Pluralization | **plural** (represents a set of records) | `orders`, `users`, `order_items` |
| Join table | both table names in alphabetical order | `order_product`, `user_role` |
| Temporal table | suffix `_history` | `order_history`, `user_audit` |

- No prefixes like `tbl_` or `tb_`.
- Avoid reserved words (`order`, `group`, `select`, `status`). If unavoidable, backtick-quote.

### Column

| Element | Style | Example |
|---|---|---|
| Column name | `snake_case` | `created_at`, `total_amount` |
| Primary key | `id` | `id` (every table must have one) |
| Foreign key | `{referenced_table_singular}_id` | `order_id`, `user_id` |
| Timestamp | `{action}_at` | `created_at`, `updated_at`, `deleted_at`, `processed_at` |
| Boolean | `is_` / `has_` / `can_` prefix | `is_active`, `is_deleted`, `is_verified` |
| Counter | `_count` suffix | `retry_count`, `login_count` |
| Money | `{name}_cents` (store as integer) | `price_cents`, `tax_cents` |
| Enum / status | `_status` suffix | `order_status`, `payment_status` |
| Type discriminator | `_type` suffix | `address_type`, `payment_type` |
| JSON / text payload | `_payload` suffix | `meta_payload`, `event_payload` |
| Flag | `_flag` suffix | `processed_flag`, `notify_flag` |

### Index

| Element | Style | Example |
|---|---|---|
| Primary key index | `PRIMARY` | (automatic) |
| Unique constraint | `uq_{table}_{column_list}` | `uq_user_email` |
| Non-unique index | `idx_{table}_{column_list}` | `idx_order_created_at` |
| Composite index | `idx_{table}_{col1}_{col2}` | `idx_order_user_id_created_at` |
| Full-text index | `ft_idx_{table}_{column}` | `ft_idx_product_name` |
| Partial / filtered index | append `_partial` | `idx_order_status_partial` |

### Naming Order

Columns that frequently appear together in queries should be ordered logically:

1. `id` (PK)
2. `{entity}_id` (FKs)
3. Business keys (`order_number`, `sku`)
4. Status / type discriminators
5. Numerical values / amounts
6. Text / content
7. Timestamps: `created_at`, `updated_at`, `deleted_at`

### SQL Convention

- **SQL keywords:** UPPERCASE (`SELECT`, `FROM`, `WHERE`, `JOIN`, `INSERT INTO`).
- Table aliases: short, meaningful (`o` for `orders`, `oi` for `order_items`).
- CTEs preferred over subqueries for readability.

```sql
SELECT o.id, o.total_amount, oi.product_name
FROM orders o
INNER JOIN order_items oi ON oi.order_id = o.id
WHERE o.created_at >= NOW() - INTERVAL 7 DAY
  AND o.order_status = 'SHIPPED'
ORDER BY o.created_at DESC;
```
