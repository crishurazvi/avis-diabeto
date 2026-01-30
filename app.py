import streamlit as st
import datetime

# ==========================================
# 0. CONFIGURARE & STILIZARE
# ==========================================
st.set_page_config(
    page_title="ADA/EASD 2022 Diabetes Architect",
    page_icon="🧬",
    layout="wide"
)

# CSS
st.markdown("""
    <style>
    .action-stop { border-left: 6px solid #d9534f; background-color: #fff5f5; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
    .action-start { border-left: 6px solid #28a745; background-color: #f0fff4; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
    .action-switch { border-left: 6px solid #007bff; background-color: #eef7ff; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
    .action-alert { border-left: 6px solid #ffc107; background-color: #fffbf0; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
    .citation { font-size: 0.85em; color: #666; font-style: italic; margin-top: 5px; }
    .med-card { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .paper { background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; font-family: 'Georgia', serif; line-height: 1.6; color: #333; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. BAZA DE DATE (COMPENDIU)
# ==========================================
MED_DETAILS = {
    "Metformin": {"efficacy": "High", "hypo": "No", "weight": "Neutral", "cv_effect": "Potential Benefit", "hf_effect": "Neutral", "renal_effect": "Neutral", "cost": "Low", "clinical": ["Troubles digestifs", "Acidose lactique rare", "Déficit B12"]},
    "SGLT2 Inhibitors": {"efficacy": "Intermediate", "hypo": "No", "weight": "Loss", "cv_effect": "Benefit (MACE)", "hf_effect": "Benefit (Major)", "renal_effect": "Benefit (DKD)", "cost": "High", "clinical": ["Mycoses génitales", "DKA euglycémique", "Hypotension"]},
    "GLP-1 RAs": {"efficacy": "High/Very High", "hypo": "No", "weight": "Loss (High)", "cv_effect": "Benefit (MACE)", "hf_effect": "Neutral", "renal_effect": "Benefit (Albuminuria)", "cost": "High", "clinical": ["Nausées/Vomissements", "Contre-ind: MEN2", "Rétinopathie (rapide)"]},
    "GIP/GLP-1 RA": {"efficacy": "Very High", "hypo": "No", "weight": "Loss (Very High)", "cv_effect": "Investigation", "hf_effect": "Investigation", "renal_effect": "Investigation", "cost": "High", "clinical": ["Nausées", "Efficacité maximale"]},
    "DPP-4 Inhibitors": {"efficacy": "Intermediate", "hypo": "No", "weight": "Neutral", "cv_effect": "Neutral", "hf_effect": "Neutral", "renal_effect": "Neutral", "cost": "High", "clinical": ["Bien toléré", "Douleurs articulaires"]},
    "Sulfonylureas": {"efficacy": "High", "hypo": "Yes", "weight": "Gain", "cv_effect": "Neutral", "hf_effect": "Neutral", "renal_effect": "Neutral", "cost": "Low", "clinical": ["Hypoglycémie", "Prise de poids"]},
    "Thiazolidinediones": {"efficacy": "High", "hypo": "No", "weight": "Gain", "cv_effect": "Potential Benefit", "hf_effect": "Risk (Edema)", "renal_effect": "Neutral", "cost": "Low", "clinical": ["Insuffisance Cardiaque", "Fractures"]},
    "Insulin": {"efficacy": "Highest", "hypo": "Yes", "weight": "Gain", "cv_effect": "Neutral", "hf_effect": "Neutral", "renal_effect": "Neutral", "cost": "Variable", "clinical": ["Hypoglycémie", "Lipodystrophies"]}
}

# ==========================================
# 2. LOGICĂ ALGORITM (Română & Franceză)
# ==========================================

# A. Logica Originală (Română) pentru Tab 1
def generate_plan_ro(meds, hba1c, target, egfr, bmi, ascvd, hf, ckd, age):
    plan = [] 
    simulated_meds = meds.copy()
    
    # 1. SAFETY
    if "Metformin" in simulated_meds:
        if egfr < 30:
            plan.append({"type": "STOP", "text": "OPRIȚI Metformin", "reason": "Contraindicație: eGFR < 30 ml/min.", "ref": "Table 1"})
            simulated_meds.remove("Metformin")
        elif egfr < 45:
            plan.append({"type": "ALERT", "text": "Reduceți doza Metformin", "reason": "Ajustare necesară eGFR 30-45.", "ref": "Clinical Considerations"})

    if "SGLT2i" in simulated_meds and egfr < 20:
        plan.append({"type": "STOP", "text": "STOP SGLT2i", "reason": "Inițiere nerecomandată eGFR < 20.", "ref": "DAPA-CKD criteria"})
        simulated_meds.remove("SGLT2i")

    if "Thiazolidinediones" in simulated_meds and hf:
        plan.append({"type": "STOP", "text": "OPRIȚI TZD", "reason": "Risc de agravare HF.", "ref": "Table 1"})
        simulated_meds.remove("Thiazolidinediones")
        
    if "DPP-4 Inhibitors" in simulated_meds and (("GLP-1 RAs" in simulated_meds) or ("GIP/GLP-1 RA" in simulated_meds)):
        plan.append({"type": "STOP", "text": "OPRIȚI DPP-4i", "reason": "Redundanță terapeutică cu GLP-1/GIP.", "ref": "Principles of Care"})
        simulated_meds.remove("DPP-4 Inhibitors")

    # 2. ORGAN PROTECTION
    if hf and "SGLT2i" not in simulated_meds and egfr >= 20:
        plan.append({"type": "START", "text": "INIȚIAȚI SGLT2i", "reason": "Beneficiu Major: Heart Failure.", "ref": "Fig 3"})
        simulated_meds.append("SGLT2i")
    
    if ckd and "SGLT2i" not in simulated_meds and egfr >= 20:
        plan.append({"type": "START", "text": "INIȚIAȚI SGLT2i", "reason": "Beneficiu Major: Progresia DKD.", "ref": "Fig 3"})
        simulated_meds.append("SGLT2i")

    if ascvd:
        has_protection = any(x in simulated_meds for x in ["SGLT2i", "GLP-1 RAs", "GIP/GLP-1 RA"])
        if not has_protection:
            plan.append({"type": "START", "text": "INIȚIAȚI GLP-1 RA sau SGLT2i", "reason": "Beneficiu MACE dovedit.", "ref": "Fig 3"})
            if bmi > 27: simulated_meds.append("GLP-1 RAs")
            else: simulated_meds.append("SGLT2i")

    # 3. GLYCEMIC GAP
    gap = hba1c - target
    if gap > 0:
        if "Metformin" not in simulated_meds and egfr >= 30:
            plan.append({"type": "START", "text": "ADĂUGAȚI Metformin", "reason": "Prima linie.", "ref": "Table 1"})
            simulated_meds.append("Metformin")
        elif bmi >= 30 and not any(x in simulated_meds for x in ["GLP-1 RAs", "GIP/GLP-1 RA", "SGLT2i"]):
             plan.append({"type": "START", "text": "ADĂUGAȚI GLP-1/GIP", "reason": "Managementul greutății.", "ref": "Weight Management"})
        elif "DPP-4 Inhibitors" in simulated_meds and gap > 0.5:
             plan.append({"type": "SWITCH", "text": "Switch DPP-4i -> GLP-1 RA", "reason": "Eficacitate superioară.", "ref": "Comparative Efficacy"})
        elif "Insulin" not in simulated_meds and not any(x in simulated_meds for x in ["GLP-1 RAs", "GIP/GLP-1 RA"]):
             plan.append({"type": "START", "text": "INIȚIAȚI GLP-1 RA (pre-Insulină)", "reason": "Recomandat înainte de insulină.", "ref": "Fig 5"})

    return plan

# B. Logica Franceză (Pentru Scrisoarea Medicală) - Generează fraze medicale
def generate_french_actions(meds, hba1c, target, egfr, bmi, ascvd, hf, ckd):
    actions = []
    simulated_meds = meds.copy()
    
    # 1. SÉCURITÉ
    if "Metformin" in simulated_meds:
        if egfr < 30:
            actions.append("- **ARRÊT Metformine** : Contre-indication absolue (DFG < 30 ml/min).")
            simulated_meds.remove("Metformin")
        elif egfr < 45:
            actions.append("- **Ajustement posologique Metformine** : Réduire la dose (DFG 30-45 ml/min).")

    if "SGLT2 Inhibitors" in simulated_meds and egfr < 20:
        actions.append("- **ARRÊT iSGLT2** : DFG < 20 ml/min (Efficacité glycémique réduite).")
        simulated_meds.remove("SGLT2 Inhibitors")
        
    if "DPP-4 Inhibitors" in simulated_meds and (("GLP-1 RAs" in simulated_meds) or ("GIP/GLP-1 RA" in simulated_meds)):
        actions.append("- **ARRÊT iDPP-4** : Redondance thérapeutique avec l'agoniste GLP-1.")
        simulated_meds.remove("DPP-4 Inhibitors")

    # 2. PROTECTION D'ORGANE
    if hf and "SGLT2 Inhibitors" not in simulated_meds and egfr >= 20:
        actions.append("- **INITIATION iSGLT2 (Dapagliflozine/Empagliflozine)** : Indication formelle pour l'Insuffisance Cardiaque (Grade A).")
        simulated_meds.append("SGLT2 Inhibitors")
    
    if ckd and "SGLT2 Inhibitors" not in simulated_meds and egfr >= 20:
        actions.append("- **INITIATION iSGLT2** : Néphroprotection recommandée pour ralentir la progression de la MRC.")
        simulated_meds.append("SGLT2 Inhibitors")

    if ascvd:
        has_protection = any(x in simulated_meds for x in ["SGLT2 Inhibitors", "GLP-1 RAs", "GIP/GLP-1 RA"])
        if not has_protection:
            rec = "aGLP-1" if bmi > 27 else "iSGLT2"
            actions.append(f"- **INITIATION {rec}** : Prévention secondaire cardiovasculaire (MACE).")

    # 3. INTENSIFICATION
    gap = hba1c - target
    if gap > 0:
        if bmi >= 30 and not any(x in simulated_meds for x in ["GLP-1 RAs", "GIP/GLP-1 RA"]):
             actions.append("- **Optimisation Pondérale** : Considérer l'ajout d'un agoniste GLP-1 ou Tirzepatide (Bénéfice perte de poids).")
        elif "DPP-4 Inhibitors" in simulated_meds:
             actions.append("- **SWITCH thérapeutique** : Remplacer iDPP-4 par aGLP-1 (Efficacité supérieure).")
        elif "Insulin" not in simulated_meds and not any(x in simulated_meds for x in ["GLP-1 RAs", "GIP/GLP-1 RA"]):
             actions.append("- **Intensification** : Introduction d'un aGLP-1 avant d'envisager l'insulinothérapie basale.")
    
    if not actions and hba1c <= target:
        actions.append("- **Maintien du traitement actuel** : Objectifs atteints.")
        
    return actions

# ==========================================
# 3. INTERFAȚĂ PRINCIPALĂ
# ==========================================

# INPUT SIDEBAR
st.sidebar.title("🧬 Données Cliniques")
age = st.sidebar.number_input("Vârsta", 18, 100, 62)
weight = st.sidebar.number_input("Greutate (kg)", 40, 250, 98)
height = st.sidebar.number_input("Înălțime (cm)", 100, 240, 175)
bmi = weight / ((height/100)**2)
st.sidebar.markdown(f"**BMI:** {bmi:.1f}")

hba1c = st.sidebar.number_input("HbA1c (%)", 4.0, 18.0, 8.5, step=0.1)
target_a1c = st.sidebar.selectbox("Țintă HbA1c", [6.5, 7.0, 7.5, 8.0], index=1)
egfr = st.sidebar.number_input("eGFR", 5, 140, 42)

ascvd = st.sidebar.checkbox("ASCVD (Cardio)")
hf = st.sidebar.checkbox("Insuficiență Cardiacă")
ckd = st.sidebar.checkbox("CKD (Renal)")

st.sidebar.markdown("**Tratament Actual:**")
selected_meds = []
if st.sidebar.checkbox("Metformin"): selected_meds.append("Metformin")
if st.sidebar.checkbox("SGLT2i"): selected_meds.append("SGLT2 Inhibitors")
if st.sidebar.checkbox("GLP-1 RA"): selected_meds.append("GLP-1 RAs")
if st.sidebar.checkbox("Tirzepatide"): selected_meds.append("GIP/GLP-1 RA")
if st.sidebar.checkbox("DPP-4i"): selected_meds.append("DPP-4 Inhibitors")
if st.sidebar.checkbox("Sulfoniluree"): selected_meds.append("Sulfonylureas")
if st.sidebar.checkbox("TZD"): selected_meds.append("Thiazolidinediones")
if st.sidebar.checkbox("Insulină"): selected_meds.append("Insulin")

# TABS
tab_algo, tab_compendium, tab_letter = st.tabs(["🧬 Algoritm (RO)", "💊 Compendiu (Tabel 1)", "📝 Avis Diabéto (FR)"])

# ----------------------------------------------------
# TAB 1: ALGORITM (Română)
# ----------------------------------------------------
with tab_algo:
    st.header("Plan de Acțiune (ADA 2022)")
    actions_ro = generate_plan_ro(selected_meds, hba1c, target_a1c, egfr, bmi, ascvd, hf, ckd, age)
    
    if not actions_ro and hba1c <= target_a1c:
        st.success("✅ Pacient controlat.")
    
    for item in actions_ro:
        color = "action-stop" if item['type'] == 'STOP' else "action-start" if item['type'] == 'START' else "action-switch"
        icon = "⛔" if item['type'] == 'STOP' else "✅" if item['type'] == 'START' else "🔄"
        st.markdown(f"""
        <div class="{color}">
            <strong>{icon} {item['type']}: {item['text']}</strong><br>{item['reason']}
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2: COMPENDIU
# ----------------------------------------------------
with tab_compendium:
    st.header("💊 Fișe Tehnice: Tabel 1")
    drug_choice = st.selectbox("Alege Clasa:", list(MED_DETAILS.keys()))
    info = MED_DETAILS[drug_choice]
    st.info(f"**Eficacitate:** {info['efficacy']} | **Greutate:** {info['weight']} | **Risc Hipo:** {info['hypo']}")
    c1, c2 = st.columns(2)
    c1.write(f"**CV:** {info['cv_effect']}")
    c1.write(f"**HF:** {info['hf_effect']}")
    c2.write(f"**Renal:** {info['renal_effect']}")
    st.warning(f"**Clinice:** {', '.join(info['clinical'])}")

# ----------------------------------------------------
# TAB 3: AVIS DIABÉTO (FRANCEZĂ)
# ----------------------------------------------------
with tab_letter:
    st.header("📝 Générateur de Compte Rendu")
    
    # Inputuri adiționale pentru realism
    c_doc1, c_doc2 = st.columns(2)
    nom_patient = c_doc1.text_input("Nom du Patient", "M. Dupont")
    nom_medecin = c_doc2.text_input("Médecin Correspondant", "Dr. Traitant")
    
    # Generare date pentru scrisoare
    date_jour = datetime.date.today().strftime("%d/%m/%Y")
    
    # Traducere comorbidități pentru text
    comurbs_text = []
    if ascvd: comurbs_text.append("Maladie Cardiovasculaire (ASCVD)")
    if hf: comurbs_text.append("Insuffisance Cardiaque")
    if ckd: comurbs_text.append("Maladie Rénale Chronique (MRC)")
    if not comurbs_text: comurbs_text.append("Pas d'antécédents cardiorénaux majeurs")
    
    # Traducere medicamente
    meds_text = ", ".join(selected_meds) if selected_meds else "Aucun traitement"
    
    # Generare Recomandări în Franceză
    french_actions = generate_french_actions(selected_meds, hba1c, target_a1c, egfr, bmi, ascvd, hf, ckd)
    
    # Construire Text Scrisoare
    scrisoare = f"""
**Date:** {date_jour}
**Pour:** {nom_medecin}
**Concerne:** Avis Diabétologique - {nom_patient}

Cher Confrère,

J'ai vu en consultation ce jour votre patient, âgé de {age} ans.

**1. PROFIL CLINIQUE ET BIOLOGIQUE**
*   **Anthropométrie:** Poids {weight} kg, Taille {height} cm, **IMC {bmi:.1f} kg/m²**.
*   **Contrôle Glycémique:** HbA1c **{hba1c}%** (Objectif : < {target_a1c}%).
*   **Fonction Rénale:** DFG (CKD-EPI) **{egfr} ml/min/1.73m²**.
*   **Comorbidités:** {', '.join(comurbs_text)}.

**2. TRAITEMENT ACTUEL**
{meds_text}

**3. ANALYSE ET SYNTHÈSE (Selon recommandations ADA/EASD 2022)**
{"Le patient présente un contrôle glycémique insuffisant." if hba1c > target_a1c else "Le contrôle glycémique est adéquat."}
{"Présence de facteurs de risque cardiorénal nécessitant une protection d'organe spécifique." if (ascvd or hf or ckd) else ""}
{"Le DFG actuel impose une vigilance sur certains traitements." if egfr < 45 else ""}

**4. CONDUITE À TENIR PROPOSÉE**
"""
    # Adăugare acțiuni
    for action in french_actions:
        scrisoare += f"{action}\n"

    scrisoare += """
\nJe reste à votre disposition pour tout complément d'information.

Cordialement,

**Dr. Diabétologue**
*Généré par ADA/EASD Architect*
"""

    # Afișare în container tip "Foaie"
    st.markdown(f'<div class="paper">{scrisoare.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    
    # Buton Copy
    st.markdown("### Copier le texte")
    st.code(scrisoare, language="markdown")
