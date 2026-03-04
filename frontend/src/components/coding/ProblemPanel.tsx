"use client";

interface TestCaseExample {
    input: string;
    expected_output: string;
    order: number;
}

interface ProblemPanelProps {
    title: string;
    difficulty: string;
    description: string;
    examples: TestCaseExample[];
}

const DIFFICULTY_STYLES: Record<string, string> = {
    easy: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    hard: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function ProblemPanel({
    title,
    difficulty,
    description,
    examples,
}: ProblemPanelProps) {
    return (
        <div className="h-full overflow-y-auto bg-[#1e1e2e] text-gray-200 p-6">
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
                <h1 className="text-xl font-bold text-white">{title}</h1>
                <span
                    className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border capitalize ${DIFFICULTY_STYLES[difficulty] || DIFFICULTY_STYLES.easy
                        }`}
                >
                    {difficulty}
                </span>
            </div>

            {/* Description */}
            <div className="prose prose-invert prose-sm max-w-none mb-6">
                {description.split("\n").map((line, i) => {
                    if (line.startsWith("## ")) {
                        return (
                            <h2 key={i} className="text-lg font-bold text-white mt-4 mb-2">
                                {line.replace("## ", "")}
                            </h2>
                        );
                    }
                    if (line.startsWith("### ")) {
                        return (
                            <h3 key={i} className="text-base font-semibold text-gray-300 mt-3 mb-1">
                                {line.replace("### ", "")}
                            </h3>
                        );
                    }
                    if (line.startsWith("- ")) {
                        return (
                            <li key={i} className="text-gray-400 ml-4 list-disc text-sm">
                                {renderInlineCode(line.replace("- ", ""))}
                            </li>
                        );
                    }
                    if (line.trim() === "") return <div key={i} className="h-2" />;
                    return (
                        <p key={i} className="text-gray-400 text-sm leading-relaxed">
                            {renderInlineCode(line)}
                        </p>
                    );
                })}
            </div>

            {/* Examples */}
            <div className="space-y-4">
                <h3 className="text-base font-semibold text-white">Examples</h3>
                {examples.map((ex, i) => (
                    <div
                        key={i}
                        className="bg-[#181825] border border-[#313244] rounded-lg p-4"
                    >
                        <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">
                            Example {i + 1}
                        </div>
                        <div className="space-y-2">
                            <div>
                                <span className="text-xs font-medium text-gray-500">Input:</span>
                                <pre className="mt-1 bg-[#11111b] rounded px-3 py-2 text-sm text-emerald-300 font-mono whitespace-pre-wrap overflow-x-auto">
                                    {ex.input}
                                </pre>
                            </div>
                            <div>
                                <span className="text-xs font-medium text-gray-500">Output:</span>
                                <pre className="mt-1 bg-[#11111b] rounded px-3 py-2 text-sm text-sky-300 font-mono whitespace-pre-wrap overflow-x-auto">
                                    {ex.expected_output}
                                </pre>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function renderInlineCode(text: string) {
    const parts = text.split(/(`[^`]+`)/g);
    return parts.map((part, i) => {
        if (part.startsWith("`") && part.endsWith("`")) {
            return (
                <code
                    key={i}
                    className="bg-[#313244] text-pink-400 px-1.5 py-0.5 rounded text-xs font-mono"
                >
                    {part.slice(1, -1)}
                </code>
            );
        }
        return <span key={i}>{part}</span>;
    });
}
