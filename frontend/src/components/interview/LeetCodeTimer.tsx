"use client";

import { useEffect, useState } from "react";

interface LeetCodeTimerProps {
    running?: boolean;
}

export default function LeetCodeTimer({ running = true }: LeetCodeTimerProps) {
    const [seconds, setSeconds] = useState(0);

    useEffect(() => {
        if (!running) return;
        const interval = setInterval(() => {
            setSeconds((s) => s + 1);
        }, 1000);
        return () => clearInterval(interval);
    }, [running]);

    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;

    const formatted = [
        h > 0 ? String(h).padStart(2, "0") : null,
        String(m).padStart(2, "0"),
        String(s).padStart(2, "0"),
    ]
        .filter(Boolean)
        .join(":");

    const isLow = seconds > 0 && h === 0 && m < 5;

    return (
        <span
            className={`font-mono text-sm font-semibold ${isLow ? "text-red-400 animate-pulse" : "text-gray-400"
                }`}
        >
            ⏱ {formatted}
        </span>
    );
}
