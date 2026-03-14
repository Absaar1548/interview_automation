"""
Code Execution Service
----------------------
Runs candidate source code using Piston API (free public endpoint).

Uses the public Piston API at https://emkc.org/api/v2/piston/execute
for secure, isolated code execution without requiring Docker or local infrastructure.
"""

import os
import logging
import httpx
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TIMEOUT_SECONDS = 10

# Language mapping: your language names -> Piston language names
LANGUAGE_MAPPING = {
    "python3": "python",
    "python": "python",
    "javascript": "javascript",
    "js": "javascript",
    "java": "java",
    "cpp": "cpp",
    "c++": "cpp",
    "c": "c",
    "csharp": "csharp",
    "c#": "csharp",
    "go": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "typescript": "typescript",
    "ts": "typescript",
}

# Piston version mapping (using "*" for latest stable version)
# Piston API will use the latest available version when "*" is specified
LANGUAGE_VERSIONS = {
    "python": "*",
    "javascript": "*",
    "java": "*",
    "cpp": "*",
    "c": "*",
    "csharp": "*",
    "go": "*",
    "rust": "*",
    "ruby": "*",
    "php": "*",
    "typescript": "*",
}


def _get_file_extension(language: str) -> str:
    """Get file extension for a language."""
    extensions = {
        "python": "py",
        "javascript": "js",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "csharp": "cs",
        "go": "go",
        "rust": "rs",
        "ruby": "rb",
        "php": "php",
        "typescript": "ts",
    }
    return extensions.get(language, "txt")


# Piston API Configuration
PISTON_API_URL = os.getenv(
    "PISTON_API_URL",
    "https://emkc.org/api/v2/piston/execute"  # Free public API endpoint
)

# Judge0 API Configuration
JUDGE0_API_URL = os.getenv("JUDGE0_API_URL", "https://ce.judge0.com")
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY", "")

# Judge0 Language IDs
JUDGE0_LANGUAGE_MAPPING = {
    "python3": 71,
    "python": 71,
    "javascript": 63,
    "js": 63,
    "java": 62,
    "cpp": 54,
    "c++": 54,
    "c": 50,
    "csharp": 51,
    "c#": 51,
    "go": 60,
    "rust": 73,
    "ruby": 72,
    "php": 68,
    "typescript": 74,
    "ts": 74,
}


async def _execute_piston(language: str, source_code: str, stdin_input: Optional[str] = None) -> Dict[str, Any]:
    """Execute code using Piston API."""
    lang = language.lower().strip()
    piston_lang = LANGUAGE_MAPPING.get(lang)
    
    if not piston_lang:
        return {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False, "error": f"Unsupported language: {language}"}
    
    version = LANGUAGE_VERSIONS.get(piston_lang, "*")
    file_extension = _get_file_extension(piston_lang)
    
    payload = {
        "language": piston_lang,
        "version": version,
        "files": [{"name": f"main.{file_extension}", "content": source_code}],
        "stdin": stdin_input or "",
        "run_timeout": TIMEOUT_SECONDS * 1000,
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(PISTON_API_URL, json=payload)
            
            if response.status_code == 401:
                return {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False, "error": "PISTON_RESTRICTED"}
                
            response.raise_for_status()
            result = response.json()
            run_result = result.get("run", {})
            
            stdout = run_result.get("output", "")
            stderr = run_result.get("stderr", "")
            exit_code = run_result.get("code", 0)
            signal = run_result.get("signal")
            timed_out = signal in ["SIGKILL", "SIGTERM"]
            
            error = None
            if timed_out:
                error = f"Execution timed out after {TIMEOUT_SECONDS} seconds."
            elif exit_code != 0:
                error = stderr if stderr else f"Program exited with code {exit_code}"
                
            return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code, "timed_out": timed_out, "error": error}
    except Exception as e:
        logger.error(f"Piston error: {e}")
        return {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False, "error": str(e)}


async def _execute_judge0(language: str, source_code: str, stdin_input: Optional[str] = None) -> Dict[str, Any]:
    """Execute code using Judge0 API."""
    lang = language.lower().strip()
    judge0_id = JUDGE0_LANGUAGE_MAPPING.get(lang)
    
    if not judge0_id:
        return {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False, "error": f"Unsupported language: {language}"}
    
    url = f"{JUDGE0_API_URL}/submissions?base64_encoded=false&wait=true"
    headers = {}
    if JUDGE0_API_KEY:
        headers["X-RapidAPI-Key"] = JUDGE0_API_KEY
        headers["X-RapidAPI-Host"] = JUDGE0_API_URL.split("//")[-1]

    payload = {
        "source_code": source_code,
        "language_id": judge0_id,
        "stdin": stdin_input or "",
        "cpu_time_limit": TIMEOUT_SECONDS,
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Judge0 status: 3=Accepted, 4=Wrong Answer, 5=Time Limit Exceeded, 6=Compilation Error, etc.
            status_id = result.get("status", {}).get("id")
            stdout = result.get("stdout") or ""
            stderr = result.get("stderr") or result.get("compile_output") or ""
            timed_out = status_id == 5
            
            exit_code = 0 if status_id == 3 else 1
            error = None
            if timed_out:
                error = f"Execution timed out after {TIMEOUT_SECONDS} seconds."
            elif status_id != 3:
                error = result.get("status", {}).get("description", "Execution failed")
                if stderr:
                    error += f": {stderr}"
            
            return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code, "timed_out": timed_out, "error": error}
    except Exception as e:
        logger.error(f"Judge0 error: {e}")
        return {"stdout": "", "stderr": "", "exit_code": -1, "timed_out": False, "error": str(e)}


async def execute_code(
    language: str,
    source_code: str,
    stdin_input: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute code using available provider (Judge0 or Piston)."""
    
    # Try Piston first IF it's likely a custom/local endpoint
    is_piston_public = "emkc.org" in PISTON_API_URL
    
    if not is_piston_public:
        res = await _execute_piston(language, source_code, stdin_input)
        if res.get("error") != "PISTON_RESTRICTED":
            return res
            
    # Fallback to Judge0
    logger.info("Using Judge0 as code execution provider")
    return await _execute_judge0(language, source_code, stdin_input)


async def run_test_cases(
    language: str,
    source_code: str,
    test_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run code against multiple test cases using Piston API.
    
    Parameters
    ----------
    language    : Programming language (e.g., "python3", "javascript", "java", "cpp")
    source_code : The candidate's solution
    test_cases  : List of dicts, each with keys:
                    - id              (str | UUID)
                    - input           (str)
                    - expected_output (str)
    
    Returns
    -------
    List of result dicts:
    [
        {
            "test_case_id"    : ...,
            "input"           : str,
            "expected_output" : str,
            "actual_output"   : str,
            "passed"          : bool,
            "error"           : str | None,
        },
        ...
    ]
    """
    results = []
    
    for tc in test_cases:
        tc_id = tc.get("id")
        stdin_input: str = tc.get("input", "")
        expected_output: str = tc.get("expected_output", "")
        
        # Execute the code for this test case
        exec_result = await execute_code(
            language=language,
            source_code=source_code,
            stdin_input=stdin_input,
        )
        
        # Normalize output for comparison
        actual_output: str = exec_result["stdout"]
        actual_stripped = actual_output.strip()
        expected_stripped = expected_output.strip()
        
        # Determine pass/fail
        execution_error = exec_result.get("error")
        timed_out = exec_result.get("timed_out", False)
        
        if timed_out:
            passed = False
            error_msg = exec_result["error"] or "Execution timed out"
        elif execution_error:
            passed = False
            error_msg = execution_error
        elif exec_result["exit_code"] != 0:
            passed = False
            error_msg = exec_result["stderr"] or f"Non-zero exit code: {exec_result['exit_code']}"
        else:
            passed = actual_stripped == expected_stripped
            error_msg = None
        
        results.append({
            "test_case_id": tc_id,
            "input": stdin_input,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "passed": passed,
            "error": error_msg,
        })
    
    return results

