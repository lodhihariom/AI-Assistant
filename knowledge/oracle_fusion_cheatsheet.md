# Oracle Fusion Applications (ERP / SCM / HCM) — integration cheat sheet

Original notes (not copied from Oracle docs). REST version strings and job names change by release; verify in the REST API and FBDI guides.

## Ways to integrate with Fusion
| Need | Typical tool |
|---|---|
| Bulk inbound (financials, SCM) | **FBDI**: CSV zip -> UCM -> ESS jobs |
| Bulk inbound (HCM) | **HDL** (HCM Data Loader) `.dat` files in a zip |
| Real-time create/update/read | **REST APIs** or **SOAP services** |
| Outbound reports/extracts | **BI Publisher (BIP)** reports, **OTBI**, ESS extracts, REST GET |
| Events | **Business events** (subscribe from OIC) |
| Manual mass edits | **ADFdi** spreadsheets, FSM CSV/config packages |

## REST API basics
- Base paths: `/fscmRestApi/resources/<version>/...` (financials/SCM), `/hcmRestApi/resources/<version>/...` (HCM), `/crmRestApi/resources/<version>/...` (CX). `latest` can be used instead of a version while testing.
- Query params: `q` (filter, e.g. `q=InvoiceNumber='INV-1'`), `limit`, `offset`, `fields`, `orderBy`, `onlyData=true`, `expand` (child resources), `totalResults=true`.
- Response: `items`, `count`, `hasMore`, `offset`, `limit`, `links`.
- POST/PATCH use `Content-Type: application/vnd.oracle.adf.resourceitem+json`; custom actions use `application/vnd.oracle.adf.action+json`.
- The `REST-Framework-Version` header controls framework behaviour (higher versions give cleaner responses).
- Child resources are separate URLs (e.g. invoice -> `child/invoiceLines`).
- Auth: Basic (dev/test), or OAuth/JWT via the identity service for production.
- Lookups: HCM exposes `commonLookups` (with a `lookupCodes` child) and `commonLookupsLOV`; FSCM has its own lookup resources. Pagination matters when a lookup type has many codes.

## ERP Integration Service (bulk data)
- SOAP: `/fscmService/ErpIntegrationService?WSDL`. REST: `.../erpintegrations` (POST with `OperationName`).
- Key operations: `uploadFileToUCM`, `importBulkData` (upload + load + import in one call), `submitESSJobRequest`, `getESSJobStatus`, `exportBulkData`, `getESSJobExecutionDetails`, `downloadESSJobExecutionDetails`.
- `loadAndImportData` is deprecated; use `importBulkData`.
- Files go to a **UCM account** per product area (names look like `fin$/payables$/import$`). The FBDI template's *Instructions* tab lists the right account, ESS job names and parameters — copy them from there.
- Payload content is Base64 of the zip file. Notification code and callback URL are optional.

## FBDI flow
1. Download the FBDI `.xlsm` template for the object (invoices, journals, items, POs...).
2. Fill the sheet, generate CSV(s), zip them.
3. Upload to UCM with the correct account and security group.
4. Run **Load Interface File for Import** (loads CSV into interface tables).
5. Run the **import job** for the module (e.g. Import Payables Invoices, Import Journals).
6. Check the job output/log and the interface tables or error reports for rejected rows.
- Most FBDI problems: wrong column order, date format, missing required columns, wrong UCM account, user without access to that account, or referencing IDs/names that do not exist (ledger, business unit, supplier site).

## UCM / ESS notes
- ESS jobs: Scheduled Processes in the UI; submit through ERP Integration Service from outside.
- Statuses: SUCCEEDED, ERROR, WARNING, RUNNING, WAIT, CANCELLED. Poll with `getESSJobStatus` or use callbacks.
- Download job logs/output for the real error text; the status alone is not enough.

## SOAP services
- Services live under `/fscmService/...`, `/hcmService/...`, `/crmService/...`. WSDL is the service URL with `?WSDL`.
- Typical failure causes: wrong namespace/prefix, ID-based fields where a name is expected (or vice versa) leading to "no data found"-style faults, missing role on the integration user.

## HCM Data Loader (HDL)
- `.dat` files with METADATA and MERGE lines per business object; zipped and loaded via the Data Exchange UI, UCM, or the HCM REST `dataLoadDataSets` resource.
- Use the HDL spreadsheet/templates and the object definitions to get attribute names right. Load order matters (parents before children).

## BI Publisher (BIP) and OTBI
- **BIP data model**: SQL data sets (read-only against Fusion), parameters, LOVs, triggers limited in SaaS; report layouts in RTF/XLSX/ExcelTemplate; output CSV/XML/PDF/Excel.
- Run reports from OIC via the report web services (e.g. `PublicReportService` `runReport`: report path, parameters, output format); the result comes back Base64.
- Programmatic creation of data models/reports is possible via catalog web services (create folder, upload report objects).
- **OTBI**: analyses/dashboards over subject areas (e.g. Payables Invoices - Transactions Real Time, Payables Invoices - Holds Real Time). "Real Time" subject areas read live transactional data. Use calculated columns (formulas) for things like aging buckets.
- For high-volume extraction prefer BIP/ESS extracts over OTBI.

## Useful Payables/Procurement tables (read in BIP, not to modify)
`AP_INVOICES_ALL`, `AP_INVOICE_LINES_ALL`, `AP_INVOICE_DISTRIBUTIONS_ALL`, `AP_HOLDS_ALL`, `AP_PAYMENT_SCHEDULES_ALL`, `POZ_SUPPLIERS`, `POZ_SUPPLIER_SITES_ALL_M`, `PO_HEADERS_ALL`, `PO_LINES_ALL`, `RCV_SHIPMENT_HEADERS`, `GL_JE_HEADERS`, `GL_JE_LINES`, `GL_CODE_COMBINATIONS`, `HZ_PARTIES`, `PER_ALL_PEOPLE_F`, `PER_ALL_ASSIGNMENTS_M`. Date-tracked tables need `SYSDATE BETWEEN effective_start_date AND effective_end_date`.

## Habits that save time
- Reproduce an issue first with Postman/SOAP UI, then build it in OIC.
- Always capture full error payloads (HTTP status + response body).
- Check the integration user's roles before debugging payloads.
- Test in a lower environment; sandbox/metadata context headers exist for customizations.
