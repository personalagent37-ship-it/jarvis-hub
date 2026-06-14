const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');
const path = require('path');
const os = require('os');
const qrImage = require('qrcode');

const app = express();
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public'));

let connectionStatus = 'Starting...';
let messageLogs = [];
let botSentMessageTexts = []; // Track text sent by Jarvis API to prevent loops
let latestQR = null;
let cachedContacts = null;

const fs = require('fs');
const STATS_FILE = path.join(__dirname, 'stats.json');
let stats = { totalRequests: 0, totalTokens: 0, estimatedCost: 0 };
if (fs.existsSync(STATS_FILE)) {
    try { stats = JSON.parse(fs.readFileSync(STATS_FILE, 'utf8')); } catch(e) {}
}

function updateStats(text) {
    stats.totalRequests += 1;
    const words = text ? text.split(' ').length : 0;
    stats.totalTokens += (words * 1.5) + 300;
    fs.writeFileSync(STATS_FILE, JSON.stringify(stats));
}

function addLog(direction, from, to, body) {
    messageLogs.unshift({ id: Date.now() + Math.random(), time: new Date().toLocaleTimeString(), direction, from, to, body });
    if (messageLogs.length > 50) messageLogs.pop();
}

// Set up the WhatsApp Client
// We use LocalAuth to save the session locally so you don't have to scan the QR code every time
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: path.join(__dirname, 'whatsapp_session') }),
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html',
    },
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-gpu',
            '--disable-extensions'
        ]
    },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
});

// Generate QR Code for authentication
client.on('qr', (qr) => {
    connectionStatus = 'Waiting for QR Scan';
    latestQR = qr;
    console.log('========================================================================');
    console.log(' JARVIS HUB ACTION REQUIRED: Please scan this QR code with your WhatsApp!');
    console.log('========================================================================');
    qrcode.generate(qr, { small: true });
});

// Authenticated Event
client.on('authenticated', () => {
    connectionStatus = 'Connected & Ready';
    latestQR = null;
    console.log('✅ JARVIS HUB: Successfully authenticated with WhatsApp!');
    console.log('🚀 JARVIS HUB: You can now start sending messages!');
});

// Ready Event
client.on('ready', async () => {
    console.log('[DEBUG] WhatsApp Web DOM is fully loaded.');
    console.log('[DEBUG] Pre-fetching contacts to avoid timeouts later...');
    try {
        const contacts = await client.getContacts();
        cachedContacts = contacts.map(c => ({ name: c.name || c.pushname || c.number, id: c.id._serialized }));
        console.log(`[DEBUG] Successfully cached ${cachedContacts.length} contacts!`);
    } catch (e) {
        console.error('[DEBUG] Failed to pre-fetch contacts:', e);
    }
});

client.on('disconnected', (reason) => {
    console.log('[JARVIS HUB ERROR] WhatsApp disconnected:', reason);
    connectionStatus = 'Disconnected. Restarting...';
    // Forcefully exit the node process so systemd will automatically restart the entire background service
    process.exit(1); 
});

// Listen for incoming WhatsApp messages (including messages you send to yourself)
client.on('message_create', async (msg) => {
    try {
        const body = msg.body ? msg.body.trim() : '';
        if (!body) return;
        
        const myNumber = client.info && client.info.wid ? client.info.wid.user : '';
        
        if (!myNumber) {
            console.log('[DEBUG] Warning: myNumber is empty. client.info might not be loaded yet.');
        }
        
        const lowerBody = body.toLowerCase();
        const explicitlyCalled = lowerBody.startsWith('jarvis') || lowerBody.startsWith('coder') || lowerBody.startsWith('antigravity');
        
        // TRUE self chat: matches exact phone number OR matches your exact private WhatsApp @lid
        const myLid = '171691921666125';
        const isSelfChat = msg.fromMe && (msg.to === msg.from || (myNumber && msg.to.includes(myNumber)) || msg.to.includes(myLid));
        
        // USER REQUIREMENT: Only process the message if Jarvis is explicitly called OR if it's a true self-chat.
        if (!isSelfChat && !explicitlyCalled) {
            return;
        }
        
        console.log(`\n[DEBUG] JARVIS INTERCEPTED MESSAGE. Body: "${body}". From: "${msg.from}", To: "${msg.to}"`);
        
        // Log the message to the dashboard
        addLog(msg.fromMe ? 'outbound' : 'inbound', msg.from, msg.to, body);

        // RACE CONDITION FIX: Ignore exact or partial messages sent by Jarvis API to prevent infinite loops
        // WhatsApp sometimes strips trailing spaces, or normalizes newlines, so we check if the body starts with or matches our sent text.
        const isBotMessage = botSentMessageTexts.some(sentMsg => 
            body === sentMsg || 
            body.startsWith(sentMsg.substring(0, 30)) || 
            sentMsg.startsWith(body.substring(0, 30))
        );
        if (isBotMessage) {
            return; 
        }
    
    console.log(`\n[WHATSAPP] Received from YOU: ${body}`);
    addLog('inbound', msg.from, msg.to, body);
    updateStats(body);
        try {
            // Forward the message to the Python Jarvis Server
            const response = await axios.post('http://localhost:5000/whatsapp_local', {
                Body: body,
                From: msg.from,
                isSelfChat: isSelfChat
            });
            console.log(`[JARVIS HUB] Forwarded to Python Brain. Result: OK`);
        } catch (error) {
            console.error(`[JARVIS HUB ERROR] Could not reach Python Server:`, error.message);
            const fallbackMsg = 'Jarvis is currently offline (Python server is not running).';
            botSentMessageTexts.push(fallbackMsg);
            if (botSentMessageTexts.length > 100) botSentMessageTexts.shift();
            client.sendMessage(msg.from, fallbackMsg);
            addLog('outbound', 'Jarvis', msg.from, 'Jarvis is offline.');
        }
    } catch (globalErr) {
        console.error('[JARVIS HUB ERROR] Crash in message_create:', globalErr);
    }
});

// Express API to allow Python to send replies back to WhatsApp
app.post('/send', async (req, res) => {
    const { to, message, mediaBase64, mediaMime } = req.body;
    if (!to || (!message && !mediaBase64)) {
        return res.status(400).send('Missing "to" and ("message" or "mediaBase64").');
    }
    
    try {
        if (message) {
            console.log(`[JARVIS HUB] Sending reply to ${to}: ${message.substring(0, 50)}...`);
            // Track the text BEFORE sending so message_create catches it immediately!
            botSentMessageTexts.push(message.trim());
            if (botSentMessageTexts.length > 100) botSentMessageTexts.shift();
        } else {
            console.log(`[JARVIS HUB] Sending media reply to ${to}`);
        }
        
        if (to !== 'WebDashboard@c.us') {
            const sendPromise = async () => {
                if (mediaBase64) {
                    const media = new MessageMedia(mediaMime || 'image/jpeg', mediaBase64, 'image.jpg');
                    await client.sendMessage(to, media, { caption: message || '' });
                } else {
                    await client.sendMessage(to, message);
                }
            };
            
            await Promise.race([
                sendPromise(),
                new Promise((_, reject) => setTimeout(() => reject(new Error('WhatsApp Web timeout')), 5000))
            ]);
        }
        
        addLog('outbound', 'Jarvis', to, message ? message : '🖼️ [Image Sent]');
        res.status(200).send('Sent');
    } catch (error) {
        console.error(`[JARVIS HUB ERROR] Failed to send message:`, error);
        res.status(500).send('Failed to send message');
    }
});

// Dashboard APIs
app.get('/api/status', async (req, res) => {
    try {
        if (client && client.pupPage) {
            // Ping the underlying browser to ensure it hasn't silently frozen
            await Promise.race([
                client.pupPage.evaluate(() => 1+1),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Browser Freeze Timeout')), 10000))
            ]);
        }
        
        let qrDataURI = null;
        if (latestQR) {
            try { qrDataURI = await qrImage.toDataURL(latestQR); } catch (e) {}
        }
        
        let orUsage = 0, orLimit = 0;
        try {
            const envFile = fs.readFileSync(path.join(__dirname, '../.env'), 'utf8');
            const match = envFile.match(/OPENROUTER_API_KEY=(.+)/);
            if (match) {
                const orRes = await axios.get('https://openrouter.ai/api/v1/auth/key', {
                    headers: { 'Authorization': `Bearer ${match[1].trim()}` },
                    timeout: 2000
                });
                if (orRes.data && orRes.data.data) {
                    orUsage = orRes.data.data.usage;
                    orLimit = orRes.data.data.limit;
                }
            }
        } catch(e) {}
        
        res.json({ status: connectionStatus, qr: qrDataURI, logs: messageLogs, stats: stats, openrouter: { usage: orUsage, limit: orLimit } });
    } catch (e) {
        console.error("[JARVIS HUB ERROR] Puppeteer browser appears frozen or slow responding. Skipping restart to allow recovery...", e.message);
        res.json({ status: "Browser Slow", qr: null, logs: messageLogs, stats: stats });
    }
});

app.get('/api/contacts', async (req, res) => {
    try {
        if (!cachedContacts) {
            const contacts = await client.getContacts();
            cachedContacts = contacts.map(c => ({ name: c.name || c.pushname || c.number, id: c.id._serialized }));
        }
        res.json(cachedContacts);
    } catch (e) {
        res.status(500).json([]);
    }
});

// Web Chat API for the Dashboard
app.post('/api/chat', async (req, res) => {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'No message provided' });

    try {
        // Forward to Python Brain just like a WhatsApp message
        addLog('inbound', 'WebDashboard', 'Jarvis', message);
        updateStats(message);
        
        await axios.post('http://localhost:5000/whatsapp_local', {
            Body: message,
            From: "WebDashboard@c.us"
        });
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: 'Failed to reach Python Brain' });
    }
});

// Reverse Proxy for Dr. Jarvis (Port 8080)
app.get('/api/doctor/logs', async (req, res) => {
    try {
        const response = await axios.get('http://localhost:8080/api/logs', { timeout: 2000 });
        res.json(response.data);
    } catch (e) {
        res.status(502).json({ logs: "Dr. Jarvis backend is currently offline or rebooting." });
    }
});

app.post('/api/doctor/chat', async (req, res) => {
    try {
        const response = await axios.post('http://localhost:8080/api/chat', req.body, { timeout: 10000 });
        res.json(response.data);
    } catch (e) {
        res.status(502).json({ error: "Dr. Jarvis backend failed to respond." });
    }
});

app.get('/api/agents', async (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        const rootDir = path.join(__dirname, '..');
        const agentsDir = path.join(rootDir, 'agents');
        
        let agents = [];
        
        // Descriptions mapping
        const descriptions = {
            'coder_agent': 'Specialized in advanced IDE interaction, writing code, and deploying software via PyAutoGUI and Shell access.',
            'doctor_agent': 'Head Doctor Agent and autonomous system administrator. Monitors system health and patches errors.',
            'email_agent': 'Manages inbox parsing, drafts professional correspondence, and filters high-priority emails.',
            'os_agent': 'Manages operating system level tasks, filesystem modifications, and process monitoring.',
            'sms_agent': 'Handles incoming SMS workflows, routing messages, and triggering mobile automations.',
            'tts_agent': 'Generates text-to-speech high fidelity voice responses using edge TTS infrastructure.',
            'coding_agent': 'Legacy autonomous coding assistant framework.'
        };
        const emojis = { 'coder_agent': '💻', 'doctor_agent': '⚕️', 'email_agent': '📧', 'os_agent': '⚙️', 'sms_agent': '💬', 'tts_agent': '🔊', 'coding_agent': '⌨️' };
        
        if (fs.existsSync(rootDir)) {
            const rootFiles = fs.readdirSync(rootDir);
            rootFiles.forEach(file => {
                if (file.endsWith('_agent.py') && file !== 'doctor_agent.py' && file !== 'coder_agent.py') {
                    const name = file.replace('.py', '');
                    agents.push({ name: name, type: 'Core Agent', active: true, desc: descriptions[name] || 'Custom autonomous agent plugin.', icon: emojis[name] || '🤖' });
                }
            });
            // Add coder and doctor explicitly
            agents.push({ name: 'coder_agent', type: 'Core Agent', active: true, desc: descriptions['coder_agent'], icon: emojis['coder_agent'] });
            agents.push({ name: 'doctor_agent', type: 'Core Agent', active: true, desc: descriptions['doctor_agent'], icon: emojis['doctor_agent'] });
        }
        
        if (fs.existsSync(agentsDir)) {
            const agentFiles = fs.readdirSync(agentsDir);
            agentFiles.forEach(file => {
                if (file.endsWith('.py') && file !== '__init__.py' && file !== 'base.py' && file !== 'dispatcher.py') {
                    const name = file.replace('.py', '');
                    agents.push({ name: name, type: 'Sub-Agent', active: true, desc: descriptions[name] || 'Custom sub-agent task handler.', icon: emojis[name] || '🤖' });
                }
            });
        }
        
        res.json(agents);
    } catch (e) {
        res.status(500).json([]);
    }
});

// WhatsApp Management APIs
app.post('/api/whatsapp/refresh', (req, res) => {
    console.log('[JARVIS HUB] Refreshing WhatsApp connection by restarting process...');
    res.json({ success: true, message: "Restarting WhatsApp Hub..." });
    setTimeout(() => { process.exit(1); }, 500);
});

// OPEN CLAW / SKILLS CONFIGURATION
const openclawDir = path.join(os.homedir(), '.openclaw');
const openclawSettingsPath = path.join(openclawDir, 'openclaw.json');

app.get('/api/openclaw', (req, res) => {
    try {
        if (!fs.existsSync(openclawSettingsPath)) {
            return res.json({ installed: false });
        }
        const data = fs.readFileSync(openclawSettingsPath, 'utf8');
        res.json({ installed: true, settings: JSON.parse(data) });
    } catch(e) {
        res.json({ installed: false, error: e.message });
    }
});

app.post('/api/openclaw', (req, res) => {
    const { baseUrl, apiKey, model } = req.body;
    try {
        if (!fs.existsSync(openclawDir)) fs.mkdirSync(openclawDir, { recursive: true });
        let settings = {};
        if (fs.existsSync(openclawSettingsPath)) {
            settings = JSON.parse(fs.readFileSync(openclawSettingsPath, 'utf8'));
        }
        if (!settings.agents) settings.agents = {};
        if (!settings.agents.defaults) settings.agents.defaults = {};
        if (!settings.agents.defaults.model) settings.agents.defaults.model = {};
        if (!settings.models) settings.models = {};
        if (!settings.models.providers) settings.models.providers = {};
        
        const fullModelId = `9router/${model}`;
        settings.agents.defaults.model.primary = fullModelId;
        
        settings.models.providers["9router"] = {
            baseUrl: baseUrl.endsWith('/v1') ? baseUrl : `${baseUrl}/v1`,
            apiKey: apiKey || "your_api_key",
            api: "openai-completions",
            models: [{ id: model, name: model.split('/').pop() }]
        };
        
        fs.writeFileSync(openclawSettingsPath, JSON.stringify(settings, null, 2));
        res.json({ success: true });
    } catch(e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/api/whatsapp/reconnect', (req, res) => {
    console.log('[JARVIS HUB] Force reconnect requested. Deleting session...');
    const sessionPath = path.join(__dirname, 'whatsapp_session');
    if (fs.existsSync(sessionPath)) {
        fs.rmSync(sessionPath, { recursive: true, force: true });
    }
    res.json({ success: true, message: "Session deleted. Generating new QR code..." });
    setTimeout(() => { process.exit(1); }, 500);
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the Express server
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`========================================================================`);
    console.log(` JARVIS HUB (Node.js) is starting...`);
    console.log(` API listening on http://localhost:${PORT}`);
    console.log(`========================================================================`);
});

// Start the WhatsApp Client
client.initialize();
