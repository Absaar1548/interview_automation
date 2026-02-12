import { InterviewQuestion } from '@/types/interview';

interface QuestionPanelProps {
    question: InterviewQuestion;
}

export default function QuestionPanel({ question }: QuestionPanelProps) {
    return (
        <div className="mt-8 border p-6 rounded-lg bg-gray-50 dark:bg-gray-900 w-full max-w-2xl text-left">
            <h2 className="text-2xl font-semibold mb-2">Question</h2>
            <div className="flex gap-4 mb-4 text-sm text-gray-500 dark:text-gray-400">
                <span className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">{question.category}</span>
                <span className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">{question.difficulty}</span>
                <span className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">{question.answer_mode}</span>
            </div>
            <p className="text-xl mb-8 font-medium">{question.prompt}</p>
        </div>
    );
}
