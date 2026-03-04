"""
Code Execution Service — runs user code in Docker containers.

Supports: python3, javascript, java, cpp
Each language has a pre-built Docker image (code-runner-<lang>).
"""

import os
import uuid
import subprocess
import tempfile
import logging
import shutil

logger = logging.getLogger(__name__)

LANGUAGE_CONFIG = {
    "python3": {
        "image": "code-runner-python",
        "filename": "solution.py",
        "compile_cmd": None,
        "run_cmd": ["python3", "/code/solution.py"],
    },
    "javascript": {
        "image": "code-runner-javascript",
        "filename": "solution.js",
        "compile_cmd": None,
        "run_cmd": ["node", "/code/solution.js"],
    },
    "java": {
        "image": "code-runner-java",
        "filename": "Solution.java",
        "compile_cmd": ["javac", "/code/Solution.java"],
        "run_cmd": ["java", "-cp", "/code", "Solution"],
    },
    "cpp": {
        "image": "code-runner-cpp",
        "filename": "solution.cpp",
        "compile_cmd": ["g++", "-o", "/code/solution", "/code/solution.cpp"],
        "run_cmd": ["/code/solution"],
    },
}

TIMEOUT_SECONDS = 10
MEMORY_LIMIT = "256m"


def execute_code(language: str, source_code: str, stdin_input: str) -> dict:
    """
    Execute user code in a Docker container.

    Returns:
        {
            "stdout": str,
            "stderr": str,
            "exit_code": int,
            "timed_out": bool,
            "error": str | None
        }
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": 1,
            "timed_out": False,
            "error": f"Unsupported language: {language}",
        }

    # Create a temp directory with the source code
    tmp_dir = tempfile.mkdtemp(prefix="coderun_")
    try:
        code_file = os.path.join(tmp_dir, config["filename"])
        with open(code_file, "w") as f:
            f.write(source_code)

        # For Java, compile first
        if config["compile_cmd"]:
            compile_result = _docker_run(
                image=config["image"],
                mount_dir=tmp_dir,
                cmd=config["compile_cmd"],
                stdin_input="",
                timeout=TIMEOUT_SECONDS,
            )
            if compile_result["exit_code"] != 0:
                return {
                    "stdout": "",
                    "stderr": compile_result["stderr"],
                    "exit_code": compile_result["exit_code"],
                    "timed_out": False,
                    "error": "Compilation error",
                }

        # Run the code
        result = _docker_run(
            image=config["image"],
            mount_dir=tmp_dir,
            cmd=config["run_cmd"],
            stdin_input=stdin_input,
            timeout=TIMEOUT_SECONDS,
        )
        return result
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _docker_run(
    image: str, mount_dir: str, cmd: list, stdin_input: str, timeout: int
) -> dict:
    """
    Execute a command inside a Docker container.
    """
    docker_cmd = [
        "docker", "run",
        "--rm",                          # auto-remove container
        "--network", "none",             # no network access
        "--memory", MEMORY_LIMIT,        # memory limit
        "--cpus", "1",                   # CPU limit
        "--pids-limit", "50",            # process limit
        "-v", f"{mount_dir}:/code",      # mount code directory
        "-w", "/code",                   # working directory
        "-i",                            # interactive (for stdin)
        image,
    ] + cmd

    try:
        proc = subprocess.run(
            docker_cmd,
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "exit_code": proc.returncode,
            "timed_out": False,
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Time limit exceeded",
            "exit_code": -1,
            "timed_out": True,
            "error": "Time limit exceeded",
        }
    except Exception as e:
        logger.error(f"Docker execution error: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "timed_out": False,
            "error": str(e),
        }


def run_test_cases(
    language: str, source_code: str, test_cases: list
) -> list[dict]:
    """
    Run code against a list of test cases.

    Each test_case should have: id, input, expected_output

    Returns list of:
        {
            "test_case_id": str,
            "input": str,
            "expected_output": str,
            "actual_output": str,
            "passed": bool,
            "error": str | None
        }
    """
    results = []
    for tc in test_cases:
        exec_result = execute_code(language, source_code, tc["input"])
        actual = exec_result["stdout"]
        expected = tc["expected_output"].strip()
        passed = actual == expected and exec_result["exit_code"] == 0

        results.append({
            "test_case_id": str(tc["id"]),
            "input": tc["input"],
            "expected_output": expected,
            "actual_output": actual,
            "passed": passed,
            "error": exec_result["error"] or (exec_result["stderr"] if exec_result["exit_code"] != 0 else None),
        })

    return results
