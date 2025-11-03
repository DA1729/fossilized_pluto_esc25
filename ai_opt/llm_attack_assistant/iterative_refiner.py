import anthropic
import os
import subprocess
import sys
from attack_generator import refine_attack_code, save_attack_script

def execute_attack_script(script_path, timeout=60):
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'execution timeout',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def analyze_execution_result(result, api_key=None):
    if result['success']:
        return None, "execution successful"

    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return None, "error: anthropic_api_key not found"

    error_context = f"""
stdout:
{result['stdout'][-1000:] if result['stdout'] else 'empty'}

stderr:
{result['stderr'][-1000:] if result['stderr'] else 'empty'}

return code: {result['returncode']}
"""

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""analyze this chipwhisperer attack execution failure:

{error_context}

identify:
1. root cause of failure
2. specific api misuse or logic error
3. suggested fix

be concise and technical."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        analysis = response.content[0].text
        return error_context, analysis

    except Exception as e:
        return error_context, f"llm analysis failed: {str(e)}"

def refine_iteratively(initial_code, script_path, max_iterations=3, api_key=None):
    print("\nstarting iterative refinement...")

    current_code = initial_code
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\niteration {iteration}/{max_iterations}")

        save_attack_script(current_code, script_path)

        print("executing attack script...")
        result = execute_attack_script(script_path)

        if result['success']:
            print("\nattack execution successful!")
            print("\nfinal output:")
            print(result['stdout'])
            return current_code, True, result

        print("execution failed")

        error_context, analysis = analyze_execution_result(result, api_key)

        if analysis == "error: anthropic_api_key not found":
            print(analysis)
            return current_code, False, result

        print("\nllm error analysis:")
        print("-" * 60)
        print(analysis)
        print("-" * 60)

        print("\ngenerating refined code...")
        refined_code = refine_attack_code(current_code, error_context + "\n\n" + analysis, api_key)

        if "failed" in refined_code.lower():
            print(refined_code)
            return current_code, False, result

        current_code = refined_code

        print("\nrefined code generated")
        print("=" * 60)
        print(current_code[:500] + "..." if len(current_code) > 500 else current_code)
        print("=" * 60)

    print(f"\nmax iterations ({max_iterations}) reached without success")
    return current_code, False, result

def suggest_improvements(code, execution_results, api_key=None):
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return "error: anthropic_api_key not found in environment"

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""review this attack code and suggest improvements:

code:
{code}

execution results:
{execution_results.get('stdout', 'no output')[:500]}

suggest:
1. performance optimizations
2. reliability improvements
3. query reduction techniques
4. better parameter selection

be specific and actionable."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    except Exception as e:
        return f"improvement suggestion failed: {str(e)}"
