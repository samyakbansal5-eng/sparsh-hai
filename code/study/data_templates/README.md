# Data templates (fill these during the studies - one row per trial)

| File | Study | Filled by |
|---|---|---|
| P1_tactile_discrimination.csv | Pilot P1 – can the 7 candidate shapes be told apart by touch? | Member 4 (experimenter) + Member 2 |
| A_identification_trials.csv | Study A – tactile caps vs plain board (RQ2) | Member 4 + Member 5 (timer) |
| B_onboarding_manual.csv | Study B condition A (manual paper mapping) | Member 3 |
| (app log) study/logs/study_B_sessions.csv | Study B condition B (AI-assisted) – written automatically by the app in Study Mode | app |
| C_generalisation_trials.csv | Study C – unseen layout transfer (RQ3) | Member 4 |
| questionnaires.csv | SUS, NASA-TLX (raw), trust items, confidence | Member 4 |
| interviews_log.csv | Stakeholder interviews (Phase 1) | Member 4 |

Rules: participant IDs only (V01.. visually impaired, C01.. caregivers, S01.. sighted pilot).
`group` must be one of: VI_blind, VI_low_vision, sighted_blindfold_pilot, caregiver.
Never mix sighted pilot rows into VI analyses - analysis.py keeps them separate automatically.
