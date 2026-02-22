import subprocess
import tempfile
import os
import time
from typing import Optional, List
from database.coding_db import TestCase, ExecutionResult


class CodingService:
    """
    Service for handling coding interview tasks and code execution.
    """
    
    # Language configurations
    LANGUAGE_CONFIG = {
        "python": {
            "extension": ".py",
            "command": ["python3"],
            "compile": False
        },
        "javascript": {
            "extension": ".js",
            "command": ["node"],
            "compile": False
        },
        "java": {
            "extension": ".java",
            "command": ["java"],
            "compile": True,
            "compile_command": ["javac"]
        },
        "cpp": {
            "extension": ".cpp",
            "command": ["./a.out"],
            "compile": True,
            "compile_command": ["g++", "-o", "a.out"]
        }
    }
    
    def __init__(self):
        pass

    async def execute_code(
        self, 
        code: str, 
        language: str, 
        stdin_input: str = "",
        timeout: int = 5
    ) -> dict:
        """
        Executes the provided code safely and returns the output.
        
        Args:
            code: Source code to execute
            language: Programming language (python, javascript, java, cpp)
            stdin_input: Input to pass to the program via stdin
            timeout: Maximum execution time in seconds
            
        Returns:
            dict with keys: output, error, execution_time_ms
        """
        if language not in self.LANGUAGE_CONFIG:
            return {
                "output": None,
                "error": f"Unsupported language: {language}",
                "execution_time_ms": 0
            }
        
        config = self.LANGUAGE_CONFIG[language]
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Handle Java class name extraction
                if language == "java":
                    # Extract class name from code
                    class_name = self._extract_java_class_name(code)
                    if not class_name:
                        return {
                            "output": None,
                            "error": "Could not find public class in Java code",
                            "execution_time_ms": 0
                        }
                    filename = f"{class_name}{config['extension']}"
                else:
                    filename = f"code{config['extension']}"
                
                filepath = os.path.join(tmpdir, filename)
                
                # Write code to file
                with open(filepath, 'w') as f:
                    f.write(code)
                
                # Compile if needed
                if config.get("compile"):
                    compile_result = self._compile_code(
                        filepath, 
                        config["compile_command"],
                        tmpdir,
                        timeout
                    )
                    if compile_result["error"]:
                        return compile_result
                
                # Execute code
                return self._run_code(
                    filepath,
                    config["command"],
                    stdin_input,
                    tmpdir,
                    timeout,
                    language
                )
                
        except Exception as e:
            return {
                "output": None,
                "error": f"Execution failed: {str(e)}",
                "execution_time_ms": 0
            }
    
    def _extract_java_class_name(self, code: str) -> Optional[str]:
        """Extract the public class name from Java code"""
        import re
        match = re.search(r'public\s+class\s+(\w+)', code)
        return match.group(1) if match else None
    
    def _compile_code(
        self, 
        filepath: str, 
        compile_command: List[str],
        cwd: str,
        timeout: int
    ) -> dict:
        """Compile code if needed"""
        try:
            cmd = compile_command + [filepath]
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                return {
                    "output": None,
                    "error": f"Compilation error:\n{result.stderr}",
                    "execution_time_ms": 0
                }
            
            return {"error": None}
            
        except subprocess.TimeoutExpired:
            return {
                "output": None,
                "error": "Compilation timeout",
                "execution_time_ms": 0
            }
        except Exception as e:
            return {
                "output": None,
                "error": f"Compilation failed: {str(e)}",
                "execution_time_ms": 0
            }
    
    def _run_code(
        self,
        filepath: str,
        command: List[str],
        stdin_input: str,
        cwd: str,
        timeout: int,
        language: str
    ) -> dict:
        """Run the code and capture output"""
        try:
            # Build command based on language
            if language == "python":
                cmd = command + [filepath]
            elif language == "javascript":
                cmd = command + [filepath]
            elif language == "java":
                # Extract class name from filepath
                class_name = os.path.splitext(os.path.basename(filepath))[0]
                cmd = command + [class_name]
            elif language == "cpp":
                cmd = command
            else:
                cmd = command + [filepath]
            
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            if result.returncode != 0:
                return {
                    "output": result.stdout,
                    "error": result.stderr,
                    "execution_time_ms": execution_time_ms
                }
            
            return {
                "output": result.stdout,
                "error": None,
                "execution_time_ms": execution_time_ms
            }
            
        except subprocess.TimeoutExpired:
            return {
                "output": None,
                "error": f"Execution timeout (exceeded {timeout}s)",
                "execution_time_ms": timeout * 1000
            }
        except Exception as e:
            return {
                "output": None,
                "error": f"Runtime error: {str(e)}",
                "execution_time_ms": 0
            }
    
    async def run_test_case(
        self,
        code: str,
        language: str,
        test_case: TestCase,
        test_index: int,
        timeout: int = 5
    ) -> ExecutionResult:
        """
        Run code against a single test case.
        
        Args:
            code: Source code
            language: Programming language
            test_case: TestCase object with input and expected output
            test_index: Index of the test case
            timeout: Maximum execution time
            
        Returns:
            ExecutionResult with pass/fail status
        """
        result = await self.execute_code(
            code=code,
            language=language,
            stdin_input=test_case.input,
            timeout=timeout
        )
        
        # Check if execution was successful
        if result["error"]:
            return ExecutionResult(
                test_case_index=test_index,
                passed=False,
                actual_output=result["output"],
                expected_output=test_case.expected_output,
                error=result["error"],
                execution_time_ms=result["execution_time_ms"],
                points_earned=0
            )
        
        # Compare output (strip whitespace for comparison)
        actual = (result["output"] or "").strip()
        expected = test_case.expected_output.strip()
        
        passed = actual == expected
        points = test_case.points if passed else 0
        
        return ExecutionResult(
            test_case_index=test_index,
            passed=passed,
            actual_output=result["output"],
            expected_output=test_case.expected_output,
            error=None,
            execution_time_ms=result["execution_time_ms"],
            points_earned=points
        )
    
    async def evaluate_submission(
        self,
        code: str,
        language: str,
        test_cases: List[TestCase],
        timeout: int = 5
    ) -> List[ExecutionResult]:
        """
        Evaluate a submission against all test cases (visible + hidden).
        
        Args:
            code: Source code
            language: Programming language
            test_cases: List of all test cases (including hidden ones)
            timeout: Maximum execution time per test
            
        Returns:
            List of ExecutionResults for each test case
        """
        results = []
        
        for i, test_case in enumerate(test_cases):
            result = await self.run_test_case(
                code=code,
                language=language,
                test_case=test_case,
                test_index=i,
                timeout=timeout
            )
            results.append(result)
        
        return results
