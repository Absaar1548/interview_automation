"use client";

import { useState, useEffect, useRef } from "react";

interface TimerProps {
    durationSec: number;
    onExpire: () => void;
}

export default function Timer({ durationSec, onExpire }: TimerProps) {
    const [remaining, setRemaining] = useState(durationSec);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const onExpireRef = useRef(onExpire);
    const hasExpiredRef = useRef(false);

    useEffect(() => {
        onExpireRef.current = onExpire;
    }, [onExpire]);

    useEffect(() => {
        setRemaining(durationSec);
        hasExpiredRef.current = false;

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        intervalRef.current = setInterval(() => {
            setRemaining((prev) => {
                if (prev <= 1) {
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                    if (!hasExpiredRef.current) {
                        hasExpiredRef.current = true;
                        onExpireRef.current();
                    }
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [durationSec]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    return (
        <div className="text-xl font-mono font-bold text-gray-800 bg-gray-100 px-4 py-2 rounded">
            {formatTime(remaining)}
        </div>
    );
}
