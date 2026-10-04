from backend.config import settings
from backend.utils.gemini_helper import generate_local_summary, get_provider


def test_generate_local_summary_is_structured_and_detailed():
    sample_text = (
        "The quarterly revenue report highlights a strong recovery across all regions. "
        "North America increased sales by 18 percent, Europe grew by 12 percent, and "
        "the Asia Pacific market expanded by 24 percent compared to the prior quarter. "
        "Operational efficiency improved through automation, reducing processing time by "
        "35 percent while lowering support costs. Customer retention remained stable, "
        "with the renewal rate reaching 91 percent and average account value rising by 9 percent. "
        "The leadership team plans to expand investment in product development and expand "
        "the enterprise sales pipeline in the next fiscal year."
    )

    summary = generate_local_summary(sample_text, "pdf")

    assert "## Document Overview" in summary
    assert "## Key Findings & Insights" in summary
    assert "## Data Points & Metrics" in summary
    assert "## Actionable Takeaways" in summary
    assert len(summary) > 800


def test_provider_selection_prefers_groq():
    original_groq_key = settings.GROQ_API_KEY

    settings.GROQ_API_KEY = ""

    try:
        assert get_provider(groq_api_key="test-key") == "groq"
        assert get_provider(api_key="unused-key") == "local"
        assert get_provider() == "local"
    finally:
        settings.GROQ_API_KEY = original_groq_key
