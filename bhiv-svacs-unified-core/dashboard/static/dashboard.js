// =====================================================
// STATUS COLORS
// =====================================================

function getStatusClass(status) {
 
    if (status === "EXECUTED") { 

        return "bg-success text-light";
    }

    if (status === "REJECTED") {

        return "bg-danger text-light";
    }

    if (status === "TOKEN_DENIED") {

        return "bg-warning text-dark";
    }

    if (status === "MUTATION_REJECTED") {

        return "bg-dark text-light";
    }

    return "bg-secondary text-light";
}


// =====================================================
// LOAD EXECUTIONS
// =====================================================

async function loadExecutions() {

    const response = await fetch(
        "/api/dashboard"
    );

    const data = await response.json();

    const container = document.getElementById(
        "execution-container"
    );

    container.innerHTML = "";

    data.forEach(item => {

        const card = document.createElement("div");

        card.className =
            `card mb-3 ${getStatusClass(item.status)}`;

        card.innerHTML = `

            <div class="card-body">

                <h5>
                    ${item.execution_id || "UNKNOWN"}
                </h5>

                <p>
                    Trace:
                    ${item.trace_id || "UNKNOWN"}
                </p>

                <p>
                    Status:
                    <strong>
                        ${item.status || "UNKNOWN"}
                    </strong>
                </p>

                <p>
                    Pipeline:
                    ${item.pipeline_stage || "UNKNOWN"}
                </p>

                <p>
                    Token:
                    ${item.token_issued}
                </p>

                <p>
                    Replay:
                    ${item.replay_available}
                </p>

                <p>
                    Hash Verified:
                    ${item.hash_chain_verified}
                </p>

                <p>
                    Timestamp:
                    ${item.timestamp || "UNKNOWN"}
                </p>

            </div>

        `;

        container.appendChild(card);

    });

}


// =====================================================
// LOAD TELEMETRY
// =====================================================

async function loadTelemetry() {

    const response = await fetch(
        "/api/telemetry"
    );

    const data = await response.json();

    const container = document.getElementById(
        "telemetry-container"
    );

    container.innerHTML = "";

    data.slice(0, 15).forEach(item => {

        const severityClass =

            item.severity === "CRITICAL"

            ? "bg-danger text-light"

            : "bg-info text-dark";

        const card = document.createElement("div");

        card.className =
            `card mb-2 ${severityClass}`;

        card.innerHTML = `

            <div class="card-body">

                <p>
                    Stage:
                    <strong>
                        ${item.stage || "UNKNOWN"}
                    </strong>
                </p>

                <p>
                    Service:
                    ${item.service || "UNKNOWN"}
                </p>

                <p>
                    Status:
                    ${item.status || "UNKNOWN"}
                </p>

                <p>
                    Severity:
                    ${item.severity || "UNKNOWN"}
                </p>

                <p>
                    Execution:
                    ${item.execution_id || "UNKNOWN"}
                </p>

                <p>
                    Timestamp:
                    ${item.timestamp || "UNKNOWN"}
                </p>

            </div>

        `;

        container.appendChild(card);

    });

}


// =====================================================
// LOAD REJECTIONS
// =====================================================

async function loadRejections() {

    const response = await fetch(
        "/api/rejections"
    );

    const data = await response.json();

    const container = document.getElementById(
        "rejection-container"
    );

    container.innerHTML = "";

    data.forEach(item => {

        const card = document.createElement("div");

        card.className =
            "card bg-danger text-light mb-3";

        const executionId =
            item.execution_id ||
            "UNKNOWN";

        const reason =
            item.reason ||
            "Unknown rejection";

        card.innerHTML = `

            <div class="card-body">

                <p>
                    Execution:
                    ${executionId}
                </p>

                <p>
                    Trace:
                    ${item.trace_id || "UNKNOWN"}
                </p>

                <p>
                    Reason:
                    ${reason}
                </p>

                <p>
                    Timestamp:
                    ${item.timestamp || "UNKNOWN"}
                </p>

            </div>

        `;

        container.appendChild(card);

    });

}


// =====================================================
// LOAD METRICS
// =====================================================

async function loadMetrics() {

    const response = await fetch(
        "/api/metrics"
    );

    const metrics = await response.json();

    const container = document.getElementById(
        "metrics-container"
    );

    if (!container) {
        return;
    }

    container.innerHTML = `

        <div class="card bg-dark text-light mb-3">

            <div class="card-body">

                <h4>
                    SYSTEM METRICS
                </h4>

                <p>
                    EXECUTED:
                    ${metrics.EXECUTED || 0}
                </p>

                <p>
                    REJECTED:
                    ${metrics.REJECTED || 0}
                </p>

                <p>
                    TOKEN_DENIED:
                    ${metrics.TOKEN_DENIED || 0}
                </p>

                <p>
                    MUTATION_REJECTED:
                    ${metrics.MUTATION_REJECTED || 0}
                </p>

            </div>

        </div>

    `;
}


// =====================================================
// REFRESH ALL
// =====================================================

function refreshDashboard() {

    loadExecutions();

    loadTelemetry();

    loadRejections();

    loadMetrics();
}


// =====================================================
// AUTO REFRESH
// =====================================================

refreshDashboard();

setInterval(
    refreshDashboard,
    2000
);
