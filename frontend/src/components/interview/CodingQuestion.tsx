import React, { useEffect } from "react"
import { useCodingStore } from "@/store/codingStore"
import ProblemPanel from "@/components/coding/ProblemPanel"
import CodeEditorPanel from "@/components/coding/CodeEditorPanel"
import ResultsPanel from "@/components/coding/ResultsPanel"

interface CodingQuestionProps {
    question: any;
    interviewId?: string | null;
}

export default function CodingQuestion({ question, interviewId }: CodingQuestionProps) {
    const {
        setProblemFromInterview,
        problem,
        results,
        resultSummary,
        isRunning,
        isSubmitting,
        error,
        submissionStatus
    } = useCodingStore()

    useEffect(() => {
        if (question) {
            setProblemFromInterview(question)
        }
    }, [question, setProblemFromInterview])

    if (!problem) return (
        <div className="flex items-center justify-center p-20 animate-pulse text-gray-400 font-medium">
            Loading problem configuration...
        </div>
    )

    return (
        <div className="flex flex-col xl:flex-row gap-2 h-[calc(100vh-100px)] min-h-[600px] bg-[#1a1a1a] p-2">
            {/* Left Column: Problem */}
            <div className="flex-1 xl:w-1/2 h-full flex flex-col">
                <ProblemPanel
                    title={problem.title}
                    difficulty={problem.difficulty}
                    description={problem.description}
                    examples={problem.examples}
                />
            </div>

            {/* Right Column: Editor & Results */}
            <div className="flex-1 xl:w-1/2 flex flex-col gap-2 h-full">
                <div className="flex-[3] overflow-hidden rounded-lg">
                    <CodeEditorPanel />
                </div>
                <div className="flex-[2] overflow-hidden rounded-lg">
                    <ResultsPanel
                        results={results}
                        summary={resultSummary}
                        isRunning={isRunning}
                        isSubmitting={isSubmitting}
                        error={error}
                        submissionStatus={submissionStatus}
                    />
                </div>
            </div>
        </div>
    )
}
