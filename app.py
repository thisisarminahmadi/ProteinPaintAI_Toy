from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("question")

    if not user_input:
        return jsonify({"error": "Missing question"}), 400
 
 # Ask GPT to interpret the User input

    system_prompt = """
    You are PaintBot, a helpful assistant that creates links to ProteinPaint visualizations and provides expert biomedical summaries.

    Given a user's question about a gene or cancer type, respond with a JSON object containing:

    - gene: the primary gene symbol to use for visualization (e.g., TP53)
    - dataset: the most likely ProteinPaint dataset (e.g., Pediatric2)
    - view: either "mutation" or "splice"
    - thought: a short informal summary of the user's intent
    - summary: what the ProteinPaint view will likely show
    - gene_background: 1–2 sentence explanation of the gene's biological role, especially in cancer
    - disease_context: 1–2 sentence explanation of the disease or biological setting mentioned
    - clinvar_summary: Optional summary of known ClinVar variants

    Example:
    {
      "gene": "TP53",
      "dataset": "Pediatric2",
      "view": "mutation",
      "thought": "You're asking to explore TP53 mutations in pediatric leukemia.",
      "summary": "This shows mutation patterns for TP53 in pediatric cancers from the Pediatric2 dataset.",
      "gene_background": "TP53 encodes the p53 tumor suppressor protein, which helps regulate cell cycle and DNA repair.",
      "disease_context": "In pediatric leukemia, TP53 mutations are associated with high-risk subtypes and may contribute to relapse.",
      "clinvar_summary": "ClinVar variant highlights:\\n• NM_000546.5(TP53):c.743G>A (p.Arg248Gln) — Pathogenic significance (Li-Fraumeni syndrome)"
    }

    Only return valid raw JSON. No explanations, no markdown, no intro text.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        reply_text = response.choices[0].message.content
        reply_json = json.loads(reply_text)

        # ClinVar data
        gene_symbol = reply_json.get("gene", "")
        clinvar_info = fetch_clinvar_summary(gene_symbol)
        logging.debug("Fetched ClinVar info: %s", clinvar_info
        reply_json["clinvar_summary"] = clinvar_info if clinvar_info and clinvar_info.strip() else reply_json.get("clinvar_summary", "")

        if clinvar_info and clinvar_info.strip():
            # Ask GPT to interpret the ClinVar summary
            interpretation_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a genomics assistant. Summarize what the following ClinVar "
                            "variant list tells us about the gene. Focus on clinical importance, "
                            "uncertainty, or mutation patterns. If the list lacks clear significance or diseases, "
                            "say the data may be incomplete."
                        )
                    },
                    {
                        "role": "user",
                        "content": clinvar_info
                    }
                ]
            )
            insight = interpretation_response.choices[0].message.content.strip()
            reply_json["clinvar_interpretation"] = insight
            logging.debug("Generated ClinVar interpretation: %s", insight)
        else:
            logging.debug("No ClinVar info available for interpretation.")

        return jsonify(reply_json)

    except Exception as e:
        logging.exception("ERROR processing GPT response")
        return jsonify({
            "error": "Could not parse GPT response as JSON.",
            "details": str(e),
            "raw": response.choices[0].message.content if 'response' in locals() else None
        }), 500


def fetch_clinvar_summary(gene_symbol):
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "clinvar",
            "term": f"{gene_symbol}[gene]",
            "retmode": "json"
        }
        search_res = requests.get(search_url, params=search_params).json()
        id_list = search_res.get("esearchresult", {}).get("idlist", [])
        logging.debug("ClinVar search id_list for %s: %s", gene_symbol, id_list)
        if not id_list:
            return None

        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "clinvar",
            "id": ",".join(id_list[:10]),
            "retmode": "json"
        }
        summary_res = requests.get(summary_url, params=summary_params).json()
        summaries = summary_res.get("result", {})
        text_summary = []

        for cid in id_list[:5]:
            variant = summaries.get(cid, {})
            title = variant.get("title", "")
            clinical_sig = variant.get("clinical_significance", {}).get("description", "")
            if not clinical_sig:
                clinical_sig = "Unknown"
            traits_raw = variant.get("trait_set", [{}])[0].get("trait_name", "")
            conditions = ""
            if isinstance(traits_raw, list):
                conditions = ", ".join([t for t in traits_raw if isinstance(t, str)])
            elif isinstance(traits_raw, str) and traits_raw.strip():
                conditions = traits_raw
            if not conditions:
                conditions = "No trait provided"

            if title:
                text_summary.append(f"• {title} — {clinical_sig} significance ({conditions})")

        clinvar_text = "ClinVar variant highlights:\n" + "\n".join(text_summary) if text_summary else ""
        logging.debug("Constructed ClinVar summary: %s", clinvar_text)
        return clinvar_text if clinvar_text.strip() else None

    except Exception as e:
        logging.exception("ClinVar fetch error")
        return None


if __name__ == "__main__":
    app.run(port=5000, debug=True)
