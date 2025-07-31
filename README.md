project-root/
│
├─ .github/                        # CI for docs, SPC data lints, towncrier …
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
├─ docs/                           # Dev (Sphinx) & User (MkDocs) sites
│
├─ src/  |  cad/                   # code, CAD
└─ released/                       # frozen DHF + RMF bundles at each review
