# Oracle Integration Cloud (OIC) — practical cheat sheet

Original notes (not copied from Oracle docs). Details change between releases, so confirm exact names in the docs for your version.

## Integration styles
- **App Driven Orchestration**: triggered by an inbound call (REST/SOAP/event). Most common for API-style flows.
- **Scheduled Orchestration**: runs on a schedule or on demand; used for polling FTP, batch jobs, periodic syncs. Has schedule parameters.
- **Basic Routing / File Transfer / Publish-Subscribe**: simpler or older styles; check which ones your instance still offers.

## Building blocks
- **Connection**: adapter + endpoint URL + security policy (Basic, OAuth, JWT, API key). Test it before activating anything that uses it. Use a connectivity agent for on-prem systems.
- **Trigger / Invoke**: the first action receives the request, invokes call out to other systems.
- **Mapper**: drag-and-drop XSLT. Use it for field mapping, functions (string, date, math), conditions (`xsl:if`/`choose`), and loops over repeating elements.
- **Actions**: Assign, Switch, For-Each, While, Scope, Wait, Notification, Log, Stage File, Call Function (JavaScript library), Throw New Fault, Stop, Return/Reply.
- **Lookups**: key/value tables for code translation between systems. Use `lookupValue(...)` in the mapper.
- **Libraries**: JavaScript functions for logic the mapper cannot do cleanly (date formatting, string cleanup, CSV helpers).
- **Integration properties / tracking fields / business identifiers**: make instances searchable in Monitoring.

## Patterns that come up constantly
### REST pagination (While loop)
1. Assign `offset = 0`, `limit = 100`, `hasMore = true`.
2. While `$hasMore = true`: invoke REST GET with `limit` and `offset`.
3. Process `items` (For-Each), then set `hasMore` from the response `hasMore` field and `offset = offset + limit`.
4. Guard against infinite loops (max iterations).
Fusion REST returns `items`, `count`, `hasMore`, `offset`, `limit`, `links`.

### Large files
- Use **Stage File** (Read File in Segments) instead of reading the whole file into memory.
- Keep payloads small in orchestration; pass file references, not content.
- Typical file flow: poll SFTP -> download -> stage -> parse/transform -> write CSV -> zip -> hand to target.

### Fusion bulk load (FBDI) from OIC
1. Build CSV (column order must match the FBDI template).
2. Zip it (Stage File "Zip files").
3. ERP Cloud adapter: **Import Bulk Data into Oracle ERP Cloud** (uploads to UCM, runs the Load Interface File for Import job, then the import job) or the separate Send Files + Submit ESS job request.
4. Track job: callback, or poll the ESS request status.
5. On failure, fetch the ESS job logs/output and surface the real error.

### Error handling
- Put risky steps inside a **Scope** with its own fault handler; use **Catch All** or specific fault handlers.
- A **Global Fault Handler** is the last safety net (send notification, log, rethrow).
- Distinguish **business faults** (bad data, 4xx) from **technical faults** (timeouts, 5xx). Retry only technical ones.
- The fault object exposes error code, reason and details; log all three.
- Use **Throw New Fault** to return a clean error to callers.
- In Monitoring you can resubmit failed instances (when the integration allows it) — design idempotently.

## Mapper and XSLT tips
- When a target element repeats, map the source repeating node to the target's repeating element (creates the for-each).
- Empty vs missing elements behave differently on the target. Use conditions so you don't send blank values that override data.
- Namespaces matter when using `xsl:value-of` manually; prefer the mapper UI.
- For debugging: add a Log or Assign step to capture intermediate values, and look at the Activity Stream.

## Monitoring and operations
- **Track Instances**: find a run by business identifier, view payloads (if tracing enabled), see where it failed.
- **Errors** page: failed instances, resubmit/abort.
- **Activity stream**: step-by-step execution view.
- Activation errors usually come from connections: not tested, wrong credentials, missing agent, or an endpoint that is unreachable. Re-test connections first.

## DevOps
- Export/import integrations as `.iar` packages; group related integrations in **Packages**.
- Versioning: identifier + version (e.g. 01.00.0000). Identifier cannot change after creation.
- OIC exposes REST APIs for integrations, connections, lookups, monitoring, so you can script deployment.

## Security
- Prefer OAuth 2.0 / JWT where possible; keep secrets in connections, never in assign steps or logs.
- Integration user in Fusion needs the right roles/privileges for the services you call (REST resource, ESS, UCM/security group). "Not authorized" usually means a missing role, not a wrong URL.
