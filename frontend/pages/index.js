import { useState } from 'react';

export default function Home() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const askPaintBot = async () => {
    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch('http://localhost:5000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question })
      });

      const data = await res.json();
      console.log("Raw reply from backend:", data);
      setResponse(data);
    } catch (error) {
      console.error("Fetch error:", error);
      setResponse({ summary: "There was an error talking to ProteinPaintAI." });
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-md p-6 space-y-4">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span role="img" aria-label="bot">🤖</span> ProteinPaintAI
        </h1>
        <p className="text-sm text-gray-500">
          Ask about genes, mutations, and cancer datasets — ProteinPaintAI brings back ProteinPaint views.
        </p>

        <input
          className="w-full border p-2 rounded"
          placeholder="e.g., Show me TP53 mutations in pediatric cancer"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button
          onClick={askPaintBot}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-300"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>

        <hr />

        {response && (
          <div className="space-y-4">
            {response.thought && (
              <p className="text-sm italic text-gray-600">{response.thought}</p>
            )}

            {response.summary && (
              <p className="text-gray-800 font-medium">{response.summary}</p>
            )}

            {response.gene_background && (
              <p className="text-gray-700 text-sm">
                🧬 <strong>{response.gene}</strong>: {response.gene_background}
              </p>
            )}

            {response.disease_context && (
              <p className="text-gray-700 text-sm">
                🩺 Disease context: {response.disease_context}
              </p>
            )}

            {typeof response.clinvar_summary === "string" && response.clinvar_summary.trim().length > 0 && (
              <div className="mt-4 text-sm bg-blue-50 border-l-4 border-blue-300 p-4 rounded">
                <h3 className="font-semibold text-blue-700 mb-1">🧬 ClinVar Summary:</h3>
                <pre className="whitespace-pre-wrap text-blue-900 font-mono text-sm">
                  {response.clinvar_summary}
                </pre>
              </div>
            )}

            {typeof response.clinvar_interpretation === "string" && response.clinvar_interpretation.trim().length > 0 && (
              <p className="text-sm text-gray-700 mt-2 italic">
                🧠 <strong>ClinVar insight:</strong> {response.clinvar_interpretation}
              </p>
            )}

            {response.gene && response.dataset && response.view && (
              <>
                <a
                  className="text-blue-500 underline"
                  href={`https://proteinpaint.stjude.org/?gene=${response.gene}&view=${response.view}&dataset=${response.dataset}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  👉 Open in ProteinPaint
                </a>
                <br />
                <a
                  className="text-blue-500 underline"
                  href={`https://proteinpaint.stjude.org/?gene=${response.gene}&genome=hg38&mds3=clinvar`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  👉 Open ClinVar track in ProteinPaint
                </a>
                <div className="-mx-6 mt-4">
                  <iframe
                    src={`https://proteinpaint.stjude.org/?gene=${response.gene}&view=${response.view}&dataset=${response.dataset}`}
                    title="ProteinPaint"
                    width="100%"
                    height="700"
                    className="border rounded"
                  />
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
