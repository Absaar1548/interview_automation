"use client";

interface Problem {
    id: string;
    title: string;
    difficulty: string;
}

interface ProblemListProps {
    problems: Problem[];
    selectedId: string | null;
    onSelect: (id: string) => void;
    loading: boolean;
}

const difficultyColor: Record<string, string> = {
    easy: "text-green-400",
    medium: "text-yellow-400",
    hard: "text-red-400",
};

const difficultyBg: Record<string, string> = {
    easy: "bg-green-900/30",
    medium: "bg-yellow-900/30",
    hard: "bg-red-900/30",
};

export default function ProblemList({
    problems,
    selectedId,
    onSelect,
    loading,
}: ProblemListProps) {
    if (loading) {
        return (
            <div className="flex flex-col gap-2 p-3">
                {[1, 2, 3].map((i) => (
                    <div
                        key={i}
                        className="h-12 rounded-lg bg-gray-700/50 animate-pulse"
                    />
                ))}
            </div>
        );
    }

    return (
        <div className="flex flex-col overflow-y-auto">
            <div className="px-4 py-3 border-b border-gray-700">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                    Problems
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">{problems.length} problems</p>
            </div>
            <div className="flex flex-col gap-1 p-2 overflow-y-auto">
                {problems.map((p, idx) => (
                    <button
                        key={p.id}
                        onClick={() => onSelect(p.id)}
                        className={`flex items-start gap-3 w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150 group ${selectedId === p.id
                                ? "bg-blue-600/20 border border-blue-500/40"
                                : "hover:bg-gray-700/50 border border-transparent"
                            }`}
                    >
                        <span className="text-gray-500 text-xs font-mono mt-0.5 w-5 shrink-0">
                            {idx + 1}.
                        </span>
                        <div className="flex flex-col gap-1 min-w-0">
                            <span
                                className={`text-sm font-medium truncate ${selectedId === p.id
                                        ? "text-blue-300"
                                        : "text-gray-200 group-hover:text-white"
                                    }`}
                            >
                                {p.title}
                            </span>
                            <span
                                className={`text-xs font-medium capitalize px-1.5 py-0.5 rounded w-fit ${difficultyColor[p.difficulty] ?? "text-gray-400"
                                    } ${difficultyBg[p.difficulty] ?? ""}`}
                            >
                                {p.difficulty}
                            </span>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}
