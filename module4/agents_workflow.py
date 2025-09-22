#!/usr/bin/env python3
"""
# Agentic Workflow: Research Assistant

This example demonstrates an agentic workflow using Strands agents with web research capabilities.

## Key Features
- Specialized agent roles working in sequence
- Direct passing of information between workflow stages
- Web research using http_request and retrieve tools
- Fact-checking and information synthesis

## How to Run
1. Navigate to the example directory
2. Run: python research_assistant.py
3. Enter queries or claims at the prompt

## Example Queries
- "Thomas Edison invented the light bulb"
- "Tuesday comes before Monday in the week"

## Workflow Process
1. Researcher Agent: Gathers web information using multiple tools
2. Analyst Agent: Verifies facts and synthesizes findings
3. Writer Agent: Creates final report
"""

from strands import Agent
from strands_tools import http_request
import os
import json
from pathlib import Path
from datetime import datetime
import webbrowser


def run_research_workflow(user_input):
    """
    Run a three-agent workflow for research and fact-checking with web sources.
    Shows progress logs during execution but presents only the final report to the user.
    
    Args:
        user_input: Research query or claim to verify
        
    Returns:
        str: The final report from the Writer Agent
    """
    
    print(f"\nProcessing: '{user_input}'")
    
    # Step 1: Researcher Agent with enhanced web capabilities
    print("\nStep 1: Researcher Agent gathering web information...")
    
    researcher_agent = Agent(
        system_prompt=(
            "You are a Researcher Agent that gathers information from the web. "
            "1. Determine if the input is a research query or factual claim "
            "2. Use your research tools (http_request, retrieve) to find relevant information "
            "3. Include source URLs and keep findings under 500 words"
        ),
        callback_handler=None,
        tools=[http_request],
        model="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    
    researcher_response = researcher_agent(
        f"Research: '{user_input}'. Use your available tools to gather information from reliable sources. "
        f"Focus on being concise and thorough, but limit web requests to 1-2 sources.",
    )
    
    # Extract only the relevant content from the researcher response
    research_findings = str(researcher_response)
    
    print("Research complete")
    print("Passing research findings to Analyst Agent...\n")
    
    # Step 2: Analyst Agent to verify facts
    print("Step 2: Analyst Agent analyzing findings...")
    
    analyst_agent = Agent(
        system_prompt=(
            "You are an Analyst Agent that verifies information. "
            "1. For factual claims: Rate accuracy from 1-5 and correct if needed "
            "2. For research queries: Identify 3-5 key insights "
            "3. Evaluate source reliability and keep analysis under 400 words"
        ),
        callback_handler=None,
        model="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    analyst_response = analyst_agent(
        f"Analyze these findings about '{user_input}':\n\n{research_findings}",
    )
    
    # Extract only the relevant content from the analyst response
    analysis = str(analyst_response)
    
    print("Analysis complete")
    print("Passing analysis to Writer Agent...\n")
    
    # Step 3: Writer Agent to create report
    print("Step 3: Writer Agent creating final report...")
    
    writer_agent = Agent(
        system_prompt=(
            "You are a Writer Agent that creates clear reports. "
            "1. For fact-checks: State whether claims are true or false "
            "2. For research: Present key insights in a logical structure "
            "3. Keep reports under 500 words with brief source mentions"
        ),
        model="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    
    # Execute the Writer Agent with the analysis (output is shown to user)
    final_report = writer_agent(
        f"Create a report on '{user_input}' based on this analysis:\n\n{analysis}"
    )
    
    print("Report creation complete")
    
    # Visual integration: render to HTML and open in browser
    try:
        output_path = _save_visual_report(str(final_report), title=f"Report - {user_input}")
        print(f"Visual report saved to: {output_path}")
        webbrowser.open(f"file://{output_path}")
    except Exception as err:
        print(f"Warning: failed to render visual report: {err}")
    
    # Return the final report
    return final_report


def _save_visual_report(markdown_report: str, title: str) -> str:
    """
    Save a visual HTML report that renders Markdown and Mermaid diagrams client-side.
    Returns the absolute path to the saved HTML file.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"report-{timestamp}.html"
    output_file = reports_dir / filename

    # Safely embed markdown as a JS string
    markdown_js = json.dumps(markdown_report)
    title_js = json.dumps(title)

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap\" rel=\"stylesheet\" />
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0b0f14;
      --fg: #e6edf3;
      --muted: #9aa4af;
      --card: #0f1720;
      --accent: #4f85ff;
      --code-bg: #0a0e14;
      --border: #1e2a3a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background: var(--bg); color: var(--fg);
    }}
    .container {{
      max-width: 880px; margin: 40px auto; padding: 24px; background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }}
    h1, h2, h3 {{ line-height: 1.2; }}
    h1 {{ font-size: 28px; margin: 0 0 12px; }}
    .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    pre, code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \\
      \"Liberation Mono\", \"Courier New\", monospace; }}
    pre {{ background: var(--code-bg); padding: 14px; border-radius: 8px; overflow: auto; border: 1px solid var(--border); }}
    code {{ background: var(--code-bg); padding: 2px 6px; border-radius: 6px; border: 1px solid var(--border); }}
    blockquote {{ margin: 0; border-left: 4px solid var(--accent); padding-left: 12px; color: var(--muted); }}
    hr {{ border: none; border-top: 1px solid var(--border); margin: 24px 0; }}
    .content img {{ max-width: 100%; border-radius: 8px; border: 1px solid var(--border); }}
    .mermaid {{ background: var(--code-bg); border-radius: 8px; border: 1px solid var(--border); padding: 12px; }}
  </style>
  <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>
  <script src=\"https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js\"></script>
  <script>mermaid.initialize({{ startOnLoad: false, theme: 'dark' }});</script>
  <script>
    const REPORT_TITLE = {title_js};
    const MARKDOWN = {markdown_js};
    document.addEventListener('DOMContentLoaded', () => {{
      document.getElementById('title').textContent = REPORT_TITLE;
      try {{
        const html = marked.parse(MARKDOWN, {{ breaks: true, mangle: false, headerIds: true }});
        // Convert fenced ```mermaid blocks into <div class="mermaid"> for Mermaid to pick up
        const converted = html.replace(/<pre><code class=\"language-mermaid\">([\s\S]*?)<\\/code><\\/pre>/g, (m, g1) => `\\n<div class=\"mermaid\">${{g1}}\n</div>\\n`);
        const contentEl = document.getElementById('content');
        contentEl.innerHTML = converted;
        // Render mermaid diagrams after dynamic insertion
        if (window.mermaid && typeof mermaid.run === 'function') {{
          mermaid.run({{ nodes: contentEl.querySelectorAll('.mermaid') }});
        }} else if (window.mermaid && typeof mermaid.init === 'function') {{
          mermaid.init(undefined, contentEl.querySelectorAll('.mermaid'));
        }}
      }} catch (err) {{
        const contentEl = document.getElementById('content');
        contentEl.innerHTML = `<div style=\"padding:12px;border:1px solid #a33;border-radius:8px;background:#2a0f0f;color:#ffd3d3\">Render error: ${{String(err)}}<pre style=\"white-space:pre-wrap\">${{MARKDOWN}}</pre></div>`;
      }}
    }});
  </script>
  <meta name=\"robots\" content=\"noindex\" />
  <meta name=\"color-scheme\" content=\"dark light\" />
  <meta name=\"theme-color\" content=\"#0b0f14\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\" />
  <meta name=\"referrer\" content=\"no-referrer\" />
  <meta charset=\"utf-8\" />
  <meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\" />
  <meta http-equiv=\"cache-control\" content=\"no-cache\" />
  <meta http-equiv=\"expires\" content=\"0\" />
  <meta http-equiv=\"pragma\" content=\"no-cache\" />
  <meta name=\"format-detection\" content=\"telephone=no\" />
  <meta name=\"apple-mobile-web-app-capable\" content=\"yes\" />
  <meta name=\"apple-mobile-web-app-status-bar-style\" content=\"black\" />
  <meta name=\"mobile-web-app-capable\" content=\"yes\" />
  <meta name=\"HandheldFriendly\" content=\"True\" />
  <meta name=\"apple-mobile-web-app-title\" content=\"Report\" />
  <meta name=\"application-name\" content=\"Report\" />
  <meta name=\"msapplication-TileColor\" content=\"#0b0f14\" />
  <meta name=\"msapplication-TileImage\" content=\"\" />
  <meta name=\"msapplication-config\" content=\"\" />
</head>
<body>
  <div class=\"container\">
    <h1 id=\"title\"></h1>
    <div class=\"subtitle\">Generated by Agentic Workflow</div>
    <div id=\"content\" class=\"content\"></div>
  </div>
</body>
</html>"""

    output_file.write_text(html, encoding="utf-8")
    return str(output_file.resolve())


if __name__ == "__main__":
    # Print welcome message
    print("\nAgentic Workflow: Research Assistant\n")
    print("This demo shows Strands agents in a workflow with web research.")
    print("Try research questions or fact-check claims.")
    print("\nExamples:")
    print("- \"What are quantum computers?\"")
    print("- \"Lemon cures cancer\"")
    print("- \"Tuesday comes before Monday in the week\"")
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break
            
            # Process the input through the workflow of agents
            final_report = run_research_workflow(user_input)
        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try a different request.")