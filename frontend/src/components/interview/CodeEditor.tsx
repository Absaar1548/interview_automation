"use client";

import { useState } from "react";
import Editor from "@monaco-editor/react";

interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
    questionId: string;
}

const SUPPORTED_LANGUAGES = [
    { id: "python", name: "Python", defaultCode: "# Write your Python code here\nprint('Hello, World!')" },
    { id: "javascript", name: "JavaScript", defaultCode: "// Write your JavaScript code here\nconsole.log('Hello, World!');" },
    { id: "java", name: "Java", defaultCode: "// Write your Java code here\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}" },
    { id: "cpp", name: "C++", defaultCode: "// Write your C++ code here\n#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello, World!\" << endl;\n    return 0;\n}" },
];

export default function CodeEditor({ value, onChange, questionId }: CodeEditorProps) {
    const [selectedLanguage, setSelectedLanguage] = useState(SUPPORTED_LANGUAGES[0]);
    const [theme, setTheme] = useState<"vs-dark" | "light">("vs-dark");
    const [output, setOutput] = useState<string>("");
    const [isExecuting, setIsExecuting] = useState(false);
    const [error, setError] = useState<string>("");

    const handleLanguageChange = (languageId: string) => {
        const language = SUPPORTED_LANGUAGES.find((lang) => lang.id === languageId);
        if (language) {
            setSelectedLanguage(language);
            onChange(language.defaultCode);
        }
    };

    const handleEditorChange = (newValue: string | undefined) => {
        onChange(newValue || "");
    };

    const handleRunCode = async () => {
        setIsExecuting(true);
        setError("");
        setOutput("");

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
            const response = await fetch(`${baseUrl}/api/v1/code/execute`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    code: value,
                    language: selectedLanguage.id,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || "Failed to execute code");
            } else if (data.error) {
                setError(data.error);
            } else {
                setOutput(data.output || "");
            }
        } catch (err) {
            setError("Failed to connect to code execution service");
        } finally {
            setIsExecuting(false);
        }
    };

    const toggleTheme = () => {
        setTheme(theme === "vs-dark" ? "light" : "vs-dark");
    };

    return (
        <div className="flex flex-col gap-4 border rounded-lg p-4 bg-gray-50">
            {/* Toolbar */}
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <label className="text-sm font-medium text-gray-700">Language:</label>
                    <select
                        value={selectedLanguage.id}
                        onChange={(e) => handleLanguageChange(e.target.value)}
                        className="px-3 py-2 border rounded bg-white text-sm"
                    >
                        {SUPPORTED_LANGUAGES.map((lang) => (
                            <option key={lang.id} value={lang.id}>
                                {lang.name}
                            </option>
                        ))}
                    </select>

                    <button
                        onClick={toggleTheme}
                        className="px-3 py-2 border rounded bg-white text-sm hover:bg-gray-100"
                    >
                        {theme === "vs-dark" ? "🌞 Light" : "🌙 Dark"}
                    </button>
                </div>

                <button
                    onClick={handleRunCode}
                    disabled={isExecuting || !value.trim()}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium"
                >
                    {isExecuting ? "Running..." : "▶ Run Code"}
                </button>
            </div>

            {/* Monaco Editor */}
            <div className="border rounded overflow-hidden" style={{ height: "400px" }}>
                <Editor
                    height="100%"
                    language={selectedLanguage.id}
                    value={value}
                    onChange={handleEditorChange}
                    theme={theme}
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: "on",
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                        wordWrap: "on",
                    }}
                />
            </div>

            {/* Output Panel */}
            {(output || error) && (
                <div className="border rounded p-4 bg-white">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-sm text-gray-700">Output:</h3>
                        <button
                            onClick={() => {
                                setOutput("");
                                setError("");
                            }}
                            className="text-xs text-gray-500 hover:text-gray-700"
                        >
                            Clear
                        </button>
                    </div>
                    <pre className={`text-sm font-mono whitespace-pre-wrap ${error ? "text-red-600" : "text-gray-800"}`}>
                        {error || output}
                    </pre>
                </div>
            )}
        </div>
    );
}
