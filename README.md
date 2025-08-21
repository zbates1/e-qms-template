# eQMS Template: GitHub-Native Quality Management System

A GitHub-native electronic Quality Management System (eQMS) for biomedical engineering startups achieving FDA 21 CFR 820 and ISO 13485 compliance.

## Quick Start Guide

### 🎯 Where to Start Based on Your Role & Project Phase

#### **New Product Development / Early Prototyping**
**Start here:** `DHF/01_UserNeeds.md` → `DHF/02_DesignInputs/`
- Define user needs and intended use
- Document design inputs (requirements)
- Set up initial risk analysis in `RMF/`
- **Next steps:** Move to design outputs and verification planning

#### **Research & Development / Proof of Concept**  
**Start here:** `experiments/` folder
- Create date-stamped experiment folder (e.g., `2025-08-19_your-experiment/`)
- Use `premortem.md` for planning
- Document daily work in `notes.md`
- **Next steps:** Transition findings to formal DHF when moving to product development

#### **Design Changes / Product Updates**
**Start here:** `DHF/05_RiskManagement/` → `DHF/02_DesignInputs/`
- Assess impact on existing risk analysis
- Update design inputs if requirements change
- Follow change control process via GitHub PRs
- **Next steps:** Update verification/validation as needed

#### **Manufacturing Transfer / Production**
**Start here:** `DHF/08_DesignTransfer/DMR_index.md`
- Review Device Master Record completeness
- Verify all design controls complete
- Set up process controls in `SPC/`
- **Next steps:** Link to ERP systems and manufacturing processes

#### **Testing & Verification**
**Start here:** `DHF/06_Verification/test_protocols/`
- Review existing test protocols
- Execute tests and document in `test_reports/`
- Update traceability matrix using `scripts/traceability-matrix.py`
- **Next steps:** Proceed to validation if verification complete

#### **Validation & Clinical**
**Start here:** `DHF/07_Validation/`
- Plan clinical or user validation studies
- Document validation protocols and reports
- **Next steps:** Prepare for regulatory submission

#### **Quality System Setup / SOPs**
**Start here:** `QMS/` folder
- Review and customize SOPs for your organization
- Set up document control procedures
- Configure GitHub workflows in `.github/`
- **Next steps:** Train team on procedures and tools

#### **Regulatory Submission Prep**
**Start here:** `scripts/compliance-report.py`
- Generate traceability matrices
- Export compliance packages
- Review completeness using validation scripts
- **Next steps:** Package DHF for submission

### 📁 Repository Structure

```
eqms-template/
│
├─ .github/                        # CI for docs, compliance validation
│
├─ QMS/                            # Company‑wide quality backbone
│   ├─ SOP‑001_DocumentControl.md
│   ├─ SOP‑002_DesignControl.md
│   ├─ SOP‑003_RiskManagement.md
│   ├─ SOP‑004_DOE‑QbD.md          # governs DoE/Quality‑by‑Design plans
│   ├─ SOP‑005_SPC.md              # governs Statistical Process Control rules
│   ├─ SOP‑006_ERP_Interfaces.md   # how DHF/DMR link to SAP
│   ├─ Registers/
│   │   ├─ DOC‑STD‑001_ApplicableStandards.xlsx
│   │   └─ DOC‑REG‑001_SAP_ObjectMap.xlsx
│   └─ Templates/
│       ├─ DoE_plan_template.xlsx
│       ├─ DesignReview_minutes.md
│       └─ DV_Report_template.md
│
├─ DHF/                            # Design History File  (product record)
│   ├─ 01_UserNeeds.md
│   ├─ 02_DesignInputs/
│   │   ├─ PRD.md
│   │   └─ SRS.md
│   ├─ 03_DesignOutputs/
│   │   ├─ electronics.bom
│   │   ├─ pcb_revA.sch
│   │   └─ mech/
│   ├─ 04_DoE‑QbD/                 # NEW – experiments that inform design space
│   │   ├─ DoE_001_mixshear.xlsx
│   │   └─ design_space_map.ipynb
│   ├─ 05_RiskManagement/          # (number bumps if you keep both 04 folders)
│   │   └─ hazard_analysis.xlsx
│   ├─ 06_Verification/
│   │   ├─ test_protocols/
│   │   └─ test_reports/
│   ├─ 07_Validation/
│   ├─ 08_DesignTransfer/
│   │   ├─ DMR_index.md            # Device Master Record
│   │   └─ manufacturing_files/
│   └─ 09_DesignReviews/           # signed PDF minutes + actions
│       └─ DR_2025‑09‑30_revA.pdf
│
├─ RMF/                            # Risk Management File (living)
│   ├─ risk_log.xlsx
│   └─ premortems/
│
├─ SPC/                            # Process‑control evidence (linked to SAP routings)
│   ├─ control_charts/
│   │   ├─ syringe_pressure_Xbar.png
│   └─ spc_scripts/                # Jupyter / Python that generate charts
│
├─ ERP/                            # Integration stubs / exported IDs
│   ├─ sap_bom_export_2025‑09‑28.xlsx
│   └─ sap_routing_003.xml
│
├─ experiments/                    # ELN — raw data & daily logs
│   └─ 2025‑09‑12_ink‑rheology/
│       ├─ premortem.md
│       ├─ notes.md                # daily log
│       └─ DV_Report.md            # summary in DV‑report style
│
├─ scripts/                        # Automation & validation tools
│   ├─ traceability-matrix.py      # Generate requirement traceability
│   ├─ compliance-report.py        # Export compliance packages  
│   └─ document-validator.py       # Validate document completeness
│
├─ docs/                           # Dev (Sphinx) & User (MkDocs) sites
│
├─ src/  |  cad/                   # code, CAD
└─ released/                       # frozen DHF + RMF bundles at each review
```

### 🔧 Essential Commands

**Validate documents:** `python scripts/document-validator.py`
**Generate traceability:** `python scripts/traceability-matrix.py`  
**Export compliance package:** `python scripts/compliance-report.py`
**Run tests:** Check specific test files in root directory

### 📋 Workflow Overview

1. **All changes** go through GitHub Pull Request approval process
2. **Document ownership** enforced via CODEOWNERS file
3. **Automated validation** via GitHub Actions on every PR
4. **Traceability** maintained through GitHub Issues and PR linking
5. **Audit trail** preserved in git history for regulatory compliance
