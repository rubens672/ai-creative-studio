import datetime
import logging
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

import json
import re
from typing import List
from getpass import getpass
#from IPython.display import display, Markdown

try:
    from .retry import GENERATE_CONTENT_CONFIG
except ImportError:
    from retry import GENERATE_CONTENT_CONFIG

load_dotenv()

logger = logging.getLogger("ai_creative_studio.content_creation")


# Define All Custom Tools
from google.adk.tools import ToolContext

# --- Content Analysis Tools ---
def count_words(text: str) -> int:
    """Counts the number of words in the provided text."""
    logger.info(f"🔧 Tool: Counting words...")
    count = len(text.split())
    logger.info(f"   Result: {count} words")
    return count

def calculate_readability_score(text: str) -> dict:
    """Calculates a readability score (0-100, higher is easier to read)."""
    logger.info(f"🔧 Tool: Calculating readability...")

    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        return {"score": 0, "grade": "Unable to calculate"}

    words = text.split()
    total_words = len(words)
    total_sentences = len(sentences)
    total_syllables = sum(count_syllables(word) for word in words)

    if total_words == 0 or total_sentences == 0:
        score = 0
    else:
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
        score = max(0, min(100, score))

    if score >= 60:
        grade = "Easy to read"
    elif score >= 50:
        grade = "Moderate"
    else:
        grade = "Complex"

    result = {"score": round(score, 2), "grade": grade}
    logger.info(f"   Result: {result['score']} - {result['grade']}")
    return result

def count_syllables(word: str) -> int:
    """Helper function to estimate syllables in a word."""
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel

    if word.endswith('e'):
        syllable_count -= 1

    return max(1, syllable_count)

def generate_hashtags(text: str, count: int = 5) -> List[str]:
    """Generates relevant hashtags from text by extracting key terms."""
    logger.info(f"🔧 Tool: Generating {count} hashtags...")

    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
        'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'of', 'to', 'for', 'in',
        'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'and',
        'or', 'but', 'if', 'then', 'than', 'so', 'this', 'that', 'these', 'those'
    }

    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    top_words = [word for word, freq in sorted_words[:count]]
    hashtags = [f"#{word.capitalize()}" for word in top_words]

    logger.info(f"   Result: {', '.join(hashtags)}")
    return hashtags


# --- Quality Check Tool ---
def calculate_content_quality_score(
    word_count: int,
    readability_score: float,
    has_headings: bool,
    has_conclusion: bool
) -> dict:
    """Calculates overall content quality score based on multiple factors."""
    logger.info(f"🔧 Tool: Calculating quality score...")

    # Word count scoring
    if word_count < 500:
        word_score = 30
    elif word_count < 800:
        word_score = 60
    elif word_count <= 2000:
        word_score = 100
    else:
        word_score = 80

    # Readability scoring
    read_score = min(100, readability_score * 1.5) if readability_score > 0 else 40

    # Structure scoring
    structure_score = 0
    if has_headings:
        structure_score += 50
    if has_conclusion:
        structure_score += 50

    # Overall quality
    overall_score = (word_score * 0.3) + (read_score * 0.3) + (structure_score * 0.4)

    result = {
        "overall_score": round(overall_score, 2),
        "word_count": word_count,
        "meets_threshold": overall_score >= 70
    }

    logger.info(f"   Result: {result['overall_score']}/100 (Threshold: {'MET' if result['meets_threshold'] else 'NOT MET'})")
    return result


# --- Session State Management ---
def update_session_state(
    tool_context: ToolContext,
    topic: str,
    target_audience: str,
    tone: str,
    keywords: str
) -> str:
    """Saves extracted content brief parameters to session state."""
    logger.info(f"🔧 Tool: Updating session state...")
    tool_context.state['topic'] = topic
    tool_context.state['target_audience'] = target_audience
    tool_context.state['tone'] = tone
    tool_context.state['keywords'] = keywords
    logger.info(f"   Saved: {topic} | {target_audience} | {tone}")
    return "Session state updated with content brief parameters."


# --- Loop Control ---
QUALITY_THRESHOLD_MET = "QUALITY_THRESHOLD_MET"

def exit_loop(tool_context: ToolContext):
    """Terminates the improvement loop when quality meets threshold."""
    logger.info(f"🔧 Tool: Quality approved. Terminating loop...")
    tool_context.actions.escalate = True
    return {"result": "Quality threshold met. Content approved."}

logger.info("✅ All custom tools defined!")


# Define All Specialist Agents
# --- Intake Agent ---
intake_agent = Agent(
    name="intake_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a content brief analyzer. From the user's request, identify:
    - Main topic
    - Target audience
    - Desired tone
    - Key SEO keywords (comma-separated)

    Then call the `update_session_state` tool with the extracted values.
    """,
    tools=[update_session_state]
)


# --- Topic Research Agent ---
topic_research_agent = Agent(
    name="topic_research_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a topic research expert. For topic: {{topic}}

    Use search to find trending angles and select the SINGLE BEST specific blog post title.
    Output format: Just the title, nothing else.

    Example: "10 AI Tools That Save Small Businesses 20 Hours Per Week"
    """,
    tools=[google_search],
    output_key="blog_topic"
)


# --- Content Drafter Agent ---
content_drafter_agent = Agent(
    name="content_drafter_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a content writer. Write a blog post: {{blog_topic}}

    Target audience: {{target_audience}}
    Tone: {{tone}}

    Create a draft (400-600 words) with:
    - Engaging introduction
    - At least 2 H2 headings
    - A conclusion section

    Output only the blog post in markdown format.
    """,
    tools=[],
    output_key="current_content"
)


# --- Quality Checker Agent ---
quality_checker_agent = Agent(
    name="quality_checker_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction=f"""
    You are a content quality analyst. Analyze: {{{{current_content}}}}

    Your job:
    1. Count approximate word count
    2. Estimate readability score (60+ is good)
    3. Check for clear headings
    4. Check for conclusion section

    Use `calculate_content_quality_score` tool.

    Then:
    - IF overall_score >= 70, respond with: '{QUALITY_THRESHOLD_MET}'
    - ELSE, respond with: 'Quality score: [score]. Issues: [specific problems]'
    """,
    tools=[calculate_content_quality_score],
    output_key="quality_feedback"
)


# --- Content Improver Agent ---
content_improver_agent = Agent(
      name="content_improver_agent",
      model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
      generate_content_config=GENERATE_CONTENT_CONFIG,
      instruction=f"""
      Current content: {{{{current_content}}}}
      Feedback: {{{{quality_feedback}}}}
      
      - IF feedback is '{QUALITY_THRESHOLD_MET}': 
        1. Call the `exit_loop` tool to terminate the loop
        2. Then respond with: "Quality threshold met! Content approved."
      
      - ELSE: improve based on issues:
        * Expand if short (add examples, details, explanations)
        * Simplify if complex (shorter sentences, simpler words)
        * Add clear H2 headings if missing
        * Add a strong conclusion if missing
      
        Output the COMPLETE improved content in markdown.
      """,
      #tools=[FunctionTool(exit_loop)],
      tools=[exit_loop],
      output_key="current_content"
)

logger.info("🧞 Core workflow agents created!")


# --- Final Content Creators (Parallel) ---
blog_post_writer_agent = Agent(
    name="blog_post_writer_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a professional blog writer. Create the final polished blog post from: {{current_content}}

    Enhance it to be publication-ready:
    - Ensure 800-1200 words
    - Add engaging subheadings
    - Include actionable tips
    - Strong call-to-action

    Target audience: {{target_audience}}
    Tone: {{tone}}

    Output only the final blog post in markdown.
    """,
    tools=[],
    output_key="final_blog_post"
)

social_media_creator_agent = Agent(
    name="social_media_creator_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a social media specialist. Create posts from: {{current_content}}

    Topic: {{topic}}
    Audience: {{target_audience}}
    Tone: {{tone}}

    Create:
    1. LinkedIn Post (150-200 words, professional)
    2. Twitter Thread (3 tweets, 280 chars each)
    3. Instagram Caption (100-150 words, with emojis and hashtags)

    Format with clear headers for each platform.
    """,
    tools=[],
    output_key="social_media_posts"
)

email_newsletter_writer_agent = Agent(
    name="email_newsletter_writer_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are an email marketing specialist. Create a newsletter from: {{current_content}}

    Topic: {{topic}}
    Audience: {{target_audience}}
    Tone: {{tone}}

    Include:
    - Subject Line (compelling, 50-60 chars)
    - Preview Text (40-50 chars)
    - Body (300-400 words with CTA)

    Format with clear sections.
    """,
    tools=[],
    output_key="email_newsletter"
)

seo_metadata_agent = Agent(
    name="seo_metadata_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are an SEO specialist. Generate metadata for: {{topic}}

    Keywords: {{keywords}}

    Create:
    1. Meta Title (50-60 chars)
    2. Meta Description (150-160 chars)
    3. URL Slug
    4. Focus Keyword
    5. 5 Related Keywords

    Format as structured list.
    """,
    tools=[],
    output_key="seo_metadata"
)


# --- Content Analyzer (Standalone) ---
content_analyzer_agent = Agent(
    name="content_analyzer_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a content analysis expert. Analyze the provided text.

    Use your tools to:
    1. Count words
    2. Calculate readability
    3. Generate 5 hashtags

    Provide a clear analysis report.
    """,
    tools=[count_words, calculate_readability_score, generate_hashtags]
)


# --- Final Packager Agent ---
final_packager_agent = Agent(
    name="final_packager_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are a content package coordinator. Assemble the final deliverable.

    You have:
    - Blog post: {{final_blog_post}}
    - Social media: {{social_media_posts}}
    - Email: {{email_newsletter}}
    - SEO: {{seo_metadata}}

    Create a comprehensive content package with:
    1. Executive Summary
    2. 📝 Blog Post section
    3. 📱 Social Media Content section
    4. 📧 Email Newsletter section
    5. 🔍 SEO Metadata section

    Present everything with proper formatting and clear section headers.
    Add a brief summary at the top.
    """
)


# --- Content Creation Agent ---
content_creation_agent = Agent(
    name="content_creation",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction=f"""
        You are an expert content strategist and topic researcher. Your goal is to help content creators
        find compelling blog topics using your search tool.

        You should:
        1.  **Understand the Niche:** If the user's request is vague, ask for details like target audience,
            content niche, and specific keywords or themes.
        2.  **Research Trends:** Use your search tool to find current trending topics, popular questions,
            and content gaps in the specified niche.
        3.  **Generate Ideas:** Suggest 5-7 specific blog post titles that are:
            - Relevant to the niche
            - Trending or evergreen
            - Actionable and specific
            - SEO-friendly
        4.  **Provide Context:** For each topic, briefly explain why it's a good choice (trend data,
            search volume insights, audience interest).
        5.  **Summarize:** Present the information in a clear, organized format with numbered suggestions.

        Be creative, data-driven, and always think about what will engage the target audience.
    """,
    description="Agent specialized in researching trending blog topics and content ideas based on niche, audience, and keywords.",
    tools=[google_search],
)

logger.info("Content Creation agent created")

logger.info("🧞 All specialist agents created!")


# Assemble All Workflow Agents
from google.adk.agents import SequentialAgent, LoopAgent, ParallelAgent

# --- Sequential: Research and Draft ---
research_and_draft_workflow = SequentialAgent(
    name="research_and_draft_workflow",
    sub_agents=[topic_research_agent, content_drafter_agent]
)

# --- Loop: Quality Improvement ---
quality_improvement_loop = LoopAgent(
    name="quality_improvement_loop",
    sub_agents=[quality_checker_agent, content_improver_agent],
    max_iterations=3
)

# --- Parallel: Multi-Channel Content Creation ---
parallel_content_creation = ParallelAgent(
    name="parallel_content_creation",
    sub_agents=[
        blog_post_writer_agent,
        social_media_creator_agent,
        email_newsletter_writer_agent,
        seo_metadata_agent
    ]
)

# --- Full Content Workflow ---
full_content_workflow = SequentialAgent(
    name="full_content_workflow",
    sub_agents=[
        intake_agent,
        research_and_draft_workflow,
        quality_improvement_loop,
        parallel_content_creation,
        final_packager_agent
    ]
)

logger.info("✅ All workflow agents assembled!")
logger.info("\n🎯 Workflow Structure:")
logger.info("   1. Intake → Parse brief")
logger.info("   2. Sequential → Research + Draft")
logger.info("   3. Loop → Quality check + Improve (up to 3 iterations)")
logger.info("   4. Parallel → Blog + Social + Email + SEO (concurrent)")
logger.info("   5. Package → Combine everything")


# Build the Master Orchestrator
from google.adk.tools.agent_tool import AgentTool
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer

# Wrap agents/workflows as tools
full_content_workflow_tool = AgentTool(agent=full_content_workflow)
content_analyzer_tool = AgentTool(agent=content_analyzer_agent)
content_creation_tool =AgentTool(agent=content_creation_agent)

root_agent = Agent(
    name="master_orchestrator_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    generate_content_config=GENERATE_CONTENT_CONFIG,
    instruction="""
    You are the Master Content Creation Studio orchestrator. Delegate tasks to specialists.

    - For FULL content creation (topic research → draft → improve → multi-channel content),
      use `full_content_workflow_tool`.

    - For ANALYZING existing text (readability, word count, hashtags),
      use `content_analyzer_tool`.

    - For RESEARCHING trending blog topics and content ideas (based on niche, audience, and keywords),
      use `content_creation_tool`

    Always delegate to the appropriate tool. Present specialist responses clearly to the user.

    MANDATORY: translate the entire final output, final output only, into Italian.
    """,
    tools=[full_content_workflow_tool, content_analyzer_tool, content_creation_tool],
)

# Crea l'applicazione e registra l'agente
app = App(
    name="multi_content_creation",
    root_agent=root_agent,
    plugins=[LoggingPlugin()],
)

logger.info("🧞 Master Orchestrator created!")
logger.info("\n🎯 Capabilities:")
logger.info("   ✅ Full content workflow (research → draft → improve → multi-channel)")
logger.info("   ✅ Quick content analysis (words, readability, hashtags)")
logger.info("   ✅ Research tranding blog topics and content ideas (based on niche, audience, and keywords)")


if __name__ == "__main__":
    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    PORT = int(os.getenv("PORT", "8080"))
    HOST = os.getenv("HOST", "0.0.0.0")
    PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")
    PUBLIC_PORT = int(os.getenv("PUBLIC_PORT", str(PORT)))
    PROTOCOL = os.getenv("PROTOCOL", "http")

    a2a_app = to_a2a(root_agent, host=PUBLIC_HOST, port=PUBLIC_PORT, protocol=PROTOCOL)

    logger.info(f"Starting Multi Content Creation on {PROTOCOL}://{HOST}:{PORT}")
    logger.info(f"Agent card: {PROTOCOL}://{HOST}:{PORT}/.well-known/agent.json")

    uvicorn.run(a2a_app, host=HOST, port=PORT)