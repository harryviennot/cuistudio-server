#!/usr/bin/env python3
"""
Generate HTML Report from Benchmark Results

Converts benchmark_results.json into a visual HTML report with:
- Side-by-side recipe comparison
- Speed/cost charts
- Quality analysis

Usage:
    python scripts/generate_benchmark_report.py benchmark_results.json
    python scripts/generate_benchmark_report.py benchmark_results.json -o report.html
"""

import argparse
import json
import html
from pathlib import Path
from datetime import datetime


def generate_html_report(data: dict, output_path: str) -> None:
    """Generate HTML report from benchmark data."""

    results = data.get("results", [])
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())

    # Calculate summary stats
    successful = [r for r in results
                  if r.get("legacy", {}).get("success")
                  and r.get("new", {}).get("success")]

    total_legacy_time = sum(r["legacy"]["duration_seconds"] for r in successful)
    total_new_time = sum(r["new"]["duration_seconds"] for r in successful)
    total_legacy_cost = sum(r["legacy"]["total_cost_usd"] for r in successful)
    total_new_cost = sum(r["new"]["total_cost_usd"] for r in successful)

    speed_change = ((total_new_time - total_legacy_time) / total_legacy_time * 100) if total_legacy_time > 0 else 0
    cost_change = ((total_new_cost - total_legacy_cost) / total_legacy_cost * 100) if total_legacy_cost > 0 else 0

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extraction Benchmark Report</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 12px;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        header p {{
            opacity: 0.9;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .card h3 {{
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        .card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }}

        .card .change {{
            font-size: 0.9rem;
            margin-top: 4px;
        }}

        .change.positive {{ color: #22c55e; }}
        .change.negative {{ color: #ef4444; }}
        .change.neutral {{ color: #666; }}

        .result-card {{
            background: white;
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .result-header {{
            background: #f8f9fa;
            padding: 16px 24px;
            border-bottom: 1px solid #eee;
        }}

        .result-header h2 {{
            font-size: 1.1rem;
            word-break: break-all;
        }}

        .result-meta {{
            display: flex;
            gap: 20px;
            margin-top: 8px;
            font-size: 0.85rem;
            color: #666;
        }}

        .result-meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1px;
            background: #eee;
        }}

        .comparison-side {{
            background: white;
            padding: 20px;
        }}

        .comparison-side h4 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid;
        }}

        .comparison-side.legacy h4 {{
            border-color: #3b82f6;
        }}

        .comparison-side.new h4 {{
            border-color: #22c55e;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}

        .metric {{
            text-align: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .metric-value {{
            font-size: 1.25rem;
            font-weight: bold;
        }}

        .metric-label {{
            font-size: 0.75rem;
            color: #666;
            text-transform: uppercase;
        }}

        .recipe-field {{
            margin-bottom: 16px;
        }}

        .recipe-field-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }}

        .recipe-field-name {{
            font-weight: 600;
            color: #333;
        }}

        .status-badge {{
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            text-transform: uppercase;
        }}

        .status-identical {{
            background: #dcfce7;
            color: #166534;
        }}

        .status-different {{
            background: #fef3c7;
            color: #92400e;
        }}

        .recipe-field-value {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            max-height: 200px;
            overflow-y: auto;
        }}

        .recipe-field-value pre {{
            white-space: pre-wrap;
            word-break: break-word;
            font-family: inherit;
        }}

        .quality-section {{
            padding: 20px;
            border-top: 1px solid #eee;
        }}

        .quality-section h4 {{
            margin-bottom: 16px;
            color: #333;
        }}

        .quality-grid {{
            display: grid;
            gap: 12px;
        }}

        .quality-item {{
            display: grid;
            grid-template-columns: 120px 1fr 1fr auto;
            gap: 12px;
            align-items: start;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .quality-field-name {{
            font-weight: 600;
        }}

        .quality-value {{
            font-size: 0.85rem;
            max-height: 100px;
            overflow-y: auto;
        }}

        .quality-analysis {{
            font-size: 0.8rem;
            color: #666;
            font-style: italic;
        }}

        .error-box {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
        }}

        .failure-stage {{
            background: #fee2e2;
            color: #991b1b;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-bottom: 8px;
            display: inline-block;
        }}

        .image-section {{
            padding: 20px;
            border-top: 1px solid #eee;
        }}

        .image-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .image-box {{
            text-align: center;
        }}

        .image-box h5 {{
            margin-bottom: 10px;
            color: #666;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}

        .image-box img {{
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .image-placeholder {{
            background: #f3f4f6;
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            padding: 40px;
            color: #9ca3af;
        }}

        .recipe-section {{
            padding: 20px;
            border-top: 1px solid #eee;
        }}

        .recipe-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .recipe-box {{
            background: #f8f9fa;
            border-radius: 8px;
            overflow: hidden;
        }}

        .recipe-box h5 {{
            background: #e5e7eb;
            padding: 10px 16px;
            margin: 0;
            font-size: 0.85rem;
            text-transform: uppercase;
            color: #374151;
        }}

        .recipe-box pre {{
            padding: 16px;
            margin: 0;
            font-size: 0.75rem;
            max-height: 400px;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .recipe-title {{
            font-size: 1.1rem;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 8px;
        }}

        .recipe-meta {{
            display: flex;
            gap: 16px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }}

        .recipe-meta-item {{
            background: #e0e7ff;
            color: #3730a3;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}

        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.85rem;
        }}

        @media (max-width: 768px) {{
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}

            .quality-item {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Extraction Benchmark Report</h1>
            <p>Generated: {timestamp}</p>
            <p>{len(results)} URLs tested | {len(successful)} successful comparisons</p>
        </header>

        <div class="summary-cards">
            <div class="card">
                <h3>Total Speed</h3>
                <div class="value">{total_legacy_time:.1f}s → {total_new_time:.1f}s</div>
                <div class="change {'positive' if speed_change < 0 else 'negative' if speed_change > 0 else 'neutral'}">
                    {speed_change:+.1f}% {'faster' if speed_change < 0 else 'slower' if speed_change > 0 else ''}
                </div>
            </div>

            <div class="card">
                <h3>Total Cost</h3>
                <div class="value">${total_legacy_cost:.4f} → ${total_new_cost:.4f}</div>
                <div class="change {'negative' if cost_change > 0 else 'positive' if cost_change < 0 else 'neutral'}">
                    {cost_change:+.1f}% {'more expensive' if cost_change > 0 else 'cheaper' if cost_change < 0 else ''}
                </div>
            </div>

            <div class="card">
                <h3>Avg Speed per URL</h3>
                <div class="value">{total_legacy_time/len(successful):.1f}s → {total_new_time/len(successful):.1f}s</div>
            </div>

            <div class="card">
                <h3>Avg Cost per URL</h3>
                <div class="value">${total_legacy_cost/len(successful):.4f} → ${total_new_cost/len(successful):.4f}</div>
            </div>
        </div>

        <h2 style="margin-bottom: 20px;">Detailed Results</h2>
"""

    # Helper function to render error with failure stage
    def render_error(data):
        error = data.get('error', 'Unknown error')
        failure_stage = data.get('failure_stage')
        stage_html = f'<span class="failure-stage">Failed at: {failure_stage}</span><br>' if failure_stage else ''
        return f'{stage_html}<div class="error-box">{html.escape(str(error))}</div>'

    # Helper function to render image
    def render_image(url, label):
        if url:
            return f'<img src="{html.escape(url)}" alt="{label}" loading="lazy">'
        return '<div class="image-placeholder">No image available</div>'

    # Add each result
    for result in results:
        url = result.get("url", "Unknown URL")
        legacy = result.get("legacy", {})
        new = result.get("new", {})
        quality = result.get("quality_comparison", {})

        # Get content type info
        legacy_type = legacy.get('content_type_detected') or legacy.get('detected_type', 'unknown')
        new_type = new.get('content_type_detected') or new.get('detected_type', 'unknown')

        html_content += f"""
        <div class="result-card">
            <div class="result-header">
                <h2>{html.escape(url)}</h2>
                <div class="result-meta">
                    <span>Type: {legacy_type} → {new_type}</span>
                    <span>Platform: {legacy.get('platform') or new.get('platform') or 'N/A'}</span>
                </div>
            </div>

            <div class="comparison-grid">
                <div class="comparison-side legacy">
                    <h4>Legacy (Flags OFF)</h4>
                    {render_error(legacy) if not legacy.get('success') else f'''
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">{legacy.get('duration_seconds', 0):.2f}s</div>
                            <div class="metric-label">Duration</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${legacy.get('total_cost_usd', 0):.4f}</div>
                            <div class="metric-label">Cost</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{legacy_type}</div>
                            <div class="metric-label">Type</div>
                        </div>
                    </div>
                    '''}
                </div>

                <div class="comparison-side new">
                    <h4>New (Flags ON)</h4>
                    {render_error(new) if not new.get('success') else f'''
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">{new.get('duration_seconds', 0):.2f}s</div>
                            <div class="metric-label">Duration</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${new.get('total_cost_usd', 0):.4f}</div>
                            <div class="metric-label">Cost</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{new_type}</div>
                            <div class="metric-label">Type</div>
                        </div>
                    </div>
                    '''}
                </div>
            </div>
"""

        # Add image comparison section
        legacy_thumb = legacy.get('thumbnail_url')
        new_thumb = new.get('thumbnail_url')
        new_generated = new.get('generated_image_url')

        if legacy_thumb or new_thumb or new_generated:
            html_content += f"""
            <div class="image-section">
                <h4 style="margin-bottom: 16px;">Images</h4>
                <div class="image-comparison">
                    <div class="image-box">
                        <h5>Legacy Thumbnail</h5>
                        {render_image(legacy_thumb, 'Legacy thumbnail')}
                    </div>
                    <div class="image-box">
                        <h5>{'New Generated' if new_generated else 'New Thumbnail'}</h5>
                        {render_image(new_generated or new_thumb, 'New image')}
                    </div>
                </div>
            </div>
"""

        # Add recipe comparison section
        legacy_recipe = legacy.get('recipe_data', {})
        new_recipe = new.get('recipe_data', {})

        if legacy_recipe or new_recipe:
            legacy_title = legacy_recipe.get('title', 'No recipe extracted') if legacy_recipe else 'Extraction failed'
            new_title = new_recipe.get('title', 'No recipe extracted') if new_recipe else 'Extraction failed'

            legacy_ingredients = len(legacy_recipe.get('ingredients', [])) if legacy_recipe else 0
            new_ingredients = len(new_recipe.get('ingredients', [])) if new_recipe else 0
            legacy_steps = len(legacy_recipe.get('instructions', [])) if legacy_recipe else 0
            new_steps = len(new_recipe.get('instructions', [])) if new_recipe else 0

            html_content += f"""
            <div class="recipe-section">
                <h4 style="margin-bottom: 16px;">Recipe Output</h4>
                <div class="recipe-comparison">
                    <div class="recipe-box">
                        <h5>Legacy Recipe</h5>
                        <div style="padding: 16px;">
                            <div class="recipe-title">{html.escape(str(legacy_title))}</div>
                            <div class="recipe-meta">
                                <span class="recipe-meta-item">{legacy_ingredients} ingredients</span>
                                <span class="recipe-meta-item">{legacy_steps} steps</span>
                            </div>
                            <details>
                                <summary style="cursor: pointer; color: #6366f1;">Show full JSON</summary>
                                <pre>{html.escape(json.dumps(legacy_recipe, indent=2, ensure_ascii=False)[:2000])}</pre>
                            </details>
                        </div>
                    </div>
                    <div class="recipe-box">
                        <h5>New Recipe</h5>
                        <div style="padding: 16px;">
                            <div class="recipe-title">{html.escape(str(new_title))}</div>
                            <div class="recipe-meta">
                                <span class="recipe-meta-item">{new_ingredients} ingredients</span>
                                <span class="recipe-meta-item">{new_steps} steps</span>
                            </div>
                            <details>
                                <summary style="cursor: pointer; color: #6366f1;">Show full JSON</summary>
                                <pre>{html.escape(json.dumps(new_recipe, indent=2, ensure_ascii=False)[:2000])}</pre>
                            </details>
                        </div>
                    </div>
                </div>
            </div>
"""

        # Add quality comparison if available
        if quality and legacy.get('success') and new.get('success'):
            html_content += """
            <div class="quality-section">
                <h4>Recipe Quality Comparison</h4>
                <div class="quality-grid">
"""
            for field, comp in quality.items():
                status = comp.get("status", "unknown")
                if status == "identical":
                    value = comp.get("value", "")
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, indent=2)
                    value_display = html.escape(str(value)[:500]) if value else "(empty)"

                    html_content += f"""
                    <div class="quality-item">
                        <div class="quality-field-name">{field}</div>
                        <div class="quality-value" colspan="2">{value_display}</div>
                        <span class="status-badge status-identical">Identical</span>
                    </div>
"""
                else:
                    legacy_val = comp.get("legacy", "")
                    new_val = comp.get("new", "")
                    analysis = comp.get("analysis", "")

                    if isinstance(legacy_val, (list, dict)):
                        legacy_val = json.dumps(legacy_val, indent=2)
                    if isinstance(new_val, (list, dict)):
                        new_val = json.dumps(new_val, indent=2)

                    legacy_display = html.escape(str(legacy_val)[:300]) if legacy_val else "(empty)"
                    new_display = html.escape(str(new_val)[:300]) if new_val else "(empty)"

                    html_content += f"""
                    <div class="quality-item">
                        <div class="quality-field-name">{field}</div>
                        <div class="quality-value"><strong>Legacy:</strong><br>{legacy_display}</div>
                        <div class="quality-value"><strong>New:</strong><br>{new_display}</div>
                        <div>
                            <span class="status-badge status-different">Different</span>
                            <div class="quality-analysis">{html.escape(analysis)}</div>
                        </div>
                    </div>
"""

            html_content += """
                </div>
            </div>
"""

        html_content += """
        </div>
"""

    html_content += """
        <footer>
            <p>Generated by Cuisto Extraction Benchmark Tool</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"HTML report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from benchmark results")
    parser.add_argument("input", help="Path to benchmark_results.json")
    parser.add_argument("-o", "--output", default="benchmark_report.html", help="Output HTML file")

    args = parser.parse_args()

    with open(args.input, 'r') as f:
        data = json.load(f)

    generate_html_report(data, args.output)


if __name__ == "__main__":
    main()
