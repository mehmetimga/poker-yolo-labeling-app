import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProject } from "@/api/projects";
import {
  useTrainingRuns,
  useCreateTrainingRun,
  useTrainingRun,
  useTrainingLiveStatus,
  useErrorMining,
  useActivateModel,
} from "@/api/training";
import type { TrainingRun, ErrorMiningEntry } from "@/types";

// ─── Status badge ────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-500",
  preparing: "bg-yellow-500",
  training: "bg-blue-500 animate-pulse",
  evaluating: "bg-purple-500 animate-pulse",
  mining: "bg-purple-500 animate-pulse",
  done: "bg-green-500",
  failed: "bg-red-500",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[status] || "bg-gray-600"}`}>
      {status}
    </span>
  );
}

// ─── Metric display helpers ──────────────────────────────────────

function MetricCard({ label, value, unit = "" }: { label: string; value: number | null | undefined; unit?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3 text-center">
      <div className="text-2xl font-bold text-white">
        {value != null ? `${(value * 100).toFixed(1)}${unit || "%"}` : "—"}
      </div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

function RawMetricCard({ label, value }: { label: string; value: number | string | null | undefined }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3 text-center">
      <div className="text-2xl font-bold text-white">
        {value != null ? String(typeof value === "number" ? value.toFixed(4) : value) : "—"}
      </div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

// ─── Per-class accuracy table ────────────────────────────────────

function PerClassTable({ perClass }: { perClass: Record<string, { ap50: number; ap50_95: number | null }> }) {
  const entries = Object.entries(perClass).sort((a, b) => a[1].ap50 - b[1].ap50);

  return (
    <div className="max-h-64 overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-gray-900">
          <tr className="text-gray-400 text-xs">
            <th className="text-left py-1 px-2">Label</th>
            <th className="text-right py-1 px-2">AP50</th>
            <th className="text-right py-1 px-2">AP50-95</th>
            <th className="py-1 px-2 w-24">Bar</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([label, m]) => {
            const pct = m.ap50 * 100;
            const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
            return (
              <tr key={label} className="border-t border-gray-800 hover:bg-gray-800/50">
                <td className="py-1 px-2 truncate max-w-[150px]">{label}</td>
                <td className="text-right py-1 px-2 font-mono">{pct.toFixed(1)}%</td>
                <td className="text-right py-1 px-2 font-mono text-gray-400">
                  {m.ap50_95 != null ? (m.ap50_95 * 100).toFixed(1) + "%" : "—"}
                </td>
                <td className="py-1 px-2">
                  <div className="w-full bg-gray-700 rounded-full h-1.5">
                    <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Error mining table ──────────────────────────────────────────

function ErrorMiningTable({ errors }: { errors: ErrorMiningEntry[] }) {
  if (errors.length === 0) {
    return <p className="text-gray-500 text-sm">No errors found — model matches ground truth.</p>;
  }

  return (
    <div className="max-h-80 overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-gray-900">
          <tr className="text-gray-400 text-xs">
            <th className="text-left py-1 px-2">Image</th>
            <th className="text-right py-1 px-2">Divergence</th>
            <th className="text-right py-1 px-2">GT</th>
            <th className="text-right py-1 px-2">Pred</th>
            <th className="text-left py-1 px-2">Missing</th>
            <th className="text-left py-1 px-2">Extra</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((err) => (
            <tr key={err.image_id} className="border-t border-gray-800 hover:bg-gray-800/50">
              <td className="py-1 px-2 truncate max-w-[120px]" title={err.filename}>
                {err.filename}
              </td>
              <td className="text-right py-1 px-2">
                <span className={`font-mono ${err.divergence >= 5 ? "text-red-400" : err.divergence >= 2 ? "text-yellow-400" : "text-gray-300"}`}>
                  {err.divergence}
                </span>
              </td>
              <td className="text-right py-1 px-2 text-gray-400">{err.gt_count}</td>
              <td className="text-right py-1 px-2 text-gray-400">{err.pred_count}</td>
              <td className="py-1 px-2 text-red-400 text-xs truncate max-w-[150px]">
                {err.missing.map((m) => `${m.label}(${m.gt}-${m.pred})`).join(", ") || "—"}
              </td>
              <td className="py-1 px-2 text-yellow-400 text-xs truncate max-w-[150px]">
                {err.extra.map((m) => `${m.label}(${m.pred}-${m.gt})`).join(", ") || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Training run detail panel ───────────────────────────────────

function RunDetail({ runId }: { runId: number }) {
  const { data: run } = useTrainingRun(runId);
  const { data: liveStatus } = useTrainingLiveStatus(
    run && !["done", "failed"].includes(run.status) ? runId : null
  );
  const { data: errorData } = useErrorMining(
    run?.status === "done" ? runId : null
  );
  const activate = useActivateModel(runId);

  if (!run) return <div className="text-gray-500">Loading...</div>;

  const isRunning = !["done", "failed"].includes(run.status);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{run.name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={run.status} />
            {isRunning && liveStatus?.progress && (
              <span className="text-xs text-gray-400">{liveStatus.progress}</span>
            )}
            {run.error_message && (
              <span className="text-xs text-red-400 truncate max-w-[300px]">{run.error_message}</span>
            )}
          </div>
        </div>
        {run.status === "done" && run.model_path && (
          <button
            onClick={() => activate.mutate()}
            disabled={activate.isPending}
            className="bg-green-600 hover:bg-green-700 disabled:opacity-50 px-3 py-1.5 rounded text-sm font-medium"
          >
            {activate.isPending ? "Activating..." : "Activate Model"}
          </button>
        )}
      </div>

      {/* Config */}
      <div className="grid grid-cols-4 gap-2 text-sm">
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400 text-xs">Base Model</div>
          <div className="font-mono">{run.base_model}</div>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400 text-xs">Epochs</div>
          <div className="font-mono">{run.epochs}</div>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400 text-xs">Batch Size</div>
          <div className="font-mono">{run.batch_size}</div>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <div className="text-gray-400 text-xs">Learning Rate</div>
          <div className="font-mono">{run.learning_rate}</div>
        </div>
      </div>

      {/* Dataset split */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 uppercase mb-2">Dataset Split ({run.split_ratio})</h4>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-blue-500" />
            <span className="text-sm">Train: {run.train_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-yellow-500" />
            <span className="text-sm">Val: {run.val_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-red-500" />
            <span className="text-sm">Test: {run.test_count}</span>
          </div>
        </div>
        {/* Visual bar */}
        {(run.train_count + run.val_count + run.test_count) > 0 && (
          <div className="flex h-3 rounded-full overflow-hidden mt-2">
            <div className="bg-blue-500" style={{ width: `${(run.train_count / (run.train_count + run.val_count + run.test_count)) * 100}%` }} />
            <div className="bg-yellow-500" style={{ width: `${(run.val_count / (run.train_count + run.val_count + run.test_count)) * 100}%` }} />
            <div className="bg-red-500" style={{ width: `${(run.test_count / (run.train_count + run.val_count + run.test_count)) * 100}%` }} />
          </div>
        )}
      </div>

      {/* Evaluation metrics */}
      {run.evaluation && (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-2">Evaluation Metrics</h4>
          <div className="grid grid-cols-4 gap-2 mb-3">
            <MetricCard label="mAP@50" value={run.evaluation.mAP50} />
            <MetricCard label="mAP@50-95" value={run.evaluation.mAP50_95} />
            <MetricCard label="Precision" value={run.evaluation.precision} />
            <MetricCard label="Recall" value={run.evaluation.recall} />
          </div>

          {/* Per-class breakdown */}
          {Object.keys(run.evaluation.per_class || {}).length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 uppercase mb-2">
                Per-Label Accuracy ({Object.keys(run.evaluation.per_class).length} classes)
              </h4>
              <PerClassTable perClass={run.evaluation.per_class} />
            </div>
          )}
        </div>
      )}

      {/* Training metrics (raw) */}
      {run.metrics && !run.evaluation && (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-2">Training Metrics</h4>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(run.metrics).slice(0, 9).map(([key, val]) => (
              <RawMetricCard key={key} label={key.replace(/metrics\//g, "")} value={val} />
            ))}
          </div>
        </div>
      )}

      {/* Error mining */}
      {errorData && errorData.errors.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-2">
            Error Mining — Top Divergences ({errorData.errors.length} / {errorData.total_evaluated} images)
          </h4>
          <ErrorMiningTable errors={errorData.errors} />
        </div>
      )}
    </div>
  );
}

// ─── New training run form ───────────────────────────────────────

function NewRunForm({ projectId, onCreated }: { projectId: number; onCreated: (id: number) => void }) {
  const create = useCreateTrainingRun(projectId);
  const [name, setName] = useState("");
  const [epochs, setEpochs] = useState(100);
  const [batchSize, setBatchSize] = useState(16);
  const [imgSize, setImgSize] = useState(640);
  const [lr, setLr] = useState(0.01);
  const [trainRatio, setTrainRatio] = useState(0.7);
  const valRatio = Math.min(0.2, 1 - trainRatio - 0.05);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    const result = await create.mutateAsync({
      name: name.trim(),
      epochs,
      batch_size: batchSize,
      img_size: imgSize,
      learning_rate: lr,
      train_ratio: trainRatio,
      val_ratio: valRatio,
      test_ratio: Math.max(0, 1 - trainRatio - valRatio),
    });
    onCreated(result.id);
    setName("");
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-4 space-y-3">
      <h4 className="text-sm font-semibold text-gray-300">Start New Training Run</h4>

      <div>
        <label className="text-xs text-gray-400">Run Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. v1-baseline-100ep"
          className="w-full bg-gray-700 rounded px-2 py-1.5 text-sm outline-none focus:ring-1 focus:ring-blue-500 mt-0.5"
          required
        />
      </div>

      <div className="grid grid-cols-4 gap-2">
        <div>
          <label className="text-xs text-gray-400">Epochs</label>
          <input type="number" value={epochs} onChange={(e) => setEpochs(+e.target.value)} min={1} max={1000}
            className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500 mt-0.5" />
        </div>
        <div>
          <label className="text-xs text-gray-400">Batch Size</label>
          <input type="number" value={batchSize} onChange={(e) => setBatchSize(+e.target.value)} min={1} max={128}
            className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500 mt-0.5" />
        </div>
        <div>
          <label className="text-xs text-gray-400">Image Size</label>
          <input type="number" value={imgSize} onChange={(e) => setImgSize(+e.target.value)} min={320} max={1280} step={32}
            className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500 mt-0.5" />
        </div>
        <div>
          <label className="text-xs text-gray-400">Learning Rate</label>
          <input type="number" value={lr} onChange={(e) => setLr(+e.target.value)} min={0.0001} max={0.1} step={0.001}
            className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500 mt-0.5" />
        </div>
      </div>

      <div>
        <label className="text-xs text-gray-400">Dataset Split (Train / Val / Test)</label>
        <div className="flex items-center gap-2 mt-1">
          <input type="range" min={0.5} max={0.9} step={0.05} value={trainRatio}
            onChange={(e) => setTrainRatio(+e.target.value)} className="flex-1" />
          <span className="text-xs font-mono w-32 text-gray-300">
            {Math.round(trainRatio * 100)} / {Math.round(valRatio * 100)} / {Math.round((1 - trainRatio - valRatio) * 100)}
          </span>
        </div>
      </div>

      <button
        type="submit"
        disabled={create.isPending || !name.trim()}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-3 py-2 rounded text-sm font-medium"
      >
        {create.isPending ? "Creating..." : "Create & Start Training"}
      </button>

      {create.isError && (
        <p className="text-red-400 text-xs">{(create.error as Error).message}</p>
      )}
    </form>
  );
}

// ─── Model comparison panel ──────────────────────────────────────

function ComparePanel({ runs }: { runs: TrainingRun[] }) {
  const completed = runs.filter((r) => r.status === "done" && r.evaluation);
  if (completed.length < 2) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h4 className="text-sm font-semibold text-gray-400 uppercase mb-3">Model Comparison</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 text-xs border-b border-gray-700">
              <th className="text-left py-2 px-2">Run</th>
              <th className="text-right py-2 px-2">mAP50</th>
              <th className="text-right py-2 px-2">mAP50-95</th>
              <th className="text-right py-2 px-2">Precision</th>
              <th className="text-right py-2 px-2">Recall</th>
              <th className="text-right py-2 px-2">Images</th>
              <th className="text-right py-2 px-2">Epochs</th>
            </tr>
          </thead>
          <tbody>
            {completed.map((run) => {
              const ev = run.evaluation!;
              return (
                <tr key={run.id} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="py-2 px-2 font-medium">{run.name}</td>
                  <td className="text-right py-2 px-2 font-mono">
                    {ev.mAP50 != null ? (ev.mAP50 * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td className="text-right py-2 px-2 font-mono">
                    {ev.mAP50_95 != null ? (ev.mAP50_95 * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td className="text-right py-2 px-2 font-mono">
                    {ev.precision != null ? (ev.precision * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td className="text-right py-2 px-2 font-mono">
                    {ev.recall != null ? (ev.recall * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td className="text-right py-2 px-2 text-gray-400">
                    {run.train_count + run.val_count + run.test_count}
                  </td>
                  <td className="text-right py-2 px-2 text-gray-400">{run.epochs}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────

export default function TrainingPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const pid = projectId ? parseInt(projectId, 10) : null;

  const { data: project } = useProject(pid);
  const { data: runs } = useTrainingRuns(pid);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  if (!pid) return null;

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/projects/${pid}`)}
            className="flex items-center gap-1 text-sm text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 px-2.5 py-1 rounded transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
            Labeling
          </button>
          <div className="w-px h-5 bg-gray-700" />
          <h2 className="font-semibold">{project?.name || "Loading..."}</h2>
          <span className="text-sm text-gray-500">Training</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate("/")}
            className="text-sm text-gray-400 hover:text-white hover:bg-gray-700 px-2.5 py-1.5 rounded transition-colors"
          >
            Projects
          </button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Run list */}
        <div className="w-72 bg-gray-850 border-r border-gray-700 flex flex-col shrink-0">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-400 uppercase">
              Training Runs ({runs?.length || 0})
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto">
            {runs?.map((run) => (
              <div
                key={run.id}
                onClick={() => setSelectedRunId(run.id)}
                className={`px-3 py-2.5 cursor-pointer border-b border-gray-800 hover:bg-gray-800 ${
                  selectedRunId === run.id ? "bg-gray-700" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{run.name}</span>
                  <StatusBadge status={run.status} />
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                  <span>{run.train_count + run.val_count + run.test_count} images</span>
                  <span>{run.epochs} epochs</span>
                  {run.evaluation?.mAP50 != null && (
                    <span className="text-green-400">mAP: {(run.evaluation.mAP50 * 100).toFixed(1)}%</span>
                  )}
                </div>
              </div>
            ))}
            {(!runs || runs.length === 0) && (
              <p className="p-3 text-gray-600 text-sm">No training runs yet.</p>
            )}
          </div>
        </div>

        {/* Right: Detail or new run form */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* New run form (always visible at top) */}
          <NewRunForm projectId={pid} onCreated={(id) => setSelectedRunId(id)} />

          {/* Model comparison */}
          {runs && runs.length >= 2 && <ComparePanel runs={runs} />}

          {/* Selected run detail */}
          {selectedRunId && (
            <div className="bg-gray-850 rounded-lg border border-gray-700 p-4">
              <RunDetail runId={selectedRunId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
