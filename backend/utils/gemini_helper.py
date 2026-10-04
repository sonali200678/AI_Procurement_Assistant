import re
from backend.config import settings

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency may be absent until installed
    Groq = None


def get_provider(api_key: str = None, groq_api_key: str = None) -> str:
    """Choose the preferred AI provider based on available API keys."""
    if groq_api_key or settings.GROQ_API_KEY:
        return "groq"
    return "local"


def get_groq_model_name(model_name: str = None) -> str:
    """Normalize the configured Groq model name and fall back to a safe default."""
    candidate = (model_name or settings.GROQ_MODEL or "llama-3.1-8b-instant").strip()
    candidate = candidate.replace("GROQ_MODEL=", "", 1).strip()
    return candidate or "llama-3.1-8b-instant"


def get_groq_client(api_key: str = None):
    """Configure and return a Groq client using the provided or configured key."""
    key = api_key or settings.GROQ_API_KEY
    if not key:
        raise ValueError(
            "Groq API key is not configured. Please add it to your server .env file "
            "or provide the X-Groq-API-Key header."
        )
    if Groq is None:
        raise RuntimeError("The groq package is not installed. Please install it to use Groq summaries.")
    return Groq(api_key=key)


def generate_local_summary(text: str, file_type: str) -> str:
    """
    Builds a detailed structured summary when Groq is not configured or unavailable.
    This keeps uploads useful without requiring an API key.
    """
    clean_text = re.sub(r"\s+", " ", text or "").strip()
    if not clean_text:
        return (
            "## Document Overview\n\n"
            "The file was uploaded and parsed successfully, but no readable text was found.\n\n"
            "## Key Findings & Insights\n\n"
            "- No textual content was available for summarization.\n"
            "- The upload may contain scanned pages, unsupported content, or an empty file.\n\n"
            "## Data Points & Metrics\n\n"
            "| Metric | Value |\n"
            "| --- | --- |\n"
            "| File type | {file_type.upper()} |\n"
            "| Extracted text | None |\n\n"
            "## Actionable Takeaways\n\n"
            "- Check that the uploaded file contains selectable text or tabular data.\n"
            "- Re-upload a higher-quality source file if the content is expected to be readable."
        ).format(file_type=file_type)

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", clean_text) if sentence.strip()]
    preview_sentences = sentences[:6] if sentences else [clean_text[:900]]

    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b", clean_text.lower())
    stopwords = {
        "that", "this", "with", "from", "have", "will", "your", "about", "there",
        "their", "which", "would", "could", "should", "were", "been", "into",
        "than", "then", "them", "these", "those", "document", "file", "also",
        "after", "before", "during", "under", "over", "when", "where", "because"
    }
    frequencies = {}
    for word in words:
        if word not in stopwords:
            frequencies[word] = frequencies.get(word, 0) + 1
    keywords = [word for word, _ in sorted(frequencies.items(), key=lambda item: item[1], reverse=True)[:8]]

    overview = " ".join(preview_sentences)
    if len(overview) > 1800:
        overview = overview[:1800].rsplit(" ", 1)[0] + "..."

    insight_items = []
    for sentence in sentences[:6]:
        cleaned_sentence = re.sub(r"\s+", " ", sentence).strip()
        if len(cleaned_sentence) > 40:
            insight_items.append(f"- {cleaned_sentence}")

    if not insight_items:
        insight_items.append(f"- The document appears to contain important information related to {file_type.upper()} content.")

    numeric_values = re.findall(r"\b\d+(?:[.,]\d+)?%?\b", clean_text)
    if numeric_values:
        metric_rows = []
        seen = set()
        for value in numeric_values[:8]:
            if value not in seen:
                seen.add(value)
                metric_rows.append(f"| {value} | Mentioned within the extracted content |")
    else:
        metric_rows = ["| No explicit numeric values detected | The text was summarized from qualitative content |"]

    keyword_line = ", ".join(keywords) if keywords else "No repeated keywords detected"

    return (
        "## Document Overview\n\n"
        f"{overview}\n\n"
        "This summary captures the main purpose, important concepts, and the most relevant supporting details extracted from the uploaded document. "
        "It is designed to give a practical overview of the material even when a live AI model is unavailable.\n\n"
        "## Key Findings & Insights\n\n"
        f"{chr(10).join(insight_items)}\n\n"
        "## Data Points & Metrics\n\n"
        f"| Metric | Notes |\n"
        f"| --- | --- |\n"
        f"| File type | {file_type.upper()} |\n"
        f"| Approximate words | {len(words)} |\n"
        f"| Repeated terms | {keyword_line} |\n"
        f"| Extracted sentences | {len(sentences)} |\n"
        f"{chr(10).join(metric_rows)}\n\n"
        "## Actionable Takeaways\n\n"
        "- Review the main themes and supporting statements in the document to confirm priorities.\n"
        "- Cross-check critical dates, names, and figures in the source file before sharing the summary externally.\n"
        "- Add a Groq API key for a richer, more nuanced AI-generated summary with deeper interpretation."
    )

def generate_local_chat_response(text: str, new_message: str) -> str:
    """
    Creates a simple document-grounded response when Groq is unavailable.
    """
    clean_text = re.sub(r"\s+", " ", text or "").strip()
    if not clean_text:
        return (
            "I could not find readable text in this document. "
            "The AI service is currently unavailable, so I cannot infer beyond the parsed content."
        )

    query_terms = {
        word
        for word in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", (new_message or "").lower())
        if word not in {"the", "and", "for", "with", "what", "from", "this", "that", "about", "give", "tell"}
    }
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", clean_text) if sentence.strip()]

    if query_terms:
        scored = []
        for sentence in sentences:
            sentence_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", sentence.lower()))
            score = len(query_terms.intersection(sentence_words))
            if score:
                scored.append((score, sentence))
        selected = [sentence for _, sentence in sorted(scored, key=lambda item: item[0], reverse=True)[:4]]
    else:
        selected = sentences[:4]

    if not selected:
        selected = [clean_text[:900]]

    answer = " ".join(selected)
    if len(answer) > 1400:
        answer = answer[:1400].rsplit(" ", 1)[0] + "..."

    return (
        "The AI service is currently unavailable, so here is a local answer from the parsed document content:\n\n"
        f"{answer}"
    )

def generate_summary(text: str, file_type: str, api_key: str = None, groq_api_key: str = None) -> str:
    """Generate a detailed markdown summary using Groq or the local fallback."""
    provider = get_provider(api_key=api_key, groq_api_key=groq_api_key)
    if provider != "groq":
        return generate_local_summary(text, file_type)

    return generate_summary_with_groq(text=text, file_type=file_type, api_key=groq_api_key)


def generate_summary_with_groq(text: str, file_type: str, api_key: str = None) -> str:
    """Generate a detailed markdown summary using the Groq API."""
    client = get_groq_client(api_key)
    model_name = get_groq_model_name()

    max_chars = 400000
    truncated_text = text[:max_chars]
    if len(text) > max_chars:
        truncated_text += "\n\n[Content truncated for length limit]"

    prompt = f"""
    You are an expert document summarizer and analyst. Analyze the following document of type '{file_type}' and provide a clean, professional, and highly detailed markdown summary.

    Please format the summary with the following markdown headings:
    1. **Document Overview**: Write 2-3 detailed paragraphs that explain the purpose, context, and overall meaning of the document.
    2. **Key Findings & Insights**: Include 6-10 bullet points covering the most important concepts, facts, and notable findings.
    3. **Data Points & Metrics**: If the document contains metrics, numbers, dates, or tabular information, organize the most relevant items into a Markdown Table. If none are present, provide a short, meaningful summary of the document's quantitative or qualitative indicators.
    4. **Actionable Takeaways**: Provide 4-6 practical recommendations or lessons derived from the content.

    Make the response detailed, evidence-based, professional, and visually structured. Avoid generic phrases and ensure the summary is substantive rather than superficial.

    Document Content:
    ---
    {truncated_text}
    ---
    """

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a careful document summarizer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1400,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        message = str(e).lower()
        if "model_not_found" in message or "does not exist" in message or "not found" in message:
            fallback_model = "llama-3.1-8b-instant"
            if model_name != fallback_model:
                try:
                    response = client.chat.completions.create(
                        model=fallback_model,
                        messages=[
                            {"role": "system", "content": "You are a careful document summarizer."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        max_tokens=1400,
                    )
                    return response.choices[0].message.content or ""
                except Exception as fallback_error:
                    raise RuntimeError(f"Groq API Error during summary generation: {fallback_error}")
        raise RuntimeError(f"Groq API Error during summary generation: {str(e)}")


def chat_with_document(text: str, chat_history: list, new_message: str, api_key: str = None, groq_api_key: str = None) -> str:
    """Send the document context and chat history to Groq and return a response."""
    provider = get_provider(api_key=api_key, groq_api_key=groq_api_key)
    if provider != "groq":
        return generate_local_chat_response(text=text, new_message=new_message)

    return chat_with_document_groq(text=text, chat_history=chat_history, new_message=new_message, api_key=groq_api_key)


def chat_with_document_groq(text: str, chat_history: list, new_message: str, api_key: str = None) -> str:
    """Use the Groq API to answer questions about the document context."""
    client = get_groq_client(api_key)
    model_name = get_groq_model_name()
    max_chars = 300000
    truncated_text = text[:max_chars]

    system_instruction = f"""
    You are Summarizerr Chat AI, an intelligent assistant. You answer questions about the document context provided below.
    Use the provided document context to formulate your response. Be objective, precise, and polite.
    If the answer cannot be found in the document context, state that clearly, but try to help as much as possible using general document information.
    Provide formatting like bullet points or code snippets in markdown if appropriate.

    Document Context:
    ---
    {truncated_text}
    ---
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": "Let's start. Please acknowledge receipt of the document context."},
        {"role": "assistant", "content": "Understood. I have read the document context and am ready to answer your questions based on its content."},
    ]

    for msg in chat_history:
        role = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
        messages.append({"role": role, "content": msg.get("content", "")})

    messages.append({"role": "user", "content": new_message})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
            max_tokens=900,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        message = str(e).lower()
        if "model_not_found" in message or "does not exist" in message or "not found" in message:
            fallback_model = "llama-3.1-8b-instant"
            if model_name != fallback_model:
                try:
                    response = client.chat.completions.create(
                        model=fallback_model,
                        messages=messages,
                        temperature=0.2,
                        max_tokens=900,
                    )
                    return response.choices[0].message.content or ""
                except Exception as fallback_error:
                    raise RuntimeError(f"Groq API Error during chat response: {fallback_error}")
        raise RuntimeError(f"Groq API Error during chat response: {str(e)}")
