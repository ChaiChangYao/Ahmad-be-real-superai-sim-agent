import { create } from "zustand";
import type { AgentMessage, AgenticProjectState, ProjectInspectionReport, SimulationPlan } from "./types";

type AssistantStore = {
  projectId: string | null;
  projectName: string;
  messages: AgentMessage[];
  inspection: ProjectInspectionReport | null;
  plan: SimulationPlan | null;
  persistedState: AgenticProjectState | null;
  loading: boolean;
  selectedTestId: string | null;
  setProjectId: (id: string | null) => void;
  setProjectName: (name: string) => void;
  setMessages: (msgs: AgentMessage[] | ((prev: AgentMessage[]) => AgentMessage[])) => void;
  appendMessage: (msg: AgentMessage) => void;
  updateMessageById: (messageId: string, updater: (msg: AgentMessage) => AgentMessage) => void;
  setInspection: (i: ProjectInspectionReport | null) => void;
  setPlan: (p: SimulationPlan | null) => void;
  setPersistedState: (s: AgenticProjectState | null) => void;
  setLoading: (v: boolean) => void;
  setSelectedTestId: (id: string | null) => void;
  resetForProject: (projectId: string | null) => void;
};

export const useAssistantStore = create<AssistantStore>((set) => ({
  projectId: null,
  projectName: "My Buildables Robot",
  messages: [],
  inspection: null,
  plan: null,
  persistedState: null,
  loading: false,
  selectedTestId: null,
  setProjectId: (id) => set({ projectId: id }),
  setProjectName: (name) => set({ projectName: name }),
  setMessages: (msgs) =>
    set((s) => ({
      messages: typeof msgs === "function" ? msgs(s.messages) : msgs,
    })),
  appendMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  updateMessageById: (messageId, updater) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === messageId ? updater(m) : m)),
    })),
  setInspection: (inspection) => set({ inspection }),
  setPlan: (plan) => set({ plan }),
  setPersistedState: (persistedState) => set({ persistedState }),
  setLoading: (loading) => set({ loading }),
  setSelectedTestId: (selectedTestId) => set({ selectedTestId }),
  resetForProject: (projectId) =>
    set({
      projectId,
      messages: [],
      inspection: null,
      plan: null,
      persistedState: null,
      selectedTestId: null,
    }),
}));
