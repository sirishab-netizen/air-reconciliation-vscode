# Air Reconciliation Prototype

A VS Code/Python starter project for a deterministic corporate-air payment reconciliation engine. The agentic exception-investigation layer will be added later.

## Architecture

```text
Bookings / Tickets / Ticket Lines / Invoices / Settlements / Refunds / Exchanges / FX
                                      |
                                      v
                                Normalization
                                      |
                                      v
                           Lifecycle classification
                                      |
                                      v
                         Deterministic reconciliation
                                      |
                         +------------+------------+
                         |                         |
                     RECONCILED                EXCEPTION
                                                   |
                                                   v
                                             Case record
                                                   |
                                            Agent later
```

## Scenarios in the dataset

1. Normal ticket
2. Tax mismatch
3. Normal exchange
4. Exchange variance
5. Full refund
6. Partial refund mismatch
7. Void with settlement
8. Duplicate settlement
9. Ancillary charges
10. FX
11. Missing settlement
12. Conflicting records

All financial values, IDs, airline names and tax amounts are synthetic/representative.

## VS Code setup

### 1. Open the project

Open this folder in VS Code:

```text
air-reconciliation-vscode/
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

macOS/Linux/WSL:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

### 3. Run tests

```bash
pytest -q
```

### 4. Run the first reconciliation demo

```bash
python -m reconciliation.demo
```

## Design principle

The deterministic engine should prove what it can using explicit rules and source records. It should create an exception case when evidence is missing, conflicting, or requires investigation. Do not send the whole monthly dataset to an LLM.
