# eQMS Architecture: GitHub-Native Quality Management System

This architecture defines a GitHub-native eQMS structure for biomedical engineering startups to achieve FDA 21 CFR 820 and ISO 13485 compliance.

## Repository Structure

```
eqms-template/
├── .github/
│   ├── workflows/           # GitHub Actions for compliance automation
│   │   ├── document-validation.yml    # Enforce naming/template compliance
│   │   ├── traceability-export.yml    # Generate traceability matrices
│   │   ├── compliance-check.yml       # Pre-merge compliance validation
│   │   └── pdf-export.yml             # Export controlled docs to PDF
│   ├── ISSUE_TEMPLATE/      # Templates for requirements, risks, tests
│   ├── PULL_REQUEST_TEMPLATE.md       # Standard PR approval workflow
│   └── CODEOWNERS           # Document ownership assignments
├── docs/
│   ├── design-controls/     # FDA 21 CFR 820.30 Design Controls
│   │   ├── requirements/    # Design inputs (user needs, intended use)
│   │   ├── specifications/  # Design outputs (device specs, drawings)
│   │   ├── verification/    # Design verification protocols/reports
│   │   ├── validation/      # Design validation protocols/reports
│   │   └── risk-management/ # ISO 14971 risk analysis files
│   ├── quality-system/      # QMS procedures and SOPs
│   │   ├── document-control/   # Document control procedures
│   │   ├── change-control/     # Change control procedures
│   │   ├── training/           # Training records and procedures
│   │   └── management-review/  # Management review records
│   ├── device-master-record/   # FDA 21 CFR 820.181 DMR
│   │   ├── device-specifications/
│   │   ├── production-procedures/
│   │   ├── quality-assurance/
│   │   └── labeling/
│   └── templates/           # Document templates for consistency
├── scripts/                 # Automation utilities
│   ├── traceability-matrix.py    # Generate requirement traceability
│   ├── compliance-report.py      # Export compliance packages
│   └── document-validator.py     # Validate document completeness
├── config/
│   ├── compliance-rules.yml      # Validation rules for documents
│   ├── traceability-mapping.yml  # Issue linking rules
│   └── export-settings.yml       # PDF generation settings
└── README.md               # Setup and usage instructions
```

## Component Interactions & Data Flow

### GitHub Native Components

**Document Control Flow:**
- `docs/*` → PR Creation → CODEOWNERS Review → Branch Protection → Merge → Immutable History

**Approval Workflow:**
- Author creates PR → Reviewers assigned via CODEOWNERS → Required approvals → Merge = Approval Record

**Traceability Flow:**
- GitHub Issues (Requirements) → Linked PRs (Design) → Linked Issues (Verification) → Automated Matrix Export

**Change Control:**
- Document Change → PR with Justification → Impact Assessment → Review → Approval → Merge

## GitHub Actions Workflows

### 1. Document Validation (`document-validation.yml`)
**Triggers**: PR to main, push to docs/
**Functions**:
- Validate file naming conventions
- Check template completeness
- Verify required metadata
- Enforce regulatory mapping

### 2. Traceability Export (`traceability-export.yml`)
**Triggers**: Weekly schedule, manual dispatch
**Functions**:
- Parse GitHub Issues for requirements
- Map issues to PRs and commits
- Generate traceability matrix
- Export to PDF for submissions

### 3. Compliance Check (`compliance-check.yml`)
**Triggers**: PR review, pre-merge
**Functions**:
- Verify all required documents present
- Check approval status
- Validate document relationships
- Block merge if non-compliant

### 4. PDF Export (`pdf-export.yml`)
**Triggers**: Release creation, manual dispatch
**Functions**:
- Export controlled documents to PDF
- Include git history and signatures
- Package for regulatory submission
- Archive with timestamps

## Document Types & Ownership

### Design Controls (CODEOWNERS assignments)
- **Requirements**: @product-manager @regulatory-affairs
- **Specifications**: @lead-engineer @design-team
- **Verification**: @test-engineer @quality-assurance
- **Validation**: @clinical-affairs @regulatory-affairs
- **Risk Management**: @risk-manager @quality-assurance

### Quality System
- **SOPs**: @quality-manager @regulatory-affairs
- **Training**: @hr-manager @quality-assurance
- **Change Control**: @change-control-board

## Issue Templates & Linking

### Requirement Issues
- Template: User need, intended use, acceptance criteria
- Labels: `requirement`, `design-input`
- Links to: Design specification PRs

### Risk Issues  
- Template: Hazard, harm, risk analysis
- Labels: `risk`, `iso-14971`
- Links to: Mitigation design PRs

### Verification Issues
- Template: Test protocol, acceptance criteria
- Labels: `verification`, `testing`
- Links to: Requirement issues, test results

## Compliance Automation

### Pre-merge Checks
- Document template compliance
- Required reviewer approval
- Traceability link validation
- Regulatory mapping verification

### Audit Trail Generation
- Git history = change record
- PR reviews = approval evidence  
- Issue links = traceability evidence
- Action logs = process evidence

### Export Capabilities
- Design History File (DHF) package
- Device Master Record (DMR) export
- Traceability matrix reports
- Compliance summary dashboards

## Integration Points

**GitHub Issues ↔ Requirements**: All requirements tracked as issues with standardized templates

**Pull Requests ↔ Document Control**: All document changes go through PR approval process

**CODEOWNERS ↔ Document Ownership**: File-level ownership enforces review requirements

**Actions ↔ Compliance**: Automated validation ensures regulatory compliance before merge

**Git History ↔ Audit Trail**: Immutable change history provides audit evidence