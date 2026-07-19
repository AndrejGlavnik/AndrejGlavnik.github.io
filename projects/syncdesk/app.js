(function () {
  const { download, uid, escapeHtml, toast } = globalThis.OpsTools;
  const workspaceStore = globalThis.WorkspaceStore;
  const views = ["connections", "schema", "logic", "changes", "issues"];
  const syncKeys = ["applications", "connections", "datasets", "fields", "calculations", "changes", "discrepancies"];
  let workspace = workspaceStore.get();
  let pendingImport = null;
  let pendingDeleteId = null;

  const state = {
    sync: normalizeSync(workspace.syncDesk),
    selectedConnectionId: null,
    view: views.includes(location.hash.slice(1)) ? location.hash.slice(1) : "connections",
    applicationFilter: "all",
    connectionSearch: "",
    connectionStatus: "all",
    schemaConnection: "all",
    schemaSearch: ""
  };

  const elements = {
    viewPanels: [...document.querySelectorAll("[data-view]")],
    viewLinks: [...document.querySelectorAll("[data-view-link]")],
    viewButtons: [...document.querySelectorAll("[data-view-button]")],
    applicationList: document.querySelector("[data-application-list]"),
    connectionList: document.querySelector("[data-connection-list]"),
    schemaLibrary: document.querySelector("[data-schema-library]"),
    calculationList: document.querySelector("[data-calculation-list]"),
    changeList: document.querySelector("[data-change-list]"),
    discrepancyList: document.querySelector("[data-discrepancy-list]"),
    connectionSearch: document.querySelector("[data-search-connections]"),
    statusFilter: document.querySelector("[data-status-filter]"),
    schemaConnectionFilter: document.querySelector("[data-schema-connection-filter]"),
    schemaSearch: document.querySelector("[data-schema-search]"),
    detailPanel: document.querySelector("[data-detail-panel]"),
    detailEmpty: document.querySelector("[data-detail-empty]"),
    detailForm: document.querySelector("[data-detail-form]"),
    detailStatus: document.querySelector("[data-detail-status]"),
    detailUpdated: document.querySelector("[data-detail-updated]"),
    linkedWork: document.querySelector("[data-linked-work]"),
    autosaveStatus: document.querySelector("[data-autosave-status]"),
    applicationModal: document.querySelector("[data-application-modal]"),
    applicationForm: document.querySelector("[data-application-form]"),
    connectionModal: document.querySelector("[data-connection-modal]"),
    connectionForm: document.querySelector("[data-connection-form]"),
    schemaModal: document.querySelector("[data-schema-modal]"),
    schemaForm: document.querySelector("[data-schema-form]"),
    calculationModal: document.querySelector("[data-calculation-modal]"),
    calculationForm: document.querySelector("[data-calculation-form]"),
    changeModal: document.querySelector("[data-change-modal]"),
    changeForm: document.querySelector("[data-change-form]"),
    manifestTargets: document.querySelector("[data-manifest-targets]"),
    recordModal: document.querySelector("[data-record-modal]"),
    recordKind: document.querySelector("[data-record-kind]"),
    recordTitle: document.querySelector("[data-record-title]"),
    recordDetail: document.querySelector("[data-record-detail]"),
    discrepancyModal: document.querySelector("[data-discrepancy-modal]"),
    discrepancyForm: document.querySelector("[data-discrepancy-form]"),
    storageModal: document.querySelector("[data-storage-modal]"),
    importModal: document.querySelector("[data-import-modal]"),
    importSummary: document.querySelector("[data-import-summary]"),
    importFile: document.querySelector("[data-import-file]"),
    deleteModal: document.querySelector("[data-delete-modal]"),
    deleteSummary: document.querySelector("[data-delete-summary]")
  };

  function now() {
    return new Date().toISOString();
  }

  function localDateString(date = new Date()) {
    const offset = date.getTimezoneOffset();
    return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 10);
  }

  function normalizeSync(value = {}) {
    return {
      applications: (value.applications || []).map(normalizeApplication),
      connections: (value.connections || []).map(normalizeConnection),
      datasets: (value.datasets || []).map(normalizeDataset),
      fields: (value.fields || []).map(normalizeField),
      calculations: (value.calculations || []).map(normalizeCalculation),
      changes: (value.changes || []).map(normalizeChange),
      discrepancies: (value.discrepancies || []).map(normalizeDiscrepancy)
    };
  }

  function normalizeApplication(value = {}) {
    return { id: value.id || uid("app"), name: value.name || "Unassigned", owner: value.owner || "", environment: value.environment || "", description: value.description || "", createdAt: value.createdAt || now(), updatedAt: value.updatedAt || now() };
  }

  function normalizeConnection(value = {}) {
    return {
      id: value.id || uid("connection"),
      applicationId: value.applicationId || "",
      name: value.name || "Untitled connection",
      sourceType: value.sourceType || "API",
      provider: value.provider || "",
      businessOwner: value.businessOwner || "",
      technicalOwner: value.technicalOwner || "",
      status: ["active", "paused", "deprecated"].includes(value.status) ? value.status : "active",
      cadence: value.cadence || "",
      coverageFrom: value.coverageFrom || "",
      coverageTo: value.coverageTo || "",
      lastSync: value.lastSync || "",
      sourceSystem: value.sourceSystem || "",
      destinationSystem: value.destinationSystem || "",
      purpose: value.purpose || "",
      grain: value.grain || "",
      notes: value.notes || "",
      runbook: value.runbook || "",
      createdAt: value.createdAt || now(),
      updatedAt: value.updatedAt || now()
    };
  }

  function normalizeDataset(value = {}) {
    return { id: value.id || uid("dataset"), connectionId: value.connectionId || "", name: value.name || "Untitled dataset", kind: value.kind || "Table", location: value.location || "", grain: value.grain || "", primaryKeys: value.primaryKeys || "", dateField: value.dateField || "", description: value.description || "", createdAt: value.createdAt || now(), updatedAt: value.updatedAt || now() };
  }

  function normalizeField(value = {}) {
    const createdAt = value.createdAt || now();
    return { id: value.id || uid("field"), datasetId: value.datasetId || "", name: value.name || "unnamed_field", kind: value.kind || "dimension", dataType: value.dataType || "text", definition: value.definition || "", sourceField: value.sourceField || "", owner: value.owner || "", versionDate: value.versionDate || String(value.version || "").match(/^\d{4}-\d{2}-\d{2}$/)?.[0] || createdAt.slice(0, 10), status: value.status || "active", notes: value.notes || "", createdAt, updatedAt: value.updatedAt || now() };
  }

  function normalizeCalculation(value = {}) {
    const createdAt = value.createdAt || now();
    const legacyVersionDate = String(value.version || "").match(/^\d{4}-\d{2}-\d{2}$/)?.[0];
    return { id: value.id || uid("calculation"), connectionId: value.connectionId || "", datasetId: value.datasetId || "", name: value.name || "Untitled calculation", outputType: value.outputType || "Metric", formula: value.formula || "", versionDate: value.versionDate || legacyVersionDate || value.effectiveFrom || createdAt.slice(0, 10), businessReason: value.businessReason || "", owner: value.owner || "", effectiveFrom: value.effectiveFrom || "", sourceFields: Array.isArray(value.sourceFields) ? value.sourceFields : parseList(value.sourceFields), validation: value.validation || "", status: value.status || "active", createdAt, updatedAt: value.updatedAt || now() };
  }

  function normalizeChange(value = {}) {
    const createdAt = value.createdAt || now();
    const legacyLinks = value.entityId ? [{ type: String(value.entityType || "record").toLowerCase(), id: value.entityId }] : [];
    return { id: value.id || uid("manifest"), commitId: value.commitId || String(value.id || uid("commit")).replace(/[^a-z0-9]/gi, "").slice(-8).toLowerCase(), connectionId: value.connectionId || "", entityLinks: Array.isArray(value.entityLinks) ? value.entityLinks : legacyLinks, title: value.title || "Untitled manifest update", reason: value.reason || "", snapshot: value.snapshot || "", versionDate: value.versionDate || value.effectiveDate || createdAt.slice(0, 10), owner: value.owner || "", approvedBy: value.approvedBy || "", ticket: value.ticket || "", validation: value.validation || "", createdAt };
  }

  function normalizeDiscrepancy(value = {}) {
    return { id: value.id || uid("discrepancy"), connectionId: value.connectionId || "", title: value.title || "Untitled discrepancy", status: ["open", "investigating", "monitoring", "resolved"].includes(value.status) ? value.status : "open", severity: value.severity || "P3", observedFrom: value.observedFrom || "", observedTo: value.observedTo || "", impact: value.impact || "", expected: value.expected || "", actual: value.actual || "", owner: value.owner || "", opsItemId: value.opsItemId || "", resolution: value.resolution || "", createdAt: value.createdAt || now(), updatedAt: value.updatedAt || now() };
  }

  function parseList(value) {
    return String(value || "").split(",").map((entry) => entry.trim()).filter(Boolean);
  }

  function persist() {
    workspace = workspaceStore.get();
    workspace.syncDesk = state.sync;
    workspaceStore.save(workspace);
  }

  function applicationName(id) {
    return state.sync.applications.find((item) => item.id === id)?.name || "Unassigned";
  }

  function connectionName(id) {
    return state.sync.connections.find((item) => item.id === id)?.name || "Unknown connection";
  }

  function datasetName(id) {
    return state.sync.datasets.find((item) => item.id === id)?.name || "All connection data";
  }

  function manifestRecordLabel(link) {
    if (link.type === "field") {
      const field = state.sync.fields.find((item) => item.id === link.id);
      return field ? `${field.name} (${field.kind})` : "Removed field";
    }
    if (link.type === "calculation") {
      const calculation = state.sync.calculations.find((item) => item.id === link.id);
      return calculation ? `${calculation.name} (calculated ${calculation.outputType.toLowerCase()})` : "Removed calculation";
    }
    if (link.type === "dataset") return datasetName(link.id);
    return connectionName(link.id);
  }

  function formatDate(value, options = { month: "short", day: "numeric", year: "numeric" }) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("en", options).format(date);
  }

  function toDateTimeInput(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
    const offset = date.getTimezoneOffset();
    return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 16);
  }

  function freshness(connection) {
    if (connection.status !== "active") return { label: connection.status, tone: "tone-neutral" };
    if (!connection.lastSync) return { label: "Not verified", tone: "tone-amber" };
    const age = Date.now() - new Date(connection.lastSync).getTime();
    if (age <= 7 * 86400000) return { label: "Current", tone: "tone-green" };
    return { label: "Review sync", tone: "tone-amber" };
  }

  function setView(view) {
    if (!views.includes(view)) return;
    state.view = view;
    if (location.hash !== `#${view}`) history.pushState(null, "", `#${view}`);
    renderViews();
  }

  function renderViews() {
    elements.viewPanels.forEach((panel) => { panel.hidden = panel.dataset.view !== state.view; });
    elements.viewLinks.forEach((link) => {
      if (link.dataset.viewLink === state.view) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    elements.viewButtons.forEach((button) => button.classList.toggle("active", button.dataset.viewButton === state.view));
  }

  function renderMetrics() {
    const openIssues = state.sync.discrepancies.filter((issue) => issue.status !== "resolved");
    const current = state.sync.connections.filter((connection) => freshness(connection).label === "Current");
    document.querySelector("[data-metric-connections]").textContent = state.sync.connections.length;
    document.querySelector("[data-metric-current]").textContent = current.length;
    document.querySelector("[data-metric-fields]").textContent = state.sync.fields.length;
    document.querySelector("[data-metric-issues]").textContent = openIssues.length;
    document.querySelector("[data-count-connections]").textContent = state.sync.connections.length;
    document.querySelector("[data-count-fields]").textContent = state.sync.fields.length;
    document.querySelector("[data-count-calculations]").textContent = state.sync.calculations.length;
    document.querySelector("[data-count-changes]").textContent = state.sync.changes.length;
    document.querySelector("[data-count-issues]").textContent = openIssues.length;
  }

  function renderApplicationOptions() {
    const options = ['<option value="">Unassigned</option>', ...state.sync.applications.map((app) => `<option value="${app.id}">${escapeHtml(app.name)}</option>`)].join("");
    document.querySelectorAll('select[name="applicationId"]').forEach((select) => {
      const value = select.value;
      select.innerHTML = options;
      if ([...select.options].some((option) => option.value === value)) select.value = value;
    });
    const connectionOptions = ['<option value="">Select connection</option>', ...state.sync.connections.map((connection) => `<option value="${connection.id}">${escapeHtml(connection.name)}</option>`)].join("");
    document.querySelectorAll('select[name="connectionId"]').forEach((select) => {
      const value = select.value;
      select.innerHTML = connectionOptions;
      if ([...select.options].some((option) => option.value === value)) select.value = value;
    });
    const schemaFilterValue = elements.schemaConnectionFilter.value || state.schemaConnection;
    elements.schemaConnectionFilter.innerHTML = `<option value="all">All connections</option>${state.sync.connections.map((connection) => `<option value="${connection.id}">${escapeHtml(connection.name)}</option>`).join("")}`;
    elements.schemaConnectionFilter.value = [...elements.schemaConnectionFilter.options].some((option) => option.value === schemaFilterValue) ? schemaFilterValue : "all";
    updateCalculationDatasets();
  }

  function renderApplications() {
    const counts = new Map();
    state.sync.connections.forEach((connection) => counts.set(connection.applicationId, (counts.get(connection.applicationId) || 0) + 1));
    elements.applicationList.innerHTML = state.sync.applications.map((app) => `
      <button class="sidebar-link ${state.applicationFilter === app.id ? "active" : ""}" type="button" data-application-filter="${app.id}">
        <span>${escapeHtml(app.name)}</span><strong>${counts.get(app.id) || 0}</strong>
      </button>`).join("");
    document.querySelector('[data-application-filter="all"]').classList.toggle("active", state.applicationFilter === "all");
  }

  function connectionCardHtml(connection) {
    const status = freshness(connection);
    const datasets = state.sync.datasets.filter((dataset) => dataset.connectionId === connection.id);
    const fieldIds = new Set(datasets.map((dataset) => dataset.id));
    const fieldCount = state.sync.fields.filter((field) => fieldIds.has(field.datasetId)).length;
    const issueCount = state.sync.discrepancies.filter((issue) => issue.connectionId === connection.id && issue.status !== "resolved").length;
    return `
      <button class="connection-card ${state.selectedConnectionId === connection.id ? "selected" : ""}" type="button" data-connection-id="${connection.id}">
        <span class="connection-card-top"><span class="connection-app">${escapeHtml(applicationName(connection.applicationId))}</span><span class="status-chip ${status.tone}">${escapeHtml(status.label)}</span></span>
        <strong>${escapeHtml(connection.name)}</strong>
        <span class="connection-purpose">${escapeHtml(connection.purpose || "Add the business purpose and expected use of this data.")}</span>
        <span class="route"><span>${escapeHtml(connection.sourceSystem || connection.sourceType)}</span><b>→</b><span>${escapeHtml(connection.destinationSystem || "Destination not set")}</span></span>
        <span class="connection-meta"><span>${escapeHtml(connection.technicalOwner || "No technical owner")}</span><span>${fieldCount} fields</span><span class="${issueCount ? "issue-text" : ""}">${issueCount} open issue${issueCount === 1 ? "" : "s"}</span></span>
      </button>`;
  }

  function renderConnections() {
    const search = state.connectionSearch.trim().toLowerCase();
    const connections = state.sync.connections
      .filter((connection) => state.applicationFilter === "all" || connection.applicationId === state.applicationFilter)
      .filter((connection) => state.connectionStatus === "all" || connection.status === state.connectionStatus)
      .filter((connection) => !search || [connection.name, connection.provider, connection.businessOwner, connection.technicalOwner, connection.sourceSystem, connection.destinationSystem, connection.purpose, applicationName(connection.applicationId)].join(" ").toLowerCase().includes(search))
      .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    elements.connectionList.innerHTML = connections.length ? connections.map(connectionCardHtml).join("") : '<div class="empty-state"><div><h3>No connections found</h3><p>Add a connection or clear the current filters.</p></div></div>';
  }

  function renderSchema() {
    const search = state.schemaSearch.trim().toLowerCase();
    const datasets = state.sync.datasets.filter((dataset) => state.schemaConnection === "all" || dataset.connectionId === state.schemaConnection);
    elements.schemaLibrary.innerHTML = datasets.length ? datasets.map((dataset) => {
      const fields = state.sync.fields.filter((field) => field.datasetId === dataset.id).filter((field) => !search || [field.name, field.kind, field.dataType, field.definition, dataset.name].join(" ").toLowerCase().includes(search));
      if (search && !fields.length) return "";
      return `
        <article class="schema-card">
          <div class="schema-head"><div><p class="kicker">${escapeHtml(connectionName(dataset.connectionId))} · ${escapeHtml(dataset.kind)}</p><h3>${escapeHtml(dataset.name)}</h3><p>${escapeHtml(dataset.location || dataset.grain || "Location and grain not documented")}</p></div><span class="count-badge">${fields.length} fields</span></div>
          <div class="schema-meta"><span><b>Grain</b>${escapeHtml(dataset.grain || "Not set")}</span><span><b>Keys</b>${escapeHtml(dataset.primaryKeys || "Not set")}</span></div>
          <div class="field-table"><div class="field-row field-head"><span>Field</span><span>Role</span><span>Type</span><span>Definition</span></div>${fields.length ? fields.map((field) => `<div class="field-row"><button class="record-link" type="button" data-record-type="field" data-record-id="${field.id}">${escapeHtml(field.name)}</button><span>${escapeHtml(field.kind)}</span><span>${escapeHtml(field.dataType)}</span><p>${escapeHtml(field.definition || "No definition")}</p></div>`).join("") : '<div class="list-empty">No matching fields</div>'}</div>
        </article>`;
    }).join("") : '<div class="empty-state"><div><h3>No schema documented</h3><p>Add a dataset and paste its metrics, dimensions, keys, or columns.</p></div></div>';
    if (!elements.schemaLibrary.textContent.trim()) elements.schemaLibrary.innerHTML = '<div class="empty-state"><div><h3>No matching fields</h3><p>Try another search or connection filter.</p></div></div>';
  }

  function renderCalculations() {
    const calculations = [...state.sync.calculations].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    elements.calculationList.innerHTML = calculations.length ? calculations.map((calculation) => `
      <article class="logic-card">
        <div class="logic-head"><div><p class="kicker">${escapeHtml(connectionName(calculation.connectionId))} · ${escapeHtml(datasetName(calculation.datasetId))}</p><h3>${escapeHtml(calculation.name)}</h3></div><span class="version-badge">${escapeHtml(calculation.versionDate)} · ${escapeHtml(calculation.outputType)}</span></div>
        <pre><code>${escapeHtml(calculation.formula)}</code></pre>
        <div class="logic-sources"><b>Sources</b>${calculation.sourceFields.length ? calculation.sourceFields.map((field) => `<span>${escapeHtml(field)}</span>`).join("") : '<span>Not documented</span>'}</div>
        <p>${escapeHtml(calculation.businessReason || "Business definition not documented")}</p>
        <div class="record-footer"><span>${escapeHtml(calculation.owner || "No owner")} · version ${escapeHtml(calculation.versionDate)}</span><button class="text-button" type="button" data-record-type="calculation" data-record-id="${calculation.id}">Open setup + history</button></div>
      </article>`).join("") : '<div class="empty-state"><div><h3>No calculated logic yet</h3><p>Document the formula, source fields, version, owner, and validation.</p></div></div>';
  }

  function renderChanges() {
    const changes = [...state.sync.changes].sort((a, b) => String(b.versionDate || b.createdAt).localeCompare(String(a.versionDate || a.createdAt)));
    elements.changeList.innerHTML = changes.length ? changes.map((change) => `
      <article class="timeline-entry"><span class="timeline-dot"></span><div class="timeline-date">${escapeHtml(change.versionDate)}</div><div class="timeline-card"><div class="logic-head"><div><p class="kicker">${escapeHtml(connectionName(change.connectionId))} · commit ${escapeHtml(change.commitId)}</p><h3>${escapeHtml(change.title)}</h3></div><span class="version-badge">${escapeHtml(change.versionDate)}</span></div><div class="manifest-tags">${change.entityLinks.length ? change.entityLinks.map((link) => `<button type="button" data-record-type="${escapeHtml(link.type)}" data-record-id="${escapeHtml(link.id)}">${escapeHtml(manifestRecordLabel(link))}</button>`).join("") : '<span>Connection-level update</span>'}</div><p>${escapeHtml(change.reason)}</p>${change.snapshot ? `<details class="snapshot"><summary>Implementation snapshot</summary><pre><code>${escapeHtml(change.snapshot)}</code></pre></details>` : ""}<div class="record-footer"><span>${escapeHtml(change.owner || "No author")}${change.approvedBy ? ` · approved by ${escapeHtml(change.approvedBy)}` : ""}</span><span>${escapeHtml(change.ticket || change.validation || "No validation link")}</span></div></div></article>`).join("") : '<div class="empty-state"><div><h3>No manifest updates</h3><p>Commit each datasource or metric change with a date, tagged records, reason, and implementation snapshot.</p></div></div>';
  }

  function renderDiscrepancies() {
    const issues = [...state.sync.discrepancies].sort((a, b) => (a.status === "resolved") - (b.status === "resolved") || new Date(b.updatedAt) - new Date(a.updatedAt));
    elements.discrepancyList.innerHTML = issues.length ? issues.map((issue) => `
      <article class="issue-card ${issue.status === "resolved" ? "is-resolved" : ""}">
        <div class="issue-head"><div><span class="priority-chip ${issue.severity === "P1" ? "tone-red" : issue.severity === "P2" ? "tone-amber" : "tone-blue"}">${escapeHtml(issue.severity)}</span><span class="status-chip tone-neutral">${escapeHtml(issue.status)}</span></div><span>${escapeHtml(connectionName(issue.connectionId))}</span></div>
        <h3>${escapeHtml(issue.title)}</h3>
        <p>${escapeHtml(issue.impact || "Business impact not documented")}</p>
        <div class="expected-actual"><div><b>Expected</b><p>${escapeHtml(issue.expected || "Not set")}</p></div><div><b>Actual</b><p>${escapeHtml(issue.actual || "Not set")}</p></div></div>
        <div class="record-footer"><span>${escapeHtml(issue.owner || "No owner")} · ${escapeHtml(issue.observedFrom || "date not set")}</span><div class="button-row"><button class="button small ghost" type="button" data-toggle-issue="${issue.id}">${issue.status === "resolved" ? "Reopen" : "Resolve"}</button>${issue.opsItemId ? '<a class="button small" href="../opsdesk/#board">Open OpsDesk</a>' : `<button class="button small" type="button" data-create-issue-task="${issue.id}">Create task</button>`}</div></div>
      </article>`).join("") : '<div class="empty-state"><div><h3>No discrepancies logged</h3><p>Capture expected versus actual behavior and link the issue to OpsDesk.</p></div></div>';
  }

  function selectedConnection() {
    return state.sync.connections.find((connection) => connection.id === state.selectedConnectionId) || null;
  }

  function linkedOpsItems(connectionId) {
    return workspaceStore.get().opsDesk.items.filter((item) => Array.isArray(item.knowledgeLinks) && item.knowledgeLinks.some((link) => link.type === "connection" && link.id === connectionId));
  }

  function renderLinkedWork(connection) {
    const items = linkedOpsItems(connection.id);
    elements.linkedWork.innerHTML = items.length ? items.map((item) => `<a class="linked-item" href="../opsdesk/#board"><span>${escapeHtml(item.title)}</span><strong>${escapeHtml(item.status)}</strong></a>`).join("") : '<div class="list-empty">No linked OpsDesk work</div>';
  }

  function renderDetail() {
    const connection = selectedConnection();
    if (!connection) {
      elements.detailEmpty.hidden = false;
      elements.detailForm.hidden = true;
      return;
    }
    renderApplicationOptions();
    const fields = ["name", "applicationId", "status", "sourceType", "provider", "businessOwner", "technicalOwner", "sourceSystem", "destinationSystem", "cadence", "coverageFrom", "coverageTo", "purpose", "grain", "notes", "runbook"];
    fields.forEach((name) => {
      const input = elements.detailForm.elements[name];
      if (input) input.value = connection[name] || "";
    });
    elements.detailForm.elements.lastSync.value = toDateTimeInput(connection.lastSync);
    const status = freshness(connection);
    elements.detailStatus.textContent = status.label;
    elements.detailStatus.className = `status-chip ${status.tone}`;
    elements.detailUpdated.textContent = `Updated ${formatDate(connection.updatedAt, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}`;
    elements.detailEmpty.hidden = true;
    elements.detailForm.hidden = false;
    renderLinkedWork(connection);
  }

  function render() {
    renderViews();
    renderMetrics();
    renderApplicationOptions();
    renderApplications();
    renderConnections();
    renderSchema();
    renderCalculations();
    renderChanges();
    renderDiscrepancies();
    renderDetail();
  }

  function openConnection(id) {
    if (!state.sync.connections.some((connection) => connection.id === id)) return;
    state.selectedConnectionId = id;
    renderConnections();
    renderDetail();
    if (window.innerWidth < 1180) elements.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function updateCalculationDatasets() {
    const connectionSelect = elements.calculationForm?.elements.connectionId;
    const datasetSelect = elements.calculationForm?.elements.datasetId;
    if (!connectionSelect || !datasetSelect) return;
    const value = datasetSelect.value;
    const datasets = state.sync.datasets.filter((dataset) => !connectionSelect.value || dataset.connectionId === connectionSelect.value);
    datasetSelect.innerHTML = `<option value="">Connection-level logic</option>${datasets.map((dataset) => `<option value="${dataset.id}">${escapeHtml(dataset.name)}</option>`).join("")}`;
    if ([...datasetSelect.options].some((option) => option.value === value)) datasetSelect.value = value;
  }

  function renderManifestTargets(connectionId = elements.changeForm.elements.connectionId.value) {
    if (!connectionId) {
      elements.manifestTargets.innerHTML = "<p>Select a connection to load its metrics, dimensions, and calculations.</p>";
      return;
    }
    const datasetIds = new Set(state.sync.datasets.filter((dataset) => dataset.connectionId === connectionId).map((dataset) => dataset.id));
    const fields = state.sync.fields.filter((field) => datasetIds.has(field.datasetId));
    const calculations = state.sync.calculations.filter((calculation) => calculation.connectionId === connectionId);
    const records = [
      ...fields.map((field) => ({ type: "field", id: field.id, name: field.name, meta: `${field.kind} · ${datasetName(field.datasetId)}` })),
      ...calculations.map((calculation) => ({ type: "calculation", id: calculation.id, name: calculation.name, meta: `calculated ${calculation.outputType.toLowerCase()} · ${datasetName(calculation.datasetId)}` }))
    ];
    elements.manifestTargets.innerHTML = records.length ? records.map((record) => `
      <label class="manifest-target"><input type="checkbox" name="entityLinks" value="${record.type}:${record.id}" /><span><strong>${escapeHtml(record.name)}</strong><small>${escapeHtml(record.meta)}</small></span></label>`).join("") : "<p>No fields or calculations are documented for this connection yet.</p>";
  }

  function manifestHistory(type, id) {
    return state.sync.changes
      .filter((change) => change.entityLinks.some((link) => link.type === type && link.id === id))
      .sort((a, b) => String(b.versionDate).localeCompare(String(a.versionDate)));
  }

  function openRecord(type, id) {
    const isCalculation = type === "calculation";
    const record = isCalculation
      ? state.sync.calculations.find((item) => item.id === id)
      : state.sync.fields.find((item) => item.id === id);
    if (!record) return;
    const dataset = isCalculation
      ? state.sync.datasets.find((item) => item.id === record.datasetId)
      : state.sync.datasets.find((item) => item.id === record.datasetId);
    const connectionId = isCalculation ? record.connectionId : dataset?.connectionId;
    const history = manifestHistory(type, id);
    elements.recordKind.textContent = isCalculation ? `Calculated ${record.outputType}` : record.kind;
    elements.recordTitle.textContent = record.name;
    elements.recordDetail.innerHTML = `
      <section class="record-setup">
        <div class="record-facts">
          <div><span>Connection</span><strong>${escapeHtml(connectionName(connectionId))}</strong></div>
          <div><span>Dataset</span><strong>${escapeHtml(datasetName(record.datasetId))}</strong></div>
          <div><span>Version date</span><strong>${escapeHtml(record.versionDate)}</strong></div>
          <div><span>Owner</span><strong>${escapeHtml(record.owner || "Not assigned")}</strong></div>
          ${isCalculation ? `<div><span>Source fields</span><strong>${escapeHtml(record.sourceFields.join(", ") || "Not documented")}</strong></div><div><span>Effective from</span><strong>${escapeHtml(record.effectiveFrom || "Not set")}</strong></div>` : `<div><span>Data type</span><strong>${escapeHtml(record.dataType)}</strong></div><div><span>Status</span><strong>${escapeHtml(record.status)}</strong></div>`}
        </div>
        <div class="setup-copy"><span>${isCalculation ? "Business definition" : "Definition"}</span><p>${escapeHtml(isCalculation ? record.businessReason || "Not documented" : record.definition || "Not documented")}</p></div>
        ${isCalculation ? `<div class="setup-code"><span>Current implementation</span><pre><code>${escapeHtml(record.formula || "No implementation saved")}</code></pre></div><div class="setup-copy"><span>Validation</span><p>${escapeHtml(record.validation || "Not documented")}</p></div>` : ""}
      </section>
      <section class="record-history">
        <div class="record-history-heading"><h3>Manifest history</h3><span>${history.length} update${history.length === 1 ? "" : "s"}</span></div>
        ${history.length ? history.map((change) => `<article class="record-commit"><div><span>${escapeHtml(change.versionDate)} · ${escapeHtml(change.commitId)}</span><strong>${escapeHtml(change.title)}</strong></div><p>${escapeHtml(change.reason)}</p>${change.snapshot ? `<pre><code>${escapeHtml(change.snapshot)}</code></pre>` : ""}<small>${escapeHtml(change.owner || "No author")}${change.ticket ? ` · ${escapeHtml(change.ticket)}` : ""}</small></article>`).join("") : '<div class="list-empty">No manifest update has tagged this record yet.</div>'}
      </section>`;
    elements.recordModal.showModal();
  }

  function syncDetailToState() {
    const connection = selectedConnection();
    if (!connection) return;
    elements.detailForm.querySelectorAll("[name]").forEach((input) => {
      connection[input.name] = input.value.trim();
    });
    connection.updatedAt = now();
    elements.autosaveStatus.textContent = "Saving…";
    persist();
    renderMetrics();
    renderConnections();
    const status = freshness(connection);
    elements.detailStatus.textContent = status.label;
    elements.detailStatus.className = `status-chip ${status.tone}`;
    elements.detailUpdated.textContent = `Updated ${formatDate(connection.updatedAt, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}`;
    elements.autosaveStatus.textContent = "Saved locally";
  }

  function createOpsTask({ connection, discrepancy = null }) {
    workspace = workspaceStore.get();
    const timestamp = now();
    const item = {
      id: uid("work"),
      title: discrepancy ? `Investigate: ${discrepancy.title}` : `Review connection: ${connection.name}`,
      type: discrepancy ? "analytics" : "task",
      status: "inbox",
      priority: discrepancy?.severity || "P3",
      due: "",
      owner: discrepancy?.owner || connection.technicalOwner,
      project: connection.name,
      tags: ["syncdesk", discrepancy ? "discrepancy" : "connection"],
      summary: discrepancy ? `${discrepancy.impact}\n\nExpected: ${discrepancy.expected}\nActual: ${discrepancy.actual}`.trim() : `Review ownership, freshness, schema, and runbook for ${connection.name}.`,
      nextAction: discrepancy ? "Reproduce the discrepancy, confirm the first divergence, and document the resolution." : "Validate the connection record and close documentation gaps.",
      blocker: "",
      expected: discrepancy?.expected || "",
      actual: discrepancy?.actual || "",
      links: `${location.origin}${location.pathname.replace(/syncdesk\/$/, "syncdesk/")}#connections`,
      knowledgeLinks: [{ type: "connection", id: connection.id }, ...(discrepancy ? [{ type: "discrepancy", id: discrepancy.id }] : [])],
      focus: false,
      archived: false,
      notes: [],
      createdAt: timestamp,
      updatedAt: timestamp,
      completedAt: ""
    };
    workspace.opsDesk.items.unshift(item);
    workspaceStore.save(workspace);
    return item;
  }

  function exportWorkspace() {
    if (elements.storageModal.open) elements.storageModal.close();
    persist();
    const payload = workspaceStore.exportPayload(workspaceStore.get());
    download(`operations-workspace-${localDateString()}.json`, JSON.stringify(payload, null, 2), "application/json;charset=utf-8");
    toast("Complete workspace exported");
  }

  function reportSheet(records, emptyMessage, widths = []) {
    const sheet = XLSX.utils.json_to_sheet(records.length ? records : [{ Message: emptyMessage }]);
    if (records.length) {
      const columns = Object.keys(records[0]);
      sheet["!cols"] = columns.map((column, index) => ({
        wch: widths[index] || Math.min(52, Math.max(14, column.length + 2))
      }));
    } else {
      sheet["!cols"] = [{ wch: Math.max(28, emptyMessage.length + 2) }];
    }
    return sheet;
  }

  function exportReport() {
    if (!globalThis.XLSX) {
      toast("Excel exporter is unavailable");
      return;
    }

    persist();
    const openDiscrepancies = state.sync.discrepancies.filter((record) => record.status !== "resolved");
    const summary = [
      { Metric: "Exported at", Value: new Date().toISOString() },
      { Metric: "Applications", Value: state.sync.applications.length },
      { Metric: "Connections", Value: state.sync.connections.length },
      { Metric: "Active connections", Value: state.sync.connections.filter((record) => record.status === "active").length },
      { Metric: "Datasets", Value: state.sync.datasets.length },
      { Metric: "Documented fields", Value: state.sync.fields.length },
      { Metric: "Calculated metrics and dimensions", Value: state.sync.calculations.length },
      { Metric: "Manifest updates", Value: state.sync.changes.length },
      { Metric: "Open discrepancies", Value: openDiscrepancies.length },
      { Metric: "Resolved discrepancies", Value: state.sync.discrepancies.length - openDiscrepancies.length }
    ];
    const applications = state.sync.applications.map((record) => ({
      ID: record.id,
      Application: record.name,
      Owner: record.owner,
      Environment: record.environment,
      Purpose: record.description,
      "Created at": record.createdAt,
      "Updated at": record.updatedAt
    }));
    const connections = state.sync.connections.map((record) => ({
      ID: record.id,
      Connection: record.name,
      Application: applicationName(record.applicationId),
      Status: record.status,
      "Source type": record.sourceType,
      Source: record.sourceSystem,
      Destination: record.destinationSystem,
      Provider: record.provider,
      "Business owner": record.businessOwner,
      "Technical owner": record.technicalOwner,
      Cadence: record.cadence,
      "Coverage from": record.coverageFrom,
      "Coverage through": record.coverageTo,
      "Last sync": record.lastSync,
      Purpose: record.purpose,
      Grain: record.grain,
      Notes: record.notes,
      Runbook: record.runbook,
      "Updated at": record.updatedAt
    }));
    const datasets = state.sync.datasets.map((record) => ({
      ID: record.id,
      Dataset: record.name,
      Connection: connectionName(record.connectionId),
      Kind: record.kind,
      Location: record.location,
      Grain: record.grain,
      "Primary keys": record.primaryKeys,
      "Date field": record.dateField,
      Description: record.description,
      "Updated at": record.updatedAt
    }));
    const fields = state.sync.fields.map((record) => {
      const dataset = state.sync.datasets.find((item) => item.id === record.datasetId);
      return {
        ID: record.id,
        Field: record.name,
        Dataset: datasetName(record.datasetId),
        Connection: dataset ? connectionName(dataset.connectionId) : "Unknown connection",
        Role: record.kind,
        "Data type": record.dataType,
        Definition: record.definition,
        "Source field": record.sourceField,
        Owner: record.owner,
        "Version date": record.versionDate,
        Status: record.status,
        Notes: record.notes,
        "Manifest updates": state.sync.changes.filter((change) => change.entityLinks.some((link) => link.type === "field" && link.id === record.id)).length,
        "Updated at": record.updatedAt
      };
    });
    const calculations = state.sync.calculations.map((record) => ({
      ID: record.id,
      Calculation: record.name,
      Output: record.outputType,
      Connection: connectionName(record.connectionId),
      Dataset: datasetName(record.datasetId),
      "Source fields": record.sourceFields.join("; "),
      "Formula / code": record.formula,
      "Business definition": record.businessReason,
      Owner: record.owner,
      "Version date": record.versionDate,
      "Effective from": record.effectiveFrom,
      Validation: record.validation,
      Status: record.status,
      "Manifest updates": state.sync.changes.filter((change) => change.entityLinks.some((link) => link.type === "calculation" && link.id === record.id)).length,
      "Updated at": record.updatedAt
    }));
    const changes = state.sync.changes.map((record) => ({
      "Commit ID": record.commitId,
      "Version date": record.versionDate,
      Connection: connectionName(record.connectionId),
      "Commit message": record.title,
      "Tagged records": record.entityLinks.map(manifestRecordLabel).join("; "),
      "What changed and why": record.reason,
      "Implementation snapshot": record.snapshot,
      "Author / owner": record.owner,
      "Approved by": record.approvedBy,
      "Ticket / decision": record.ticket,
      "Validation / rollout": record.validation,
      "Created at": record.createdAt
    }));
    const discrepancies = state.sync.discrepancies.map((record) => ({
      ID: record.id,
      Discrepancy: record.title,
      Connection: connectionName(record.connectionId),
      Status: record.status,
      Severity: record.severity,
      "Observed from": record.observedFrom,
      "Observed through": record.observedTo,
      "Business impact": record.impact,
      Expected: record.expected,
      Actual: record.actual,
      Owner: record.owner,
      Resolution: record.resolution,
      "Linked OpsDesk item": record.opsItemId,
      "Updated at": record.updatedAt
    }));

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, reportSheet(summary, "No summary available", [34, 34]), "Summary");
    XLSX.utils.book_append_sheet(workbook, reportSheet(applications, "No applications documented"), "Applications");
    XLSX.utils.book_append_sheet(workbook, reportSheet(connections, "No connections documented"), "Connections");
    XLSX.utils.book_append_sheet(workbook, reportSheet(datasets, "No datasets documented"), "Datasets");
    XLSX.utils.book_append_sheet(workbook, reportSheet(fields, "No fields documented"), "Fields");
    XLSX.utils.book_append_sheet(workbook, reportSheet(calculations, "No calculated logic documented"), "Calculations");
    XLSX.utils.book_append_sheet(workbook, reportSheet(changes, "No manifest updates documented"), "Manifest");
    XLSX.utils.book_append_sheet(workbook, reportSheet(discrepancies, "No discrepancies documented"), "Discrepancies");
    XLSX.writeFile(workbook, `syncdesk-report-${localDateString()}.xlsx`, { compression: true });
    toast("Complete SyncDesk report exported");
  }

  function prepareImport(payload, fileName) {
    const isLegacy = payload?.app === "OpsDesk" && Array.isArray(payload?.items);
    const isWorkspace = payload?.schemaVersion === 2 && Array.isArray(payload?.opsDesk?.items);
    if (!isLegacy && !isWorkspace) throw new Error("Invalid workspace");
    const imported = workspaceStore.normalize(payload);
    const syncCount = syncKeys.reduce((sum, key) => sum + imported.syncDesk[key].length, 0);
    pendingImport = imported;
    elements.importSummary.textContent = `${fileName} contains ${imported.opsDesk.items.length} OpsDesk items and ${syncCount} SyncDesk records. Your current browser workspace will remain unchanged until you choose Merge or Replace.`;
    elements.importModal.showModal();
  }

  function applyImport(mode) {
    if (!pendingImport) return;
    workspace = mode === "merge" ? workspaceStore.merge(workspaceStore.get(), pendingImport) : workspaceStore.normalize(pendingImport);
    workspace = workspaceStore.save(workspace);
    state.sync = normalizeSync(workspace.syncDesk);
    state.selectedConnectionId = null;
    pendingImport = null;
    elements.importModal.close();
    render();
    toast(mode === "merge" ? "Workspace merged" : "Workspace replaced");
  }

  function requestConnectionDelete() {
    const connection = selectedConnection();
    if (!connection) return;
    pendingDeleteId = connection.id;
    elements.deleteSummary.textContent = `“${connection.name}” and all of its SyncDesk records will be removed permanently.`;
    elements.deleteModal.showModal();
  }

  function deleteConnection() {
    if (!pendingDeleteId) return;
    const datasetIds = new Set(state.sync.datasets.filter((dataset) => dataset.connectionId === pendingDeleteId).map((dataset) => dataset.id));
    state.sync.connections = state.sync.connections.filter((connection) => connection.id !== pendingDeleteId);
    state.sync.datasets = state.sync.datasets.filter((dataset) => dataset.connectionId !== pendingDeleteId);
    state.sync.fields = state.sync.fields.filter((field) => !datasetIds.has(field.datasetId));
    state.sync.calculations = state.sync.calculations.filter((record) => record.connectionId !== pendingDeleteId);
    state.sync.changes = state.sync.changes.filter((record) => record.connectionId !== pendingDeleteId);
    state.sync.discrepancies = state.sync.discrepancies.filter((record) => record.connectionId !== pendingDeleteId);
    state.selectedConnectionId = null;
    pendingDeleteId = null;
    persist();
    elements.deleteModal.close();
    render();
    toast("Connection deleted permanently");
  }

  document.addEventListener("click", (event) => {
    const viewLink = event.target.closest("[data-view-link]");
    const viewButton = event.target.closest("[data-view-button]");
    const appFilter = event.target.closest("[data-application-filter]");
    const connectionTarget = event.target.closest("[data-connection-id]");
    if (viewLink) { event.preventDefault(); setView(viewLink.dataset.viewLink); }
    if (viewButton) setView(viewButton.dataset.viewButton);
    if (appFilter) { state.applicationFilter = appFilter.dataset.applicationFilter; renderApplications(); renderConnections(); }
    if (connectionTarget) openConnection(connectionTarget.dataset.connectionId);
    if (event.target.closest("[data-new-application]")) { elements.applicationForm.reset(); elements.applicationModal.showModal(); }
    if (event.target.closest("[data-new-connection]")) { elements.connectionForm.reset(); renderApplicationOptions(); elements.connectionModal.showModal(); }
    if (event.target.closest("[data-new-schema]")) { elements.schemaForm.reset(); renderApplicationOptions(); elements.schemaModal.showModal(); }
    if (event.target.closest("[data-new-calculation]")) {
      elements.calculationForm.reset();
      renderApplicationOptions();
      elements.calculationForm.elements.versionDate.value = localDateString();
      elements.calculationForm.elements.effectiveFrom.value = localDateString();
      updateCalculationDatasets();
      elements.calculationModal.showModal();
    }
    if (event.target.closest("[data-new-change]")) {
      elements.changeForm.reset();
      renderApplicationOptions();
      elements.changeForm.elements.versionDate.value = localDateString();
      if (state.selectedConnectionId) elements.changeForm.elements.connectionId.value = state.selectedConnectionId;
      renderManifestTargets();
      elements.changeModal.showModal();
    }
    if (event.target.closest("[data-new-discrepancy]")) { elements.discrepancyForm.reset(); renderApplicationOptions(); elements.discrepancyModal.showModal(); }
    if (event.target.closest("[data-dialog-close]")) event.target.closest("dialog").close();
    if (event.target.closest("[data-close-detail]")) { state.selectedConnectionId = null; renderConnections(); renderDetail(); }
    const recordTarget = event.target.closest("[data-record-type][data-record-id]");
    if (recordTarget) openRecord(recordTarget.dataset.recordType, recordTarget.dataset.recordId);
    if (event.target.closest("[data-export-report]")) exportReport();
    if (event.target.closest("[data-export-workspace]")) exportWorkspace();
    if (event.target.closest("[data-import-trigger]")) elements.importFile.click();
    if (event.target.closest("[data-storage-guide]")) elements.storageModal.showModal();
    if (event.target.closest("[data-import-close]")) { pendingImport = null; elements.importModal.close(); }
    const importMode = event.target.closest("[data-import-mode]");
    if (importMode) applyImport(importMode.dataset.importMode);
    if (event.target.closest("[data-delete-connection]")) requestConnectionDelete();
    if (event.target.closest("[data-delete-close]")) { pendingDeleteId = null; elements.deleteModal.close(); }
    if (event.target.closest("[data-confirm-delete]")) deleteConnection();
    if (event.target.closest("[data-create-ops-task]")) {
      const connection = selectedConnection();
      if (connection) { createOpsTask({ connection }); renderLinkedWork(connection); toast("OpsDesk task created"); }
    }
    const issueTask = event.target.closest("[data-create-issue-task]");
    if (issueTask) {
      const issue = state.sync.discrepancies.find((record) => record.id === issueTask.dataset.createIssueTask);
      const connection = issue && state.sync.connections.find((record) => record.id === issue.connectionId);
      if (issue && connection) { issue.opsItemId = createOpsTask({ connection, discrepancy: issue }).id; issue.updatedAt = now(); persist(); renderDiscrepancies(); toast("Linked OpsDesk task created"); }
    }
    const toggleIssue = event.target.closest("[data-toggle-issue]");
    if (toggleIssue) {
      const issue = state.sync.discrepancies.find((record) => record.id === toggleIssue.dataset.toggleIssue);
      if (issue) { issue.status = issue.status === "resolved" ? "open" : "resolved"; issue.updatedAt = now(); persist(); render(); toast(issue.status === "resolved" ? "Discrepancy resolved" : "Discrepancy reopened"); }
    }
  });

  elements.applicationForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(elements.applicationForm).entries());
    state.sync.applications.push(normalizeApplication(values));
    persist();
    elements.applicationModal.close();
    render();
    toast("Application added");
  });

  elements.connectionForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(elements.connectionForm).entries());
    const connection = normalizeConnection({ ...values, status: "active" });
    state.sync.connections.unshift(connection);
    state.selectedConnectionId = connection.id;
    persist();
    elements.connectionModal.close();
    render();
    toast("Connection created");
  });

  elements.schemaForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(elements.schemaForm).entries());
    const dataset = normalizeDataset(values);
    state.sync.datasets.push(dataset);
    String(values.fields || "").split("\n").map((line) => line.trim()).filter(Boolean).forEach((line) => {
      const [name, kind, dataType, ...definition] = line.split("|").map((part) => part.trim());
      state.sync.fields.push(normalizeField({ datasetId: dataset.id, name, kind: kind || "dimension", dataType: dataType || "text", definition: definition.join(" | ") }));
    });
    persist();
    elements.schemaModal.close();
    setView("schema");
    render();
    toast("Schema saved");
  });

  elements.calculationForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(elements.calculationForm).entries());
    state.sync.calculations.unshift(normalizeCalculation({ ...values, sourceFields: parseList(values.sourceFields) }));
    persist();
    elements.calculationModal.close();
    setView("logic");
    render();
    toast("Calculation documented");
  });

  elements.changeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(elements.changeForm);
    const values = Object.fromEntries(formData.entries());
    const entityLinks = formData.getAll("entityLinks").map((value) => {
      const [type, id] = value.split(":");
      return { type, id };
    });
    const change = normalizeChange({ ...values, entityLinks });
    state.sync.changes.unshift(change);
    if (formData.has("applySnapshot") && change.snapshot && entityLinks.length === 1 && entityLinks[0].type === "calculation") {
      const calculation = state.sync.calculations.find((item) => item.id === entityLinks[0].id);
      if (calculation) {
        calculation.formula = change.snapshot;
        calculation.versionDate = change.versionDate;
        calculation.updatedAt = now();
      }
    }
    persist();
    elements.changeModal.close();
    setView("changes");
    render();
    toast("Manifest update committed");
  });

  elements.discrepancyForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(elements.discrepancyForm);
    const values = Object.fromEntries(formData.entries());
    const issue = normalizeDiscrepancy(values);
    state.sync.discrepancies.unshift(issue);
    if (formData.has("createOpsTask")) {
      const connection = state.sync.connections.find((record) => record.id === issue.connectionId);
      if (connection) issue.opsItemId = createOpsTask({ connection, discrepancy: issue }).id;
    }
    persist();
    elements.discrepancyModal.close();
    setView("issues");
    render();
    toast(issue.opsItemId ? "Discrepancy and OpsDesk task created" : "Discrepancy logged");
  });

  elements.detailForm.addEventListener("input", syncDetailToState);
  elements.detailForm.addEventListener("change", syncDetailToState);
  elements.connectionSearch.addEventListener("input", () => { state.connectionSearch = elements.connectionSearch.value; renderConnections(); });
  elements.statusFilter.addEventListener("change", () => { state.connectionStatus = elements.statusFilter.value; renderConnections(); });
  elements.schemaConnectionFilter.addEventListener("change", () => { state.schemaConnection = elements.schemaConnectionFilter.value; renderSchema(); });
  elements.schemaSearch.addEventListener("input", () => { state.schemaSearch = elements.schemaSearch.value; renderSchema(); });
  elements.calculationForm.elements.connectionId.addEventListener("change", updateCalculationDatasets);
  elements.changeForm.elements.connectionId.addEventListener("change", () => renderManifestTargets());

  elements.importFile.addEventListener("change", async () => {
    const file = elements.importFile.files?.[0];
    if (!file) return;
    try { prepareImport(JSON.parse(await file.text()), file.name); }
    catch { toast("This file is not a valid workspace backup"); }
    finally { elements.importFile.value = ""; }
  });

  window.addEventListener("hashchange", () => {
    const next = location.hash.slice(1);
    if (views.includes(next)) { state.view = next; renderViews(); }
  });

  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("./sw.js").catch(() => {
      /* SyncDesk remains usable online when service-worker registration is unavailable. */
    });
  }

  render();
})();
