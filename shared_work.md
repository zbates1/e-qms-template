# Shared Work

This file coordinates the collaborative work of all AI agents on the project.

## 1. Goal

Build a GitHub-native eQMS template with automated compliance workflows, document templates, traceability automation, and CODEOWNERS structure for FDA 21 CFR 820 and ISO 13485 compliance.

---

## 2. To-Do List

**Task Statuses:**
- `- [ ] T###: Task Name` (Available)
- `- [WIP:AgentName] T###: Task Name` (Work in Progress - **CLAIMED**)
- `- [x] T###: Task Name` (Completed)

### GitHub Actions Workflows
- [x] T001: Create .github/workflows/document-validation.yml enforcing naming conventions and template compliance
- [x] T002: Create .github/workflows/traceability-export.yml generating automated traceability matrices from Issues/PRs
- [x] T003: Create .github/workflows/compliance-check.yml for pre-merge validation of document relationships
- [WIP:Kyle] T004: Create .github/workflows/pdf-export.yml for controlled document export with git history

### Document Templates & Structure
- [ ] T005: Create .github/ISSUE_TEMPLATE/ with requirement.md, risk.md, verification.md templates
- [ ] T006: Create .github/PULL_REQUEST_TEMPLATE.md for standard approval workflow
- [ ] T007: Create docs/templates/ with design-input.md, design-output.md, verification-protocol.md templates
- [ ] T008: Create docs/design-controls/ directory structure with placeholder files
- [ ] T009: Create docs/quality-system/ directory structure with SOP templates
- [ ] T010: Create docs/device-master-record/ directory structure

### Automation Scripts
- [ ] T011: Create scripts/traceability-matrix.py parsing GitHub Issues and generating requirement traceability
- [ ] T012: Create scripts/compliance-report.py exporting compliance packages for regulatory submission
- [ ] T013: Create scripts/document-validator.py validating document completeness and relationships

### Configuration & Control Files
- [ ] T014: Create .github/CODEOWNERS with document ownership assignments per architecture
- [ ] T015: Create config/compliance-rules.yml defining validation rules for documents
- [ ] T016: Create config/traceability-mapping.yml defining Issue linking rules
- [ ] T017: Create config/export-settings.yml for PDF generation settings

### Extended QMS Structure (Your Current Layout)
- [ ] T018: Create QMS/ directory with SOPs (DocumentControl, DesignControl, RiskManagement, DOE-QbD, SPC, ERP_Interfaces)
- [ ] T019: Create QMS/Registers/ with DOC-STD-001_ApplicableStandards.xlsx and DOC-REG-001_SAP_ObjectMap.xlsx templates
- [ ] T020: Create QMS/Templates/ with DoE_plan_template.xlsx, DesignReview_minutes.md, DV_Report_template.md
- [ ] T021: Create DHF/ structure with numbered directories (01_UserNeeds through 09_DesignReviews)
- [ ] T022: Create DHF/04_DoE-QbD/ for experiments and design_space_map.ipynb template
- [ ] T023: Create RMF/ with risk_log.xlsx template and premortems/ directory
- [ ] T024: Create SPC/ with control_charts/ and spc_scripts/ for statistical process control
- [ ] T025: Create ERP/ integration directory with SAP export templates
- [ ] T026: Create experiments/ directory structure for ELN with premortem.md and notes.md templates
- [ ] T027: Create released/ directory for frozen DHF+RMF bundles at design reviews

---

## 3. Action Log

[Manager Agent | 2025-08-18 15:00] Action: Created product_requirements.md and architecture.md. Next: T001.
[Kyle | 2025-08-18 15:05] Action: Claimed T002 traceability-export workflow. Next: T002.
[Kyle | 2025-08-18 15:15] Action: Completed T002 traceability-export workflow. Next: T004.
[Kyle | 2025-08-18 15:16] Action: Claimed T004 PDF export workflow. Next: T004.
[Isaac | 2025-08-18 19:25] Action: Completed T001 document-validation workflow with scripts/document-validator.py. Next: T005.
[Greta | 2025-08-18 19:30] Action: Completed T003 compliance-check workflow with validation scripts. Next: T005.