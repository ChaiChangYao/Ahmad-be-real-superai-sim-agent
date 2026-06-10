import { create } from "zustand";
import type { JointGuess } from "./jointGuesses";
import type { GenesisCatalog, ManifestState, RunResult, TestCatalogItem } from "./types";

export type ViewportMeshMode = "visual" | "collision" | "both";

type SimStore = {
  selectedProjectId: string;
  selectedPartId: string | null;
  selectedScenarioId: string;
  manifest: ManifestState | null;
  manifestBaseline: string;
  dirty: boolean;
  manifestStatus: "saved" | "unsaved" | "validation_error";
  validationErrors: string[];
  lastSavedAt: string | null;
  lastRunManifestVersion: number | null;
  logs: string[];
  metrics: Record<string, unknown>;
  runTimeseries: Array<Record<string, unknown>>;
  lastRun: RunResult | null;
  interactiveSessionId: string | null;
  currentCommand: string;
  setupError: string | null;
  selectedTestId: string | null;
  testsCatalog: TestCatalogItem[];
  availableTests: TestCatalogItem[];
  genesisCatalog: GenesisCatalog | null;
  controlMode: "remote_control" | "built_in_behavior" | "control_script" | "joint_command_table" | "trajectory_test";
  viewMode: "perspective" | "visual" | "debug";
  showPayloadPreview: boolean;
  showSkeleton: boolean;
  isSimulationRunning: boolean;
  viewportResizeKey: number;
  playbackFrameIndex: number;
  playbackPlaying: boolean;
  viewportMeshMode: ViewportMeshMode;
  showComOverlay: boolean;
  showJointAxesOverlay: boolean;
  showSensorRaysOverlay: boolean;
  showWireRoutesOverlay: boolean;
  pendingJointGuesses: JointGuess[];
  setPlaybackFrameIndex: (index: number) => void;
  setPlaybackPlaying: (playing: boolean) => void;
  setViewportMeshMode: (mode: ViewportMeshMode) => void;
  setShowComOverlay: (show: boolean) => void;
  setShowJointAxesOverlay: (show: boolean) => void;
  setShowSensorRaysOverlay: (show: boolean) => void;
  setShowWireRoutesOverlay: (show: boolean) => void;
  setPendingJointGuesses: (guesses: JointGuess[]) => void;
  removePendingJointGuess: (guessId: string) => void;
  setViewMode: (mode: SimStore["viewMode"]) => void;
  setShowPayloadPreview: (show: boolean) => void;
  setShowSkeleton: (show: boolean) => void;
  setIsSimulationRunning: (running: boolean) => void;
  bumpViewportResize: () => void;
  setSelectedTestId: (testId: string | null) => void;
  setTestsCatalog: (tests: TestCatalogItem[]) => void;
  setAvailableTests: (tests: TestCatalogItem[]) => void;
  setGenesisCatalog: (catalog: GenesisCatalog | null) => void;
  setControlMode: (mode: SimStore["controlMode"]) => void;
  setSelectedProjectId: (projectId: string) => void;
  setSelectedPartId: (partId: string | null) => void;
  setSelectedScenarioId: (scenarioId: string) => void;
  setManifest: (manifest: ManifestState) => void;
  patchManifest: (updater: (manifest: ManifestState) => ManifestState) => void;
  markSaved: (manifest: ManifestState) => void;
  setValidationErrors: (errors: string[]) => void;
  addLog: (line: string) => void;
  setLogs: (lines: string[]) => void;
  setMetrics: (metrics: Record<string, unknown>) => void;
  setRunResult: (run: RunResult) => void;
  setRunTimeseries: (series: Array<Record<string, unknown>>) => void;
  setInteractiveSessionId: (sessionId: string | null) => void;
  setCurrentCommand: (command: string) => void;
  setSetupError: (error: string | null) => void;
};

export const useSimStore = create<SimStore>((set) => ({
  selectedProjectId: "default-robot-dog",
  selectedPartId: null,
  selectedScenarioId: "stand_balance",
  manifest: null,
  manifestBaseline: "",
  dirty: false,
  manifestStatus: "saved",
  validationErrors: [],
  lastSavedAt: null,
  lastRunManifestVersion: null,
  logs: [],
  metrics: {},
  runTimeseries: [],
  lastRun: null,
  interactiveSessionId: null,
  currentCommand: "stand",
  setupError: null,
  selectedTestId: null,
  testsCatalog: [],
  availableTests: [],
  genesisCatalog: null,
  controlMode: "remote_control",
  viewMode: "perspective",
  showPayloadPreview: false,
  showSkeleton: false,
  isSimulationRunning: false,
  viewportResizeKey: 0,
  playbackFrameIndex: 0,
  playbackPlaying: false,
  viewportMeshMode: "visual",
  showComOverlay: false,
  showJointAxesOverlay: false,
  showSensorRaysOverlay: false,
  showWireRoutesOverlay: true,
  pendingJointGuesses: [],
  setPlaybackFrameIndex: (playbackFrameIndex) => set({ playbackFrameIndex }),
  setPlaybackPlaying: (playbackPlaying) => set({ playbackPlaying }),
  setViewportMeshMode: (viewportMeshMode) => set({ viewportMeshMode }),
  setShowComOverlay: (showComOverlay) => set({ showComOverlay }),
  setShowJointAxesOverlay: (showJointAxesOverlay) => set({ showJointAxesOverlay }),
  setShowSensorRaysOverlay: (showSensorRaysOverlay) => set({ showSensorRaysOverlay }),
  setShowWireRoutesOverlay: (showWireRoutesOverlay) => set({ showWireRoutesOverlay }),
  setPendingJointGuesses: (pendingJointGuesses) => set({ pendingJointGuesses }),
  removePendingJointGuess: (guessId) =>
    set((state) => ({ pendingJointGuesses: state.pendingJointGuesses.filter((g) => g.id !== guessId) })),
  setSelectedProjectId: (selectedProjectId) => set({ selectedProjectId }),
  setSelectedPartId: (selectedPartId) => set({ selectedPartId }),
  setSelectedScenarioId: (selectedScenarioId) => set({ selectedScenarioId }),
  setManifest: (manifest) =>
    set({
      manifest,
      manifestBaseline: JSON.stringify(manifest),
      dirty: false,
      manifestStatus: "saved",
      validationErrors: [],
      lastSavedAt: manifest.updated_at ?? null,
      controlMode: (manifest.controls?.mode as SimStore["controlMode"]) ?? "remote_control"
    }),
  patchManifest: (updater) =>
    set((state) => {
      if (!state.manifest) return state;
      const nextManifest = updater(state.manifest);
      const baseline = state.manifestBaseline || JSON.stringify(state.manifest);
      const dirty = JSON.stringify(nextManifest) !== baseline;
      return { manifest: nextManifest, dirty, manifestStatus: dirty ? "unsaved" : "saved" };
    }),
  markSaved: (manifest) =>
    set({
      manifest,
      manifestBaseline: JSON.stringify(manifest),
      dirty: false,
      manifestStatus: "saved",
      validationErrors: [],
      lastSavedAt: manifest.updated_at ?? new Date().toISOString()
    }),
  setValidationErrors: (validationErrors) =>
    set({
      validationErrors,
      manifestStatus: validationErrors.length > 0 ? "validation_error" : "saved"
    }),
  addLog: (line) => set((state) => ({ logs: [...state.logs, line] })),
  setLogs: (logs) => set({ logs }),
  setMetrics: (metrics) => set({ metrics }),
  setRunResult: (lastRun) =>
    set({
      lastRun,
      metrics: lastRun.metrics,
      logs: lastRun.logs,
      runTimeseries: lastRun.state_timeseries,
      lastRunManifestVersion: lastRun.manifest_version_used,
      playbackFrameIndex: 0,
      playbackPlaying: false
    }),
  setRunTimeseries: (runTimeseries) => set({ runTimeseries }),
  setInteractiveSessionId: (interactiveSessionId) => set({ interactiveSessionId }),
  setCurrentCommand: (currentCommand) => set({ currentCommand }),
  setSetupError: (setupError) => set({ setupError }),
  setSelectedTestId: (selectedTestId) => set({ selectedTestId }),
  setTestsCatalog: (testsCatalog) => set({ testsCatalog }),
  setAvailableTests: (availableTests) => set({ availableTests }),
  setGenesisCatalog: (genesisCatalog) => set({ genesisCatalog }),
  setControlMode: (controlMode) => set({ controlMode }),
  setViewMode: (viewMode) => set({ viewMode }),
  setShowPayloadPreview: (showPayloadPreview) => set({ showPayloadPreview }),
  setShowSkeleton: (showSkeleton) => set({ showSkeleton }),
  setIsSimulationRunning: (isSimulationRunning) => set({ isSimulationRunning }),
  bumpViewportResize: () => set((state) => ({ viewportResizeKey: state.viewportResizeKey + 1 }))
}));
