import { useState } from "react";
import type { ImageRecord } from "@/types";
import { useProjectStore } from "@/stores/projectStore";
import { useBatchUpdateStatus, useBatchAssignSchema } from "@/api/images";
import { useSchemaDefinitions } from "@/api/schemas";
import StatusFilter from "./StatusFilter";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-gray-500",
  in_progress: "bg-yellow-500",
  labeled: "bg-blue-500",
  reviewed: "bg-purple-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
};

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
    selectedImageIds,
    toggleImageSelection,
    selectAllImages,
    clearSelection,
    isMultiSelectMode,
    setMultiSelectMode,
  } = useProjectStore();

  const batchStatus = useBatchUpdateStatus(projectId);
  const batchSchema = useBatchAssignSchema(projectId);
  const { data: schemas } = useSchemaDefinitions();
  const [showSchemaDropdown, setShowSchemaDropdown] = useState(false);

  const handleBatchStatus = async (status: string) => {
    await batchStatus.mutateAsync({ image_ids: selectedImageIds, status });
    clearSelection();
  };

  const handleBatchSchema = async (schemaName: string) => {
    await batchSchema.mutateAsync({ image_ids: selectedImageIds, schema_name: schemaName });
    clearSelection();
    setShowSchemaDropdown(false);
  };

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
