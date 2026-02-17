"use client";

import CodeEditor from "@/components/interview/CodeEditor";
import { useState } from "react";

export default function CodeEditorTestPage() {
    const [code, setCode] = useState("# Write your Python code here\nprint('Hello, World!')");

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-6xl mx-auto">
                <h1 className="text-3xl font-bold mb-2 text-gray-800">Monaco Code Editor Test</h1>
                <p className="text-gray-600 mb-6">
                    Lorem ipsum dolor sit amet consectetur adipisicing elit.
                    Cum neque doloremque autem porro temporibus
                    tempore possimus velit non hic soluta nam maxime
                    nobis corrupti pariatur aliquam,
                    maiores reiciendis vero aperiam!
                </p>

                <div className="bg-white rounded-lg shadow-lg p-6">
                    <CodeEditor
                        value={code}
                        onChange={setCode}
                        questionId="test-question-1"
                    />
                </div>

            </div>
        </div>
    );
}
