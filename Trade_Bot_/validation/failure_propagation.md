# Failure Propagation Validation

| Scenario | API failure | DB corrupt entries | Logs truthful | Result |
| --- | --- | --- | --- | --- |
| DB failure | True (500) | None written by failing store | Error surfaced | PASS |
| Invalid input | True (422) | No valid audit row created | Validation error surfaced | PASS |
| Partial internal failure | True (500) | Primary audit DB size unchanged: True | Exception logged by API path | PASS |

No failure scenario returned a success envelope, and no corrupt portfolio update was accepted.