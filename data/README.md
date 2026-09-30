# Air Reconciliation Synthetic Dataset
Synthetic data for a deterministic corporate-air payment reconciliation prototype.
All values, IDs, airline names and tax amounts are mock/representative, not live airline data.

12 scenarios:
normal ticket; tax mismatch; normal exchange; exchange variance; full refund;
partial refund mismatch; void; duplicate settlement; ancillary charges; FX;
missing settlement; conflicting records.

Recommended flow:
1) normalize sources
2) classify lifecycle
3) calculate expected financial position
4) match components and totals
5) detect exceptions
6) create a case record for unresolved exceptions
7) later send only those cases to the agent.
