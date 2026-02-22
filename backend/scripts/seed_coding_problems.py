"""
Seed script to populate the database with sample coding problems.
Run this script to add test problems for development and testing.

Usage:
    python3 scripts/seed_coding_problems.py
"""

import asyncio
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import connect_to_mongo, close_mongo_connection
from database.coding_db import CodingProblem, TestCase, create_problem


async def seed_problems():
    """Create sample coding problems"""
    
    # Problem 1: Two Sum
    two_sum = CodingProblem(
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
Two space-separated integers (the indices)
""",
        difficulty="easy",
        time_limit_sec=5,
        memory_limit_mb=256,
        test_cases=[
            TestCase(
                input="2 7 11 15\n9",
                expected_output="0 1",
                is_hidden=False,
                points=20
            ),
            TestCase(
                input="3 2 4\n6",
                expected_output="1 2",
                is_hidden=False,
                points=20
            ),
            TestCase(
                input="3 3\n6",
                expected_output="0 1",
                is_hidden=True,
                points=20
            ),
            TestCase(
                input="-1 -2 -3 -4 -5\n-8",
                expected_output="2 4",
                is_hidden=True,
                points=20
            ),
            TestCase(
                input="0 4 3 0\n0",
                expected_output="0 3",
                is_hidden=True,
                points=20
            )
        ],
        sample_code={
            "python": """# Read input
nums = list(map(int, input().split()))
target = int(input())

# Your solution here
# Print the result as: index1 index2
""",
            "javascript": """// Read input
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

let lines = [];
rl.on('line', (line) => lines.push(line));
rl.on('close', () => {
    const nums = lines[0].split(' ').map(Number);
    const target = parseInt(lines[1]);
    
    // Your solution here
    // Print the result as: index1 index2
});
"""
        }
    )
    
    # Problem 2: Palindrome Check
    palindrome = CodingProblem(
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
Explanation: "raceacar" is not a palindrome.
```

**Input Format:**
Single line containing the string

**Output Format:**
Single word: "true" or "false"
""",
        difficulty="easy",
        time_limit_sec=3,
        memory_limit_mb=128,
        test_cases=[
            TestCase(
                input="A man, a plan, a canal: Panama",
                expected_output="true",
                is_hidden=False,
                points=25
            ),
            TestCase(
                input="race a car",
                expected_output="false",
                is_hidden=False,
                points=25
            ),
            TestCase(
                input=" ",
                expected_output="true",
                is_hidden=True,
                points=25
            ),
            TestCase(
                input="0P",
                expected_output="false",
                is_hidden=True,
                points=25
            )
        ],
        sample_code={
            "python": """# Read input
s = input()

# Your solution here
# Print 'true' or 'false'
""",
            "javascript": """// Read input
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

rl.on('line', (s) => {
    // Your solution here
    // Print 'true' or 'false'
    rl.close();
});
"""
        }
    )
    
    # Problem 3: Fizz Buzz
    fizzbuzz = CodingProblem(
        title="Fizz Buzz",
        description="""Given an integer `n`, return a string array where:

- For multiples of 3, print "Fizz"
- For multiples of 5, print "Buzz"
- For multiples of both 3 and 5, print "FizzBuzz"
- Otherwise, print the number

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
n lines, each containing the result for that number
""",
        difficulty="easy",
        time_limit_sec=2,
        memory_limit_mb=128,
        test_cases=[
            TestCase(
                input="5",
                expected_output="1\n2\nFizz\n4\nBuzz",
                is_hidden=False,
                points=30
            ),
            TestCase(
                input="15",
                expected_output="1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz",
                is_hidden=False,
                points=30
            ),
            TestCase(
                input="3",
                expected_output="1\n2\nFizz",
                is_hidden=True,
                points=40
            )
        ],
        sample_code={
            "python": """# Read input
n = int(input())

# Your solution here
# Print one result per line
""",
            "javascript": """// Read input
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

rl.on('line', (line) => {
    const n = parseInt(line);
    
    // Your solution here
    // Print one result per line
    
    rl.close();
});
"""
        }
    )
    
    # Insert problems
    await connect_to_mongo()
    
    print("Seeding coding problems...")
    
    p1 = await create_problem(two_sum)
    print(f"✓ Created: {p1.title} (ID: {p1.id})")
    
    p2 = await create_problem(palindrome)
    print(f"✓ Created: {p2.title} (ID: {p2.id})")
    
    p3 = await create_problem(fizzbuzz)
    print(f"✓ Created: {p3.title} (ID: {p3.id})")
    
    await close_mongo_connection()
    
    print("\n✅ Seeding complete!")
    print(f"\nCreated {3} problems:")
    print(f"  - {p1.title} ({p1.difficulty})")
    print(f"  - {p2.title} ({p2.difficulty})")
    print(f"  - {p3.title} ({p3.difficulty})")


if __name__ == "__main__":
    asyncio.run(seed_problems())
