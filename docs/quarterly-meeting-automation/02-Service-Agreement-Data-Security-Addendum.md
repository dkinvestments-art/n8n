# SERVICE AGREEMENT WITH DATA SECURITY ADDENDUM

## Professional Services Agreement for Workflow Automation Development

**Effective Date:** _______________

**Agreement Number:** _______________

---

## PARTIES

**Client ("Firm"):**
- Company Name: _______________
- Address: _______________
- Primary Contact: _______________
- Email: _______________

**Service Provider ("Developer"):**
- Company/Individual Name: _______________
- Address: _______________
- Primary Contact: _______________
- Email: _______________

---

## PART 1: SERVICE AGREEMENT

### 1. SCOPE OF SERVICES

#### 1.1 Project Description
The Developer shall design, build, and deliver workflow automation systems
using n8n and related tools to automate the Firm's quarterly client meeting
preparation process, as described in the Developer Requirements Specification
(attached or referenced separately).

#### 1.2 Deliverables
The Developer shall deliver the following:

| # | Deliverable | Format |
|---|------------|--------|
| 1 | n8n workflow JSON exports (all workflows) | `.json` files |
| 2 | Google Sheets tax calculation templates | Google Sheets / `.xlsx` |
| 3 | Google Docs/Slides meeting agenda templates | Google Docs / Slides |
| 4 | Client profile matrix template | Google Sheets |
| 5 | Setup and configuration guide | Markdown / PDF |
| 6 | API connection documentation | Markdown / PDF |
| 7 | Training / walkthrough recording | Video (Loom or similar) |
| 8 | Troubleshooting and FAQ document | Markdown / PDF |

#### 1.3 Out of Scope
The following are explicitly outside the scope of this engagement:
- (a) Accessing the Firm's production systems or client data
- (b) Connecting workflows to live client accounts
- (c) Tax return preparation or tax advice of any kind
- (d) Ongoing system administration or maintenance (unless separately agreed)
- (e) Data migration or cleanup in QBO or other systems

---

### 2. DEVELOPMENT METHODOLOGY

#### 2.1 Sandbox-Only Development
**All development and testing shall be performed exclusively in sandbox
and test environments.** The Developer shall:

- (a) Use Intuit's QBO Developer Sandbox for all QuickBooks-related development
- (b) Use test/dummy Google Workspace accounts for Google integrations
- (c) Use fabricated, synthetic data that does not correspond to any real person
  or business entity
- (d) Operate their own n8n instance (self-hosted or cloud) for development
- (e) Never request, access, or store actual client data from the Firm

#### 2.2 No Production Access
The Developer shall NOT have access to:
- The Firm's production n8n instance
- The Firm's QuickBooks Online accounts or any client QBO accounts
- The Firm's Karbon, payroll software, or GoHighLevel accounts
- The Firm's Google Workspace (production)
- Any client financial data, tax returns, or personally identifiable information

#### 2.3 Handoff Process
Upon completion of each deliverable:
1. Developer exports the workflow/template from their sandbox environment
2. Developer delivers the export files to the Firm via secure transfer
3. The Firm imports the deliverables into their own production environment
4. The Firm connects their own API credentials
5. The Firm tests with real data independently
6. Developer provides support via screen share (Firm shares screen;
   Developer does not access Firm systems directly)

---

### 3. PROJECT TIMELINE AND MILESTONES

| Phase | Description | Duration | Milestone |
|-------|------------|----------|-----------|
| 1 | Requirements review and design | Week 1-2 | Architecture document approved |
| 2 | Core workflow build (API clients) | Week 3-4 | QBO + payroll auto-pull workflows delivered |
| 3 | Adaptive workflows (non-API clients) | Week 4-5 | Document intake + email request workflows delivered |
| 4 | Tax calculation + scorecard engine | Week 5-6 | Google Sheets templates delivered |
| 5 | Meeting prep output (agenda, slides) | Week 6-7 | Output templates delivered |
| 6 | Documentation and handoff | Week 7-8 | All documentation and training delivered |
| 7 | Support and iteration | Week 8-10 | Bug fixes, adjustments |

---

### 4. COMPENSATION

#### 4.1 Fee Structure
- [ ] **Fixed Price:** $_______________
- [ ] **Hourly Rate:** $_______________ per hour, not to exceed _____ hours
- [ ] **Milestone-Based:** (see schedule below)

#### 4.2 Milestone Payment Schedule (if applicable)

| Milestone | % of Total | Amount | Due Upon |
|-----------|-----------|--------|----------|
| Project kickoff | 25% | $_____ | Signing of this agreement |
| Phase 2 delivery | 25% | $_____ | Approval of core workflows |
| Phase 5 delivery | 25% | $_____ | Approval of all templates |
| Final handoff | 25% | $_____ | Completion of documentation and training |

#### 4.3 Payment Terms
Invoices are due within ___ days of receipt. Late payments accrue interest
at ___% per month.

---

### 5. INTELLECTUAL PROPERTY

#### 5.1 Work Product Ownership
All deliverables created under this Agreement are **works made for hire** and
shall be the sole property of the Firm upon full payment. This includes:
- All n8n workflow files and configurations
- All templates, formulas, and layouts
- All documentation created for this project
- Any custom code or scripts developed for this project

#### 5.2 Developer's Pre-Existing IP
The Developer retains ownership of any tools, frameworks, libraries, or
methodologies that existed prior to this engagement. To the extent any
pre-existing IP is incorporated into the deliverables, the Developer grants
the Firm a perpetual, non-exclusive, royalty-free license to use such IP
as part of the delivered workflows.

#### 5.3 Open Source
If any open-source components are used, the Developer shall document all
open-source licenses and confirm compatibility with the Firm's intended use.

---

### 6. WARRANTIES AND REPRESENTATIONS

The Developer warrants that:
- (a) The deliverables shall function substantially as described in the
  requirements specification
- (b) The Developer has the skills, experience, and authority to perform
  the services
- (c) The deliverables will not infringe upon any third-party intellectual
  property rights
- (d) The Developer will comply with all applicable laws, including but not
  limited to data protection and privacy laws

---

### 7. LIMITATION OF LIABILITY

#### 7.1 Cap
The Developer's total liability under this Agreement shall not exceed the
total fees paid by the Firm under this Agreement.

#### 7.2 Exception
The liability cap in Section 7.1 shall NOT apply to:
- (a) Breaches of confidentiality (governed by the NDA)
- (b) Unauthorized disclosure of tax return information (governed by IRC 7216)
- (c) Breaches of the Data Security Addendum (Part 2 of this Agreement)
- (d) Willful misconduct or gross negligence

---

### 8. TERMINATION

#### 8.1 Termination for Convenience
Either party may terminate this Agreement with thirty (30) days' written
notice. The Firm shall pay for all work completed through the termination date.

#### 8.2 Termination for Cause
Either party may terminate immediately upon written notice if the other party:
- (a) Materially breaches this Agreement and fails to cure within fifteen
  (15) days of written notice
- (b) Breaches any confidentiality or data security obligation (no cure period)
- (c) Becomes insolvent or files for bankruptcy

#### 8.3 Effect of Termination
Upon termination:
- Developer delivers all completed and in-progress work product to the Firm
- Developer destroys all Firm Confidential Information per the NDA
- Surviving provisions: Sections 5, 6, 7, and the Data Security Addendum

---

## PART 2: DATA SECURITY ADDENDUM

### 9. PURPOSE AND REGULATORY CONTEXT

This Addendum establishes data security requirements for the Developer in
recognition of the Firm's obligations under:

- **IRC Section 7216** — Criminal penalties for unauthorized disclosure of
  tax return information
- **Gramm-Leach-Bliley Act (GLBA)** — Requires financial institutions
  (including tax preparers) to protect customer financial information
- **FTC Safeguards Rule (16 CFR Part 314)** — Requires assessment of
  third-party service provider security
- **IRS Publication 4557** — Safeguarding taxpayer data guidelines
- **State data breach notification laws** — Applicable state requirements

---

### 10. IRS COMPLIANCE: AVOIDING 7216 DISCLOSURE

#### 10.1 Primary Strategy: No Disclosure, No 7216 Trigger

The parties agree that the **primary and preferred approach** is to structure
the engagement so that no tax return information (as defined in IRC 7216 and
Treasury Regulation 301.7216-1) is ever disclosed to the Developer.

This is accomplished through:

**(a) Synthetic Data Development**
- The Developer builds and tests all workflows using only fabricated,
  synthetic data that does not correspond to any real taxpayer
- Synthetic data shall be clearly marked as "TEST DATA - NOT REAL"
- Synthetic data shall use obviously fake names (e.g., "Jane Testclient"),
  fake EINs (e.g., 00-0000000), and fabricated financial figures

**(b) Sandbox Environment Isolation**
- All development occurs in isolated sandbox environments
- Intuit QBO Developer Sandbox (developer.intuit.com) for QuickBooks workflows
- Separate test Google accounts for Google Workspace integrations
- Developer's own n8n instance, completely separate from Firm's production

**(c) Credential Separation**
- The Developer never possesses or uses production API credentials
- All API credentials for real client accounts are entered by the Firm
  after handoff
- Sandbox API credentials are separate from production credentials

**(d) Screen Share Protocol**
- During any troubleshooting or support calls, the Firm shares their screen
- The Developer does not remotely access the Firm's systems
- If client data is visible during screen sharing, the Firm is responsible
  for redacting or minimizing exposure
- Screen sharing sessions shall not be recorded by the Developer

**(e) Communication Sanitization**
- All bug reports, change requests, and communications from the Firm to the
  Developer shall be sanitized of client data
- Screenshots shared with the Developer must have client names, numbers,
  and identifiers redacted
- The Firm may use sample/dummy data to illustrate issues

#### 10.2 Secondary Strategy: Anonymized/De-Identified Data

If the Firm determines that limited real data structures (not content) would
improve development quality, the following de-identification protocol may
be used:

**(a) Acceptable De-Identified Data**
- QBO chart of accounts structure (account names only, no balances)
- Transaction category lists (no amounts, dates, or payee names)
- Report column headers and field layouts
- Workflow trigger conditions (e.g., "when description contains X")

**(b) De-Identification Requirements**
- All personally identifiable information must be removed
- All financial amounts must be replaced with fabricated figures
- All dates must be shifted by a random offset
- All names (individuals, businesses) must be replaced with fictitious names
- De-identified data must not be re-identifiable through any combination
  of remaining fields

**(c) When This Approach Is Used**
- The Firm documents the specific data elements shared and the de-identification
  steps taken
- The de-identified data is transmitted via encrypted channel
- The Developer destroys the de-identified data when no longer needed

#### 10.3 Tertiary Strategy: 7216 Consent (Last Resort Only)

If, despite best efforts, the Developer must access actual tax return
information to resolve a critical issue:

**(a) Pre-Conditions**
- The Firm documents why synthetic/de-identified data is insufficient
- The Firm's managing partner approves the disclosure in writing
- The affected client(s) sign a 7216 consent form (see NDA Exhibit A)

**(b) Consent Requirements (per Rev. Proc. 2013-14)**
- Consent must be in writing
- Consent must identify the specific taxpayer data to be disclosed
- Consent must name the Developer as the recipient
- Consent must describe the purpose of the disclosure
- Consent must state the date it expires
- Consent must inform the taxpayer that they may decline

**(c) Limitations**
- Only the minimum necessary data shall be disclosed
- The Developer shall access the data only during supervised sessions
- The Developer shall not retain copies of the data
- The Firm shall log the disclosure (date, data elements, purpose, duration)

**(d) Expected Usage: Rare to Never**
This option exists as a safety valve. The Firm's goal is to complete the
entire engagement without ever triggering this section.

---

### 11. TECHNICAL SECURITY REQUIREMENTS

#### 11.1 Developer Environment Security
The Developer shall maintain the following security controls:

| Control | Requirement |
|---------|------------|
| Encryption at rest | AES-256 or equivalent for all stored project files |
| Encryption in transit | TLS 1.2+ for all data transfers |
| Access control | Multi-factor authentication on all development systems |
| Device security | Full-disk encryption on development machines |
| Network security | Secure/private network for development (no public WiFi for project work) |
| Antivirus/EDR | Current endpoint protection on all development machines |
| Patching | Operating systems and development tools kept current |

#### 11.2 n8n Instance Security (Developer's Sandbox)
- n8n instance shall be password-protected with a strong, unique password
- If cloud-hosted, the instance shall be hosted with a reputable provider
  (e.g., n8n Cloud, AWS, GCP, Azure, DigitalOcean)
- If self-hosted, the instance shall not be exposed to the public internet
  without authentication
- Workflow execution logs shall not contain real client data

#### 11.3 File Transfer Security
All deliverables shall be transferred via:
- Encrypted email attachment (password communicated separately), OR
- Secure cloud storage link (Google Drive with restricted access,
  expiring link), OR
- Version control (private GitHub/GitLab repository with access controls)

Deliverables shall NOT be transferred via:
- Unencrypted email
- Public file sharing links
- USB drives or physical media (unless encrypted)
- Chat messages (Slack, Teams, Discord, etc.) for files containing
  any configuration details

---

### 12. INCIDENT RESPONSE

#### 12.1 Notification
If the Developer becomes aware of or reasonably suspects any:
- Unauthorized access to Confidential Information
- Data breach involving any project-related data
- Loss or theft of devices containing project files
- Unauthorized disclosure of any information covered by this Agreement

The Developer shall notify the Firm within **twenty-four (24) hours** of
discovery via phone and email to the Firm's designated contact.

#### 12.2 Cooperation
The Developer shall:
- Cooperate fully with the Firm's investigation
- Preserve all relevant logs and evidence
- Assist with notification to affected parties if required
- Implement remedial measures as directed by the Firm

#### 12.3 Costs
The Developer shall bear all costs arising from a security incident caused
by the Developer's failure to comply with this Addendum.

---

### 13. AUDIT AND VERIFICATION

#### 13.1 Right to Audit
The Firm may, upon reasonable notice, request evidence that the Developer
is complying with this Addendum. Evidence may include:
- Screenshots of security configurations (with sensitive details redacted)
- Written attestation of compliance
- Confirmation that no real client data is present in development systems

#### 13.2 Annual Certification
If the engagement exceeds twelve (12) months, the Developer shall provide
an annual written certification of compliance with this Addendum.

---

### 14. FIRM'S RESPONSIBILITIES

The Firm acknowledges its own obligations:

#### 14.1 WISP Maintenance
The Firm shall maintain a Written Information Security Plan (WISP) as required
by IRS Publication 4557 and GLBA, and shall update it to reflect this
third-party engagement.

#### 14.2 Credential Management
The Firm is solely responsible for:
- Entering and managing all production API credentials
- Securing access to production systems (QBO, Rippling, Karbon, etc.)
- Ensuring that production credentials are never shared with the Developer

#### 14.3 Data Sanitization
When communicating with the Developer, the Firm is responsible for:
- Redacting client data from screenshots and communications
- Using synthetic examples when describing issues
- Not accidentally sharing real client data in support conversations

#### 14.4 Post-Handoff Security
After importing workflows into production, the Firm is responsible for:
- Securing their n8n instance with appropriate access controls
- Encrypting stored credentials within n8n's credential manager
- Monitoring workflow execution logs for sensitive data exposure
- Restricting access to the n8n instance to authorized personnel only

---

## SIGNATURES

**Firm:**

Signature: ___________________________

Printed Name: ___________________________

Title: ___________________________

Date: ___________________________

**Developer:**

Signature: ___________________________

Printed Name: ___________________________

Title: ___________________________

Date: ___________________________

---

*This agreement is a template and should be reviewed by a qualified attorney
before execution. Tax compliance provisions should be reviewed by a tax
professional familiar with IRC Section 7216 and GLBA requirements.*
