---
title: Pharmacokinetic Models in Critical Care
summary: Mathematical models and parameters for drug disposition in critically ill patients.
---

# Pharmacokinetic Models in Critical Care

## Population Pharmacokinetics

### Volume of Distribution Changes

**Pathophysiological Alterations in Critical Illness:**
- Increased vascular permeability leads to expanded extracellular volume
- Fluid resuscitation further increases volume of distribution
- Hypoalbuminemia affects protein binding of drugs
- Organ dysfunction alters tissue distribution patterns

**Clinical Implications:**
- Loading doses may need adjustment for hydrophilic drugs
- Steady-state concentrations achieved later
- Monitoring becomes more critical for narrow therapeutic index drugs

### Clearance Modifications

**Hepatic Clearance:**
- Reduced hepatic blood flow in shock states
- Cytochrome P450 enzyme downregulation in inflammation
- Competition for metabolic pathways with endogenous substrates

**Renal Clearance:**
- Acute kidney injury affects drug elimination
- Continuous renal replacement therapy alters clearance patterns
- Filtration fraction changes with hemodynamic instability

## Vasopressor Pharmacokinetics

### Norepinephrine
**Distribution:**
- Volume of distribution: 8.8 L (single-pass pulmonary extraction)
- Protein binding: 25% to plasma proteins
- Tissue uptake: Rapid via neuronal and extraneuronal mechanisms

**Metabolism:**
- Primary pathway: Catechol-O-methyltransferase (COMT)
- Secondary pathway: Monoamine oxidase (MAO)
- Active metabolites: Normetanephrine, vanillylmandelic acid

**Elimination:**
- Clearance: 2.2 L/min (primarily hepatic)
- Half-life: 2-3 minutes (rapid redistribution)
- Renal excretion: <3% unchanged drug

### Epinephrine
**Pharmacokinetic Parameters:**
- Bioavailability: 100% (IV), variable (subcutaneous)
- Volume of distribution: 2.8 L/kg
- Clearance: 3.2 L/min
- Half-life: 2-3 minutes

**Special Considerations:**
- Rapid tissue uptake and metabolism
- Significant first-pass pulmonary extraction
- Stress-dose effects in critical illness

### Vasopressin
**Distribution Characteristics:**
- Volume of distribution: 0.2 L/kg (small, primarily intravascular)
- Protein binding: Negligible
- Receptor binding: High affinity V1a receptors

**Elimination:**
- Clearance: 9.7 mL/min/kg
- Half-life: 10-35 minutes (dose-dependent)
- Metabolism: Hepatic and renal
- Active metabolites: None clinically significant

## Dose-Response Relationships

### Norepinephrine Dose-Response
**Low Dose (0.01-0.1 mcg/kg/min):**
- Primarily beta-1 effects
- Mild increase in cardiac output
- Minimal vasoconstriction

**Moderate Dose (0.1-0.5 mcg/kg/min):**
- Balanced alpha and beta effects
- Increased MAP and cardiac output
- Therapeutic range for most patients

**High Dose (>0.5 mcg/kg/min):**
- Predominantly alpha effects
- Risk of peripheral ischemia
- Consider additional agents

### Epinephrine Dose-Response
**Low Dose (0.01-0.1 mcg/kg/min):**
- Beta-2 mediated vasodilation
- Increased cardiac output
- May decrease MAP initially

**High Dose (>0.1 mcg/kg/min):**
- Alpha effects predominate
- Significant vasoconstriction
- Increased cardiac work and oxygen consumption

## Therapeutic Drug Monitoring

### Direct Monitoring
- **Real-time hemodynamic response:** MAP, cardiac output
- **Tissue perfusion markers:** Lactate, ScvO₂, urine output
- **Adverse effect monitoring:** ECG, peripheral circulation

### Biomarker Correlation
- **Catecholamine levels:** Limited clinical utility due to rapid metabolism
- **Metabolite levels:** Research applications for dose optimization
- **Pharmacogenomic markers:** CYP2D6, COMT polymorphisms

## Model-Based Dosing

### Population Pharmacokinetic Models
**Norepinephrine in Sepsis:**
- Typical clearance: 39.4 L/h/70kg
- Interpatient variability: 45% CV
- Covariates: Body weight, severity of illness

**Vasopressin Population Model:**
- Clearance: 0.58 L/h/kg
- Volume: 0.2 L/kg
- Covariates: Creatinine clearance, albumin

### Bayesian Dosing Approaches
- **Prior information:** Population parameters
- **Individual data:** Patient-specific covariates and response
- **Posterior estimation:** Personalized parameters for optimal dosing

## Special Populations

### Renal Dysfunction
- **Norepinephrine:** No dose adjustment needed (hepatic metabolism)
- **Vasopressin:** Prolonged half-life, consider dose reduction
- **CRRT effects:** Minimal drug removal due to high protein binding

### Hepatic Dysfunction
- **Reduced clearance:** All catecholamines affected
- **Prolonged half-life:** Monitor for accumulation
- **Alternative agents:** Consider vasopressin as first-line

### Pediatric Considerations
- **Weight-based dosing:** Use actual body weight for calculations
- **Developmental pharmacology:** Immature enzyme systems
- **Dosing ranges:** Often require higher weight-based doses

## Future Directions

### Precision Medicine Applications
- **Pharmacogenomic testing:** CYP450 polymorphisms
- **Biomarker-guided therapy:** Troponin, natriuretic peptides
- **Machine learning models:** Predictive dosing algorithms

### Novel Monitoring Technologies
- **Continuous cardiac output monitoring:** Non-invasive techniques
- **Microcirculation assessment:** Sublingual capillaroscopy
- **Tissue oxygen monitoring:** Near-infrared spectroscopy
