# Deletion Runbook

Deleting a source immediately:

1. marks it `deleting`;
2. clears its active version so retrieval cannot select it;
3. marks artifact evidence links `missing`;
4. deletes document versions, chunks, vectors, and ingestion jobs;
5. removes the local object; and
6. marks the source record `deleted` for lifecycle evidence.

The application does not claim immediate erasure from infrastructure-provider
backups. Providers or local backups may retain encrypted historical copies
according to their retention policy.

Drive revocation removes the encrypted refresh token from the private schema
and calls Google's revocation endpoint. It does not delete the original file.
