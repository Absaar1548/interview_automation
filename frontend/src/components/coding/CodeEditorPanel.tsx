import React from "react"
import Editor from "@monaco-editor/react"
import { useCodingStore } from "@/store/codingStore"
import { useInterviewStore } from "@/store/interviewStore"

export default function CodeEditorPanel() {
    const {
        language,
        code,
        setCode,
        setLanguage,
        problem,
        isSubmitted,
        isSubmitting,
        isRunning,
        runCurrentCode,
        submitCurrentCode
    } = useCodingStore()

    const interviewId = useInterviewStore(s => s.interviewId)
    // We don't have a direct candidateId in interviewStore, but we can get it from auth if needed, 
    // or the backend can infer it from the interview session.
    // For now, let's just pass interviewId.

    const handleEditorChange = (value: string | undefined) => {
        setCode(value || "")
    }

    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setLanguage(e.target.value)
    }

    const supportedLanguages = [
        { label: "Python3", value: "python3", monaco: "python" },
        { label: "JavaScript", value: "javascript", monaco: "javascript" },
        { label: "Java", value: "java", monaco: "java" },
        { label: "C++", value: "cpp", monaco: "cpp" }
    ]

    const currentMonacoLang = supportedLanguages.find(l => l.value === language)?.monaco || "python"

    return (
        <div className="flex flex-col h-full bg-[#1e1e1e] rounded-lg overflow-hidden border border-[#3e3e42] shadow-xl">
            <div className="px-4 py-2 border-b border-[#3e3e42] flex items-center justify-between bg-[#313131]">
                <div className="flex items-center gap-4">
                    <select
                        value={language}
                        onChange={handleLanguageChange}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="bg-[#3e3e42] text-[#eff1f6] border border-[#5c5c60] rounded px-3 py-1.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-[#7a7a7d] disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
                    >
                        {supportedLanguages.map(l => (
                            <option key={l.value} value={l.value}>
                                {l.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => runCurrentCode()}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="px-4 py-1.5 bg-[#3e3e42] text-[#eff1f6] text-xs font-bold rounded-md hover:bg-[#4a4a4e] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                    >
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6V4z" /></svg>
                        Run
                    </button>
                    <button
                        onClick={() => submitCurrentCode(interviewId || undefined)}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="px-4 py-1.5 bg-[#2cbb5d] text-white text-xs font-bold rounded-md hover:bg-[#32cd66] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                    >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        Submit
                    </button>
                </div>
            </div>

            <div className="flex-1 relative min-h-[400px] bg-[#1e1e1e]">
                <Editor
                    height="100%"
                    language={currentMonacoLang}
                    theme="vs-dark"
                    value={code}
                    onChange={handleEditorChange}
                    options={{
                        readOnly: isSubmitted,
                        minimap: { enabled: false },
                        fontSize: 14,
                        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        padding: { top: 16, bottom: 16 },
                        renderLineHighlight: "all",
                        matchBrackets: "always",
                    }}
                />
                {isSubmitted && (
                    <div className="absolute inset-0 bg-[#1e1e1e]/60 z-10 pointer-events-none flex items-center justify-center backdrop-blur-[1px]">
                        <div className="bg-[#2cbb5d] text-white px-6 py-2 rounded-full shadow-lg text-sm font-bold tracking-wide translate-y-20">
                            Solution Submitted - View Only
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
