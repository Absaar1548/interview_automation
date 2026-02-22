from fastapi import APIRouter
from pydantic import BaseModel

# Import mock backend components
from mock_backend.interview_store import (
    create_interview,
    transition_state,
    InterviewState,
    INTERVIEWS
)

router = APIRouter()

class BootstrapResponse(BaseModel):
    interview_id: str
    candidate_token: str

@router.get("/bootstrap", response_model=BootstrapResponse)
def dev_bootstrap():
    """
    Development-only endpoint to create a real session in memory.
    1. Creates session with fixed token 'dev-candidate-token'.
    2. Transitions to READY state (skipping resume parsing for dev speed).
    3. Returns session details.
    """
    token = "dev-candidate-token"
    
    # Clean up existing dev session if any, to allow repeated bootstraps
    # Find existing session for this token and remove/terminate it or just let create_interview handle it (it raises error)
    # create_interview raises ValueError if active session exists.
    # For dev bootstrap, we probably want to FORCE a new session.
    
    # 1. Force cleanup of old dev session
    keys_to_remove = []
    for iid, session in INTERVIEWS.items():
        if session.candidate_token == token:
            keys_to_remove.append(iid)
    
    for k in keys_to_remove:
        print(f"Cleaning up old dev session: {k}")
        del INTERVIEWS[k]

    # 2. Create new session
    session = create_interview(token)
    
    # 3. Fast-forward state to READY
    # Current: CREATED
    transition_state(session, InterviewState.RESUME_PARSED)
    transition_state(session, InterviewState.READY)
    
    return {
        "interview_id": session.interview_id,
        "candidate_token": session.candidate_token
    }


# ============ Seed Coding Problems ============

class SeedResponse(BaseModel):
    message: str
    created: int

@router.post("/seed-problems", response_model=SeedResponse)
async def seed_problems():
    """
    Dev-only: seed sample coding problems into MongoDB.
    Safe to call multiple times (checks for duplicates by title).
    """
    from database.coding_db import CodingProblem, TestCase, create_problem
    from database.connection import get_database

    db = get_database()

    PROBLEMS = [
        CodingProblem(
            title="Two Sum",
            description="""Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

**Example 1:**
```
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

**Example 2:**
```
Input: nums = [3,2,4], target = 6
Output: [1,2]
```

**Constraints:**
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- -10^9 <= target <= 10^9
- Only one valid answer exists.

**Input Format:**
First line: space-separated integers (the array)
Second line: single integer (the target)

**Output Format:**
Two space-separated integers (the indices)""",
            difficulty="easy",
            time_limit_sec=5,
            memory_limit_mb=256,
            test_cases=[
                TestCase(input="2 7 11 15\n9", expected_output="0 1", is_hidden=False, points=20),
                TestCase(input="3 2 4\n6", expected_output="1 2", is_hidden=False, points=20),
                TestCase(input="3 3\n6", expected_output="0 1", is_hidden=True, points=20),
                TestCase(input="-1 -2 -3 -4 -5\n-8", expected_output="2 4", is_hidden=True, points=20),
                TestCase(input="0 4 3 0\n0", expected_output="0 3", is_hidden=True, points=20),
            ],
            sample_code={
                "python": "# Read input\nnums = list(map(int, input().split()))\ntarget = int(input())\n\n# Your solution here\n# Print the result as: index1 index2\n",
                "javascript": "const readline = require('readline');\nconst rl = readline.createInterface({ input: process.stdin });\nlet lines = [];\nrl.on('line', (line) => lines.push(line));\nrl.on('close', () => {\n    const nums = lines[0].split(' ').map(Number);\n    const target = parseInt(lines[1]);\n    // Your solution here\n});\n",
            }
        ),
        CodingProblem(
            title="Valid Palindrome",
            description="""A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

**Example 1:**
```
Input: s = "A man, a plan, a canal: Panama"
Output: true
Explanation: "amanaplanacanalpanama" is a palindrome.
```

**Example 2:**
```
Input: s = "race a car"
Output: false
```

**Input Format:**
Single line containing the string

**Output Format:**
Single word: "true" or "false\"""",
            difficulty="easy",
            time_limit_sec=3,
            memory_limit_mb=128,
            test_cases=[
                TestCase(input="A man, a plan, a canal: Panama", expected_output="true", is_hidden=False, points=25),
                TestCase(input="race a car", expected_output="false", is_hidden=False, points=25),
                TestCase(input=" ", expected_output="true", is_hidden=True, points=25),
                TestCase(input="0P", expected_output="false", is_hidden=True, points=25),
            ],
            sample_code={
                "python": "# Read input\ns = input()\n\n# Your solution here\n# Print 'true' or 'false'\n",
            }
        ),
        CodingProblem(
            title="FizzBuzz",
            description="""Given an integer `n`, for each number from 1 to n print:

- `FizzBuzz` if divisible by both 3 and 5
- `Fizz` if divisible by 3
- `Buzz` if divisible by 5
- The number itself otherwise

**Example:**
```
Input: n = 5
Output:
1
2
Fizz
4
Buzz
```

**Input Format:**
Single integer n

**Output Format:**
n lines, each containing the result for that number""",
            difficulty="easy",
            time_limit_sec=2,
            memory_limit_mb=128,
            test_cases=[
                TestCase(input="5", expected_output="1\n2\nFizz\n4\nBuzz", is_hidden=False, points=30),
                TestCase(input="15", expected_output="1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz", is_hidden=False, points=30),
                TestCase(input="3", expected_output="1\n2\nFizz", is_hidden=True, points=40),
            ],
            sample_code={
                "python": "n = int(input())\n\n# Your solution here\n# Print one result per line\n",
            }
        ),
        CodingProblem(
            title="Reverse Linked List",
            description="""Given the head of a singly linked list, reverse the list, and return the reversed list.

For this problem, the list is given as a space-separated sequence of integers.

**Example 1:**
```
Input: 1 2 3 4 5
Output: 5 4 3 2 1
```

**Example 2:**
```
Input: 1 2
Output: 2 1
```

**Constraints:**
- The number of nodes in the list is in the range [0, 5000].
- -5000 <= Node.val <= 5000

**Input Format:**
Single line: space-separated integers representing the list

**Output Format:**
Space-separated integers of the reversed list""",
            difficulty="medium",
            time_limit_sec=3,
            memory_limit_mb=128,
            test_cases=[
                TestCase(input="1 2 3 4 5", expected_output="5 4 3 2 1", is_hidden=False, points=25),
                TestCase(input="1 2", expected_output="2 1", is_hidden=False, points=25),
                TestCase(input="1", expected_output="1", is_hidden=True, points=50),
            ],
            sample_code={
                "python": "# Read the linked list as a list of values\nnums = list(map(int, input().split()))\n\n# Your solution here — reverse it\n# Print result as space-separated integers\n",
            }
        ),
        CodingProblem(
            title="Maximum Subarray",
            description="""Given an integer array `nums`, find the subarray with the largest sum, and return its sum.

**Example 1:**
```
Input: -2 1 -3 4 -1 2 1 -5 4
Output: 6
Explanation: The subarray [4,-1,2,1] has the largest sum 6.
```

**Example 2:**
```
Input: 1
Output: 1
```

**Example 3:**
```
Input: 5 4 -1 7 8
Output: 23
```

**Constraints:**
- 1 <= nums.length <= 10^5
- -10^4 <= nums[i] <= 10^4

**Input Format:**
Single line: space-separated integers

**Output Format:**
Single integer (the maximum subarray sum)""",
            difficulty="medium",
            time_limit_sec=3,
            memory_limit_mb=256,
            test_cases=[
                TestCase(input="-2 1 -3 4 -1 2 1 -5 4", expected_output="6", is_hidden=False, points=30),
                TestCase(input="1", expected_output="1", is_hidden=False, points=30),
                TestCase(input="5 4 -1 7 8", expected_output="23", is_hidden=True, points=40),
            ],
            sample_code={
                "python": "nums = list(map(int, input().split()))\n\n# Hint: Kadane's Algorithm\n# Your solution here\n# Print the maximum subarray sum\n",
            }
        ),
    ]

    created_count = 0
    for prob in PROBLEMS:
        existing = await db.coding_problems.find_one({"title": prob.title})
        if not existing:
            await create_problem(prob)
            created_count += 1

    total = await db.coding_problems.count_documents({})
    return SeedResponse(
        message=f"Done. Created {created_count} new problems. Total in DB: {total}.",
        created=created_count
    )

