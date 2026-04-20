import {
  beginBoundaryDrawSession,
  completeBoundaryDrawSession,
  createInteractionSessionState,
  resetBoundaryDrawSession,
} from "./interaction_state.mjs";
import {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  bearingBetweenPoints,
  clampReplayIndex,
  createDefaultFieldProfile,
  destinationPoint,
  deriveRunwayEndpoints,
  densityToScanSpacing,
  exportFieldProfile,
  formatBoundaryPolygon,
  getByPath,
  haversineDistance,
  importFieldProfile,
  insertVertexIntoPolygon,
  parseBoundaryText,
  parseFlightLogCsv,
  replayIndexFromProgress,
  replayProgressForIndex,
  scanSpacingToDensity,
  setByPath,
  stripClosedPolygon,
  syncLandingFromRunway,
  validateFieldProfile,
} from "./logic.mjs";

const STORAGE_KEYS = {
  credentials: "fieldEditor.amap.credentials",
};

function loadConfiguredCredentials() {
  const configured = globalThis.__FIELD_EDITOR_CONFIG__?.amap;
  if (!configured || typeof configured !== "object") {
    return { key: "", securityJsCode: "" };
  }
  return {
    key: typeof configured.key === "string" ? configured.key.trim() : "",
    securityJsCode:
      typeof configured.securityJsCode === "string" ? configured.securityJsCode.trim() : "",
  };
}

function resolveInitialCredentials() {
  const stored = loadStoredCredentials();
  const configured = loadConfiguredCredentials();
  if (configured.key && configured.securityJsCode) {
    return configured;
  }
  return stored;
}

const dom = {
  credentialPanel: document.querySelector("#credential-panel"),
  credentialsForm: document.querySelector("#credentials-form"),
  amapKeyInput: document.querySelector("#amap-key-input"),
  amapSecurityCodeInput: document.querySelector("#amap-security-code-input"),
  retryMapButton: document.querySelector("#retry-map-button"),
  clearCredentialsButton: document.querySelector("#clear-credentials-button"),
  mapStatus: document.querySelector("#map-status"),
  interactionStatus: document.querySelector("#interaction-status"),
  newFieldButton: document.querySelector("#new-field-button"),
  importFileInput: document.querySelector("#import-file-input"),
  replayFileInput: document.querySelector("#replay-file-input"),
  exportButton: document.querySelector("#export-button"),
  drawBoundaryButton: document.querySelector("#draw-boundary-button"),
  editBoundaryButton: document.querySelector("#edit-boundary-button"),
  setRunwayButton: document.querySelector("#set-runway-button"),
  setDropPointButton: document.querySelector("#set-drop-point-button"),
  fitViewButton: document.querySelector("#fit-view-button"),
  clearOverlaysButton: document.querySelector("#clear-overlays-button"),
  boundaryPolygonText: document.querySelector("#boundary-polygon-text"),
  blockingErrors: document.querySelector("#blocking-errors"),
  advisoryWarnings: document.querySelector("#advisory-warnings"),
  replayPlayButton: document.querySelector("#replay-play-button"),
  replayPauseButton: document.querySelector("#replay-pause-button"),
  replayFitButton: document.querySelector("#replay-fit-button"),
  replaySpeedSelect: document.querySelector("#replay-speed-select"),
  replayProgressInput: document.querySelector("#replay-progress-input"),
  replayStatus: document.querySelector("#replay-status"),
  replaySampleSummary: document.querySelector("#replay-sample-summary"),
  replayReleaseSummary: document.querySelector("#replay-release-summary"),
  replayDropSummary: document.querySelector("#replay-drop-summary"),
  landingApproachSummary: document.querySelector("#landing-approach-summary"),
  scanDensityInput: document.querySelector("#scan-density-input"),
  scanDensityLabel: document.querySelector("#scan-density-label"),
  mapContainer: document.querySelector("#map-container"),
  fieldForm: document.querySelector("#field-form"),
  basemapButtons: [...document.querySelectorAll("[data-basemap-mode]")],
};

globalThis.__fieldEditorExports = globalThis.__fieldEditorExports || {};
globalThis.__fieldEditorExports.createDefaultFieldProfile = createDefaultFieldProfile;
globalThis.__fieldEditorExports.importFieldProfile = importFieldProfile;
globalThis.__fieldEditorExports.exportFieldProfile = exportFieldProfile;
globalThis.__fieldEditorExports.validateFieldProfile = validateFieldProfile;

const appState = {
  fieldProfile: createDefaultFieldProfile(),
  validation: validateFieldProfile(createDefaultFieldProfile()),
  credentials: resolveInitialCredentials(),
  mapReady: false,
  interactionMode: "idle",
  mapError: null,
  pendingRunwayStart: null,
  basemapMode: "standard",
  replay: {
    data: null,
    currentIndex: 0,
    isPlaying: false,
    speed: 1,
    lastFrameAtMs: 0,
    animationFrameId: null,
    loadedFileName: "",
  },
};

const mapState = {
  AMap: null,
  map: null,
  mouseTool: null,
  polygonEditor: null,
  polygonEditorSyncHandler: null,
  boundaryClickHandler: null,
  boundaryClickAttached: false,
  drawHandler: null,
  interactionSession: createInteractionSessionState(),
  overlays: {
    boundaryPolygon: null,
    boundaryVertexMarkers: [],
    runwayStartMarker: null,
    runwayEndMarker: null,
    runwayCenterline: null,
    landingApproachMarker: null,
    landingApproachLine: null,
    scanPolyline: null,
    dropPointMarker: null,
    replayTrajectoryLine: null,
    replayAircraftMarker: null,
    replayReleaseMarker: null,
    replayActualDropMarker: null,
    attackApproachLine: null,
    attackExitLine: null,
    takeoffPathLine: null,
    missionChainLine: null,
  },
};

function loadStoredCredentials() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.credentials);
    if (!raw) {
      return { key: "", securityJsCode: "" };
    }
    const parsed = JSON.parse(raw);
    return {
      key: parsed.key ?? "",
      securityJsCode: parsed.securityJsCode ?? "",
    };
  } catch {
    return { key: "", securityJsCode: "" };
  }
}

function saveCredentials(credentials) {
  localStorage.setItem(STORAGE_KEYS.credentials, JSON.stringify(credentials));
  appState.credentials = credentials;
}

function clearCredentials() {
  localStorage.removeItem(STORAGE_KEYS.credentials);
  appState.credentials = { key: "", securityJsCode: "" };
  dom.amapKeyInput.value = "";
  dom.amapSecurityCodeInput.value = "";
}

function setInteractionStatus(message) {
  dom.interactionStatus.textContent = message;
}

function setMapStatus(message, isError = false) {
  dom.mapStatus.textContent = message;
  dom.mapStatus.style.color = isError ? "#b91c1c" : "#475569";
}

function updateBasemapButtons() {
  for (const button of dom.basemapButtons) {
    const isActive = button.dataset.basemapMode === appState.basemapMode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  }
}

function closePolygonEditor() {
  mapState.polygonEditor?.close?.();
  clearBoundaryVertexMarkers();
}

function rebuildMouseTool() {
  if (!mapState.AMap || !mapState.map) {
    mapState.mouseTool = null;
    return null;
  }
  mapState.mouseTool = new mapState.AMap.MouseTool(mapState.map);
  return mapState.mouseTool;
}

function ensureMouseTool() {
  return mapState.mouseTool ?? rebuildMouseTool();
}

function closeActiveMapTools({ preserveRunwayStart = false } = {}) {
  if (mapState.mouseTool && mapState.drawHandler) {
    mapState.mouseTool.off?.("draw", mapState.drawHandler);
  }
  mapState.mouseTool?.close?.(true);
  mapState.drawHandler = null;
  resetBoundaryDrawSession(mapState.interactionSession);
  closePolygonEditor();
  mapState.mouseTool = null;
  if (!preserveRunwayStart) {
    appState.pendingRunwayStart = null;
  }
}

function rectangleBoundsToPolygon(bounds) {
  return [
    bounds.getNorthWest(),
    bounds.getNorthEast(),
    bounds.getSouthEast(),
    bounds.getSouthWest(),
  ].map(pointFromLngLat);
}

function finalizeBoundaryDrawing() {
  if (mapState.mouseTool && mapState.drawHandler) {
    mapState.mouseTool.off?.("draw", mapState.drawHandler);
  }
  mapState.mouseTool?.close?.(true);
  mapState.drawHandler = null;
  resetBoundaryDrawSession(mapState.interactionSession);
  mapState.mouseTool = null;
}

function destroyMap() {
  closePolygonEditor();
  resetBoundaryDrawSession(mapState.interactionSession);
  if (mapState.map) {
    mapState.map.destroy();
  }
  mapState.AMap = null;
  mapState.map = null;
  mapState.mouseTool = null;
  mapState.polygonEditor = null;
  mapState.polygonEditorSyncHandler = null;
  mapState.boundaryClickHandler = null;
  mapState.boundaryClickAttached = false;
  mapState.drawHandler = null;
  for (const key of Object.keys(mapState.overlays)) {
    mapState.overlays[key] = key === "boundaryVertexMarkers" ? [] : null;
  }
  appState.mapReady = false;
  dom.mapContainer.classList.remove("map-ready");
}

async function initializeMap() {
  const credentials = appState.credentials;
  if (!credentials.key || !credentials.securityJsCode) {
    setMapStatus("请先填写 AMap 凭据。", true);
    return;
  }
  if (!globalThis.AMapLoader) {
    setMapStatus("未检测到 AMapLoader，请检查 loader.js 是否成功加载。", true);
    return;
  }
  try {
    destroyMap();
    window._AMapSecurityConfig = {
      securityJsCode: credentials.securityJsCode,
    };
    setMapStatus("正在初始化地图...");
    const terrainMode = appState.basemapMode === "terrain";
    const AMap = await globalThis.AMapLoader.load({
      key: credentials.key,
      version: terrainMode ? "2.1Beta" : "2.0",
      plugins: ["AMap.Scale", "AMap.ToolBar", "AMap.MouseTool"],
    });
    mapState.AMap = AMap;

    const mapOptions = {
      zoom: DEFAULT_ZOOM,
      center: [DEFAULT_CENTER.lon, DEFAULT_CENTER.lat],
      resizeEnable: true,
    };

    if (terrainMode) {
      mapOptions.viewMode = "3D";
      mapOptions.terrain = true;
    } else if (appState.basemapMode === "satellite") {
      mapOptions.viewMode = "2D";
      mapOptions.layers = [
        new AMap.TileLayer.Satellite(),
        new AMap.TileLayer.RoadNet(),
      ];
    } else {
      mapOptions.viewMode = "2D";
      mapOptions.mapStyle = "amap://styles/normal";
    }

    mapState.map = new AMap.Map("map-container", mapOptions);
    mapState.map.addControl(new AMap.Scale());
    mapState.map.addControl(new AMap.ToolBar());
    rebuildMouseTool();
    mapState.map.on("click", handleMapClick);
    appState.mapReady = true;
    dom.mapContainer.classList.add("map-ready");
    updateBasemapButtons();
    setMapStatus("地图已初始化。可开始框选飞行区域、设置跑道和扫场参数。", false);
    renderOverlays();
  } catch (error) {
    appState.mapError = error;
    setMapStatus(`地图初始化失败：${error instanceof Error ? error.message : String(error)}`, true);
  }
}

function overlayList() {
  return Object.values(mapState.overlays).filter(Boolean);
}

function hasReplayData() {
  return Boolean(appState.replay.data?.samples?.length);
}

function getReplayCurrentSample() {
  if (!hasReplayData()) {
    return null;
  }
  return appState.replay.data.samples[appState.replay.currentIndex] ?? null;
}

function cancelReplayAnimation() {
  if (appState.replay.animationFrameId !== null) {
    cancelAnimationFrame(appState.replay.animationFrameId);
    appState.replay.animationFrameId = null;
  }
}

function stopReplayPlayback() {
  appState.replay.isPlaying = false;
  appState.replay.lastFrameAtMs = 0;
  cancelReplayAnimation();
  syncReplayControls();
}

function syncReplayControls() {
  const hasData = hasReplayData();
  dom.replayPlayButton.disabled = !hasData || appState.replay.isPlaying;
  dom.replayPauseButton.disabled = !hasData || !appState.replay.isPlaying;
  dom.replayFitButton.disabled = !hasData;
  dom.replaySpeedSelect.disabled = !hasData;
  dom.replayProgressInput.disabled = !hasData;
  dom.replayProgressInput.value = String(
    hasData ? Math.round(replayProgressForIndex(appState.replay.currentIndex, appState.replay.data.sampleCount)) : 0,
  );
}

function formatReplaySeconds(seconds) {
  if (!Number.isFinite(seconds)) {
    return "0.0s";
  }
  return `${seconds.toFixed(1)}s`;
}

function renderReplayStatus() {
  const data = appState.replay.data;
  if (!data) {
    dom.replayStatus.textContent = "尚未加载 flight_log。";
    dom.replaySampleSummary.textContent = "暂无回放样本。";
    dom.replayReleaseSummary.textContent = "Release 信息：暂无。";
    dom.replayDropSummary.textContent = "实际投弹点：暂无。";
    syncReplayControls();
    return;
  }

  const currentSample = getReplayCurrentSample();
  dom.replayStatus.textContent = `已加载 ${appState.replay.loadedFileName || "flight_log"}。`;
  dom.replaySampleSummary.textContent = `样本 ${appState.replay.currentIndex + 1}/${data.sampleCount}，时长 ${formatReplaySeconds(data.durationS)}，当前 ${formatReplaySeconds(currentSample?.relativeTimeS ?? 0)}。`;
  dom.replayReleaseSummary.textContent =
    data.releaseSampleIndex >= 0
      ? `Release 信息：已记录，第 ${data.releaseSampleIndex + 1} 个样本。`
      : data.hasReleaseMetadata
        ? "Release 信息：日志包含字段，但未记录成功触发。"
        : "Release 信息：日志缺少 release 字段。";
  dom.replayDropSummary.textContent = data.actualDrop
    ? `实际投弹点：${data.actualDrop.lat.toFixed(6)}, ${data.actualDrop.lon.toFixed(6)}${data.actualDrop.source ? ` (${data.actualDrop.source})` : ""}`
    : data.hasActualDropMetadata
      ? "实际投弹点：日志已支持，但本次任务未确认。"
      : "实际投弹点：日志缺少 actual_drop 字段。";
  syncReplayControls();
}

function createReplayMarkerContent(className) {
  const element = document.createElement("div");
  element.className = className;
  return element;
}

function ensureReplayMarker(name, position, title, className) {
  if (!mapState.map || !mapState.AMap || !position) {
    return null;
  }
  const existing = mapState.overlays[name];
  if (existing) {
    existing.setPosition(position);
    existing.setTitle?.(title);
    return existing;
  }
  const marker = new mapState.AMap.Marker({
    position,
    title,
    content: createReplayMarkerContent(className),
    offset: new mapState.AMap.Pixel(-9, -9),
    bubble: false,
    zIndex: 250,
  });
  marker.setMap(mapState.map);
  mapState.overlays[name] = marker;
  return marker;
}

function renderReplayOverlays() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const data = appState.replay.data;
  if (!data || data.samples.length === 0) {
    removeOverlay("replayTrajectoryLine");
    removeOverlay("replayAircraftMarker");
    removeOverlay("replayReleaseMarker");
    removeOverlay("replayActualDropMarker");
    renderReplayStatus();
    return;
  }

  const fullPath = data.samples.map((sample) => [sample.lon, sample.lat]);
  if (!mapState.overlays.replayTrajectoryLine) {
    mapState.overlays.replayTrajectoryLine = new mapState.AMap.Polyline({
      path: fullPath,
      strokeColor: "#0f766e",
      strokeWeight: 4,
      strokeOpacity: 0.9,
      zIndex: 140,
    });
    mapState.overlays.replayTrajectoryLine.setMap(mapState.map);
  } else {
    mapState.overlays.replayTrajectoryLine.setPath(fullPath);
  }

  const currentSample = getReplayCurrentSample();
  if (currentSample) {
    ensureReplayMarker(
      "replayAircraftMarker",
      [currentSample.lon, currentSample.lat],
      "回放飞机位置",
      "replay-trajectory-marker",
    );
  }

  if (data.releaseSampleIndex >= 0) {
    const releaseSample = data.samples[data.releaseSampleIndex];
    ensureReplayMarker(
      "replayReleaseMarker",
      [releaseSample.lon, releaseSample.lat],
      "Release 触发点",
      "replay-release-marker",
    );
  } else {
    removeOverlay("replayReleaseMarker");
  }

  if (data.actualDrop) {
    ensureReplayMarker(
      "replayActualDropMarker",
      [data.actualDrop.lon, data.actualDrop.lat],
      "实际投弹点",
      "replay-actual-drop-marker",
    );
  } else {
    removeOverlay("replayActualDropMarker");
  }

  renderReplayStatus();
}

function fitMapToReplay() {
  if (!mapState.map || !hasReplayData()) {
    return;
  }
  const overlays = [
    mapState.overlays.replayTrajectoryLine,
    mapState.overlays.replayAircraftMarker,
    mapState.overlays.replayReleaseMarker,
    mapState.overlays.replayActualDropMarker,
  ].filter(Boolean);
  if (overlays.length > 0) {
    mapState.map.setFitView(overlays);
  }
}

function setReplayIndex(index) {
  if (!hasReplayData()) {
    return;
  }
  appState.replay.currentIndex = clampReplayIndex(index, appState.replay.data.sampleCount);
  renderReplayOverlays();
}

function tickReplay(frameAtMs) {
  if (!appState.replay.isPlaying || !hasReplayData()) {
    return;
  }
  const sampleCount = appState.replay.data.sampleCount;
  if (sampleCount <= 1) {
    stopReplayPlayback();
    return;
  }
  if (!appState.replay.lastFrameAtMs) {
    appState.replay.lastFrameAtMs = frameAtMs;
  }
  const elapsedMs = frameAtMs - appState.replay.lastFrameAtMs;
  const advance = (elapsedMs / 1000) * appState.replay.speed;
  if (advance >= 1) {
    const nextIndex = Math.min(sampleCount - 1, appState.replay.currentIndex + Math.floor(advance));
    appState.replay.lastFrameAtMs = frameAtMs;
    setReplayIndex(nextIndex);
    if (nextIndex >= sampleCount - 1) {
      stopReplayPlayback();
      return;
    }
  }
  appState.replay.animationFrameId = requestAnimationFrame(tickReplay);
}

function startReplayPlayback() {
  if (!hasReplayData()) {
    return;
  }
  if (appState.replay.currentIndex >= appState.replay.data.sampleCount - 1) {
    appState.replay.currentIndex = 0;
  }
  appState.replay.isPlaying = true;
  appState.replay.lastFrameAtMs = 0;
  syncReplayControls();
  cancelReplayAnimation();
  appState.replay.animationFrameId = requestAnimationFrame(tickReplay);
}

function loadReplayData(data, fileName = "") {
  stopReplayPlayback();
  appState.replay.data = data;
  appState.replay.currentIndex = 0;
  appState.replay.loadedFileName = fileName;
  renderAll({ fitView: false, populateForm: false });
  fitMapToReplay();
}

function fitMapToOverlays() {
  if (!mapState.map) {
    return;
  }
  const overlays = overlayList();
  if (overlays.length === 0) {
    mapState.map.setZoomAndCenter(DEFAULT_ZOOM, [DEFAULT_CENTER.lon, DEFAULT_CENTER.lat]);
    return;
  }
  mapState.map.setFitView(overlays);
}

function isBoundaryEditingActive() {
  return appState.interactionMode === "editBoundary" && Boolean(mapState.overlays.boundaryPolygon);
}

function isMapPlacementMode() {
  return appState.interactionMode === "setRunway" || appState.interactionMode === "setDropPoint";
}

function shouldBoundaryEnterEditMode() {
  return (
    appState.interactionMode === "idle" ||
    appState.interactionMode === "editBoundary" ||
    appState.interactionMode === "setRunway" ||
    appState.interactionMode === "setDropPoint"
  );
}

function syncBoundaryOverlayInteractivity() {
  const polygon = mapState.overlays.boundaryPolygon;
  const handler = mapState.boundaryClickHandler;
  if (!polygon || !handler) {
    return;
  }

  if (shouldBoundaryEnterEditMode()) {
    if (!mapState.boundaryClickAttached) {
      polygon.on("click", handler);
      mapState.boundaryClickAttached = true;
    }
    return;
  }

  if (mapState.boundaryClickAttached) {
    polygon.off?.("click", handler);
    mapState.boundaryClickAttached = false;
  }
}

function setInteractionMode(mode, message) {
  appState.interactionMode = mode;
  if (mode !== "setRunway" && mode !== "setDropPoint") {
    appState.pendingRunwayStart = null;
  }
  syncBoundaryOverlayInteractivity();
  setInteractionStatus(`当前模式：${message}`);
}

function activateInteractionMode(mode, message, options = {}) {
  closeActiveMapTools({ preserveRunwayStart: options.preserveRunwayStart ?? false });
  setInteractionMode(mode, message);
}

function pointFromLngLat(lnglat) {
  return {
    lat: lnglat.getLat(),
    lon: lnglat.getLng(),
  };
}

function handleMapClick(event) {
  if (!mapState.AMap) {
    return;
  }
  const lnglat = event.lnglat;
  if (!lnglat) {
    return;
  }
  if (appState.interactionMode === "setRunway") {
    const point = pointFromLngLat(lnglat);
    if (!appState.pendingRunwayStart) {
      appState.pendingRunwayStart = point;
      setInteractionStatus("当前模式：设置跑道，请再点击一次地图确定跑道终点。");
      return;
    }
    syncLandingFromRunway(appState.fieldProfile, appState.pendingRunwayStart, point);
    activateInteractionMode("idle", "空闲");
    renderAll({ fitView: false, populateForm: true });
    return;
  }
  if (appState.interactionMode === "setDropPoint") {
    const point = pointFromLngLat(lnglat);
    appState.fieldProfile.attack_run.fallback_drop_point = { lat: point.lat, lon: point.lon };
    activateInteractionMode("idle", "空闲");
    renderAll({ fitView: false, populateForm: true });
    setInteractionStatus(`已设置降级投弹点 (${point.lat.toFixed(6)}, ${point.lon.toFixed(6)})`);
    return;
  }
}

function ensureMarker(name, position, label) {
  if (!mapState.map || !mapState.AMap || !position) {
    return null;
  }
  const existing = mapState.overlays[name];
  if (existing) {
    existing.setPosition(position);
    existing.setTitle?.(label);
    existing.setLabel?.({ direction: "top", content: label });
    return existing;
  }
  const marker = new mapState.AMap.Marker({
    position,
    draggable: true,
    title: label,
    label: {
      direction: "top",
      content: label,
    },
  });
  marker.setMap(mapState.map);
  marker.on("dragging", () => syncMarkersFromMap(name));
  marker.on("dragend", () => syncMarkersFromMap(name));
  mapState.overlays[name] = marker;
  return marker;
}

function syncMarkersFromMap(name) {
  const marker = mapState.overlays[name];
  if (!marker) {
    return;
  }
  const position = marker.getPosition();
  if (!position) {
    return;
  }
  if (name === "runwayStartMarker" || name === "runwayEndMarker") {
    const fallback = deriveRunwayEndpoints(appState.fieldProfile);
    const runwayStart =
      name === "runwayStartMarker"
        ? pointFromLngLat(position)
        : readMarkerPoint("runwayStartMarker") ?? fallback.start;
    const runwayEnd =
      name === "runwayEndMarker"
        ? pointFromLngLat(position)
        : readMarkerPoint("runwayEndMarker") ?? fallback.end;
    syncLandingFromRunway(appState.fieldProfile, runwayStart, runwayEnd);
  }
  if (name === "dropPointMarker") {
    const point = pointFromLngLat(position);
    appState.fieldProfile.attack_run.fallback_drop_point = { lat: point.lat, lon: point.lon };
  }
  renderAll({ fitView: false, populateForm: true });
}

function readMarkerPoint(name) {
  const marker = mapState.overlays[name];
  const position = marker?.getPosition?.();
  if (!position) {
    return null;
  }
  return pointFromLngLat(position);
}

function removeOverlay(name) {
  const overlay = mapState.overlays[name];
  if (!overlay || !mapState.map) {
    mapState.overlays[name] = null;
    return;
  }
  mapState.map.remove(overlay);
  mapState.overlays[name] = null;
}

function clearBoundaryVertexMarkers() {
  if (!mapState.map || !Array.isArray(mapState.overlays.boundaryVertexMarkers)) {
    mapState.overlays.boundaryVertexMarkers = [];
    return;
  }
  for (const marker of mapState.overlays.boundaryVertexMarkers) {
    mapState.map.remove(marker);
  }
  mapState.overlays.boundaryVertexMarkers = [];
}

function createBoundaryVertexHandleContent() {
  const handle = document.createElement("div");
  handle.style.width = "12px";
  handle.style.height = "12px";
  handle.style.borderRadius = "999px";
  handle.style.background = "#ffffff";
  handle.style.border = "3px solid #2563eb";
  handle.style.boxShadow = "0 1px 4px rgba(15, 23, 42, 0.35)";
  return handle;
}

function syncBoundaryFromVertexMarkers({ populateForm = true } = {}) {
  const polygon = mapState.overlays.boundaryPolygon;
  const markers = mapState.overlays.boundaryVertexMarkers;
  if (!polygon || !Array.isArray(markers) || markers.length === 0) {
    appState.fieldProfile.boundary.polygon = [];
    renderAll({ fitView: false, populateForm });
    return;
  }

  const points = markers.map((marker) => {
    const position = marker.getPosition();
    return {
      lat: position.getLat(),
      lon: position.getLng(),
    };
  });

  appState.fieldProfile.boundary.polygon = points;
  polygon.setPath(points.map((point) => [point.lon, point.lat]));
  appState.validation = validateFieldProfile(appState.fieldProfile);
  if (populateForm) {
    populateFormFromState();
  }
  renderValidation();
  renderLanding();
  renderScanPreview();
}

function addBoundaryVertexAtPoint(point) {
  appState.fieldProfile.boundary.polygon = insertVertexIntoPolygon(
    appState.fieldProfile.boundary.polygon,
    point,
  );
  renderAll({ fitView: false, populateForm: true });
}

function removeBoundaryVertex(index) {
  const points = stripClosedPolygon(appState.fieldProfile.boundary.polygon);
  if (points.length <= 3) {
    setInteractionStatus("当前模式：编辑飞行区域，至少保留 3 个锚点。");
    return;
  }
  appState.fieldProfile.boundary.polygon = [
    ...points.slice(0, index),
    ...points.slice(index + 1),
  ];
  renderAll({ fitView: false, populateForm: true });
}

function applyBoundaryPolygon(points, { fitView = false, openEditor = false } = {}) {
  appState.fieldProfile.boundary.polygon = points;
  renderAll({ fitView, populateForm: true });
  if (openEditor && mapState.overlays.boundaryPolygon) {
    setInteractionMode("editBoundary", "编辑飞行区域");
    renderAll({ fitView: false, populateForm: true });
    return;
  }
  activateInteractionMode("idle", "空闲");
}

function renderBoundary() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const points = stripClosedPolygon(appState.fieldProfile.boundary.polygon);
  if (points.length === 0) {
    closePolygonEditor();
    removeOverlay("boundaryPolygon");
    return;
  }
  const path = points.map((point) => [point.lon, point.lat]);
  if (!mapState.overlays.boundaryPolygon) {
    mapState.overlays.boundaryPolygon = new mapState.AMap.Polygon({
      path,
      strokeColor: "#2563eb",
      strokeWeight: 3,
      strokeOpacity: 0.95,
      fillColor: "#60a5fa",
      fillOpacity: 0.22,
      bubble: true,
    });
    mapState.overlays.boundaryPolygon.setMap(mapState.map);
    mapState.boundaryClickHandler = (event) => {
      if (isMapPlacementMode()) {
        handleMapClick(event);
        return;
      }
      if (isBoundaryEditingActive()) {
        const lnglat = event?.lnglat;
        if (lnglat) {
          addBoundaryVertexAtPoint(pointFromLngLat(lnglat));
          setInteractionStatus("当前模式：编辑飞行区域，已新增锚点。");
        }
        return;
      }
      setInteractionMode("editBoundary", "编辑飞行区域");
      renderAll({ fitView: false, populateForm: true });
    };
    mapState.boundaryClickAttached = false;
    syncBoundaryOverlayInteractivity();
  } else {
    mapState.overlays.boundaryPolygon.setPath(path);
  }
  if (isBoundaryEditingActive()) {
    clearBoundaryVertexMarkers();
    mapState.overlays.boundaryVertexMarkers = points.map((point, index) => {
      const marker = new mapState.AMap.Marker({
        position: [point.lon, point.lat],
        draggable: true,
        content: createBoundaryVertexHandleContent(),
        offset: new mapState.AMap.Pixel(-6, -6),
        zIndex: 200,
        bubble: false,
      });
      marker.setMap(mapState.map);
      marker.on("dragging", () => {
        syncBoundaryFromVertexMarkers({ populateForm: true });
      });
      marker.on("dragend", () => {
        syncBoundaryFromVertexMarkers({ populateForm: true });
      });
      marker.on("click", (event) => {
        event?.stopPropagation?.();
      });
      marker.on("dblclick", (event) => {
        event?.stopPropagation?.();
        removeBoundaryVertex(index);
      });
      return marker;
    });
  } else {
    clearBoundaryVertexMarkers();
  }
  syncBoundaryOverlayInteractivity();
}

function renderLanding() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const runway = deriveRunwayEndpoints(appState.fieldProfile);
  const runwayStart = runway.start;
  const runwayEnd = runway.end;
  ensureMarker("runwayStartMarker", [runwayStart.lon, runwayStart.lat], "跑道起点 / 接地点");
  ensureMarker("runwayEndMarker", [runwayEnd.lon, runwayEnd.lat], "跑道终点");

  const runwayPath = [
    [runwayStart.lon, runwayStart.lat],
    [runwayEnd.lon, runwayEnd.lat],
  ];
  if (!mapState.overlays.runwayCenterline) {
    mapState.overlays.runwayCenterline = new mapState.AMap.Polyline({
      path: runwayPath,
      strokeColor: "#dc2626",
      strokeWeight: 4,
      strokeOpacity: 0.95,
    });
    mapState.overlays.runwayCenterline.setMap(mapState.map);
  } else {
    mapState.overlays.runwayCenterline.setPath(runwayPath);
  }

  const approach = appState.validation.derivedApproach;
  if (!approach) {
    removeOverlay("landingApproachLine");
    removeOverlay("landingApproachMarker");
    return;
  }

  ensureMarker("landingApproachMarker", [approach.lon, approach.lat], "进近点").setDraggable?.(false);
  const approachPath = [
    [approach.lon, approach.lat],
    [runwayStart.lon, runwayStart.lat],
  ];
  if (!mapState.overlays.landingApproachLine) {
    mapState.overlays.landingApproachLine = new mapState.AMap.Polyline({
      path: approachPath,
      strokeColor: "#7c3aed",
      strokeWeight: 3,
      strokeOpacity: 0.95,
      strokeStyle: "dashed",
    });
    mapState.overlays.landingApproachLine.setMap(mapState.map);
  } else {
    mapState.overlays.landingApproachLine.setPath(approachPath);
  }
}

function renderScanPreview() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const preview = appState.validation.scanPreview;
  if (!preview.length) {
    removeOverlay("scanPolyline");
    return;
  }
  const path = preview.map((point) => [point.lon, point.lat]);
  if (!mapState.overlays.scanPolyline) {
    mapState.overlays.scanPolyline = new mapState.AMap.Polyline({
      path,
      strokeColor: "#059669",
      strokeWeight: 3,
      strokeOpacity: 0.95,
      showDir: true,
    });
    mapState.overlays.scanPolyline.setMap(mapState.map);
  } else {
    mapState.overlays.scanPolyline.setPath(path);
  }
}

function renderAttackRun() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const dropPoint = appState.fieldProfile.attack_run.fallback_drop_point;
  if (!dropPoint || !Number.isFinite(dropPoint.lat) || !Number.isFinite(dropPoint.lon)) {
    removeOverlay("dropPointMarker");
    removeOverlay("attackApproachLine");
    removeOverlay("attackExitLine");
    return;
  }
  ensureMarker("dropPointMarker", [dropPoint.lon, dropPoint.lat], "降级投弹点 (预览)");

  const approach = appState.validation.derivedApproach;
  const landing = appState.fieldProfile.landing;
  const attackCfg = appState.fieldProfile.attack_run;

  let heading;
  let distanceToApproach;
  if (approach) {
    distanceToApproach = haversineDistance(dropPoint.lat, dropPoint.lon, approach.lat, approach.lon);
  }
  if (approach && distanceToApproach > 30) {
    heading = bearingBetweenPoints(dropPoint, approach);
  } else {
    heading = (landing.heading_deg + 180) % 360;
  }

  const approachDist = attackCfg.approach_distance_m;
  let exitDist = attackCfg.exit_distance_m;
  if (approach && distanceToApproach !== undefined) {
    const minHandoff = Math.max(30, Math.min(approachDist, landing.runway_length_m));
    const maxSafeExit = Math.max(0, distanceToApproach - minHandoff);
    exitDist = Math.min(exitDist, maxSafeExit);
  }

  const approachPoint = destinationPoint(dropPoint.lat, dropPoint.lon, (heading + 180) % 360, approachDist);
  const exitPoint = destinationPoint(dropPoint.lat, dropPoint.lon, heading, exitDist);

  const approachPath = [
    [approachPoint.lon, approachPoint.lat],
    [dropPoint.lon, dropPoint.lat],
  ];
  if (!mapState.overlays.attackApproachLine) {
    mapState.overlays.attackApproachLine = new mapState.AMap.Polyline({
      path: approachPath,
      strokeColor: "#ea580c",
      strokeWeight: 3,
      strokeOpacity: 0.9,
      strokeStyle: "dashed",
    });
    mapState.overlays.attackApproachLine.setMap(mapState.map);
  } else {
    mapState.overlays.attackApproachLine.setPath(approachPath);
  }

  const exitPath = [
    [dropPoint.lon, dropPoint.lat],
    [exitPoint.lon, exitPoint.lat],
  ];
  if (!mapState.overlays.attackExitLine) {
    mapState.overlays.attackExitLine = new mapState.AMap.Polyline({
      path: exitPath,
      strokeColor: "#a855f7",
      strokeWeight: 3,
      strokeOpacity: 0.9,
      strokeStyle: "dashed",
    });
    mapState.overlays.attackExitLine.setMap(mapState.map);
  } else {
    mapState.overlays.attackExitLine.setPath(exitPath);
  }
}

function renderTakeoffPath() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const takeoff = appState.validation.derivedTakeoff;
  if (!takeoff) {
    removeOverlay("takeoffPathLine");
    return;
  }
  const path = [
    [takeoff.start_lon, takeoff.start_lat],
    [takeoff.climbout_lon, takeoff.climbout_lat],
  ];
  if (!mapState.overlays.takeoffPathLine) {
    mapState.overlays.takeoffPathLine = new mapState.AMap.Polyline({
      path,
      strokeColor: "#f59e0b",
      strokeWeight: 3,
      strokeOpacity: 0.9,
    });
    mapState.overlays.takeoffPathLine.setMap(mapState.map);
  } else {
    mapState.overlays.takeoffPathLine.setPath(path);
  }
}

function renderMissionChain() {
  if (!mapState.map || !mapState.AMap) {
    return;
  }
  const takeoff = appState.validation.derivedTakeoff;
  const scan = appState.validation.scanPreview;
  const approach = appState.validation.derivedApproach;

  const points = [];
  if (takeoff) {
    points.push([takeoff.climbout_lon, takeoff.climbout_lat]);
  }
  if (scan.length > 0) {
    points.push([scan[0].lon, scan[0].lat]);
    points.push([scan[scan.length - 1].lon, scan[scan.length - 1].lat]);
  }
  if (approach) {
    points.push([approach.lon, approach.lat]);
  }

  if (points.length < 2) {
    removeOverlay("missionChainLine");
    return;
  }
  if (!mapState.overlays.missionChainLine) {
    mapState.overlays.missionChainLine = new mapState.AMap.Polyline({
      path: points,
      strokeColor: "#94a3b8",
      strokeWeight: 2,
      strokeOpacity: 0.7,
      strokeStyle: "dashed",
    });
    mapState.overlays.missionChainLine.setMap(mapState.map);
  } else {
    mapState.overlays.missionChainLine.setPath(points);
  }
}

function renderOverlays() {
  if (!appState.mapReady) {
    return;
  }
  renderBoundary();
  renderLanding();
  renderScanPreview();
  renderAttackRun();
  renderTakeoffPath();
  renderMissionChain();
  renderReplayOverlays();
}

function renderValidation() {
  dom.blockingErrors.replaceChildren();
  dom.advisoryWarnings.replaceChildren();
  for (const message of appState.validation.blocking) {
    const item = document.createElement("li");
    item.textContent = message;
    dom.blockingErrors.append(item);
  }
  for (const message of appState.validation.advisory) {
    const item = document.createElement("li");
    item.textContent = message;
    dom.advisoryWarnings.append(item);
  }
  dom.exportButton.disabled = appState.validation.blocking.length > 0;
  if (appState.validation.derivedApproach) {
    const { lat, lon, alt_m, distance_m } = appState.validation.derivedApproach;
    const takeoff = appState.validation.derivedTakeoff;
    const previewLines = [
      "landing_approach",
      `lat=${lat.toFixed(6)}`,
      `lon=${lon.toFixed(6)}`,
      `alt_m=${alt_m.toFixed(1)}`,
      `distance_m=${distance_m.toFixed(1)}`,
      "",
      "scan_preview",
      `waypoints=${appState.validation.scanPreview.length}`,
    ];
    if (takeoff) {
      previewLines.push(
        "",
        "takeoff_preview",
        `heading_deg=${takeoff.heading_deg.toFixed(1)}`,
        `start_lat=${takeoff.start_lat.toFixed(6)}`,
        `start_lon=${takeoff.start_lon.toFixed(6)}`,
        `climbout_lat=${takeoff.climbout_lat.toFixed(6)}`,
        `climbout_lon=${takeoff.climbout_lon.toFixed(6)}`,
        `climb_angle_deg=${takeoff.climb_angle_deg.toFixed(1)}`,
      );
    }
    dom.landingApproachSummary.textContent = previewLines.join("\n");
  } else {
    dom.landingApproachSummary.textContent = "尚未计算或存在 blocking 校验错误。";
  }
}

function populateFormFromState() {
  for (const input of dom.fieldForm.querySelectorAll("[data-path]")) {
    const path = input.dataset.path;
    const type = input.dataset.type;
    const value = getByPath(appState.fieldProfile, path);
    if (type === "boolean") {
      input.checked = Boolean(value);
    } else if (type === "number") {
      input.value = Number.isFinite(value) ? String(value) : "";
    } else {
      input.value = value ?? "";
    }
  }
  dom.boundaryPolygonText.value = formatBoundaryPolygon(appState.fieldProfile.boundary.polygon);
  const density = scanSpacingToDensity(appState.fieldProfile.scan.spacing_m);
  dom.scanDensityInput.value = String(density);
  dom.scanDensityLabel.textContent = `${density}%`;
}

function renderAll({ fitView = false, populateForm = false } = {}) {
  appState.validation = validateFieldProfile(appState.fieldProfile);
  if (populateForm) {
    populateFormFromState();
  }
  renderValidation();
  renderOverlays();
  if (fitView) {
    fitMapToOverlays();
  }
}

function resetFieldProfile() {
  appState.fieldProfile = createDefaultFieldProfile();
  appState.pendingRunwayStart = null;
  renderAll({ fitView: true, populateForm: true });
}

function parseFieldInputValue(input) {
  const type = input.dataset.type;
  if (type === "boolean") {
    return input.checked;
  }
  if (type === "number") {
    const numeric = Number(input.value);
    return Number.isFinite(numeric) ? numeric : 0;
  }
  return input.value;
}

function downloadFile(filename, contents) {
  const blob = new Blob([contents], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function handleImport(event) {
  const [file] = event.target.files ?? [];
  if (!file) {
    return;
  }
  try {
    const rawText = await file.text();
    const parsed = JSON.parse(rawText);
    appState.fieldProfile = importFieldProfile(parsed);
    appState.pendingRunwayStart = null;
    renderAll({ fitView: true, populateForm: true });
    setInteractionStatus(`当前模式：已导入 ${file.name}`);
  } catch (error) {
    setInteractionStatus(`导入失败：${error instanceof Error ? error.message : String(error)}`);
  } finally {
    event.target.value = "";
  }
}

async function handleReplayImport(event) {
  const [file] = event.target.files ?? [];
  if (!file) {
    return;
  }
  try {
    const rawText = await file.text();
    loadReplayData(parseFlightLogCsv(rawText), file.name);
    setInteractionStatus(`当前模式：已加载回放日志 ${file.name}`);
  } catch (error) {
    stopReplayPlayback();
    appState.replay.data = null;
    appState.replay.loadedFileName = "";
    renderReplayOverlays();
    setInteractionStatus(`回放日志导入失败：${error instanceof Error ? error.message : String(error)}`);
  } finally {
    event.target.value = "";
  }
}

function handleExport() {
  renderAll({ fitView: false, populateForm: false });
  if (appState.validation.blocking.length > 0) {
    setInteractionStatus("存在 blocking 错误，无法导出。请先修复校验问题。");
    return;
  }
  const exported = exportFieldProfile(appState.fieldProfile);
  downloadFile("field.json", `${JSON.stringify(exported, null, 2)}\n`);
  setInteractionStatus("已生成 field.json 下载。导出坐标为 WGS84。");
}

function handleBoundaryTextChange() {
  try {
    appState.fieldProfile.boundary.polygon = parseBoundaryText(dom.boundaryPolygonText.value);
    renderAll({ fitView: false, populateForm: false });
    setInteractionStatus("已从文本区域更新飞行区域。");
  } catch (error) {
    setInteractionStatus(`Boundary 解析失败：${error instanceof Error ? error.message : String(error)}`);
  }
}

function startBoundaryDrawing() {
  const mouseTool = ensureMouseTool();
  if (!mouseTool) {
    setInteractionStatus("地图尚未初始化，无法框选飞行区域。");
    return;
  }
  closeActiveMapTools();
  rebuildMouseTool();
  const sessionId = beginBoundaryDrawSession(mapState.interactionSession);
  mapState.drawHandler = (event) => {
    if (!completeBoundaryDrawSession(mapState.interactionSession, sessionId)) {
      return;
    }
    const temporaryOverlay = event.obj;
    finalizeBoundaryDrawing();
    const bounds = event.obj?.getBounds?.();
    if (temporaryOverlay) {
      mapState.map?.remove?.(temporaryOverlay);
    }
    if (!bounds) {
      activateInteractionMode("idle", "空闲");
      return;
    }
    const polygon = rectangleBoundsToPolygon(bounds);
    applyBoundaryPolygon(polygon, { fitView: true, openEditor: true });
  };
  mapState.mouseTool.on("draw", mapState.drawHandler);
  mapState.mouseTool.rectangle({
    strokeColor: "#2563eb",
    strokeWeight: 3,
    strokeOpacity: 0.95,
    fillColor: "#60a5fa",
    fillOpacity: 0.22,
  });
  setInteractionMode("drawBoundary", "框选飞行区域（拖拽完成矩形，按 Esc 取消）");
}

function handleBoundaryDrawCancel() {
  if (appState.interactionMode !== "drawBoundary") {
    return;
  }
  finalizeBoundaryDrawing();
  closePolygonEditor();
  setInteractionMode("idle", "空闲");
}

function handleGlobalKeydown(event) {
  if (event.key !== "Escape") {
    return;
  }
  if (appState.interactionMode === "drawBoundary") {
    event.preventDefault();
    handleBoundaryDrawCancel();
  }
}

function openBoundaryEditor() {
  if (!mapState.overlays.boundaryPolygon) {
    setInteractionStatus("当前没有飞行区域可编辑。");
    return;
  }
  closeActiveMapTools();
  setInteractionMode("editBoundary", "编辑飞行区域");
  renderAll({ fitView: false, populateForm: true });
}

function clearSpatialOverlays() {
  closeActiveMapTools();
  const defaults = createDefaultFieldProfile();
  appState.fieldProfile.boundary.polygon = [];
  appState.fieldProfile.landing.touchdown_point.lat = defaults.landing.touchdown_point.lat;
  appState.fieldProfile.landing.touchdown_point.lon = defaults.landing.touchdown_point.lon;
  appState.fieldProfile.landing.heading_deg = defaults.landing.heading_deg;
  appState.fieldProfile.landing.runway_length_m = defaults.landing.runway_length_m;
  appState.fieldProfile.attack_run.fallback_drop_point = null;
  appState.pendingRunwayStart = null;
  renderAll({ fitView: false, populateForm: true });
  setInteractionStatus("已清空飞行区域，并将跑道和投弹点重置到默认位置。");
}

function setBasemapMode(mode) {
  if (!mode || appState.basemapMode === mode) {
    updateBasemapButtons();
    return;
  }
  appState.basemapMode = mode;
  updateBasemapButtons();
  if (!appState.credentials.key || !appState.credentials.securityJsCode) {
    setMapStatus("已切换底图模式。填写凭据后初始化地图即可生效。", false);
    return;
  }
  initializeMap();
}

function wireEventHandlers() {
  dom.credentialsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const credentials = {
      key: dom.amapKeyInput.value.trim(),
      securityJsCode: dom.amapSecurityCodeInput.value.trim(),
    };
    saveCredentials(credentials);
    await initializeMap();
  });

  dom.retryMapButton.addEventListener("click", async () => {
    saveCredentials({
      key: dom.amapKeyInput.value.trim(),
      securityJsCode: dom.amapSecurityCodeInput.value.trim(),
    });
    await initializeMap();
  });

  dom.clearCredentialsButton.addEventListener("click", () => {
    clearCredentials();
    destroyMap();
    setMapStatus("已清除凭据。请重新填写后初始化地图。", false);
  });

  dom.newFieldButton.addEventListener("click", () => {
    resetFieldProfile();
    setInteractionStatus("当前模式：已重置为新建 field profile。");
  });

  dom.importFileInput.addEventListener("change", handleImport);
  dom.replayFileInput.addEventListener("change", handleReplayImport);
  dom.exportButton.addEventListener("click", handleExport);
  dom.boundaryPolygonText.addEventListener("change", handleBoundaryTextChange);
  dom.drawBoundaryButton.addEventListener("click", startBoundaryDrawing);
  dom.editBoundaryButton.addEventListener("click", openBoundaryEditor);
  globalThis.addEventListener("keydown", handleGlobalKeydown);
  dom.setRunwayButton.addEventListener("click", () => {
    appState.pendingRunwayStart = null;
    activateInteractionMode("setRunway", "设置跑道，请点击地图确定起点和终点", { preserveRunwayStart: true });
  });
  dom.setDropPointButton.addEventListener("click", () => {
    activateInteractionMode("setDropPoint", "设置降级投弹点，请点击地图确定位置");
  });
  dom.replayPlayButton.addEventListener("click", startReplayPlayback);
  dom.replayPauseButton.addEventListener("click", stopReplayPlayback);
  dom.replayFitButton.addEventListener("click", fitMapToReplay);
  dom.replaySpeedSelect.addEventListener("change", () => {
    appState.replay.speed = Math.max(0.25, Number(dom.replaySpeedSelect.value) || 1);
  });
  dom.replayProgressInput.addEventListener("input", () => {
    if (!hasReplayData()) {
      return;
    }
    setReplayIndex(replayIndexFromProgress(Number(dom.replayProgressInput.value), appState.replay.data.sampleCount));
  });
  dom.fitViewButton.addEventListener("click", fitMapToOverlays);
  dom.clearOverlaysButton.addEventListener("click", clearSpatialOverlays);
  dom.scanDensityInput.addEventListener("input", () => {
    const density = Number(dom.scanDensityInput.value);
    appState.fieldProfile.scan.spacing_m = densityToScanSpacing(density);
    dom.scanDensityLabel.textContent = `${density}%`;
    renderAll({ fitView: false, populateForm: true });
  });

  for (const button of dom.basemapButtons) {
    button.addEventListener("click", () => {
      setBasemapMode(button.dataset.basemapMode);
    });
  }

  for (const input of dom.fieldForm.querySelectorAll("[data-path]")) {
    if (input.readOnly) {
      continue;
    }
    input.addEventListener("input", () => {
      const path = input.dataset.path;
      setByPath(appState.fieldProfile, path, parseFieldInputValue(input));
      renderAll({ fitView: false, populateForm: false });
    });
  }
}

async function boot() {
  dom.amapKeyInput.value = appState.credentials.key;
  dom.amapSecurityCodeInput.value = appState.credentials.securityJsCode;
  dom.replaySpeedSelect.value = String(appState.replay.speed);
  populateFormFromState();
  renderAll({ fitView: false, populateForm: false });
  renderReplayStatus();
  updateBasemapButtons();
  wireEventHandlers();
  if (appState.credentials.key && appState.credentials.securityJsCode) {
    await initializeMap();
  } else {
    setMapStatus("尚未配置 AMap 凭据。请输入后初始化地图。", false);
  }
}

boot();
