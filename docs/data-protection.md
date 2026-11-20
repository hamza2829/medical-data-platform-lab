# Standards and data protection note

FHIR resource JSON is stored as a typed resource with a `schema_version` column and an append-only version snapshot for every create or update. The demo profile is `1.0.0` and covers only the fields needed for the synthetic Patient, Observation and Device flows. It is not a substitute for a national FHIR implementation guide.

The sensor path accepts only known demo vital types, checks that both referenced Patient and Device resources exist, validates the numeric range, and stores the message as a FHIR R4 Observation. MQTT payloads are never written to logs. API audit events identify the actor and operation without duplicating clinical fields.

Researcher routes return pseudonymous Patient identities and rewritten Observation references; names, birth dates, addresses, contact details and identifiers are excluded. Pseudonymization uses an HMAC key configured through `PSEUDONYMIZATION_SALT` (or the Django secret key fallback), so use a separate strong secret in any non-demo deployment. Pseudonymized data may still be sensitive and remains subject to access controls.

The individual GDPR export and delete routes are demonstrations of API behavior. They do not verify the requester, satisfy every statutory requirement, define backups/retention, or prove compliance. This application is synthetic-only and must not be used to process real health information.
