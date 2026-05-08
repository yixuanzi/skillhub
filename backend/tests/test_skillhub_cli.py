import shlex
import subprocess


def run_shell_function(function_name: str, argument: str) -> str:
    quoted_argument = shlex.quote(argument)
    command = f"""
set +e
source /Users/guisheng.guo/workspace/skillhub/backend/scripts/skillhub gateway placeholder -method GET -path placeholder -token placeholder >/dev/null 2>&1 || true
if ! command -v {function_name} >/dev/null 2>&1; then
  exit 99
fi
{function_name} {quoted_argument}
"""
    result = subprocess.run(["bash", "-lc", command], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"shell function failed: rc={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}")
    return result.stdout.strip()


def test_json_to_query_params_preserves_colon_in_string_value():
    result = run_shell_function(
        'json_to_query_params',
        '{"filter":"last_login_user:\'wenhao.wu\'","limit":100}'
    )

    assert result == 'filter=last_login_user%3A%27wenhao.wu%27&limit=100'
