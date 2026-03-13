import { useState } from "react";
import type { ImageRecord } from "@/types";
import { useProjectStore } from "@/stores/projectStore";
import { useBatchUpdateStatus, useBatchAssignSchema, useBatchInference, useTaskStatus } from "@/api/images";
import { useSchemaDefinitions } from "@/api/schemas";
import StatusFilter from "./StatusFilter";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-gray-500",
  in_progress: "bg-yellow-500",
  labeled: "bg-blue-500",
  reviewed: "bg-purple-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
  pre_annotated: "bg-cyan-500",
};

const SORT_OPTIONS = [
  { value: "filename", label: "Name" },
  { value: "confidence_asc", label: "Confidence \u2191" },
  { value: "confidence_desc", label: "Confidence \u2193" },
  { value: "created_at", label: "Date" },
];

function ConfidenceDot({ confidence }: { confidence: number | null | undefined }) {
  if (confidence == null) return null;
  const color =
    confidence >= 0.8 ? "bg-green-400" : confidence >= 0.5 ? "bg-yellow-400" : "bg-red-400";
  const pct = Math.round(confidence * 100);
  return (
    <span className={`w-2 h-2 rounded-full shrink-0 ${color}`} title={`${pct}% confidence`} />
  );
}

interface Props {
  images: ImageRecord[];
  projectId: number;
}

export default function ImageQueue({ images, projectId }: Props) {
  const {
    selectedImageId,
    setSelectedImageId,
    statusFilter,
    setStatusFilter,
    sortOrder,
    setSortOrder,
    selectedImageIds,
    toggleImageSelection,
    selectAllImages,
    clearSelection,
    isMultiSelectMode,
    setMultiSelectMode,
  } = useProjectStore();

  const batchStatus = useBatchUpdateStatus(projectId);
  const batchSchema = useBatchAssignSchema(projectId);
  const batchInference = useBatchInference(projectId);
  const { data: schemas } = useSchemaDefinitions();
  const [showSchemaDropdown, setShowSchemaDropdown] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const { data: taskStatus } = useTaskStatus(taskId);

  const handleBatchStatus = async (status: string) => {
    await batchStatus.mutateAsync({ image_ids: selectedImageIds, status });
    clearSelection();
  };

  const handleBatchSchema = async (schemaName: string) => {
    await batchSchema.mutateAsync({ image_ids: selectedImageIds, schema_name: schemaName });
    clearSelection();
    setShowSchemaDropdown(false);
  };

  const handleBatchInfer = async () => {
    const result = await batchInference.mutateAsync({});
    if (result.task_id) {
      setTaskId(result.task_id);
    }
  };

  const isInferRunning = taskId != null && taskStatus?.status !== "done";
  const allSelected = images.length > 0 && selectedImageIds.length === images.length;

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">
            Images ({images.length})
          </h3>
          <button
            onClick={() => setMultiSelectMode(!isMultiSelectMode)}
            className={`text-xs px-2 py-0.5 rounded ${isMultiSelectMode ? "bg-blue-600 text-white" : "bg-gray-700 hover:bg-gray-600 text-gray-400"}`}
          >
            Select
          </button>
        </div>
        <StatusFilter value={statusFilter} onChange={setStatusFilter} />
        {/* Sort dropdown */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs text-gray-500">Sort:</span>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="text-xs bg-gray-700 text-gray-300 rounded px-1.5 py-0.5 outline-none focus:ring-1 focus:ring-blue-500"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        {/* Batch inference button */}
        <button
          onClick={handleBatchInfer}
          disabled={batchInference.isPending || isInferRunning}
          className="mt-2 w-full text-xs bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-2 py-1.5 rounded font-medium"
        >
          {isInferRunning ? "Running Model..." : "Run Model on All"}
        </button>
        {/* Progress bar */}
        {isInferRunning && taskStatus && (
          <div className="mt-1.5">
            <div className="flex justify-between text-xs text-gray-400 mb-0.5">
              <span>{taskStatus.completed}/{taskStatus.total}</span>
              <span>{Math.round((taskStatus.completed / taskStatus.total) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1.5">
              <div
                className="bg-orange-500 h-1.5 rounded-full transition-all"
                style={{ width: `${(taskStatus.completed / taskStatus.total) * 100}%` }}
              />
            </div>
          </div>
        )}
        {taskStatus?.status === "done" && (
          <div className="mt-1 text-xs text-green-400">
            Done! {taskStatus.completed} processed{taskStatus.errors > 0 ? `, ${taskStatus.errors} errors` : ""}
          </div>
        )}
        {isMultiSelectMode && (
          <button
            onClick={() => allSelected ? clearSelection() : selectAllImages(images.map((i) => i.id))}
            className="text-xs text-blue-400 hover:text-blue-300 mt-1"
          >
            {allSelected ? "Deselect All" : "Select All"}
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {images.map((img) => (
          <div
            key={img.id}
            onClick={() => {
              if (isMultiSelectMode) {
                toggleImageSelection(img.id);
              } else {
                setSelectedImageId(img.id);
              }
            }}
            className={`px-3 py-2 cursor-pointer border-b border-gray-800 hover:bg-gray-800 flex items-center gap-2 ${
              selectedImageId === img.id && !isMultiSelectMode ? "bg-gray-700" : ""
            } ${selectedImageIds.includes(img.id) && isMultiSelectMode ? "bg-blue-900/30" : ""}`}
          >
            {isMultiSelectMode && (
              <input
                type="checkbox"
                checked={selectedImageIds.includes(img.id)}
                onChange={() => toggleImageSelection(img.id)}
                onClick={(e) => e.stopPropagation()}
                className="shrink-0"
              />
            )}
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${STATUS_COLORS[img.status] || "bg-gray-500"}`}
            />
            <span className="text-sm truncate flex-1">{img.filename}</span>
            <ConfidenceDot confidence={img.schema_confidence} />
            {img.annotation_count > 0 && (
              <span className="text-xs text-gray-500">
                {img.annotation_count}
              </span>
            )}
          </div>
        ))}
        {images.length === 0 && (
          <p className="p-3 text-gray-600 text-sm">
            No images. Click "Import Images" to add some.
          </p>
        )}
      </div>

      {/* Batch action bar */}
      {isMultiSelectMode && selectedImageIds.length > 0 && (
        <div className="p-2 border-t border-gray-700 bg-gray-800 space-y-1">
          <div className="text-xs text-gray-400 mb-1">
            {selectedImageIds.length} selected
          </div>
          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => handleBatchStatus("labeled")}
              disabled={batchStatus.isPending}
              className="text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-2 py-1 rounded"
            >
              Mark Done
            </button>
            <button
              onClick={() => handleBatchStatus("reviewed")}
              disabled={batchStatus.isPending}
              className="text-xs bg-purple-600 hover:bg-purple-700 disabled:opacity-50 px-2 py-1 rounded"
            >
              Mark Reviewed
            </button>
            <div className="relative">
              <button
                onClick={() => setShowSchemaDropdown(!showSchemaDropdown)}
                className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded"
              >
                Assign Schema
              </button>
              {showSchemaDropdown && schemas && (
                <div className="absolute bottom-full left-0 mb-1 bg-gray-800 border border-gray-600 rounded shadow-lg max-h-48 overflow-y-auto z-20 w-48">
                  {schemas.schemas.map((s: { name: string }) => (
                    <button
                      key={s.name}
                      onClick={() => handleBatchSchema(s.name)}
                      className="block w-full text-left text-xs px-2 py-1.5 hover:bg-gray-700 truncate"
                    >
                      {s.name.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => { clearSelection(); setMultiSelectMode(false); }}
              className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
