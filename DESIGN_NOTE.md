# System Design & Architecture Decisions

This note reviews the engineering design decisions, database normalization tradeoffs, access control expansions, and security requirements necessary for deploying this service into a production environment.

---

## 1. Database Schema Selection & Normalization Tradeoffs
The schema models four primary relational structures: `Users`, `Sessions`, `Evaluations`, and a `ParentStudent` mapping table. 

To support the requirement that parents can only view their own child's sessions, we extended the user roles to include a `"student"` role and separated parent-student mappings into a specialized association table. This preserves **Third Normal Form (3NF)**:
*   It avoids adding redundant, nullable `parent_id` fields inside the `Users` table itself, preventing empty columns for teacher or admin accounts.
*   It enables a parent to have multiple children (and vice versa, supporting multi-parent households) without altering core user tables.

**Tradeoff**: This normalization requires an additional join/query against the `parent_students` table on the session read paths, introducing slight read latency. However, for a take-home scale and standard transactional platforms, the structural integrity and prevention of update anomalies far outweigh the sub-millisecond query overhead.

---

## 2. RBAC Adaptability

### Adding a Fourth Role
The system utilizes a modular `RoleChecker` dependency. Introducing a fourth role (e.g., a `"student"` or `"school_admin"`) is straightforward:
1. Add the role name to the allowed role set in the `UserCreate` Pydantic validator.
2. Update path annotations (e.g., `Depends(RoleChecker(["admin", "teacher", "school_admin"]))`).
If role complexity grows, we would transition from hardcoded role strings to a **Role-Permissions mapping table** (storing roles and specific actions) to decouple permissions from users.

### Supporting Nested Organizations
In nested hierarchies (e.g., School District ➔ School ➔ Department ➔ Classroom), strict role comparisons break down. To solve this:
1. Introduce an `organizations` table with a self-referential `parent_id` to build a directed tree structure.
2. Link `Users` and `Sessions` to an `organization_id` column.
3. The authorization dependency would query recursively (using SQL CTEs) to ensure a user's organizational node is an ancestor of the requested session's organizational node.

---

## 3. Production Readiness Gaps
For this service to be production-safe, the following components must be implemented:
*   **Alembic Migrations**: The database tables are currently generated implicitly. In production, Alembic migrations must manage the state of the schema, run in CI pipelines, and execute via `alembic upgrade head` inside the container startup script.
*   **Secret Management**: Secrets are stored in `.env`. Production environments should pull credentials dynamically from secure storage engines like HashiCorp Vault, AWS Secrets Manager, or Google Secret Manager.
*   **HTTPS/TLS**: Direct FastAPI exposure is vulnerable. A reverse proxy (e.g., Nginx, Traefik, or AWS ALB) should sit in front to handle TLS termination (HTTPS) and route traffic safely.
*   **Structured Logging & Monitoring**: Replace standard logging with structured JSON logs and integrate an APM tool (e.g., Sentry for exceptions, Prometheus & Grafana for system health and request rates).
*   **Rate Limiting**: Protect endpoints against DDoS/brute-force attacks using Redis-based rate limiting (such as `slowapi` or Nginx rate limits).
*   **Automated Backups**: Configure scheduled daily snapshots and point-in-time recovery (PITR) for the PostgreSQL database.
