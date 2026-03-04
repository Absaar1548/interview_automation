"""
Seed script to populate the database with coding problems and test cases.

Usage:
    /Users/mohdsaif/Desktop/interview_automation/.venv/bin/python seed_problems.py
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings


PROBLEMS = [
    {
        "title": "Two Sum",
        "description": """## Two Sum

Given an array of integers `nums` and an integer `target`, return the **indices** of the two numbers such that they add up to `target`.

You may assume that each input would have **exactly one solution**, and you may not use the same element twice.

Return the answer as two space-separated indices (0-indexed).

### Input Format
- First line: space-separated integers (the array)
- Second line: the target integer

### Output Format
- Two space-separated indices
""",
        "difficulty": "easy",
        "time_limit_sec": 900,
        "starter_code": {
            "python3": 'import sys\n\ndef two_sum(nums, target):\n    # Write your solution here\n    pass\n\n# Read input\nnums = list(map(int, input().split()))\ntarget = int(input())\nresult = two_sum(nums, target)\nprint(result[0], result[1])\n',
            "javascript": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nconst lines = [];\nrl.on("line", (line) => lines.push(line.trim()));\nrl.on("close", () => {\n    const nums = lines[0].split(" ").map(Number);\n    const target = parseInt(lines[1]);\n    const result = twoSum(nums, target);\n    console.log(result[0] + " " + result[1]);\n});\n\nfunction twoSum(nums, target) {\n    // Write your solution here\n}\n',
            "java": 'import java.util.*;\n\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        // Write your solution here\n        return new int[]{};\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] parts = sc.nextLine().trim().split(" ");\n        int[] nums = new int[parts.length];\n        for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n        int target = Integer.parseInt(sc.nextLine().trim());\n        int[] result = twoSum(nums, target);\n        System.out.println(result[0] + " " + result[1]);\n    }\n}\n',
            "cpp": '#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\n\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Write your solution here\n    return {};\n}\n\nint main() {\n    string line;\n    getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums;\n    int n;\n    while (iss >> n) nums.push_back(n);\n    int target;\n    cin >> target;\n    vector<int> result = twoSum(nums, target);\n    cout << result[0] << " " << result[1] << endl;\n    return 0;\n}\n',
        },
        "test_cases": [
            {"input": "2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False, "order": 1},
            {"input": "3 2 4\n6", "expected_output": "1 2", "is_hidden": False, "order": 2},
            {"input": "3 3\n6", "expected_output": "0 1", "is_hidden": False, "order": 3},
            {"input": "1 5 3 7 2\n9", "expected_output": "1 3", "is_hidden": True, "order": 4},
            {"input": "-1 -2 -3 -4 -5\n-8", "expected_output": "2 4", "is_hidden": True, "order": 5},
            {"input": "0 4 3 0\n0", "expected_output": "0 3", "is_hidden": True, "order": 6},
        ],
    },
    {
        "title": "Reverse String",
        "description": """## Reverse String

Write a function that reverses a string. The input string is given as a single line.

### Input Format
- A single line containing the string to reverse

### Output Format
- The reversed string
""",
        "difficulty": "easy",
        "time_limit_sec": 900,
        "starter_code": {
            "python3": '# Read input and print the reversed string\ns = input()\n# Write your solution here\nprint(s)\n',
            "javascript": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nrl.on("line", (line) => {\n    // Write your solution here\n    console.log(line);\n    rl.close();\n});\n',
            "java": 'import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine();\n        // Write your solution here\n        System.out.println(s);\n    }\n}\n',
            "cpp": '#include <iostream>\n#include <string>\n#include <algorithm>\nusing namespace std;\n\nint main() {\n    string s;\n    getline(cin, s);\n    // Write your solution here\n    cout << s << endl;\n    return 0;\n}\n',
        },
        "test_cases": [
            {"input": "hello", "expected_output": "olleh", "is_hidden": False, "order": 1},
            {"input": "Hannah", "expected_output": "hannaH", "is_hidden": False, "order": 2},
            {"input": "abcdef", "expected_output": "fedcba", "is_hidden": False, "order": 3},
            {"input": "a", "expected_output": "a", "is_hidden": True, "order": 4},
            {"input": "racecar", "expected_output": "racecar", "is_hidden": True, "order": 5},
            {"input": "12345", "expected_output": "54321", "is_hidden": True, "order": 6},
        ],
    },
    {
        "title": "FizzBuzz",
        "description": """## FizzBuzz

Given an integer `n`, print the numbers from `1` to `n`. But for multiples of 3, print `"Fizz"` instead of the number, for multiples of 5 print `"Buzz"`, and for multiples of both 3 and 5 print `"FizzBuzz"`.

### Input Format
- A single integer `n`

### Output Format
- `n` lines, each containing the appropriate output
""",
        "difficulty": "easy",
        "time_limit_sec": 900,
        "starter_code": {
            "python3": 'n = int(input())\n# Write your solution here\nfor i in range(1, n + 1):\n    print(i)\n',
            "javascript": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nrl.on("line", (line) => {\n    const n = parseInt(line.trim());\n    // Write your solution here\n    for (let i = 1; i <= n; i++) {\n        console.log(i);\n    }\n    rl.close();\n});\n',
            "java": 'import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = Integer.parseInt(sc.nextLine().trim());\n        // Write your solution here\n        for (int i = 1; i <= n; i++) {\n            System.out.println(i);\n        }\n    }\n}\n',
            "cpp": '#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n    // Write your solution here\n    for (int i = 1; i <= n; i++) {\n        cout << i << endl;\n    }\n    return 0;\n}\n',
        },
        "test_cases": [
            {"input": "5", "expected_output": "1\n2\nFizz\n4\nBuzz", "is_hidden": False, "order": 1},
            {"input": "15", "expected_output": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz", "is_hidden": False, "order": 2},
            {"input": "3", "expected_output": "1\n2\nFizz", "is_hidden": False, "order": 3},
            {"input": "1", "expected_output": "1", "is_hidden": True, "order": 4},
            {"input": "30", "expected_output": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n16\n17\nFizz\n19\nBuzz\nFizz\n22\n23\nFizz\nBuzz\n26\nFizz\n28\n29\nFizzBuzz", "is_hidden": True, "order": 5},
        ],
    },
    {
        "title": "Palindrome Check",
        "description": """## Palindrome Check

Given a string `s`, determine if it is a palindrome. Consider only alphanumeric characters and ignore cases.

### Input Format
- A single line containing the string

### Output Format
- Print `true` if the string is a palindrome, `false` otherwise
""",
        "difficulty": "easy",
        "time_limit_sec": 900,
        "starter_code": {
            "python3": 's = input()\n# Write your solution here\n# Print "true" or "false"\n',
            "javascript": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nrl.on("line", (line) => {\n    // Write your solution here\n    // Print "true" or "false"\n    rl.close();\n});\n',
            "java": 'import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine();\n        // Write your solution here\n        // Print "true" or "false"\n    }\n}\n',
            "cpp": '#include <iostream>\n#include <string>\n#include <algorithm>\n#include <cctype>\nusing namespace std;\n\nint main() {\n    string s;\n    getline(cin, s);\n    // Write your solution here\n    // Print "true" or "false"\n    return 0;\n}\n',
        },
        "test_cases": [
            {"input": "A man a plan a canal Panama", "expected_output": "true", "is_hidden": False, "order": 1},
            {"input": "race a car", "expected_output": "false", "is_hidden": False, "order": 2},
            {"input": "Was it a car or a cat I saw", "expected_output": "true", "is_hidden": False, "order": 3},
            {"input": " ", "expected_output": "true", "is_hidden": True, "order": 4},
            {"input": "ab", "expected_output": "false", "is_hidden": True, "order": 5},
            {"input": "0P", "expected_output": "false", "is_hidden": True, "order": 6},
        ],
    },
    {
        "title": "Maximum Subarray",
        "description": """## Maximum Subarray

Given an integer array `nums`, find the contiguous subarray (containing at least one number) which has the **largest sum** and return its sum.

### Input Format
- A single line of space-separated integers

### Output Format
- A single integer — the maximum subarray sum
""",
        "difficulty": "medium",
        "time_limit_sec": 900,
        "starter_code": {
            "python3": 'nums = list(map(int, input().split()))\n# Write your solution here (Kadane\'s algorithm)\n# Print the maximum subarray sum\n',
            "javascript": 'const readline = require("readline");\nconst rl = readline.createInterface({ input: process.stdin });\nrl.on("line", (line) => {\n    const nums = line.trim().split(" ").map(Number);\n    // Write your solution here (Kadane\'s algorithm)\n    // console.log(result);\n    rl.close();\n});\n',
            "java": 'import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] parts = sc.nextLine().trim().split(" ");\n        int[] nums = new int[parts.length];\n        for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);\n        // Write your solution here (Kadane\'s algorithm)\n        // System.out.println(result);\n    }\n}\n',
            "cpp": '#include <iostream>\n#include <vector>\n#include <sstream>\n#include <climits>\nusing namespace std;\n\nint main() {\n    string line;\n    getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums;\n    int n;\n    while (iss >> n) nums.push_back(n);\n    // Write your solution here (Kadane\'s algorithm)\n    // cout << result << endl;\n    return 0;\n}\n',
        },
        "test_cases": [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6", "is_hidden": False, "order": 1},
            {"input": "1", "expected_output": "1", "is_hidden": False, "order": 2},
            {"input": "5 4 -1 7 8", "expected_output": "23", "is_hidden": False, "order": 3},
            {"input": "-1", "expected_output": "-1", "is_hidden": True, "order": 4},
            {"input": "-2 -1", "expected_output": "-1", "is_hidden": True, "order": 5},
            {"input": "1 2 3 4 5", "expected_output": "15", "is_hidden": True, "order": 6},
        ],
    },
]


async def seed_problems():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Check if problems already exist
        result = await conn.execute(text("SELECT COUNT(*) FROM coding_problems"))
        count = result.scalar()
        if count > 0:
            print(f"[SKIP] {count} coding problems already exist. Delete them first to re-seed.")
            await engine.dispose()
            return

        for prob in PROBLEMS:
            problem_id = uuid.uuid4()
            # SQLAlchemy stores enum names (EASY/MEDIUM/HARD), not values
            difficulty_upper = prob["difficulty"].upper()
            await conn.execute(
                text("""
                    INSERT INTO coding_problems (id, title, description, difficulty, starter_code, time_limit_sec)
                    VALUES (:id, :title, :description, :difficulty, CAST(:starter_code AS jsonb), :time_limit_sec)
                """),
                {
                    "id": problem_id,
                    "title": prob["title"],
                    "description": prob["description"],
                    "difficulty": difficulty_upper,
                    "starter_code": __import__("json").dumps(prob["starter_code"]),
                    "time_limit_sec": prob["time_limit_sec"],
                },
            )

            for tc in prob["test_cases"]:
                await conn.execute(
                    text("""
                        INSERT INTO test_cases (id, problem_id, input, expected_output, is_hidden, "order")
                        VALUES (:id, :problem_id, :input, :expected_output, :is_hidden, :order)
                    """),
                    {
                        "id": uuid.uuid4(),
                        "problem_id": problem_id,
                        "input": tc["input"],
                        "expected_output": tc["expected_output"],
                        "is_hidden": tc["is_hidden"],
                        "order": tc["order"],
                    },
                )

            print(f"  [OK] Seeded: {prob['title']} ({len(prob['test_cases'])} test cases)")

    print(f"\n[OK] Successfully seeded {len(PROBLEMS)} coding problems.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_problems())
