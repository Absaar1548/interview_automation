"use client";

import Editor from "@monaco-editor/react";
import {
    SupportedLanguage,
    LANGUAGE_LABELS,
    MONACO_LANGUAGE_MAP,
    useCodingStore,
} from "@/store/codingStore";

export default function CodeEditorPanel() {
    const language = useCodingStore((s) => s.language);
    const code = useCodingStore((s) => s.code);
    const isSubmitted = useCodingStore((s) => s.isSubmitted);
    const setLanguage = useCodingStore((s) => s.setLanguage);
    const setCode = useCodingStore((s) => s.setCode);

    const currentCode = code[language] || "";
    const monacoLang = MONACO_LANGUAGE_MAP[language];

    return (
        <div className="flex flex-col h-full bg-[#1e1e2e]">
            {/* Language selector */}
            <div className="flex items-center gap-2 px-4 py-2 bg-[#181825] border-b border-[#313244]">
                <label className="text-xs text-gray-500 font-medium">Language:</label>
                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
                    disabled={isSubmitted}
                    className="bg-[#313244] text-gray-200 text-sm rounded-md px-3 py-1.5 border border-[#45475a] focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 cursor-pointer"
                >
                    {(Object.keys(LANGUAGE_LABELS) as SupportedLanguage[]).map(
                        (lang) => (
                            <option key={lang} value={lang}>
                                {LANGUAGE_LABELS[lang]}
                            </option>
                        )
                    )}
                </select>
            </div>

            {/* Monaco Editor */}
            <div className="flex-1 min-h-0">
                <Editor
                    height="100%"
                    language={monacoLang}
                    value={currentCode}
                    onChange={(val) => setCode(val || "")}
                    theme="vs-dark"
                    options={{
                        fontSize: 14,
                        fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                        wordWrap: "on",
                        readOnly: isSubmitted,
                        padding: { top: 12 },
                        lineNumbers: "on",
                        renderLineHighlight: "line",
                        bracketPairColorization: { enabled: true },
                        cursorBlinking: "smooth",
                        smoothScrolling: true,
                    }}
                />
            </div>
        </div>
    );
}
