# Quarterly Client Meeting Preparation — Automation Project

## Document Index

This folder contains all documentation needed to engage a third-party
developer to build the quarterly meeting preparation automation system.

### Legal & Compliance Documents

| Document | Purpose | Share with Developer? |
|----------|---------|----------------------|
| [01 — NDA](./01-NDA-Third-Party-Developer.md) | Non-Disclosure Agreement with 7216-aware protections | Yes — sign before project begins |
| [02 — Service Agreement](./02-Service-Agreement-Data-Security-Addendum.md) | Service contract + Data Security Addendum | Yes — sign before project begins |
| [04 — IRS Compliance Guide](./04-IRS-Compliance-Guide.md) | Internal guide for maintaining 7216/GLBA compliance | No — internal reference only |

### Technical Documents

| Document | Purpose | Share with Developer? |
|----------|---------|----------------------|
| [03 — Developer Requirements Spec](./03-Developer-Requirements-Specification.md) | Complete technical specification and SOW | Yes — primary development reference |
| [05 — Comprehensive Workflow Documentation](./05-Comprehensive-Workflow-Documentation.md) | Full process documentation with visual diagrams | Yes — reference for understanding the system |

## Engagement Sequence

1. **Both parties sign** documents 01 (NDA) and 02 (Service Agreement)
2. **Share** documents 03 and 05 with the Developer
3. **Keep** document 04 internal — follow its guidance throughout
4. **Developer builds** in sandbox per the requirements spec
5. **Firm imports** deliverables and connects production credentials
6. **Firm validates** with real client data independently

## IRS Compliance Strategy Summary

This engagement uses a **three-tier compliance approach** designed so that
no client 7216 consent forms are needed under normal circumstances:

- **Strategy 1 (Default):** Developer uses only synthetic/sandbox data.
  No tax return information is disclosed. No 7216 triggered.
- **Strategy 2 (Fallback):** If real data patterns are needed, the Firm
  provides de-identified data with all PII and financial figures removed.
- **Strategy 3 (Last Resort):** If actual client data is required, obtain
  7216 consent from the affected client first.

See [04 — IRS Compliance Guide](./04-IRS-Compliance-Guide.md) for full details.
