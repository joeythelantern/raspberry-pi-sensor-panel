import si from 'systeminformation';
import axios from 'axios';

// --- Configuration ---
// Replace with your actual API endpoint
const API_ENDPOINT = 'http://localhost:1337/stats'; 
const SEND_INTERVAL_MS = 5000; // 5 seconds

/**
 * @interface SystemStats
 * @description Defines the structure of the data we will be sending.
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


/**
 * @function getSystemStats
 * @description Gathers various system statistics robustly.
 * @returns {Promise<SystemStats>} A promise that resolves with the system stats.
 */
async function getSystemStats(): Promise<SystemStats> {
    try {
        // Fetch all data concurrently for efficiency
        const [cpuData, gpuData, memData, diskData, networkData, cpuTemp] = await Promise.all([
            si.currentLoad(),
            si.graphics(),
            si.mem(),
            si.disksIO(),
            si.networkStats(),
            si.cpuTemperature()
        ]);

        const stats: SystemStats = {
            timestamp: new Date().toISOString(),
            cpu: {
                usage: cpuData?.currentLoad || null,
                temperature: cpuTemp?.main || null
            },
            gpu: {
                // Note: GPU usage/temp can be tricky and might not be available on all systems/OS.
                usage: gpuData?.controllers?.[0]?.utilizationGpu || null,
                temperature: gpuData?.controllers?.[0]?.temperatureGpu || null
            },
            memory: {
                total: memData?.total || 0,
                used: memData?.used || 0,
                free: memData?.free || 0
            },
            disk: {
                io: {
                    // Safely access disk I/O, defaulting to 0 if unavailable.
                    read: diskData?.rIO || 0,
                    write: diskData?.wIO || 0
                }
            },
            network: {
                io: {
                    // Summing up all interfaces for a total
                    received: networkData?.reduce((acc, iface) => acc + (iface.rx_bytes || 0), 0) || 0,
                    sent: networkData?.reduce((acc, iface) => acc + (iface.tx_bytes || 0), 0) || 0
                }
            }
        };

        return stats;
    } catch (error) {
        console.error("Error gathering system stats:", error);
        // Re-throw the error to be caught by the caller
        throw error;
    }
}

/**
 * @function sendSystemStats
 * @description Sends the collected system stats to the API endpoint.
 * @param {SystemStats} stats - The system statistics to send.
 */
async function sendSystemStats(stats: SystemStats): Promise<void> {
    try {
        console.log('Sending data to API:', JSON.stringify(stats, null, 2));
        const response = await axios.post(API_ENDPOINT, stats, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        console.log(`Data sent successfully. API responded with status: ${response.status}`);
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error('Error sending data to API:', error.message);
            if (error.response) {
                console.error('API Response:', error.response.data);
            }
        } else {
            console.error('An unexpected error occurred:', error);
        }
    }
}

/**
 * @function main
 * @description The main function of the application.
 */
function main() {
    console.log('Starting system stats monitor...');
    console.log(`Data will be sent to ${API_ENDPOINT} every ${SEND_INTERVAL_MS / 1000} seconds.`);

    // Set an interval to collect and send data
    setInterval(async () => {
        try {
            const stats = await getSystemStats();
            console.log("Sending Stats: ", stats);
            await sendSystemStats(stats);
        } catch (error) {
            // The error is already logged in getSystemStats, but you could add more handling here if needed.
            console.error("Failed to process and send stats.");
        }
    }, SEND_INTERVAL_MS);

    // Initial run
    (async () => {
        try {
            const stats = await getSystemStats();
            await sendSystemStats(stats);
        } catch (error) {
            console.error("Failed to process and send stats on initial run.");
        }
    })();
}

// --- Start the application ---
main();
