import importlib.util
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
BASH_CLI = SCRIPTS / "skillhub"
PY_CLI = SCRIPTS / "skillhub.py"


def _load_py_cli():
    spec = importlib.util.spec_from_file_location("skillhub_cli_py", PY_CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


py_cli = _load_py_cli()


def run_shell(snippet: str, env=None) -> subprocess.CompletedProcess:
    """Source the bash CLI (to load its functions), then run `snippet`."""
    command = f"""
set +e
source {shlex.quote(str(BASH_CLI))} gateway placeholder -method GET -path placeholder -token placeholder >/dev/null 2>&1 || true
{snippet}
"""
    return subprocess.run(["bash", "-lc", command], capture_output=True, text=True, check=False, env=env)


def run_shell_function(function_name: str, *arguments: str) -> str:
    quoted = " ".join(shlex.quote(a) for a in arguments)
    result = run_shell(f"""
if ! command -v {function_name} >/dev/null 2>&1; then
  exit 99
fi
{function_name} {quoted}
""")
    if result.returncode != 0:
        raise AssertionError(f"shell function failed: rc={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}")
    return result.stdout.strip()


def test_json_to_query_params_preserves_colon_in_string_value():
    result = run_shell_function(
        'json_to_query_params',
        '{"filter":"last_login_user:\'wenhao.wu\'","limit":100}'
    )

    assert result == 'filter=last_login_user%3A%27wenhao.wu%27&limit=100'


BASE = "{PLACEHOLDER_SKILLHUB_URL}/api/v1/skills/"


class TestListUrl:
    """`list` must percent-encode its search term and page.

    Unencoded, a space made curl reject the URL and `a&page=2` smuggled an extra
    query parameter in. Both CLIs must build the same URL.
    """

    @pytest.mark.parametrize("search_term, page, expected", [
        ("", "", BASE),
        ("crowd", "", BASE + "?search=crowd"),
        ("soar ai", "", BASE + "?search=soar%20ai"),
        ("a&page=2", "", BASE + "?search=a%26page%3D2"),
        ("x#frag?y=1", "", BASE + "?search=x%23frag%3Fy%3D1"),
        ("漏洞", "2", BASE + "?search=%E6%BC%8F%E6%B4%9E&page=2"),
        ("", "3", BASE + "?page=3"),
    ])
    def test_both_clis_build_the_encoded_url(self, search_term, page, expected):
        assert run_shell_function("build_list_url", search_term, page) == expected
        assert py_cli.build_list_url(search_term, page) == expected

    @pytest.mark.parametrize("value, expected", [
        ("vulnerability_info", "vulnerability_info"),
        ("a b/c", "a%20b%2Fc"),
    ])
    def test_install_path_segment_is_encoded(self, value, expected):
        assert run_shell_function("url_encode", value) == expected
        assert py_cli.url_encode(value) == expected


class TestDiagnosticsGoToStderr:
    """info/warning must not pollute stdout, so `skillhub list | jq` works."""

    def test_bash_info_and_warning_write_to_stderr(self):
        result = run_shell("info hello-info; warning hello-warning")

        assert result.stdout == ""
        assert "hello-info" in result.stderr
        assert "hello-warning" in result.stderr

    def test_python_info_and_warning_write_to_stderr(self, capsys):
        py_cli.info("hello-info")
        py_cli.warning("hello-warning")
        captured = capsys.readouterr()

        assert captured.out == ""
        assert "hello-info" in captured.err
        assert "hello-warning" in captured.err


ANSI = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture
def home(tmp_path):
    """A clean HOME with no SKILLHUB_API_KEY in the environment.

    Returns (env, write_env_file). The real SKILLHUB_API_KEY of whoever runs
    the tests must never leak into these cases.
    """
    env = {k: v for k, v in os.environ.items() if k != "SKILLHUB_API_KEY"}
    env["HOME"] = str(tmp_path)

    def write_env_file(content: str) -> Path:
        env_dir = tmp_path / ".skillhub"
        env_dir.mkdir(exist_ok=True)
        env_file = env_dir / ".env"
        env_file.write_text(content, encoding="utf-8")
        return env_file

    return env, write_env_file


def bash_resolved_token(env) -> str:
    # Sourcing sets TOKEN from its own -token placeholder; reset it first.
    result = run_shell('TOKEN=""; resolve_token; printf "%s" "$TOKEN"', env=env)
    assert result.returncode == 0, result.stderr
    return result.stdout


def py_resolved_token(env, monkeypatch, token: str = "") -> str:
    monkeypatch.setenv("HOME", env["HOME"])
    if "SKILLHUB_API_KEY" in env:
        monkeypatch.setenv("SKILLHUB_API_KEY", env["SKILLHUB_API_KEY"])
    else:
        monkeypatch.delenv("SKILLHUB_API_KEY", raising=False)
    return py_cli.resolve_token(token)


def run_cli(impl: str, env, *args: str):
    """Run either CLI end-to-end; returns (returncode, combined output)."""
    cmd = ["bash", str(BASH_CLI)] if impl == "bash" else ["python3", str(PY_CLI)]
    result = subprocess.run([*cmd, *args], capture_output=True, text=True, check=False, env=env)
    return result.returncode, ANSI.sub("", result.stdout + result.stderr).strip()


class TestEnvFileToken:
    """With neither -token nor SKILLHUB_API_KEY, read ~/.skillhub/.env."""

    @pytest.mark.parametrize("content, expected", [
        ("SKILLHUB_API_KEY=sk_plain\n", "sk_plain"),
        ("export SKILLHUB_API_KEY=sk_exported\n", "sk_exported"),
        ('SKILLHUB_API_KEY="sk_double"\n', "sk_double"),
        ("SKILLHUB_API_KEY='sk_single'\n", "sk_single"),
        ("  SKILLHUB_API_KEY = sk_spaced  \n", "sk_spaced"),
        ("SKILLHUB_API_KEY=sk_commented # my laptop key\n", "sk_commented"),
        ("SKILLHUB_API_KEY=sk_tab_comment\t# note\n", "sk_tab_comment"),
        ('export SKILLHUB_API_KEY="sk_quoted"  # note\n', "sk_quoted"),
        ("SKILLHUB_API_KEY='sk_q#hash' # note\n", "sk_q#hash"),
        ("SKILLHUB_API_KEY=sk_has#hash\n", "sk_has#hash"),
        ("# SKILLHUB_API_KEY=sk_disabled\nSKILLHUB_API_KEY=sk_enabled\n", "sk_enabled"),
        ("SKILLHUB_API_KEY=sk_first\nSKILLHUB_API_KEY=sk_last\n", "sk_last"),
        ("OTHER=x\nSKILLHUB_API_KEY_OLD=sk_wrong\nSKILLHUB_API_KEY=sk_right\n", "sk_right"),
        ("SKILLHUB_API_KEY=sk_crlf\r\n", "sk_crlf"),
        ("SKILLHUB_API_KEY=sk_no_newline", "sk_no_newline"),
        ("OTHER=x\n", ""),
        ("", ""),
    ])
    def test_both_clis_parse_the_env_file_the_same_way(self, home, monkeypatch, content, expected):
        env, write_env_file = home
        write_env_file(content)

        assert bash_resolved_token(env) == expected
        assert py_resolved_token(env, monkeypatch) == expected

    def test_missing_env_file_yields_no_token(self, home, monkeypatch):
        env, _ = home

        assert bash_resolved_token(env) == ""
        assert py_resolved_token(env, monkeypatch) == ""

    def test_env_file_is_parsed_not_executed(self, home, monkeypatch, tmp_path):
        env, write_env_file = home
        marker = tmp_path / "pwned"
        write_env_file(f"SKILLHUB_API_KEY=$(touch {marker})\n")

        assert bash_resolved_token(env) == f"$(touch {marker})"
        assert py_resolved_token(env, monkeypatch) == f"$(touch {marker})"
        assert not marker.exists()

    def test_env_var_beats_env_file(self, home, monkeypatch):
        env, write_env_file = home
        write_env_file("SKILLHUB_API_KEY=sk_from_file\n")
        env["SKILLHUB_API_KEY"] = "sk_from_env"

        assert bash_resolved_token(env) == "sk_from_env"
        assert py_resolved_token(env, monkeypatch) == "sk_from_env"

    def test_token_option_beats_env_var_and_file(self, home, monkeypatch):
        env, write_env_file = home
        write_env_file("SKILLHUB_API_KEY=sk_from_file\n")
        env["SKILLHUB_API_KEY"] = "sk_from_env"

        assert py_resolved_token(env, monkeypatch, token="sk_from_flag") == "sk_from_flag"


class TestEnvFileTokenEndToEnd:
    """The token a real command sends, seen through -v's curl echo.

    The request itself fails (placeholder URL); only the echoed header matters.
    """

    @pytest.mark.parametrize("impl", ["bash", "py"])
    @pytest.mark.parametrize("use_env_var, use_flag, expected", [
        (False, False, "sk_from_file"),
        (True, False, "sk_from_env"),
        (True, True, "sk_from_flag"),
    ])
    def test_priority_flag_then_env_var_then_file(self, home, impl, use_env_var, use_flag, expected):
        env, write_env_file = home
        write_env_file("SKILLHUB_API_KEY=sk_from_file\n")
        if use_env_var:
            env["SKILLHUB_API_KEY"] = "sk_from_env"
        args = ["composio", "search", "hello", "-v"]
        if use_flag:
            args += ["-token", "sk_from_flag"]

        _rc, out = run_cli(impl, env, *args)

        assert f"Bearer {expected}'" in out, out

    @pytest.mark.parametrize("command", [
        ["getme"],
        ["composio", "search", "hello"],
        ["gateway", "res", "-method", "GET", "-path", "x"],
    ])
    def test_no_token_anywhere_points_at_the_env_file(self, home, command):
        env, _ = home

        bash_rc, bash_out = run_cli("bash", env, *command)
        py_rc, py_out = run_cli("py", env, *command)

        assert bash_rc != 0 and py_rc != 0
        assert "No authentication token found" in bash_out
        assert "~/.skillhub/.env" in bash_out
        assert bash_out == py_out
