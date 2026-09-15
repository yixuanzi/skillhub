"""CLI-level tests for `skillhub composio`.

`scripts/skillhub.py` documents itself as mirroring `scripts/skillhub`'s CLI
contract, so almost every case here asserts both implementations *and* that the
two agree - a divergence between them is the failure mode worth catching.

Nothing here reaches the network: request bodies are built and arguments are
validated before any HTTP call is made.
"""
import importlib.util
import json
import re
import shlex
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
BASH_CLI = SCRIPTS / "skillhub"
PY_CLI = SCRIPTS / "skillhub.py"

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _load_py_cli():
    spec = importlib.util.spec_from_file_location("skillhub_cli", PY_CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


py_cli = _load_py_cli()


def bash_body(function_name: str, *args: str) -> dict:
    """Source the bash CLI and call one of its request-body builders."""
    quoted = " ".join(shlex.quote(a) for a in args)
    script = f"""
set +e
source {shlex.quote(str(BASH_CLI))} gateway placeholder -method GET -path placeholder -token placeholder >/dev/null 2>&1 || true
if ! command -v {function_name} >/dev/null 2>&1; then
  exit 99
fi
{function_name} {quoted}
"""
    result = subprocess.run(["bash", "-lc", script], capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
    return json.loads(result.stdout.strip())


def run_cli(impl: str, *args: str):
    """Run either CLI end-to-end and return (returncode, combined output)."""
    cmd = ["bash", str(BASH_CLI)] if impl == "bash" else ["python3", str(PY_CLI)]
    result = subprocess.run([*cmd, *args], capture_output=True, text=True, check=False)
    return result.returncode, ANSI.sub("", result.stdout + result.stderr).strip()


class TestSearchBody:
    """known_fields is optional and must be omitted entirely when unset."""

    def test_use_case_only(self):
        assert bash_body("composio_search_body", "send an email", "") == {"use_case": "send an email"}

    def test_use_case_with_known_fields(self):
        assert bash_body("composio_search_body", "search issues in jira", "project_key:VMS") == {
            "use_case": "search issues in jira",
            "known_fields": "project_key:VMS",
        }

    def test_quoting_survives_the_shell(self):
        """The body is built in python precisely so text never needs escaping."""
        tricky = "post a 'quoted' message with \"double quotes\" & $dollars"
        assert bash_body("composio_search_body", tricky, "")["use_case"] == tricky


class TestSchemaBody:
    """The endpoint takes a list; the CLI must be able to send more than one."""

    def test_single_slug(self):
        assert bash_body("composio_schema_body", "JIRA_SEARCH_ISSUES") == {
            "tool_slugs": ["JIRA_SEARCH_ISSUES"]
        }

    def test_multiple_slugs_keep_their_order(self):
        assert bash_body("composio_schema_body", "C_TOOL", "A_TOOL", "B_TOOL") == {
            "tool_slugs": ["C_TOOL", "A_TOOL", "B_TOOL"]
        }


class TestExecBatchBody:
    """--tools is the batch form; both CLIs validate it identically."""

    VALID = '[{"tool_slug":"A"},{"tool_slug":"B","arguments":{"x":1}}]'

    def test_arguments_default_to_an_empty_object(self):
        expected = {"tools": [
            {"tool_slug": "A", "arguments": {}},
            {"tool_slug": "B", "arguments": {"x": 1}},
        ]}
        assert bash_body("composio_exec_batch_body", self.VALID) == expected
        assert {"tools": py_cli.parse_composio_tools(self.VALID)} == expected

    def test_fifty_entries_are_allowed(self):
        raw = json.dumps([{"tool_slug": f"T{i}"} for i in range(50)])
        assert len(py_cli.parse_composio_tools(raw)) == 50
        assert len(bash_body("composio_exec_batch_body", raw)["tools"]) == 50

    @pytest.mark.parametrize("raw,expected_message", [
        ("not json", "invalid JSON for --tools"),
        ('{"tool_slug":"A"}', "--tools must be a non-empty JSON array"),
        ("[]", "--tools must be a non-empty JSON array"),
        ('["A"]', "--tools[0] must be a JSON object"),
        ('[{"arguments":{}}]', '--tools[0] requires a non-empty "tool_slug"'),
        ('[{"tool_slug":""}]', '--tools[0] requires a non-empty "tool_slug"'),
        ('[{"tool_slug":"A","arguments":[]}]', "--tools[0].arguments must be a JSON object"),
    ])
    def test_rejects_malformed_input_the_same_way(self, raw, expected_message):
        script = f"""
set +e
source {shlex.quote(str(BASH_CLI))} gateway p -method GET -path p -token p >/dev/null 2>&1 || true
composio_exec_batch_body {shlex.quote(raw)}
"""
        bash_result = subprocess.run(["bash", "-lc", script], capture_output=True, text=True, check=False)
        assert bash_result.returncode != 0
        assert expected_message in bash_result.stderr

        with pytest.raises(SystemExit):
            py_cli.parse_composio_tools(raw)

    def test_over_fifty_entries_is_rejected(self):
        raw = json.dumps([{"tool_slug": f"T{i}"} for i in range(51)])
        script = f"""
set +e
source {shlex.quote(str(BASH_CLI))} gateway p -method GET -path p -token p >/dev/null 2>&1 || true
composio_exec_batch_body {shlex.quote(raw)}
"""
        result = subprocess.run(["bash", "-lc", script], capture_output=True, text=True, check=False)
        assert result.returncode != 0
        assert "at most 50 entries, got 51" in result.stderr


class TestArgumentValidationParity:
    """Bad flag combinations must fail before any request, identically in both CLIs."""

    CASES = [
        (["composio", "search", "a", "b"], "takes a single use case"),
        (["composio", "search", "a", "--tools", "[]"], "--tools is only valid for 'composio exec'"),
        (["composio", "search", "a", "--inputs", "{}"], "--inputs is only valid for 'composio exec'"),
        (["composio", "search"], "requires a use case"),
        (["composio", "schema"], "requires at least one tool name"),
        (["composio", "schema", "A", "--known-fields", "k:v"], "--known-fields is only valid for 'composio search'"),
        (["composio", "schema", "A", "--tools", "[]"], "--tools is only valid for 'composio exec'"),
        (["composio", "exec"], "requires a tool name"),
        (["composio", "exec", "A", "B"], "takes one tool name"),
        (["composio", "exec", "A", "--tools", '[{"tool_slug":"B"}]'], "either a tool name or --tools, not both"),
        (["composio", "exec", "--tools", '[{"tool_slug":"B"}]', "--inputs", "{}"],
         "put arguments inside --tools instead"),
        (["composio", "exec", "A", "--known-fields", "k:v"], "--known-fields is only valid for 'composio search'"),
        (["composio", "search", "a", "--known-fields"], "requires a value"),
        (["composio", "exec", "A", "--tools"], "requires a value"),
        (["composio", "bogus", "A"], "Unknown composio subcommand"),
        (["composio", "search", "a", "--nope"], "Unknown option for composio command"),
    ]

    @pytest.mark.parametrize("args,expected", CASES, ids=[" ".join(c[0]) for c in CASES])
    def test_both_clis_reject_identically(self, args, expected):
        bash_rc, bash_out = run_cli("bash", *args)
        py_rc, py_out = run_cli("py", *args)

        assert bash_rc != 0 and py_rc != 0
        assert expected in bash_out, bash_out
        assert expected in py_out, py_out
        assert bash_out == py_out


class TestVersionFlag:
    """--version prints the version; -v stays verbose mode.

    The version lives in one variable per CLI (SKILLHUB_VERSION) and the two
    must not drift apart.
    """

    EXPECTED = "1.0.1"

    def test_python_cli_declares_the_version(self):
        assert py_cli.SKILLHUB_VERSION == self.EXPECTED

    def test_bash_cli_declares_the_same_version(self):
        source = BASH_CLI.read_text()
        assert f'SKILLHUB_VERSION="{self.EXPECTED}"' in source

    @pytest.mark.parametrize("impl", ["bash", "py"])
    @pytest.mark.parametrize("flag", ["--version", "-version"])
    def test_version_flag_prints_the_version(self, impl, flag):
        rc, out = run_cli(impl, flag)

        assert rc == 0
        assert out == f"skillhub {self.EXPECTED}"

    def test_both_clis_print_the_same_version(self):
        assert run_cli("bash", "--version") == run_cli("py", "--version")

    @pytest.mark.parametrize("impl", ["bash", "py"])
    def test_help_header_carries_the_version(self, impl):
        _rc, out = run_cli(impl, "-h")
        assert f"SkillHub CLI Tool v{self.EXPECTED}" in out

    @pytest.mark.parametrize("impl", ["bash", "py"])
    def test_dash_v_is_still_verbose_not_version(self, impl):
        """Regression guard: -v must not be hijacked by the version flag.

        `-v` alone is not a valid invocation (no res_type), so it must fail the
        way any bad res_type does - not print a version and exit 0.
        """
        rc, out = run_cli(impl, "-v")

        assert rc != 0
        assert self.EXPECTED not in out

    @pytest.mark.parametrize("impl", ["bash", "py"])
    def test_dash_v_still_enables_verbose_on_a_real_command(self, impl):
        """-v on a composio call still reaches the verbose curl echo."""
        rc, out = run_cli(impl, "composio", "search", "hello", "-v", "-token", "t")

        # The request itself fails (placeholder URL), but the verbose line must
        # have been printed first, carrying the body the parser built.
        assert rc != 0
        assert '"use_case": "hello"' in out


class TestHelpText:
    """`-h` must describe the flags that actually exist."""

    @pytest.mark.parametrize("impl", ["bash", "py"])
    @pytest.mark.parametrize("fragment", [
        "--known-fields",
        "--tools",
        "composio schema <TOOL_SLUG> [TOOL_SLUG ...]",
        "COMPOSIO_SEARCH_TOOLS",
        "COMPOSIO_GET_TOOL_SCHEMAS",
        "COMPOSIO_MULTI_EXECUTE_TOOL",
    ])
    def test_help_mentions_composio_options(self, impl, fragment):
        _rc, out = run_cli(impl, "-h")
        assert fragment in out

    def test_both_help_texts_are_identical(self):
        _bash_rc, bash_out = run_cli("bash", "-h")
        _py_rc, py_out = run_cli("py", "-h")
        assert bash_out == py_out
