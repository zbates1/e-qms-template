# Product Requirements: GitHub-based eQMS

## Vision & Goal
A GitHub-native electronic Quality Management System (eQMS) for biomedical engineering startups.  
This system provides FDA 21 CFR 820 and ISO 13485 compliant workflows for document control, approvals, traceability, and submission readiness, without requiring expensive QMS software.  
Primary users: founders, engineers, regulatory affairs staff, and quality managers at early-stage medtech startups.

---

## Key Features & User Stories with Regulatory Mapping

### 1. Document Management & Version Control
- **User Story**: As a startup founder, I want all design and risk documents version-controlled so that every change is timestamped and auditable.
- **Implementation**: GitHub repos with PRs and branches. GitHub Actions enforce naming conventions and file organization.
- **Regulatory Mapping**:
  - FDA 21 CFR 820.40 (Document Controls)
  - ISO 13485:2016 §4.2.4 (Control of Documents)

---

### 2. Approval Workflows & e-Signatures
- **User Story**: As a regulatory affairs lead, I want documented approvals for every controlled document.
- **Implementation**: GitHub PR reviews = approval gates. CODEOWNERS enforce mandatory reviewers. Optional GitHub Apps for e-signatures (21 CFR Part 11 alignment).
- **Regulatory Mapping**:
  - FDA 21 CFR 11.200 (Electronic Signatures)
  - FDA 21 CFR 820.40 (Document Approval & Distribution)
  - ISO 13485:2016 §4.2.5 (Control of Records)

---

### 3. Traceability & Change Control
- **User Story**: As a quality manager, I want automated traceability reports to include in a 510(k) submission.
- **Implementation**: GitHub Issues link requirements → design → verification → risk files. GitHub Actions export traceability matrix.
- **Regulatory Mapping**:
  - FDA 21 CFR 820.30 (Design Controls)
  - ISO 13485:2016 §7.3.2–7.3.7 (Design & Development Planning, Inputs, Outputs, Verification, Validation, Changes)

---

### 4. FDA/ISO Compliance Enforcement
- **User Story**: As a startup, I want to export a compliance package from GitHub to accelerate regulatory submissions.
- **Implementation**: GitHub Actions enforce template completeness before merge. Automated PDF export of controlled docs + change history.
- **Regulatory Mapping**:
  - FDA 21 CFR 820.70 (Production & Process Controls)
  - FDA 21 CFR 820.181 (Device Master Record)
  - FDA 21 CFR 820.184 (Device History Record)
  - ISO 13485:2016 §4.2.3 (Medical Device File)

---

### 5. Collaboration & Ownership
- **User Story**: As a project manager, I want to assign owners to each SOP and track review progress.
- **Implementation**: CODEOWNERS file assigns ownership. GitHub Issues & labels for review status ("In Draft," "Under Review," "Approved").
- **Regulatory Mapping**:
  - FDA 21 CFR 820.25 (Personnel)
  - FDA 21 CFR 820.40 (Document Distribution & Responsibility)
  - ISO 13485:2016 §6.2 (Human Resources / Responsibilities & Authorities)

---

## Non-Functional Requirements
- 100% GitHub-native (repos, Actions, Issues, PRs, CODEOWNERS).
- Data integrity: all changes timestamped & immutable via git history.
- Scalability: support multiple projects/repos for modular DHF/Technical File organization.
- Security: enforce branch protections, required reviews, and repository access controls.

---

## Compliance Note
This system is designed to align with:
- **FDA 21 CFR Part 11 & 820**
- **ISO 13485:2016**
for document control, design history files, traceability, and electronic signatures.  
While GitHub provides the infrastructure, compliance depends on proper SOPs, training, and audit trails configured by the organization.
