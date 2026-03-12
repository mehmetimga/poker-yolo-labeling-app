import type { ImageRecord } from "@/types";
import { useProjectStore } from "@/stores/projectStore";
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
}

export default function ImageQueue({ images }: Props) {
  const { selectedImageId, setSelectedImageId, statusFilter, setStatusFilter } =
    useProjectStore();

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">
          Images ({images.length})
        </h3>
        <StatusFilter value={statusFilter} onChange={setStatusFilter} />
      </div>
      <div className="flex-1 overflow-y-auto">
        {images.map((img) => (
          <div
            key={img.id}
            onClick={() => setSelectedImageId(img.id)}
            className={`px-3 py-2 cursor-pointer border-b border-gray-800 hover:bg-gray-800 flex items-center gap-2 ${
              selectedImageId === img.id ? "bg-gray-700" : ""
            }`}
          >
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
    </div>
  );
}
