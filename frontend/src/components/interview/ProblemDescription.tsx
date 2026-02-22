"use client";

interface TestCase {
    input: string;
    expected_output: string;
    is_hidden: boolean;
}

interface ProblemDescriptionProps {
    title: string;
    difficulty: string;
    description: string;
    timeLimitSec: number;
    memoryLimitMb: number;
    testCases: TestCase[];
}

const difficultyColor: Record<string, string> = {
    easy: "text-green-400 bg-green-900/30 border-green-700/40",
    medium: "text-yellow-400 bg-yellow-900/30 border-yellow-700/40",
    hard: "text-red-400 bg-red-900/30 border-red-700/40",
};

export default function ProblemDescription({
    title,
    difficulty,
    description,
    timeLimitSec,
    memoryLimitMb,
}: ProblemDescriptionProps) {
    // Parse the description to render nicely
    const paragraphs = description.split("\n\n");

    const renderParagraph = (text: string, idx: number) => {
        // Code block
        if (text.includes("```")) {
            const parts = text.split("```");
            return (
                <div key={idx}>
                    {parts.map((part, pIdx) =>
                        pIdx % 2 === 1 ? (
                            <pre
                                key={pIdx}
                                className="bg-gray-900/80 rounded-lg p-3 text-xs font-mono text-gray-200 overflow-x-auto border border-gray-700 my-2 whitespace-pre-wrap"
                            >
                                {part.trim()}
                            </pre>
                        ) : (
                            <span
                                key={pIdx}
                                className="text-sm text-gray-300 leading-relaxed"
                                dangerouslySetInnerHTML={{
                                    __html: part
                                        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                                        .replace(/`(.+?)`/g, '<code class="bg-gray-700 px-1 rounded text-blue-300 text-xs">$1</code>')
                                        .replace(/\n/g, "<br/>"),
                                }}
                            />
                        )
                    )}
                </div>
            );
        }

        // Bold headers like **Example 1:**
        if (text.startsWith("**")) {
            return (
                <p
                    key={idx}
                    className="text-sm text-gray-300 leading-relaxed"
                    dangerouslySetInnerHTML={{
                        __html: text
                            .replace(/\*\*(.+?)\*\*/g, "<strong class='text-gray-100'>$1</strong>")
                            .replace(/`(.+?)`/g, '<code class="bg-gray-700 px-1 rounded text-blue-300 text-xs">$1</code>')
                            .replace(/\n/g, "<br/>"),
                    }}
                />
            );
        }

        // Bullet list
        if (text.includes("\n- ")) {
            const lines = text.split("\n");
            return (
                <ul key={idx} className="list-disc list-inside space-y-1">
                    {lines.map((line, lIdx) => (
                        <li
                            key={lIdx}
                            className="text-sm text-gray-300"
                            dangerouslySetInnerHTML={{
                                __html: line
                                    .replace(/^- /, "")
                                    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                                    .replace(/`(.+?)`/g, '<code class="bg-gray-700 px-1 rounded text-blue-300 text-xs">$1</code>'),
                            }}
                        />
                    ))}
                </ul>
            );
        }

        return (
            <p
                key={idx}
                className="text-sm text-gray-300 leading-relaxed"
                dangerouslySetInnerHTML={{
                    __html: text
                        .replace(/\*\*(.+?)\*\*/g, "<strong class='text-gray-100'>$1</strong>")
                        .replace(/`(.+?)`/g, '<code class="bg-gray-700 px-1 rounded text-blue-300 text-xs">$1</code>')
                        .replace(/\n/g, "<br/>"),
                }}
            />
        );
    };

    return (
        <div className="h-full overflow-y-auto p-5">
            {/* Title + difficulty */}
            <div className="flex items-start gap-3 mb-4">
                <h1 className="text-xl font-bold text-white">{title}</h1>
                <span
                    className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full capitalize border mt-0.5 ${difficultyColor[difficulty] ?? "text-gray-400 bg-gray-800 border-gray-700"
                        }`}
                >
                    {difficulty}
                </span>
            </div>

            {/* Meta chips */}
            <div className="flex gap-3 mb-5">
                <span className="text-xs text-gray-500 bg-gray-800 rounded px-2 py-1">
                    ⏱ Time Limit: {timeLimitSec}s
                </span>
                <span className="text-xs text-gray-500 bg-gray-800 rounded px-2 py-1">
                    💾 Memory: {memoryLimitMb} MB
                </span>
            </div>

            {/* Description */}
            <div className="flex flex-col gap-3">
                {paragraphs.map((para, idx) => renderParagraph(para.trim(), idx))}
            </div>
        </div>
    );
}
