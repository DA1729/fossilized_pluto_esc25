import anthropic
import os
from api_templates import (
    timing_attack_template,
    power_analysis_template,
    glitch_attack_template,
    cpa_attack_template,
    api_usage_guide
)

def select_template(vulnerability_type):
    vulnerability_type = vulnerability_type.lower()

    if 'timing' in vulnerability_type:
        return timing_attack_template, 'timing'
    elif 'glitch' in vulnerability_type or 'fault' in vulnerability_type:
        return glitch_attack_template, 'glitch'
    elif 'cpa' in vulnerability_type or 'correlation' in vulnerability_type:
        return cpa_attack_template, 'cpa'
    elif 'dpa' in vulnerability_type or 'differential' in vulnerability_type or 'power' in vulnerability_type:
        return power_analysis_template, 'power'
    else:
        return power_analysis_template, 'power'

def generate_attack_code(llm_analysis, challenge_info, api_key=None):
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return "error: anthropic_api_key not found in environment"

    template, attack_type = select_template(llm_analysis)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""generate a complete attack script based on this analysis:

{llm_analysis}

challenge information:
{challenge_info}

requirements:
1. use this chipwhisperer api template as reference:

{template}

2. important chipwhisperer api usage rules:
{api_usage_guide}

3. generate complete, working python code
4. use snake_case naming
5. no comments in code
6. minimal print statements
7. handle errors appropriately
8. include main() function with scope.dis() and target.dis() cleanup

output only the python code, no explanations."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text

        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()

        return code

    except Exception as e:
        return f"code generation failed: {str(e)}"

def refine_attack_code(original_code, error_message, api_key=None):
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return "error: anthropic_api_key not found in environment"

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""fix this chipwhisperer attack code that failed:

original code:
{original_code}

error encountered:
{error_message}

chipwhisperer api reference:
{api_usage_guide}

provide corrected code that fixes the error. output only python code, no explanations."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text

        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()

        return code

    except Exception as e:
        return f"code refinement failed: {str(e)}"

def generate_complete_attack(trace_summary, llm_analysis, challenge_name, firmware_path, api_key=None):
    print(f"\ngenerating attack code for {challenge_name}...")

    challenge_info = f"""
challenge name: {challenge_name}
firmware path: {firmware_path}
trace analysis: {trace_summary}
"""

    code = generate_attack_code(llm_analysis, challenge_info, api_key)

    print("\ngenerated attack code:")
    print("=" * 60)
    print(code)
    print("=" * 60)

    return code

def save_attack_script(code, filename):
    try:
        with open(filename, 'w') as f:
            f.write(code)
        print(f"\nattack script saved to {filename}")
        return True
    except Exception as e:
        print(f"failed to save: {str(e)}")
        return False
