# ACAT Submission Bundle

This repository is structured as an ACAT-ready submission bundle for an application to vary the termination date to 28 April 2026.

## Final bundle

The top level of this repository is reserved for the filing set:

- `00 – Statement – Application to Vary Termination Date.pdf`
- `01 – Index of Evidence (READ THIS FIRST).pdf`
- `Exhibit A – Rental Applications.pdf`
- `Exhibit B – Payment History & ACAT Compliance.pdf`
- `Exhibit C – Income & Financial Capacity.pdf`
- `Exhibit D – Autism Assessment Appointment.pdf`
- `Exhibit E – Medical Wait Times Evidence.pdf`
- `Exhibit F – Rental Ledger & Lease Documents.pdf`
- `Exhibit G – Supporting Communication.pdf`
- `Exhibit H – Exit Preparation Evidence.pdf`

## Source materials

Original evidence files are stored in:

- `source/original-evidence/`

The bundle generator script and editable text sources are stored in:

- `scripts/generate_acat_bundle.py`
- `bundle-src/statement.txt`
- `bundle-src/index.txt`

## Notes

- Exhibits `D`, `E`, and `H` are generated as placeholders if source evidence has not yet been provided.
- Replace those placeholders with actual documents before filing if you have the medical appointment confirmation, wait-time evidence, or exit-preparation records.

## Regenerate

Run:

```powershell
python scripts/generate_acat_bundle.py
```
