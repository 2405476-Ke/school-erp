# Security Remediation: Breaking Changes Implementation Plan

## Analysis of the Copilot Report
Your Copilot agent has successfully cleared the immediate technical debt (Hybrid Path executed successfully!). The pipeline is green, unit tests pass, and the low-hanging dependency vulnerabilities are resolved.

The remaining blocker for a completely clean SAST/Security Audit is the outdated high-risk dependencies: `fastify`, `@fastify/http-proxy`, `@fastify/jwt`, and `bcrypt`. Upgrading these involves **breaking changes**, which is why the agent paused.

## Strategic Recommendation
**Prioritize the structural security upgrades over TypeScript warnings.**

TypeScript `any` warnings do not cause runtime vulnerabilities. Outdated `fastify` and `bcrypt` packages *do* cause failed SOC 2 Penetration Tests and SAST audits.

You should direct your Copilot to execute the **Fastify Stack** and **Bcrypt Major Upgrade** tracks.

---

## The Execution Plan (Instructions for Copilot)

Copy and paste this exact strategic plan back to your Copilot agent so it can systematically execute the breaking changes without taking down the pipeline.

### Phase 1: Fastify Stack Breaking-Change Tranche

**Agent Instructions:**
1.  **Isolate:** Create a new local feature branch (e.g., `feat/fastify-security-upgrade`).
2.  **Upgrade Root:** Run the major version upgrades for the Fastify ecosystem in `services/api-gateway` and any other utilizing microservices:
    `npm install fastify@latest @fastify/http-proxy@latest @fastify/jwt@latest`
3.  **Remediate Breaking API Changes:** 
    *   Review the Fastify v4 to v5 (or relevant version) migration guide.
    *   Update any customized error handlers, plugin registrations (`fastify.register`), or logging implementations that broke during the upgrade in `services/api-gateway/src/index.ts`.
4.  **Test:** Run `npm run test:all` specifically watching the Gateway integration tests to ensure proxy routing and JWT validation via OPA policies still function.

### Phase 2: Bcrypt Native Build & Runtime Tranche

**Agent Instructions:**
1.  **Upgrade:** Run `npm install bcrypt@6` (or latest major) in `services/auth-service`.
2.  **Environment Check:** `bcrypt` requires node-gyp and native C++ build tools depending on the Node runtime environment. 
3.  **Dockerfile Verification:** Open `services/auth-service/Dockerfile`. Ensure that the builder image stage has the necessary compilation tools installed (e.g., `apk add --no-cache python3 make g++` if using Alpine) before the `npm install` runs, otherwise the container build will fail in CI.
4.  **Test:** Ensure unit tests covering password hashing algorithms (even if only used as fallback to WebAuthn) pass correctly.

### Phase 3: Validation and PR Creation

**Agent Instructions:**
1.  Run the full hybrid pipeline locally: Lint, Tests, and SAST Audit.
2.  Once `npm audit` shows 0 High/Critical vulnerabilities for these specific packages, stop.
3.  Do **NOT** proceed to the TypeScript warning hardening yet. Present the diff summary for these breaking network/crypto changes first.
