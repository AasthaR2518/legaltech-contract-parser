import os
import spacy
from .models import Document, ExtractedClause, RiskFlag

# Load the lightweight English model
nlp = None
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    print(f"Error loading spaCy model: {e}")

JARGON_RULES = [
    {
        "term": "sole discretion",
        "risk_level": "HIGH",
        "reason": "Allows one party to make decisions unilaterally without the consent or reasonable consultation of the other party.",
        "suggested_fix": "Change 'sole discretion' to 'mutual agreement' or 'reasonable discretion' to ensure balanced decision making."
    },
    {
        "term": "unlimited liability",
        "risk_level": "HIGH",
        "reason": "Exposes the business to infinite financial risk without any cap.",
        "suggested_fix": "Add a limitation of liability clause capping maximum exposure to fees paid or a specific reasonable amount."
    },
    {
        "term": "indemnify and hold harmless",
        "risk_level": "MEDIUM",
        "reason": "Creates broad and potentially costly legal obligations to pay for the other party's losses or legal costs.",
        "suggested_fix": "Ensure the indemnity clause is mutual, has a liability cap, and excludes indirect or consequential damages."
    },
    {
        "term": "unilateral",
        "risk_level": "MEDIUM",
        "reason": "Creates one-sided rights or obligations (e.g., unilateral termination) that favor only one party.",
        "suggested_fix": "Negotiate to make these rights mutual, requiring notice or written consent from both parties."
    }
]

def analyze_contract_text(document, text):
    """
    Parses contract text using spaCy and heuristics to extract:
    1. Contracting Parties (using NER)
    2. Governing Law clause
    3. Dangerous legal jargon (and flags risks)
    """
    global nlp
    if not nlp:
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"Failed to load spaCy: {e}")
            return False

    # Clear any existing clauses and risk flags for this document to avoid duplication
    ExtractedClause.objects.filter(document=document).delete()

    # 1. Contracting Parties Extraction (NER)
    # Check the first 1500 characters where parties are typically declared
    intro_text = text[:1500]
    doc_intro = nlp(intro_text)
    
    parties = []
    ignored_entities = {"agreement", "contract", "party", "parties", "exhibit", "schedule", "witnesseth", "effective date", "date"}
    
    for ent in doc_intro.ents:
        if ent.label_ in ("ORG", "PERSON"):
            entity_text = ent.text.strip().replace("\n", " ")
            # Basic cleanup: remove trailing punctuations and verify it's not a generic term
            clean_entity = entity_text.strip(".,;:\"'() ")
            if clean_entity and len(clean_entity) > 2:
                if clean_entity.lower() not in ignored_entities and clean_entity not in parties:
                    # Don't add generic nouns that spaCy might misclassify
                    parties.append(clean_entity)
            if len(parties) >= 3: # limit to top 3 identified parties
                break

    if parties:
        document.contracting_parties = ", ".join(parties)
    else:
        document.contracting_parties = "Unknown / Not detected"
    
    document.save()

    # Split text into paragraphs for clause and risk analysis
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    # 2. Isolate Governing Law / Jurisdiction Clause
    gov_law_found = False
    gov_keywords = ["governed by", "governing law", "jurisdiction", "exclusive jurisdiction", "laws of"]
    
    for i, p_text in enumerate(paragraphs):
        # Skip short titles/headings (less than 8 words)
        if len(p_text.split()) < 8:
            continue
        # Scan for governing law keywords
        if any(keyword in p_text.lower() for keyword in gov_keywords):
            # Isolate this clause
            clause = ExtractedClause.objects.create(
                document=document,
                clause_type="Governing Law",
                raw_text=p_text,
                page_number=None # Defaulting to None for raw text processing
            )
            gov_law_found = True
            
            # Simple heuristic check for governing law jurisdiction risk
            # For example, if it specifies a foreign country, or doesn't mention standard jurisdictions
            common_safe_jurisdictions = ["india", "delaware", "new york", "california", "united kingdom", "england"]
            if not any(jurs in p_text.lower() for jurs in common_safe_jurisdictions):
                RiskFlag.objects.create(
                    clause=clause,
                    risk_level="LOW",
                    reason="The governing law is set to a non-standard or foreign jurisdiction, or not explicitly stated as standard.",
                    suggested_fix="Ensure the jurisdiction is set to a local court or a mutually agreed neutral jurisdiction (e.g. Singapore, London)."
                )
            break # Extract first matching governing law clause

    # If no governing law clause was isolated, flag a general warning
    if not gov_law_found:
        dummy_clause = ExtractedClause.objects.create(
            document=document,
            clause_type="Governing Law (Missing)",
            raw_text="No explicit governing law or jurisdiction clause was found in this contract.",
            page_number=None
        )
        RiskFlag.objects.create(
            clause=dummy_clause,
            risk_level="MEDIUM",
            reason="Missing governing law clause means disputes might lead to costly jurisdictional fights in unexpected courts.",
            suggested_fix="Add a standard Governing Law & Jurisdiction clause specifying which state or country's laws apply."
        )

    # 3. Dangerous Jargon & Risk-Scoring
    for i, p_text in enumerate(paragraphs):
        # Skip checking short headings or page break texts
        if len(p_text) < 20 or "--- page break ---" in p_text.lower():
            continue
            
        matched_rules = []
        for rule in JARGON_RULES:
            if rule["term"] in p_text.lower():
                matched_rules.append(rule)
                
        if matched_rules:
            # Determine overall clause type based on highest risk term found
            highest_risk_rule = max(matched_rules, key=lambda r: 3 if r["risk_level"] == "HIGH" else 2)
            
            clause_type = "Risk Clause"
            if "indemnify" in highest_risk_rule["term"]:
                clause_type = "Indemnification Obligations"
            elif "discretion" in highest_risk_rule["term"]:
                clause_type = "Unilateral Discretion"
            elif "liability" in highest_risk_rule["term"]:
                clause_type = "Liability Provision"
            elif "unilateral" in highest_risk_rule["term"]:
                clause_type = "Unilateral Provision"

            clause = ExtractedClause.objects.create(
                document=document,
                clause_type=clause_type,
                raw_text=p_text,
                page_number=None
            )
            
            for rule in matched_rules:
                RiskFlag.objects.create(
                    clause=clause,
                    risk_level=rule["risk_level"],
                    reason=f"Found dangerous jargon '{rule['term']}': {rule['reason']}",
                    suggested_fix=rule["suggested_fix"]
                )

    return True
