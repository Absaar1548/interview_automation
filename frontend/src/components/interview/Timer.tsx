import { useEffect, useState } from 'react';

interface TimerProps {
    duration: number;
    active: boolean;
    onExpire: () => void;
}

export default function Timer({ duration, active, onExpire }: TimerProps) {
    const [timeLeft, setTimeLeft] = useState(duration);

    useEffect(() => {
        // Reset timer when duration changes or it becomes active
        setTimeLeft(duration);
    }, [duration, active]);

    useEffect(() => {
        if (!active || timeLeft <= 0) return;

        const intervalId = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(intervalId);
                    onExpire();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(intervalId);
    }, [active, timeLeft, onExpire]);

    // Format time as MM:SS
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    return (
        <div className={`text-xl font-mono font-bold ${timeLeft < 10 ? 'text-red-500 animate-pulse' : 'text-gray-700 dark:text-gray-300'}`}>
            {formattedTime}
        </div>
    );
}
