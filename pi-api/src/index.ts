import express, { Request, Response } from 'express';
import cors from 'cors';

// --- Configuration ---
const PORT = process.env.PORT || 1337;
const MAX_HISTORY_LENGTH = 60;

/**
 * @interface SystemStats
 * @description Defines the structure of the data we expect to receive.
 * This should match the interface in the sender application.
 */
interface SystemStats {
    timestamp: string;
    cpu: {
        usage: number | null;
        temperature: number | null;
    };
    gpu: {
        usage: number | null;
        temperature: number | null;
    };
    memory: {
        total: number;
        used: number;
        free: number;
    };
    disk: {
        io: {
            read: number;
            write: number;
        };
    };
    network: {
        io: {
            received: number;
            sent: number;
        };
    };
}

// --- In-Memory Storage ---
// An array to store the history of received stats.
const statsHistory: SystemStats[] = [];

// --- Express App Setup ---
const app = express();

// Middlewares
app.use(cors()); // Enable Cross-Origin Resource Sharing
app.use(express.json()); // Enable JSON body parsing

// --- API Endpoints ---

/**
 * @route   POST /stats
 * @desc    Receives system stats from a client and stores them.
 * @access  Public
 */
app.post('/stats', (req: Request, res: Response) => {
    const newStats: SystemStats = req.body;

    // Basic validation to ensure we have a timestamp
    if (!newStats || !newStats.timestamp) {
        return res.status(400).json({ message: 'Invalid data format. Timestamp is required.' });
    }
    
    // Add the new stats to the beginning of the array
    statsHistory.unshift(newStats);

    // Trim the array to keep only the last MAX_HISTORY_LENGTH entries
    if (statsHistory.length > MAX_HISTORY_LENGTH) {
        statsHistory.length = MAX_HISTORY_LENGTH; // More efficient than splice
    }

    console.log(`Received new stats at ${newStats.timestamp}. History size: ${statsHistory.length}`);
    res.status(201).json({ message: 'Stats received successfully.' });
});

/**
 * @route   GET /stats/latest
 * @desc    Returns the most recently received system stats.
 * @access  Public
 */
app.get('/stats/latest', (req: Request, res: Response) => {
    if (statsHistory.length === 0) {
        return res.status(404).json({ message: 'No stats available yet.' });
    }

    // The latest stats are at the first index since we use unshift()
    const latestStats = statsHistory[0];
    res.status(200).json(latestStats);
});

/**
 * @route   GET /stats/history
 * @desc    Returns the entire history of received stats.
 * @access  Public
 */
app.get('/stats/history', (req: Request, res: Response) => {
    res.status(200).json(statsHistory);
});


// --- Start Server ---
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});