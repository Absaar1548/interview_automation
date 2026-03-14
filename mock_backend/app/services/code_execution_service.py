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

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    from azure.mgmt.containerinstance.models import (
        ContainerGroup,
        Container,
        ContainerPort,
        EnvironmentVariable,
        ResourceRequests,
        ResourceRequirements,
        OperatingSystemTypes,
        ImageRegistryCredential,
    )
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TIMEOUT_SECONDS = 10

# Piston API Configuration
PISTON_API_URL = os.getenv(
    "PISTON_API_URL",
    "https://emkc.org/api/v2/piston/execute"  # Free public API endpoint
)

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


def is_azure_aci_configured() -> bool:
    """Check if Azure Container Instances configuration is present."""
    is_enabled = str(getattr(settings, "USE_AZURE_ACI", "false")).lower() == "true"
    has_config = bool(getattr(settings, "AZURE_SUBSCRIPTION_ID", None) and getattr(settings, "AZURE_ACI_RESOURCE_GROUP", None))
    return is_enabled and has_config

async def execute_code(
    language: str,
    source_code: str,
    stdin_input: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute code using Piston API.
    
    Parameters
    ----------
    language    : Programming language (e.g., "python3", "javascript", "java", "cpp")
    source_code : The source code to execute
    stdin_input : Optional stdin input for the program
    
    Returns
    -------
    {
        "stdout"   : str,
        "stderr"   : str,
        "exit_code": int,
        "timed_out": bool,
        "error"    : str | None,
    }
    """
    # Map language name to Piston format
    lang = language.lower().strip()
    piston_lang = LANGUAGE_MAPPING.get(lang)
    
    if not piston_lang:
        supported = ", ".join(sorted(set(LANGUAGE_MAPPING.keys())))
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "timed_out": False,
            "error": str(e),
        }
    
    version = LANGUAGE_VERSIONS.get(piston_lang, "*")
    file_extension = _get_file_extension(piston_lang)
    
    # Prepare Piston API request payload
    payload = {
        "language": piston_lang,
        "version": version,
        "files": [
            {
                "name": f"main.{file_extension}",
                "content": source_code,
            }
        ],
        "stdin": stdin_input or "",
        "run_timeout": TIMEOUT_SECONDS * 1000,  # Piston uses milliseconds
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(PISTON_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Piston API response structure
            run_result = result.get("run", {})
            
            # Extract output and error information
            stdout = run_result.get("output", "")
            stderr = run_result.get("stderr", "")
            exit_code = run_result.get("code", 0)
            
            # Check if execution timed out (Piston returns signal "SIGKILL" on timeout)
            signal = run_result.get("signal")
            timed_out = signal == "SIGKILL" or signal == "SIGTERM"
            
            # Determine if there was an error
            error = None
            if timed_out:
                error = f"Execution timed out after {TIMEOUT_SECONDS} seconds."
            elif exit_code != 0:
                error = stderr if stderr else f"Program exited with code {exit_code}"
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "error": error,
            }
            
    except httpx.TimeoutException:
        logger.warning(f"Piston API request timed out for language: {language}")
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "timed_out": True,
            "error": f"Request to Piston API timed out after 15 seconds.",
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Piston API HTTP error: {e.response.status_code} - {e.response.text}")
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "timed_out": False,
            "error": f"Piston API error: HTTP {e.response.status_code}",
        }
    except Exception as exc:
        logger.exception(f"Unexpected error calling Piston API: {exc}")
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "timed_out": False,
            "error": f"Unexpected error: {str(exc)}",
        }


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
            interview_id=interview_id,
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

