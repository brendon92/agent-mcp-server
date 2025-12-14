// Global state
let tools = [];
let selectedTool = null;
let tasks = { active: [], history: [] };
let consoleEvents = [];
let ws = null;

// Tool Examples Database
const toolExamples = {
    // Browser tools (puppeteer)
    'puppeteer_navigate': [
        { name: 'Navigate to Google', args: { url: 'https://www.google.com' } },
        { name: 'Navigate to GitHub', args: { url: 'https://github.com' } },
        { name: 'Navigate to localhost', args: { url: 'http://localhost:8000' } }
    ],
    'puppeteer_screenshot': [
        { name: 'Screenshot Full Page', args: { name: 'fullpage', fullPage: true } },
        { name: 'Screenshot Viewport', args: { name: 'viewport' } },
        { name: 'Screenshot Element', args: { name: 'element', selector: '#main' } }
    ],
    'puppeteer_click': [
        { name: 'Click Button', args: { selector: 'button.submit' } },
        { name: 'Click Link', args: { selector: 'a.nav-link' } },
        { name: 'Click by Text', args: { selector: 'text=Click Here' } }
    ],
    'puppeteer_fill': [
        { name: 'Fill Email', args: { selector: 'input[type="email"]', value: 'user@example.com' } },
        { name: 'Fill Password', args: { selector: 'input[type="password"]', value: 'password123' } },
        { name: 'Fill Search', args: { selector: 'input[name="q"]', value: 'search query' } }
    ],
    'puppeteer_evaluate': [
        { name: 'Get Page Title', args: { script: 'document.title' } },
        { name: 'Get All Links', args: { script: 'Array.from(document.links).map(l => l.href)' } },
        { name: 'Get Element Count', args: { script: 'document.querySelectorAll("div").length' } }
    ],

    // Browser tools (fetch)
    'fetch_url': [
        { name: 'Fetch HTML Page', args: { url: 'https://example.com' } },
        { name: 'Fetch API JSON', args: { url: 'https://api.github.com/users/github' } },
        { name: 'Fetch with Headers', args: { url: 'https://api.example.com', headers: { 'User-Agent': 'MCP-Client' } } }
    ],

    // Command tools
    'run_command': [
        { name: 'List Files', args: { command: 'ls -la' } },
        { name: 'Check Disk Usage', args: { command: 'df -h' } },
        { name: 'Show Processes', args: { command: 'ps aux | head -20' } }
    ],
    'kill_process': [
        { name: 'Kill by PID', args: { process: '12345' } },
        { name: 'Kill by Name', args: { process: 'python' } }
    ],

    // Filesystem tools
    'fs_read_file': [
        { name: 'Read README', args: { path: 'README.md' } },
        { name: 'Read Config', args: { path: 'config/workspace_config.yaml' } },
        { name: 'Read Package', args: { path: 'package.json' } }
    ],
    'fs_list_directory': [
        { name: 'List Current Dir', args: { path: '.' } },
        { name: 'List Source Dir', args: { path: './src' } },
        { name: 'List Config Dir', args: { path: './config' } }
    ],
    'convert_to_markdown': [
        { name: 'Convert PDF', args: { filePath: 'document.pdf' } },
        { name: 'Convert DOCX', args: { filePath: 'document.docx' } },
        { name: 'Convert HTML', args: { filePath: 'page.html' } }
    ],

    // VCS tools
    'git_read_repo': [
        { name: 'Read Current Repo', args: { repoPath: '.' } },
        { name: 'Read Specific Repo', args: { repoPath: '/path/to/repo' } },
        { name: 'Read with Branch', args: { repoPath: '.', branch: 'main' } }
    ],
    'git_log': [
        { name: 'Recent 10 Commits', args: { maxCount: 10 } },
        { name: 'Recent 50 Commits', args: { maxCount: 50 } },
        { name: 'Commits Since Date', args: { since: '2024-01-01', maxCount: 100 } }
    ],

    // Browser tools (playwright)
    'playwright_fetch': [
        { name: 'Fetch Page Content', args: { url: 'https://example.com' } },
        { name: 'Fetch and Wait', args: { url: 'https://example.com', wait_for_selector: 'h1' } }
    ],

    // Database tools
    'sqlite_query': [
        { name: 'List Tables', args: { query: 'SELECT name FROM sqlite_master WHERE type="table";' } },
        { name: 'Select All', args: { query: 'SELECT * FROM users LIMIT 10;' } }
    ],
    'postgres_query': [
        { name: 'List Tables', args: { query: 'SELECT table_name FROM information_schema.tables WHERE table_schema = "public";' } },
        { name: 'Select All', args: { query: 'SELECT * FROM users LIMIT 10;' } }
    ],

    // Developer tools
    'run_code': [
        { name: 'Python Hello World', args: { language: 'python', code: 'print("Hello, World!")' } },
        { name: 'Python Calculation', args: { language: 'python', code: 'print(2 + 2)' } }
    ],

    // Web Search tools
    'search_duckduckgo': [
        { name: 'Search Python', args: { query: 'python programming' } },
        { name: 'Search MCP', args: { query: 'model context protocol' } }
    ],
    'search_multi_engine': [
        { name: 'Search (Not Implemented)', args: { query: 'test query' } }
    ],
    'search_searxng': [
        { name: 'Search Example', args: { query: 'example search' } }
    ]
};

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const toolCategories = document.getElementById('toolCategories');
const toolSearch = document.getElementById('toolSearch');
const toolInspector = document.getElementById('toolInspector');
const exampleSelect = document.getElementById('exampleSelect');
const playgroundForm = document.getElementById('playgroundForm');
const toolArgs = document.getElementById('toolArgs');
const executionResult = document.getElementById('executionResult');
const resultContent = document.getElementById('resultContent');
const taskTableBody = document.getElementById('taskTableBody');
const consoleOutput = document.getElementById('consoleOutput');
const btnReset = document.getElementById('btnReset');

// Initialize
async function init() {
    // Check for token
    const token = localStorage.getItem('mcp_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    await checkHealth();
    await loadTools();
    connectWebSocket();
    startTaskPolling();
}

// Authenticated Fetch Wrapper
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('mcp_token');
    if (!token) {
        window.location.href = '/login.html';
        throw new Error('No token found');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        localStorage.removeItem('mcp_token');
        window.location.href = '/login.html';
        throw new Error('Unauthorized');
    }

    return response;
}

// Health Check
async function checkHealth() {
    try {
        const response = await authFetch('/api/health');
        const data = await response.json();

        if (data.status === 'running') {
            statusIndicator.className = 'status-indicator status-healthy';
            statusText.textContent = 'Healthy';
        } else {
            statusIndicator.className = 'status-indicator status-error';
            statusText.textContent = 'Stopped';
        }
    } catch (error) {
        statusIndicator.className = 'status-indicator status-error';
        statusText.textContent = 'Error';
    }
}

// Load Tools
async function loadTools() {
    try {
        const response = await authFetch('/api/tools');
        const data = await response.json();
        tools = data.tools;
        renderToolExplorer();
        populateToolFilter();
    } catch (error) {
        console.error('Failed to load tools:', error);
    }
}

// Render Tool Explorer
function renderToolExplorer() {
    const categories = {};

    // Group tools by category
    tools.forEach(tool => {
        const cat = tool.category || 'Other';
        if (!categories[cat]) {
            categories[cat] = [];
        }
        categories[cat].push(tool);
    });

    // Render categories
    let html = '';
    Object.keys(categories).sort().forEach(category => {
        html += `
            <div class="category">
                <div class="category-header">${category} (${categories[category].length})</div>
                <div class="category-tools">
                    ${categories[category].map(tool => `
                        <div class="tool-item" data-tool="${tool.name}">
                            <span class="tool-name">${tool.name}</span>
                            <span class="tool-type">${tool.type}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });

    toolCategories.innerHTML = html;

    // Add click handlers
    document.querySelectorAll('.tool-item').forEach(item => {
        item.addEventListener('click', () => {
            const toolName = item.dataset.tool;
            selectTool(toolName);
        });
    });
}

// Select Tool
function selectTool(toolName) {
    selectedTool = tools.find(t => t.name === toolName);

    if (!selectedTool) return;

    // Update active state
    document.querySelectorAll('.tool-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tool="${toolName}"]`)?.classList.add('active');

    // Update inspector
    toolInspector.querySelector('.inspector-placeholder').style.display = 'none';
    toolInspector.querySelector('.inspector-content').style.display = 'block';
    document.getElementById('inspectorName').textContent = selectedTool.name;
    document.getElementById('inspectorCategory').textContent = selectedTool.category || 'N/A';
    document.getElementById('inspectorType').textContent = selectedTool.type;
    document.getElementById('inspectorDescription').textContent = selectedTool.description || 'No description available';

    // Update playground - populate examples
    populateExamples(selectedTool.name);
    resetPlayground();
}

// Populate Examples Dropdown
function populateExamples(toolName) {
    exampleSelect.innerHTML = '';

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = `${toolName} - Custom`;
    exampleSelect.appendChild(defaultOption);

    // Add examples if available
    const examples = toolExamples[toolName] || [];
    examples.forEach((example, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = example.name;
        exampleSelect.appendChild(option);
    });

    // Disable the dropdown if there are no examples beyond the 'Custom' option
    exampleSelect.disabled = examples.length === 0;
}

// Handle Example Selection
exampleSelect.addEventListener('change', (e) => {
    const exampleIndex = e.target.value;

    if (exampleIndex === '') {
        // Custom - reset to empty
        toolArgs.value = '{}';
    } else if (selectedTool) {
        // Load example
        const examples = toolExamples[selectedTool.name] || [];
        const example = examples[exampleIndex];
        if (example) {
            toolArgs.value = JSON.stringify(example.args, null, 2);
        }
    }
});

// Reset Playground
function resetPlayground() {
    toolArgs.value = '{}';
    exampleSelect.selectedIndex = 0;
    executionResult.style.display = 'none';
}

// Reset Button Handler
btnReset.addEventListener('click', resetPlayground);

// Execute Tool
playgroundForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedTool) {
        alert('Please select a tool first');
        return;
    }

    let args = {};
    try {
        args = JSON.parse(toolArgs.value || '{}');
    } catch (error) {
        alert('Invalid JSON in arguments');
        return;
    }

    try {
        const response = await authFetch('/api/tools/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool_name: selectedTool.name,
                arguments: args
            })
        });

        const result = await response.json();

        // Display result
        executionResult.style.display = 'block';
        resultContent.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        executionResult.style.display = 'block';
        resultContent.textContent = `Error: ${error.message}`;
    }
});

// WebSocket Connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 3000);
    };
}

// Handle Event
function handleEvent(event) {
    consoleEvents.unshift(event);
    if (consoleEvents.length > 1000) {
        consoleEvents.pop();
    }

    renderConsoleLog();

    // Update task manager if task event
    if (event.type.startsWith('task_')) {
        updateTaskManager();
    }
}

// Render Console Log
function renderConsoleLog() {
    const searchTerm = document.getElementById('logSearch').value.toLowerCase();
    const filterType = document.getElementById('logFilterType').value;
    const filterTool = document.getElementById('logFilterTool').value;

    // Get column visibility
    const colVisibility = {
        timestamp: document.querySelector('[data-col="timestamp"]')?.checked ?? true,
        tool: document.querySelector('[data-col="tool"]')?.checked ?? true,
        taskId: document.querySelector('[data-col="taskId"]')?.checked ?? true,
        args: document.querySelector('[data-col="args"]')?.checked ?? true,
        result: document.querySelector('[data-col="result"]')?.checked ?? true,
        status: document.querySelector('[data-col="status"]')?.checked ?? true
    };

    // Filter events
    let filtered = consoleEvents.filter(event => {
        if (filterType && event.type !== filterType) return false;
        if (filterTool && event.tool_name !== filterTool) return false;
        if (searchTerm) {
            const searchableText = JSON.stringify(event).toLowerCase();
            if (!searchableText.includes(searchTerm)) return false;
        }
        return true;
    });

    if (filtered.length === 0) {
        consoleOutput.innerHTML = '<div class="console-placeholder">No events to display</div>';
        return;
    }

    // Render events
    let html = '<div class="console-entries">';
    filtered.forEach((event, index) => {
        const statusClass = event.type === 'task_failed' ? 'error' : event.type === 'task_completed' ? 'success' : 'info';

        // Calculate content length to determine if expandable
        const argsStr = event.arguments ? JSON.stringify(event.arguments) : '';
        const resultStr = event.result ? (typeof event.result === 'string' ? event.result : JSON.stringify(event.result)) : '';
        const isExpandable = (argsStr.length + resultStr.length) > 80;

        html += `<div class="console-entry ${statusClass}" id="log-entry-${index}">`;

        if (isExpandable) {
            html += `<span class="console-expand-icon" onclick="toggleLogEntry(${index})">▶</span>`;
        } else {
            html += `<span class="console-expand-icon" style="opacity: 0; cursor: default">▶</span>`;
        }

        if (colVisibility.timestamp) {
            const timeStr = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '-';
            html += `<span class="console-time">${timeStr}</span>`;
        }
        if (colVisibility.status) {
            html += `<span class="console-type">${event.type}</span>`;
        }
        if (colVisibility.tool && event.tool_name) {
            html += `<span class="console-tool">${event.tool_name}</span>`;
        }
        if (colVisibility.taskId && event.task_id) {
            html += `<span class="console-task-id">${event.task_id.substring(0, 8)}</span>`;
        }
        if (colVisibility.args && event.arguments) {
            html += `<span class="console-args">${argsStr}</span>`;
        }
        if (colVisibility.result && event.result) {
            html += `<span class="console-result">${resultStr}</span>`;
        }

        html += '</div>';
    });
    html += '</div>';

    consoleOutput.innerHTML = html;
}

function toggleLogEntry(index) {
    const entry = document.getElementById(`log-entry-${index}`);
    if (entry) {
        entry.classList.toggle('expanded');
    }
}

// Task Manager
async function updateTaskManager() {
    try {
        const response = await authFetch('/api/tasks');
        tasks = await response.json();
        renderTaskManager();
    } catch (error) {
        console.error('Failed to update tasks:', error);
    }
}

function startTaskPolling() {
    setInterval(updateTaskManager, 2000);
}

function renderTaskManager() {
    const allTasks = [...tasks.active, ...tasks.history.slice(0, 10)];

    if (allTasks.length === 0) {
        taskTableBody.innerHTML = '<tr class="empty-state"><td colspan="6">No tasks yet</td></tr>';
        return;
    }

    let html = '';
    allTasks.forEach(task => {
        const statusIcon = task.status === 'running' ? '⏳' : task.status === 'completed' ? '✅' : '❌';
        const duration = task.duration ? `${task.duration.toFixed(2)}s` : '-';

        html += `
            <tr data-task-id="${task.task_id}">
                <td><input type="checkbox" class="task-checkbox" value="${task.task_id}"></td>
                <td>${statusIcon}</td>
                <td>${task.task_id.substring(0, 8)}...</td>
                <td>${task.tool_name}</td>
                <td>${duration}</td>
                <td>
                    ${task.status === 'running' ? `<button class="btn btn-sm btn-danger" onclick="cancelTask('${task.task_id}')">Cancel</button>` : '-'}
                </td>
            </tr>
        `;
    });

    taskTableBody.innerHTML = html;
}

// Task Actions
async function cancelTask(taskId) {
    try {
        await authFetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
        updateTaskManager();
    } catch (error) {
        console.error('Failed to cancel task:', error);
    }
}

document.getElementById('btnKillAll').addEventListener('click', async () => {
    if (confirm('Are you sure you want to cancel all running tasks?')) {
        try {
            await authFetch('/api/tasks/cancel_all', { method: 'POST' });
            updateTaskManager();
        } catch (error) {
            console.error('Failed to cancel all tasks:', error);
        }
    }
});

document.getElementById('btnKillSelected').addEventListener('click', async () => {
    const selected = Array.from(document.querySelectorAll('.task-checkbox:checked')).map(cb => cb.value);

    if (selected.length === 0) {
        alert('No tasks selected');
        return;
    }

    for (const taskId of selected) {
        await cancelTask(taskId);
    }
});

// Enable/disable kill selected button
document.addEventListener('change', (e) => {
    if (e.target.classList.contains('task-checkbox')) {
        const anyChecked = document.querySelectorAll('.task-checkbox:checked').length > 0;
        document.getElementById('btnKillSelected').disabled = !anyChecked;
    }
});

// Server state tracking
let serverState = 'stopped';
let stopAttempts = 0;

// Poll server state
async function updateServerState() {
    try {
        const response = await authFetch('/api/server/state');
        const data = await response.json();
        serverState = data.state;
        stopAttempts = data.stop_attempts;

        // Update button states
        updateServerControls();
    } catch (error) {
        console.error('Failed to update server state:', error);
    }
}

// Update server control buttons based on state
function updateServerControls() {
    const btnStart = document.getElementById('btnStart');
    const btnStop = document.getElementById('btnStop');
    const btnRestart = document.getElementById('btnRestart');

    // START button
    if (serverState === 'stopped') {
        btnStart.disabled = false;
        btnStart.textContent = 'Start';
    } else if (serverState === 'starting') {
        btnStart.disabled = true;
        btnStart.textContent = 'Starting...';
    } else {
        btnStart.disabled = true;
        btnStart.textContent = 'Start';
    }

    // STOP button
    if (serverState === 'running') {
        btnStop.disabled = false;
        btnStop.textContent = `Stop (${stopAttempts}/3)`;
    } else if (serverState === 'stopping') {
        btnStop.disabled = false;
        btnStop.textContent = `Stopping... (${stopAttempts}/3)`;
    } else if (serverState === 'starting') {
        btnStop.disabled = true;
        btnStop.textContent = 'Stop';
    } else {
        btnStop.disabled = true;
        btnStop.textContent = 'Stop';
    }

    // RESTART button
    if (serverState === 'running' || serverState === 'stopped') {
        btnRestart.disabled = false;
    } else {
        btnRestart.disabled = true;
    }
}

// Server Controls
document.getElementById('btnStart').addEventListener('click', async () => {
    if (serverState !== 'stopped') {
        alert('Server is not stopped');
        return;
    }

    try {
        const response = await authFetch('/api/server/start', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            alert(`Server started successfully (PID: ${data.pid})`);
            await updateServerState();
        } else {
            alert(`Failed to start server: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error starting server: ${error.message}`);
    }
});

document.getElementById('btnStop').addEventListener('click', async () => {
    if (serverState === 'starting') {
        alert('Cannot stop while server is starting');
        return;
    }

    if (serverState === 'stopped') {
        alert('Server is already stopped');
        return;
    }

    // Confirm force kill after 3 attempts
    if (stopAttempts >= 2) {
        if (!confirm('Server did not stop gracefully after 2 attempts. Force kill?')) {
            return;
        }
    }

    try {
        const force = stopAttempts >= 2;
        const response = await authFetch(`/api/server/stop?force=${force}`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            if (data.status === 'stopped') {
                alert(`Server stopped (${data.method})`);
            } else if (data.status === 'stopping') {
                alert(`Server is stopping gracefully (attempt ${data.attempts}/3)`);
            }
            await updateServerState();
        } else {
            alert(`Failed to stop server: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error stopping server: ${error.message}`);
    }
});

document.getElementById('btnRestart').addEventListener('click', async () => {
    if (serverState === 'starting' || serverState === 'stopping') {
        alert('Cannot restart while server is starting or stopping');
        return;
    }

    if (!confirm('Are you sure you want to restart the server?')) {
        return;
    }

    try {
        const response = await authFetch('/api/server/restart', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            alert('Server restarted successfully');
            await updateServerState();
        } else {
            alert(`Failed to restart server: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error restarting server: ${error.message}`);
    }
});

// Poll server state periodically
setInterval(updateServerState, 3000);
updateServerState(); // Initial update


// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;

        // Update active states
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById(tabName).classList.add('active');
    });
});

// Console Controls
document.getElementById('btnClearLog').addEventListener('click', () => {
    consoleEvents = [];
    renderConsoleLog();
});

document.getElementById('logSearch').addEventListener('input', renderConsoleLog);
document.getElementById('logFilterType').addEventListener('change', renderConsoleLog);
document.getElementById('logFilterTool').addEventListener('change', renderConsoleLog);

document.querySelectorAll('.col-toggle').forEach(toggle => {
    toggle.addEventListener('change', renderConsoleLog);
});

// Tool Search
toolSearch.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    document.querySelectorAll('.tool-item').forEach(item => {
        const toolName = item.querySelector('.tool-name').textContent.toLowerCase();
        item.style.display = toolName.includes(searchTerm) ? 'flex' : 'none';
    });
});

// Populate Tool Filter
function populateToolFilter() {
    const toolNames = [...new Set(tools.map(t => t.name))].sort();
    const select = document.getElementById('logFilterTool');

    toolNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        select.appendChild(option);
    });
}

// Start
init();
