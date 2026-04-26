const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// In-memory data store for rage statistics
const rageData = {
    totalFrustrations: 0,
    rageClickCount: 0,
    sessions: [],
};

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'UP', message: 'Backend is running and collecting your anger.' });
});

// Endpoint to report rage metrics
app.post('/api/rage', (req, res) => {
    const { action, clicks, timeSpent, details } = req.body;

    // Log the anger
    console.log(`[Rage Event] Action: ${action}, Clicks: ${clicks}, Time Spent: ${timeSpent}ms`);

    rageData.totalFrustrations += 1;
    rageData.rageClickCount += (clicks || 1);

    rageData.sessions.push({
        action,
        clicks,
        timeSpent,
        details,
        timestamp: new Date().toISOString()
    });

    res.status(200).json({
        message: 'Your rage has been successfully recorded. Thank you for your frustration.',
        currentStats: {
            totalFrustrations: rageData.totalFrustrations,
            rageClickCount: rageData.rageClickCount
        }
    });
});

// Endpoint to get the leaderboard of rage
app.get('/api/rage/stats', (req, res) => {
    res.json(rageData);
});

app.listen(PORT, () => {
    console.log(`Rage Collector API is listening on port ${PORT}`);
});
