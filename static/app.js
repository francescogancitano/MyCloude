document.addEventListener("DOMContentLoaded", () => {
    const loginContainer = document.getElementById("login-container");
    const mainContainer = document.getElementById("main-container");
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");
    const logoutButton = document.getElementById("logout-button");
    const connectButton = document.getElementById("ssh-connect-button");
    const disconnectButton = document.getElementById("ssh-disconnect-button");
    const addTabButton = document.getElementById("add-tab-button");
    const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
    const connectionPill = document.getElementById("connection-pill");
    const metricsUpdatedAt = document.getElementById("metrics-updated-at");
    const metricStatus = document.getElementById("metric-status");
    const terminalTabsEl = document.getElementById("terminal-tabs");
    const terminalContainer = document.getElementById("terminal-container");
    const containerEl = document.getElementById("main-layout-container");
    const panelResizer = document.getElementById("panel-resizer");

    const metricFields = {
        cpu: document.getElementById("metric-cpu"),
        temp: document.getElementById("metric-temp"),
        ram: document.getElementById("metric-ram"),
        disk: document.getElementById("metric-disk"),
        net_in: document.getElementById("metric-net-in"),
        net_out: document.getElementById("metric-net-out"),
    };

    let token = null;
    let metricsInterval = null;
    let terminalTabs = [];
    let activeTabId = null;
    let tabCounter = 0;

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        loginError.textContent = "";

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        try {
            const response = await fetch("/api/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                loginError.textContent = errorData.detail || "Login failed.";
                return;
            }

            const data = await response.json();
            token = data.access_token;
            showMainContent();
        } catch (error) {
            loginError.textContent = "Network error during login.";
        }
    });

    logoutButton.addEventListener("click", () => {
        token = null;
        showLogin();
    });

    connectButton.addEventListener("click", () => {
        connectActiveTab();
    });

    disconnectButton.addEventListener("click", () => {
        disconnectActiveTab();
    });

    addTabButton.addEventListener("click", () => {
        createTerminalTab();
    });

    sidebarToggleBtn.addEventListener("click", () => {
        const isHidden = containerEl.classList.toggle("sidebar-hidden");
        sidebarToggleBtn.textContent = isHidden ? ">" : "<";
        
        // We wait a tiny bit for the CSS transition grid layout to finalize sizing
        setTimeout(() => {
            const activeTab = getActiveTab();
            if (activeTab) {
                activeTab.fitAddon.fit();
            }
        }, 320);
    });

    function showMainContent() {
        loginContainer.classList.add("hidden");
        mainContainer.classList.remove("hidden");
        if (!terminalTabs.length) {
            createTerminalTab();
        }
        startMetricsPolling();
    }

    function showLogin() {
        mainContainer.classList.add("hidden");
        loginContainer.classList.remove("hidden");
        stopMetricsPolling();
        disconnectAllTabs();
        resetMetricsView();
        setConnectionState(false);
    }

    function createTerminalTab() {
        tabCounter += 1;
        const id = `tab-${tabCounter}`;

        const tabItem = document.createElement("div");
        tabItem.className = "terminal-tab";
        const tabButton = document.createElement("button");
        tabButton.className = "terminal-tab-label";
        tabButton.textContent = `Terminal ${tabCounter}`;
        tabButton.addEventListener("click", () => switchTab(id));
        const closeButton = document.createElement("button");
        closeButton.className = "terminal-tab-close";
        closeButton.textContent = "×";
        closeButton.title = "Close tab";
        closeButton.addEventListener("click", (event) => {
            event.stopPropagation();
            closeTerminalTab(id);
        });
        tabItem.append(tabButton, closeButton);
        terminalTabsEl.appendChild(tabItem);

        const pane = document.createElement("div");
        pane.className = "terminal-pane";
        pane.dataset.tabId = id;
        const termEl = document.createElement("div");
        termEl.className = "terminal-instance";
        pane.appendChild(termEl);
        terminalContainer.appendChild(pane);

        const term = new Terminal({
            cursorBlink: true,
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 13,
            theme: {
                background: "#081014",
                foreground: "#d8ece8",
                cursor: "#20b486",
                selectionBackground: "rgba(32, 180, 134, 0.25)",
            },
        });
        const fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.open(termEl);

        const tab = {
            id,
            item: tabItem,
            button: tabButton,
            closeButton,
            pane,
            term,
            fitAddon,
            socket: null,
            connected: false,
        };

        term.onData((data) => {
            if (tab.socket && tab.socket.readyState === WebSocket.OPEN) {
                tab.socket.send(JSON.stringify({ type: "input", data }));
            }
        });

        term.onResize((size) => {
            if (tab.socket && tab.socket.readyState === WebSocket.OPEN) {
                tab.socket.send(JSON.stringify({ type: "resize", cols: size.cols, rows: size.rows }));
            }
        });

        terminalTabs.push(tab);
        switchTab(id);
    }

    function closeTerminalTab(id) {
        if (terminalTabs.length === 1) {
            return;
        }
        const tab = terminalTabs.find((t) => t.id === id);
        if (!tab) return;

        if (tab.socket) {
            tab.socket.close();
            tab.socket = null;
        }
        tab.connected = false;

        tab.term.dispose();
        tab.pane.remove();
        tab.item.remove();
        terminalTabs = terminalTabs.filter((t) => t.id !== id);

        if (activeTabId === id) {
            switchTab(terminalTabs[terminalTabs.length - 1].id);
        } else {
            const activeTab = getActiveTab();
            setConnectionState(activeTab ? activeTab.connected : false);
        }
    }

    function getActiveTab() {
        return terminalTabs.find((t) => t.id === activeTabId) || null;
    }

    function switchTab(id) {
        activeTabId = id;
        terminalTabs.forEach((tab) => {
            const active = tab.id === id;
            tab.item.classList.toggle("active", active);
            tab.pane.classList.toggle("active", active);
        });
        const activeTab = getActiveTab();
        if (activeTab) {
            activeTab.fitAddon.fit();
            activeTab.term.focus();
            setConnectionState(activeTab.connected);
        }
    }

    function setConnectionState(isOnline) {
        connectionPill.textContent = isOnline ? "Connected" : "Offline";
        connectionPill.classList.toggle("online", isOnline);
        connectionPill.classList.toggle("offline", !isOnline);
    }

    function updateTabConnectedStyle(tab) {
        tab.item.classList.toggle("connected", tab.connected);
        if (tab.id === activeTabId) {
            setConnectionState(tab.connected);
        }
    }

    function connectActiveTab() {
        const activeTab = getActiveTab();
        if (!token || !activeTab) {
            return;
        }
        if (activeTab.socket && activeTab.socket.readyState === WebSocket.OPEN) {
            activeTab.term.writeln("Session already connected.");
            return;
        }

        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/terminal`;
        activeTab.term.writeln("Connecting to remote host...");

        const socket = new WebSocket(wsUrl);
        activeTab.socket = socket;

        socket.onopen = () => {
            activeTab.connected = true;
            updateTabConnectedStyle(activeTab);
            activeTab.term.writeln("WebSocket connected. Initializing SSH...");
            socket.send(
                JSON.stringify({
                    type: "auth",
                    token,
                    cols: activeTab.term.cols,
                    rows: activeTab.term.rows,
                })
            );
        };

        socket.onclose = (event) => {
            activeTab.connected = false;
            activeTab.socket = null;
            updateTabConnectedStyle(activeTab);
            activeTab.term.writeln(`Session closed (code ${event.code}).`);
        };

        socket.onerror = () => {
            activeTab.connected = false;
            updateTabConnectedStyle(activeTab);
            activeTab.term.writeln("WebSocket error.");
        };

        socket.onmessage = (event) => {
            if (typeof event.data === "string") {
                activeTab.term.write(event.data);
                return;
            }

            const reader = new FileReader();
            reader.onload = () => {
                activeTab.term.write(reader.result);
            };
            reader.readAsText(event.data);
        };
    }

    function disconnectActiveTab() {
        const activeTab = getActiveTab();
        if (!activeTab || !activeTab.socket) {
            return;
        }
        activeTab.socket.close();
        activeTab.socket = null;
        activeTab.connected = false;
        updateTabConnectedStyle(activeTab);
    }

    function disconnectAllTabs() {
        terminalTabs.forEach((tab) => {
            if (tab.socket) {
                tab.socket.close();
                tab.socket = null;
            }
            tab.connected = false;
            updateTabConnectedStyle(tab);
            tab.term.clear();
        });
    }

    function formatMetric(value, suffix = "") {
        if (value === null || value === undefined) return "--";
        const num = Number(value);
        if (Number.isNaN(num)) return String(value);
        return `${num.toFixed(2)}${suffix}`;
    }

    function updateStatusBadge(status) {
        const normalized = String(status || "unknown").toLowerCase();
        metricStatus.textContent = String(status || "Unknown");
        metricStatus.classList.remove("ok", "warning", "critical");

        if (normalized === "ok") metricStatus.classList.add("ok");
        if (normalized === "warning") metricStatus.classList.add("warning");
        if (normalized === "critical") metricStatus.classList.add("critical");
    }

    function renderMetrics(metrics) {
        metricFields.cpu.textContent = formatMetric(metrics.cpuUsedPct, "%");
        metricFields.temp.textContent = formatMetric(metrics.cpuTemperature, "°C");
        metricFields.ram.textContent = formatMetric(metrics.ramUsedInPct, "%");
        metricFields.disk.textContent = formatMetric(metrics.diskUsedInPct, "%");
        metricFields.net_in.textContent = formatMetric(metrics.networkTrafficIn, " kbps");
        metricFields.net_out.textContent = formatMetric(metrics.networkTrafficOut, " kbps");
        updateStatusBadge(metrics.status);
        metricsUpdatedAt.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }

    function resetMetricsView() {
        Object.values(metricFields).forEach((field) => {
            field.textContent = "--";
        });
        metricStatus.textContent = "Unknown";
        metricStatus.classList.remove("ok", "warning", "critical");
        metricsUpdatedAt.textContent = "Waiting for data";
    }

    async function fetchMetrics() {
        if (!token) return;

        try {
            const response = await fetch("/api/metrics", {
                headers: { Authorization: `Bearer ${token}` },
            });

            if (!response.ok) {
                metricsUpdatedAt.textContent = "Unable to fetch metrics";
                return;
            }

            const data = await response.json();
            const metrics = data && data.length ? data[0] : null;
            if (!metrics) {
                metricsUpdatedAt.textContent = "No metrics available yet";
                return;
            }

            renderMetrics(metrics);
        } catch (error) {
            metricsUpdatedAt.textContent = "Metrics connection error";
        }
    }

    function startMetricsPolling() {
        fetchMetrics();
        metricsInterval = setInterval(fetchMetrics, 5000);
    }

    function stopMetricsPolling() {
        clearInterval(metricsInterval);
        metricsInterval = null;
    }

    function initPanelResizer() {
        let dragging = false;
        const minWidth = 280;
        const maxWidthPadding = 460;

        panelResizer.addEventListener("mousedown", () => {
            if (window.innerWidth <= 1024) return;
            dragging = true;
            panelResizer.classList.add("dragging");
            document.body.style.userSelect = "none";
        });

        window.addEventListener("mousemove", (event) => {
            if (!dragging || window.innerWidth <= 1024) return;
            const rect = containerEl.getBoundingClientRect();
            const maxWidth = Math.max(minWidth, rect.width - maxWidthPadding);
            const nextWidth = Math.min(Math.max(event.clientX - rect.left, minWidth), maxWidth);
            containerEl.style.setProperty("--metrics-panel-width", `${nextWidth}px`);
            const activeTab = getActiveTab();
            if (activeTab) {
                activeTab.fitAddon.fit();
            }
        });

        window.addEventListener("mouseup", () => {
            dragging = false;
            panelResizer.classList.remove("dragging");
            document.body.style.userSelect = "";
        });
    }

    window.addEventListener("resize", () => {
        const activeTab = getActiveTab();
        if (activeTab) {
            activeTab.fitAddon.fit();
        }
        if (window.innerWidth <= 1024) {
            containerEl.style.removeProperty("--metrics-panel-width");
        }
    });

    resetMetricsView();
    setConnectionState(false);
    initPanelResizer();
});
