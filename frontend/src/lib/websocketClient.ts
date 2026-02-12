import { useInterviewStore } from '@/store/interviewStore';
import { InterviewState } from '@/types/interview';

let warningInterval: NodeJS.Timeout | null = null;
let terminationTimeout: NodeJS.Timeout | null = null;

export const connect = () => {
    // Prevent multiple connections
    if (warningInterval || terminationTimeout) return;

    const store = useInterviewStore.getState();
    if (store.currentState !== InterviewState.IN_PROGRESS) return;

    // Start warning interval (every 5 seconds)
    warningInterval = setInterval(() => {
        const currentStore = useInterviewStore.getState();
        // Only emit events if still in progress
        if (currentStore.currentState === InterviewState.IN_PROGRESS) {
            currentStore.addViolation();
        } else {
            disconnect(); // Auto-disconnect if state changed externally
        }
    }, 5000);

    // Start potential termination timeout (random 12-18s)
    const randomDelay = Math.floor(Math.random() * (18000 - 12000 + 1) + 12000);
    terminationTimeout = setTimeout(() => {
        // 30% chance to terminate
        if (Math.random() < 0.3) {
            const currentStore = useInterviewStore.getState();
            if (currentStore.currentState === InterviewState.IN_PROGRESS) {
                currentStore.setState(InterviewState.TERMINATED);
                disconnect();
            }
        }
    }, randomDelay);
};

export const disconnect = () => {
    if (warningInterval) {
        clearInterval(warningInterval);
        warningInterval = null;
    }
    if (terminationTimeout) {
        clearTimeout(terminationTimeout);
        terminationTimeout = null;
    }
};
