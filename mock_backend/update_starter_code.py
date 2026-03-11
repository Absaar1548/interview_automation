import asyncio
import json
from sqlalchemy import select
from app.db.sql.session import AsyncSessionLocal
from app.db.sql.models.coding_problem import CodingProblem

BOILERPLATES = {
    "Two Sum": {
        "python3": """import sys, json

def two_sum(nums, target):
    # Your code here
    pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 2:
        nums = json.loads(lines[0])
        target = json.loads(lines[1])
        result = two_sum(nums, target)
        print(json.dumps(result).replace(' ', ''))
""",
        "javascript": """const fs = require('fs');

function twoSum(nums, target) {
    // Your code here
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 2) {
    const nums = JSON.parse(input[0]);
    const target = JSON.parse(input[1]);
    const result = twoSum(nums, target);
    console.log(JSON.stringify(result).replace(/ /g, ''));
}
""",
        "java": """import java.util.*;
import java.io.*;

class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Your code here
        return new int[]{};
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line1 = reader.readLine();
        String line2 = reader.readLine();
        if (line1 != null && line2 != null) {
            String[] parts = line1.replace("[", "").replace("]", "").split(",");
            int[] nums = new int[parts.length];
            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i].trim());
            int target = Integer.parseInt(line2.trim());
            
            Solution sol = new Solution();
            int[] res = sol.twoSum(nums, target);
            System.out.print("[");
            for (int i = 0; i < res.length; i++) {
                System.out.print(res[i]);
                if (i < res.length - 1) System.out.print(",");
            }
            System.out.println("]");
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>

using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Your code here
        return {};
    }
};

int main() {
    string line1, line2;
    if (getline(cin, line1) && getline(cin, line2)) {
        vector<int> nums;
        string cleaned = line1.substr(1, line1.length() - 2);
        stringstream ss(cleaned);
        string item;
        while (getline(ss, item, ',')) {
            nums.push_back(stoi(item));
        }
        int target = stoi(line2);
        
        Solution sol;
        vector<int> res = sol.twoSum(nums, target);
        cout << "[";
        for (size_t i = 0; i < res.size(); i++) {
            cout << res[i] << (i < res.size() - 1 ? "," : "");
        }
        cout << "]" << endl;
    }
    return 0;
}
"""
    },
    "Palindrome Number": {
        "python3": """import sys, json

def is_palindrome(x):
    # Your code here
    pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 1:
        x = int(lines[0])
        result = is_palindrome(x)
        print("true" if result else "false")
""",
        "javascript": """const fs = require('fs');

function isPalindrome(x) {
    // Your code here
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 1) {
    const x = parseInt(input[0]);
    const result = isPalindrome(x);
    console.log(result ? "true" : "false");
}
""",
        "java": """import java.util.*;
import java.io.*;

class Solution {
    public boolean isPalindrome(int x) {
        // Your code here
        return false;
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line = reader.readLine();
        if (line != null) {
            int x = Integer.parseInt(line.trim());
            Solution sol = new Solution();
            boolean res = sol.isPalindrome(x);
            System.out.println(res ? "true" : "false");
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <string>

using namespace std;

class Solution {
public:
    bool isPalindrome(int x) {
        // Your code here
        return false;
    }
};

int main() {
    string line;
    if (getline(cin, line)) {
        int x = stoi(line);
        Solution sol;
        bool res = sol.isPalindrome(x);
        cout << (res ? "true" : "false") << endl;
    }
    return 0;
}
"""
    },
    "FizzBuzz": {
        "python3": """import sys, json

def fizz_buzz(n):
    # Your code here
    pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 1:
        n = int(lines[0])
        result = fizz_buzz(n)
        print(json.dumps(result).replace(' ', ''))
""",
        "javascript": """const fs = require('fs');

function fizzBuzz(n) {
    // Your code here
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 1) {
    const n = parseInt(input[0]);
    const result = fizzBuzz(n);
    console.log(JSON.stringify(result).replace(/ /g, ''));
}
""",
        "java": """import java.util.*;
import java.io.*;

class Solution {
    public List<String> fizzBuzz(int n) {
        // Your code here
        return new ArrayList<>();
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line = reader.readLine();
        if (line != null) {
            int n = Integer.parseInt(line.trim());
            Solution sol = new Solution();
            List<String> res = sol.fizzBuzz(n);
            System.out.print("[");
            for (int i = 0; i < res.size(); i++) {
                System.out.print("\\"" + res.get(i) + "\\"");
                if (i < res.size() - 1) System.out.print(",");
            }
            System.out.println("]");
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <vector>
#include <string>

using namespace std;

class Solution {
public:
    vector<string> fizzBuzz(int n) {
        // Your code here
        return {};
    }
};

int main() {
    string line;
    if (getline(cin, line)) {
        int n = stoi(line);
        Solution sol;
        vector<string> res = sol.fizzBuzz(n);
        cout << "[";
        for (size_t i = 0; i < res.size(); i++) {
            cout << "\\"" << res[i] << "\\"" << (i < res.size() - 1 ? "," : "");
        }
        cout << "]" << endl;
    }
    return 0;
}
"""
    },
    "Merge Two Sorted Lists": {
        "python3": """import sys, json

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def merge_two_lists(list1, list2):
    # Your code here
    pass

def build_list(arr):
    dummy = ListNode()
    curr = dummy
    for val in arr:
        curr.next = ListNode(val)
        curr = curr.next
    return dummy.next

def serialize_list(node):
    res = []
    while node:
        res.append(node.val)
        node = node.next
    return res

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 2:
        l1_arr = json.loads(lines[0])
        l2_arr = json.loads(lines[1])
        result = merge_two_lists(build_list(l1_arr), build_list(l2_arr))
        print(json.dumps(serialize_list(result)).replace(' ', ''))
""",
        "javascript": """const fs = require('fs');

function ListNode(val, next) {
    this.val = (val===undefined ? 0 : val)
    this.next = (next===undefined ? null : next)
}

function mergeTwoLists(list1, list2) {
    // Your code here
}

function buildList(arr) {
    let dummy = new ListNode();
    let curr = dummy;
    for (let val of arr) {
        curr.next = new ListNode(val);
        curr = curr.next;
    }
    return dummy.next;
}

function serializeList(node) {
    let res = [];
    while (node) {
        res.push(node.val);
        node = node.next;
    }
    return res;
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 2) {
    const l1Arr = JSON.parse(input[0]);
    const l2Arr = JSON.parse(input[1]);
    const result = mergeTwoLists(buildList(l1Arr), buildList(l2Arr));
    console.log(JSON.stringify(serializeList(result)).replace(/ /g, ''));
}
""",
        "java": """import java.util.*;
import java.io.*;

class ListNode {
    int val;
    ListNode next;
    ListNode() {}
    ListNode(int val) { this.val = val; }
    ListNode(int val, ListNode next) { this.val = val; this.next = next; }
}

class Solution {
    public ListNode mergeTwoLists(ListNode list1, ListNode list2) {
        // Your code here
        return null;
    }

    public static ListNode buildList(int[] arr) {
        ListNode dummy = new ListNode();
        ListNode curr = dummy;
        for (int val : arr) {
            curr.next = new ListNode(val);
            curr = curr.next;
        }
        return dummy.next;
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line1 = reader.readLine();
        String line2 = reader.readLine();
        if (line1 != null && line2 != null) {
            String[] p1 = line1.replace("[", "").replace("]", "").split(",");
            int[] arr1 = new int[p1.length == 1 && p1[0].isEmpty() ? 0 : p1.length];
            if (arr1.length > 0) for (int i = 0; i < p1.length; i++) arr1[i] = Integer.parseInt(p1[i].trim());

            String[] p2 = line2.replace("[", "").replace("]", "").split(",");
            int[] arr2 = new int[p2.length == 1 && p2[0].isEmpty() ? 0 : p2.length];
            if (arr2.length > 0) for (int i = 0; i < p2.length; i++) arr2[i] = Integer.parseInt(p2[i].trim());
            
            Solution sol = new Solution();
            ListNode res = sol.mergeTwoLists(buildList(arr1), buildList(arr2));
            
            System.out.print("[");
            while (res != null) {
                System.out.print(res.val);
                if (res.next != null) System.out.print(",");
                res = res.next;
            }
            System.out.println("]");
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>

using namespace std;

struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};

class Solution {
public:
    ListNode* mergeTwoLists(ListNode* list1, ListNode* list2) {
        // Your code here
        return nullptr;
    }
};

ListNode* buildList(const vector<int>& arr) {
    ListNode dummy;
    ListNode* curr = &dummy;
    for (int val : arr) {
        curr->next = new ListNode(val);
        curr = curr->next;
    }
    return dummy.next;
}

int main() {
    string line1, line2;
    if (getline(cin, line1) && getline(cin, line2)) {
        vector<int> arr1, arr2;
        
        string cleaned1 = line1.substr(1, line1.length() - 2);
        if (!cleaned1.empty()) {
            stringstream ss1(cleaned1);
            string item;
            while (getline(ss1, item, ',')) arr1.push_back(stoi(item));
        }

        string cleaned2 = line2.substr(1, line2.length() - 2);
        if (!cleaned2.empty()) {
            stringstream ss2(cleaned2);
            string item;
            while (getline(ss2, item, ',')) arr2.push_back(stoi(item));
        }
        
        Solution sol;
        ListNode* res = sol.mergeTwoLists(buildList(arr1), buildList(arr2));
        cout << "[";
        while (res != nullptr) {
            cout << res->val << (res->next ? "," : "");
            res = res->next;
        }
        cout << "]" << endl;
    }
    return 0;
}
"""
    },
    "Longest Substring Without Repeating Characters": {
        "python3": """import sys, json

def length_of_longest_substring(s):
    # Your code here
    pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 1:
        s = json.loads(lines[0])
        result = length_of_longest_substring(s)
        print(result)
""",
        "javascript": """const fs = require('fs');

function lengthOfLongestSubstring(s) {
    // Your code here
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 1) {
    const s = JSON.parse(input[0]);
    const result = lengthOfLongestSubstring(s);
    console.log(result);
}
""",
        "java": """import java.util.*;
import java.io.*;

class Solution {
    public int lengthOfLongestSubstring(String s) {
        // Your code here
        return 0;
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line = reader.readLine();
        if (line != null) {
            // Remove surround quotes
            if (line.length() >= 2 && line.startsWith("\\"") && line.endsWith("\\"")) {
                line = line.substring(1, line.length() - 1);
            }
            Solution sol = new Solution();
            int res = sol.lengthOfLongestSubstring(line);
            System.out.println(res);
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <string>

using namespace std;

class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        // Your code here
        return 0;
    }
};

int main() {
    string line;
    if (getline(cin, line)) {
        if (line.length() >= 2 && line.front() == '"' && line.back() == '"') {
            line = line.substr(1, line.length() - 2);
        }
        Solution sol;
        int res = sol.lengthOfLongestSubstring(line);
        cout << res << endl;
    }
    return 0;
}
"""
    },
    "Valid Anagram": {
        "python3": """import sys, json

def is_anagram(s, t):
    # Your code here
    pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(lines) >= 2:
        s = json.loads(lines[0])
        t = json.loads(lines[1])
        result = is_anagram(s, t)
        print("true" if result else "false")
""",
        "javascript": """const fs = require('fs');

function isAnagram(s, t) {
    // Your code here
}

const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split('\\n');
if (input.length >= 2) {
    const s = JSON.parse(input[0]);
    const t = JSON.parse(input[1]);
    const result = isAnagram(s, t);
    console.log(result ? "true" : "false");
}
""",
        "java": """import java.util.*;
import java.io.*;

class Solution {
    public boolean isAnagram(String s, String t) {
        // Your code here
        return false;
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line1 = reader.readLine();
        String line2 = reader.readLine();
        if (line1 != null && line2 != null) {
            if (line1.length() >= 2) line1 = line1.substring(1, line1.length() - 1);
            if (line2.length() >= 2) line2 = line2.substring(1, line2.length() - 1);
            Solution sol = new Solution();
            boolean res = sol.isAnagram(line1, line2);
            System.out.println(res ? "true" : "false");
        }
    }
}
""",
        "cpp": """#include <iostream>
#include <string>

using namespace std;

class Solution {
public:
    bool isAnagram(string s, string t) {
        // Your code here
        return false;
    }
};

int main() {
    string line1, line2;
    if (getline(cin, line1) && getline(cin, line2)) {
        if (line1.length() >= 2) line1 = line1.substr(1, line1.length() - 2);
        if (line2.length() >= 2) line2 = line2.substr(1, line2.length() - 2);
        Solution sol;
        bool res = sol.isAnagram(line1, line2);
        cout << (res ? "true" : "false") << endl;
    }
    return 0;
}
"""
    }
}

async def update_problems():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CodingProblem))
        problems = result.scalars().all()
        updated_count = 0
        for p in problems:
            if p.title in BOILERPLATES:
                print(f"Updating: {p.title}")
                # Set Python, JS, Java, and C++ properly
                p.starter_code = BOILERPLATES[p.title]
                session.add(p)
                updated_count += 1
        
        await session.commit()
        print(f"Successfully updated {updated_count} starter_code sets.")

if __name__ == "__main__":
    asyncio.run(update_problems())
