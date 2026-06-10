import type { AgentMessage } from "@/lib/agentic/types";
import { MissingMeshTable } from "./MissingMeshTable";
import { MissingMetadataTable } from "./MissingMetadataTable";
import { EngineeringReportCard } from "./EngineeringReportCard";
import { RecoveryActions } from "./RecoveryActions";
import { RunExecutionCard } from "./RunExecutionCard";
import { SimulationPlanCard } from "./SimulationPlanCard";
import { TestRecommendationCards } from "./TestRecommendationCards";
import { accent } from "../buildablesTheme";
import { AgentTimelineCard } from "./AgentTimelineCard";

type Props = {
  message: AgentMessage;
  selectedTestId?: string | null;
  onAction?: (actionId: string, actionTitle?: string) => void;
  onSelectTest?: (testId: string) => void;
  onConfigure?: (testId: string) => void;
  onUseDefaults?: (testId: string) => void;
  actionBusy?: boolean;
  hideStepPreview?: boolean;
};

export function AssistantMessageView({
  message,
  selectedTestId,
  onAction,
  onSelectTest,
  onConfigure,
  onUseDefaults,
  actionBusy,
  hideStepPreview,
}: Props) {
  const isUser = message.role === "user";

  if (message.type === "test_recommendations" && message.tests) {
    return (
      <div data-testid="test-recommendations" className={`max-w-full ${isUser ? "ml-8" : "mr-4"}`}>
        <div className="mb-1 text-[9px] text-slate-500">Buildables Assistant · tests</div>
        <TestRecommendationCards
          tests={message.tests}
          specs={message.specs}
          selectedTestId={selectedTestId}
          onSelectTest={onSelectTest}
          onConfigure={onConfigure}
          onUseDefaults={onUseDefaults}
        />
      </div>
    );
  }

  if (message.type === "missing_requirements") {
    return (
      <div data-testid="missing-requirements-card" className="mr-4 rounded border border-slate-200 bg-slate-50 p-2">
        <div className={`mb-1 text-[10px] font-semibold ${accent}`}>Missing dependencies</div>
        {message.missingMeshes?.length ? <MissingMeshTable meshes={message.missingMeshes} /> : null}
        {message.missingMetadata?.length ? (
          <div className="mt-2">
            <MissingMetadataTable rows={message.missingMetadata} />
          </div>
        ) : null}
      </div>
    );
  }

  if (message.type === "engineering_report" && message.engineeringReport) {
    return (
      <div className="mr-4 space-y-2">
        <EngineeringReportCard
          report={message.engineeringReport}
          onViewFull={() => onAction?.("view_engineering_report")}
          onCopy={() => onAction?.("copy_report_summary")}
          onDownload={() => onAction?.("download_report_md")}
        />
        {message.actions ? (
          <RecoveryActions
            actions={message.actions}
            onAction={(id, title) => onAction?.(id, title)}
            busy={actionBusy}
            hideStepPreview={hideStepPreview}
          />
        ) : null}
      </div>
    );
  }

  if (message.type === "simulation_plan" && message.plan) {
    return (
      <div className="mr-4">
        <SimulationPlanCard plan={message.plan} />
      </div>
    );
  }

  if (message.type === "execution_status" && message.executionRun) {
    return (
      <div className="mr-4 space-y-1">
        <div className="text-[9px] text-slate-500">Execution status</div>
        <RunExecutionCard run={message.executionRun} />
        {message.text ? <p className="text-[9px] text-slate-500">{message.text}</p> : null}
      </div>
    );
  }

  if (message.type === "recovery_actions" && message.actions) {
    return (
      <div className="mr-4 rounded border border-slate-200 bg-slate-50 p-2">
        <div className={`mb-2 text-[10px] font-semibold ${accent}`}>Recovery & next steps</div>
        {message.text ? <p className="mb-2 text-[10px] text-slate-600">{message.text}</p> : null}
        <RecoveryActions
          actions={message.actions}
          onAction={(id, title) => onAction?.(id, title)}
          busy={actionBusy}
          hideStepPreview={hideStepPreview}
        />
      </div>
    );
  }

  if (message.type === "asset_summary" && message.inspection) {
    const inv = message.inspection;
    const robot = inv.robot_descriptions.find((r) => r.parsed);
    return (
      <div className="mr-4 rounded border border-slate-200/80 bg-slate-50 p-2 text-[10px] text-slate-700">
        <div className={`font-semibold ${accent}`}>Project assets</div>
        <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[9px] text-slate-600">
          <span>Assets: {inv.assets.length}</span>
          <span>Missing meshes: {inv.missing_mesh_count}</span>
          {robot ? (
            <>
              <span>Links: {robot.links_count}</span>
              <span>Joints: {robot.joints_count} ({robot.movable_joints_count} movable)</span>
            </>
          ) : null}
        </div>
      </div>
    );
  }

  if (message.type === "error" && message.error) {
    const err = message.error;
    return (
      <div
        data-testid="assistant-error-message"
        className="mr-4 rounded border border-red-200 bg-red-50 p-2 text-[10px] text-red-800"
      >
        <div className="font-semibold">{err.title}</div>
        <p className="mt-1">{err.explanation}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            data-testid="error-copy-logs"
            className="rounded border border-red-300 px-2 py-0.5 text-[9px] hover:bg-red-100"
            onClick={() => void navigator.clipboard.writeText(err.copyable_debug_details ?? err.explanation)}
          >
            Copy logs
          </button>
          <button
            type="button"
            data-testid="error-retry-preflight"
            className="rounded border border-red-300 px-2 py-0.5 text-[9px] hover:bg-red-100"
            onClick={() => onAction?.("run_preflight")}
            disabled={actionBusy}
          >
            Retry preflight
          </button>
        </div>
      </div>
    );
  }

  if (message.type === "agent_timeline" && message.timelineSteps?.length) {
    return (
      <div className="mr-4">
        <AgentTimelineCard steps={message.timelineSteps} headline={message.text ?? "Agent progress"} />
      </div>
    );
  }

  if (message.type === "clarification_question") {
    return (
      <div className="mr-4 rounded border border-amber-300/40 bg-amber-50 p-2 text-[10px] text-amber-900">
        <span className="font-semibold">Clarification: </span>
        {message.text}
      </div>
    );
  }

  const bubble = isUser
    ? "ml-8 rounded-lg bg-slate-100 px-3 py-2 text-slate-900"
    : "mr-4 rounded-lg border border-slate-200/80 bg-white px-3 py-2 text-slate-800";

  return (
    <div className={bubble} data-testid={isUser ? "user-message" : "assistant-text-message"}>
      {!isUser ? <div className="mb-1 text-[9px] text-[#c2410c]">Buildables Assistant</div> : null}
      {isUser && message.attachments?.length ? (
        <div className="mb-1 text-[9px] text-slate-600" data-testid="user-message-attachments">
          {message.attachments.map((f) => (
            <span key={f} className="mr-2 inline-block rounded bg-slate-700/60 px-1.5 py-0.5">
              {f}
            </span>
          ))}
        </div>
      ) : null}
      <p className="whitespace-pre-wrap text-[11px] leading-relaxed">{message.text}</p>
    </div>
  );
}
