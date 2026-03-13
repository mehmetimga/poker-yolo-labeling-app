import { useRef, useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  useReviewQueue,
  useSubmitReview,
  useReviewComments,
} from "@/api/review";
import { useAnnotations } from "@/api/annotations";
import { getImageFileUrl } from "@/api/images";
import { useTaxonomy } from "@/api/schemas";
import UserBadge from "@/components/UserBadge";
import type { Annotation } from "@/types";

export default function ReviewPage() {
  const { projectId } = useParams();
  const pid = projectId ? parseInt(projectId) : null;
  const navigate = useNavigate();
  const { data: queue, isLoading } = useReviewQueue(pid);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Top bar */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="flex items-center gap-1 text-sm text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 px-2.5 py-1 rounded transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
            Back
          </button>
          <div className="w-px h-5 bg-gray-700" />
          <h2 className="text-lg font-bold">Review</h2>
          <span className="text-sm text-gray-500">{queue?.length ?? 0} in queue</span>
        </div>
        <UserBadge />
      </div>

      <div className="flex flex-1 overflow-hidden">
      {/* Sidebar — review queue */}
      <div className="w-72 border-r border-gray-700 flex flex-col">
        <div className="px-3 py-2.5 border-b border-gray-700">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Queue</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <p className="text-gray-400 text-sm p-4">Loading...</p>
          )}
          {queue?.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelectedId(item.id)}
              className={`px-4 py-3 cursor-pointer border-b border-gray-800 hover:bg-gray-800 ${
                selectedId === item.id ? "bg-gray-800" : ""
              }`}
            >
              <p className="text-sm font-medium truncate">{item.filename}</p>
              <div className="flex gap-2 text-xs text-gray-400 mt-1">
                {item.assigned_schema && (
                  <span className="bg-gray-700 px-1.5 py-0.5 rounded">
                    {item.assigned_schema}
                  </span>
                )}
                <span>{item.annotation_count} annotations</span>
              </div>
            </div>
          ))}
          {queue?.length === 0 && !isLoading && (
            <p className="text-gray-500 text-sm p-4">
              No images to review.
            </p>
          )}
        </div>
      </div>

      {/* Main — review panel */}
      <div className="flex-1 flex flex-col">
        {selectedId ? (
          <ReviewPanel imageId={selectedId} onDone={() => setSelectedId(null)} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select an image from the queue to review
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

function ReviewPanel({
  imageId,
  onDone,
}: {
  imageId: number;
  onDone: () => void;
}) {
  const submitReview = useSubmitReview(imageId);
  const { data: comments } = useReviewComments(imageId);
  const { data: annotations } = useAnnotations(imageId);
  const { data: taxonomy } = useTaxonomy();
  const [comment, setComment] = useState("");
  const [decision, setDecision] = useState<string>("approved");
  const [showBoxes, setShowBoxes] = useState(true);

  const labelColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (taxonomy?.labels) {
      for (const l of taxonomy.labels) {
        map[l.name] = l.color;
      }
    }
    return map;
  }, [taxonomy]);

  const handleSubmit = () => {
    submitReview.mutate(
      { decision, comment },
      {
        onSuccess: () => {
          setComment("");
          onDone();
        },
      }
    );
  };

  const decisionStyles: Record<string, { active: string; inactive: string }> = {
    approved: {
      active: "bg-green-600 text-white ring-2 ring-green-400",
      inactive: "border border-green-600 text-green-400 hover:bg-green-600/20",
    },
    rejected: {
      active: "bg-red-600 text-white ring-2 ring-red-400",
      inactive: "border border-red-600 text-red-400 hover:bg-red-600/20",
    },
    needs_work: {
      active: "bg-yellow-600 text-white ring-2 ring-yellow-400",
      inactive: "border border-yellow-600 text-yellow-400 hover:bg-yellow-600/20",
    },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Image preview with annotation overlay */}
      <div className="flex-1 flex items-center justify-center bg-gray-950 p-4 relative overflow-hidden">
        <AnnotatedImage
          imageId={imageId}
          annotations={showBoxes ? annotations ?? [] : []}
          labelColorMap={labelColorMap}
        />
      </div>

      {/* Toggle + annotation summary bar */}
      <div className="px-4 py-2 border-t border-gray-700 flex items-center gap-3 bg-gray-850">
        <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={showBoxes}
            onChange={(e) => setShowBoxes(e.target.checked)}
            className="accent-blue-500"
          />
          Show boxes
        </label>
        {annotations && (
          <span className="text-xs text-gray-500">
            {annotations.length} annotations
          </span>
        )}
        {annotations && annotations.length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {Object.entries(
              annotations.reduce<Record<string, number>>((acc, a) => {
                acc[a.label] = (acc[a.label] || 0) + 1;
                return acc;
              }, {})
            ).map(([label, count]) => (
              <span
                key={label}
                className="text-xs px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: (labelColorMap[label] || "#6b7280") + "33",
                  color: labelColorMap[label] || "#9ca3af",
                  border: `1px solid ${labelColorMap[label] || "#6b7280"}55`,
                }}
              >
                {label} ({count})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Previous comments */}
      {comments && comments.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-700 max-h-32 overflow-y-auto">
          <p className="text-xs text-gray-400 mb-1">Previous reviews:</p>
          {comments.map((c) => (
            <div key={c.id} className="text-xs mb-1">
              <span className="text-blue-400">{c.reviewer_username}</span>{" "}
              <span
                className={
                  c.decision === "approved"
                    ? "text-green-400"
                    : c.decision === "rejected"
                    ? "text-red-400"
                    : "text-yellow-400"
                }
              >
                [{c.decision}]
              </span>{" "}
              <span className="text-gray-300">{c.comment}</span>
            </div>
          ))}
        </div>
      )}

      {/* Decision panel */}
      <div className="p-4 border-t border-gray-700 bg-gray-800">
        <div className="flex gap-2 mb-3">
          {(["approved", "rejected", "needs_work"] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDecision(d)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                decision === d
                  ? decisionStyles[d].active
                  : decisionStyles[d].inactive
              }`}
            >
              {d === "needs_work" ? "Needs Work" : d.charAt(0).toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add a review comment..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-gray-100 mb-3 resize-none"
          rows={2}
        />
        <button
          onClick={handleSubmit}
          disabled={submitReview.isPending}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 px-4 py-2 rounded text-sm font-medium"
        >
          {submitReview.isPending ? "Submitting..." : "Submit Review"}
        </button>
      </div>
    </div>
  );
}

const ZOOM_STEP = 1.3;
const PAN_STEP = 80;

function AnnotatedImage({
  imageId,
  annotations,
  labelColorMap,
}: {
  imageId: number;
  annotations: Annotation[];
  labelColorMap: Record<string, string>;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  const handleImageLoad = () => {
    if (imgRef.current) {
      setImgSize({
        w: imgRef.current.naturalWidth,
        h: imgRef.current.naturalHeight,
      });
    }
  };

  // Reset zoom/pan when imageId changes
  useEffect(() => {
    setImgSize(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [imageId]);

  // Fit image to container
  const fitToView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  // Zoom centered on viewport
  const zoomBy = useCallback(
    (factor: number) => {
      setZoom((prev) => Math.max(0.1, Math.min(10, prev * factor)));
    },
    []
  );

  // Scroll wheel zoom
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left - rect.width / 2;
      const mouseY = e.clientY - rect.top - rect.height / 2;

      const oldZoom = zoom;
      const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      const newZoom = Math.max(0.1, Math.min(10, oldZoom * factor));

      // Zoom toward mouse position
      const scale = newZoom / oldZoom;
      setPan((prev) => ({
        x: mouseX - scale * (mouseX - prev.x),
        y: mouseY - scale * (mouseY - prev.y),
      }));
      setZoom(newZoom);
    };

    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => container.removeEventListener("wheel", handleWheel);
  }, [zoom]);

  // Mouse drag panning
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      setIsPanning(true);
      panStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y };
    },
    [pan]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isPanning) return;
      setPan({
        x: panStart.current.panX + (e.clientX - panStart.current.x),
        y: panStart.current.panY + (e.clientY - panStart.current.y),
      });
    },
    [isPanning]
  );

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT") return;

      switch (e.key) {
        case "=":
        case "+":
          if (e.metaKey || e.ctrlKey) { e.preventDefault(); zoomBy(ZOOM_STEP); }
          break;
        case "-":
          if (e.metaKey || e.ctrlKey) { e.preventDefault(); zoomBy(1 / ZOOM_STEP); }
          break;
        case "0":
          if (e.metaKey || e.ctrlKey) { e.preventDefault(); fitToView(); }
          break;
        case "ArrowLeft":
          e.preventDefault(); setPan((p) => ({ ...p, x: p.x + PAN_STEP })); break;
        case "ArrowRight":
          e.preventDefault(); setPan((p) => ({ ...p, x: p.x - PAN_STEP })); break;
        case "ArrowUp":
          e.preventDefault(); setPan((p) => ({ ...p, y: p.y + PAN_STEP })); break;
        case "ArrowDown":
          e.preventDefault(); setPan((p) => ({ ...p, y: p.y - PAN_STEP })); break;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [zoomBy, fitToView]);

  const zoomPercent = Math.round(zoom * 100);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden"
      style={{ cursor: isPanning ? "grabbing" : "grab" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Toolbar */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-1 bg-gray-900/85 backdrop-blur-sm rounded-lg px-2 py-1.5 select-none shadow-lg border border-gray-700/50">
        {/* Zoom out */}
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => zoomBy(1 / ZOOM_STEP)}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-lg font-bold"
          title="Zoom out (Ctrl+-)"
        >
          -
        </button>

        <span className="text-xs text-gray-400 w-11 text-center tabular-nums font-mono">
          {zoomPercent}%
        </span>

        {/* Zoom in */}
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => zoomBy(ZOOM_STEP)}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-lg font-bold"
          title="Zoom in (Ctrl++)"
        >
          +
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Fit */}
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={fitToView}
          className="px-2 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-xs font-medium"
          title="Fit to view (Ctrl+0)"
        >
          Fit
        </button>

        {/* 1:1 */}
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
          className="px-2 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-xs font-medium"
          title="Original size (100%)"
        >
          1:1
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Pan arrows */}
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setPan((p) => ({ ...p, x: p.x + PAN_STEP }))}
          className="w-6 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
          title="Pan left"
        >
          <svg width="10" height="10" viewBox="0 0 12 12" fill="currentColor"><path d="M8 1L3 6l5 5"/></svg>
        </button>
        <div className="flex flex-col">
          <button
            onMouseDown={(e) => e.stopPropagation()}
            onClick={() => setPan((p) => ({ ...p, y: p.y + PAN_STEP }))}
            className="w-6 h-3.5 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
            title="Pan up"
          >
            <svg width="10" height="7" viewBox="0 0 12 8" fill="currentColor"><path d="M1 7l5-5 5 5"/></svg>
          </button>
          <button
            onMouseDown={(e) => e.stopPropagation()}
            onClick={() => setPan((p) => ({ ...p, y: p.y - PAN_STEP }))}
            className="w-6 h-3.5 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
            title="Pan down"
          >
            <svg width="10" height="7" viewBox="0 0 12 8" fill="currentColor"><path d="M1 1l5 5 5-5"/></svg>
          </button>
        </div>
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setPan((p) => ({ ...p, x: p.x - PAN_STEP }))}
          className="w-6 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
          title="Pan right"
        >
          <svg width="10" height="10" viewBox="0 0 12 12" fill="currentColor"><path d="M4 1l5 5-5 5"/></svg>
        </button>
      </div>

      {/* Image dimensions - bottom left */}
      {imgSize && (
        <div className="absolute bottom-2 left-2 z-10 bg-gray-900/80 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-500 font-mono">
          {imgSize.w} x {imgSize.h}px
        </div>
      )}

      {/* Zoomable/pannable container */}
      <div
        className="w-full h-full flex items-center justify-center"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: "center center",
        }}
      >
        <div className="relative">
          <img
            ref={imgRef}
            src={getImageFileUrl(imageId)}
            alt="Review"
            className="max-h-[calc(100vh-200px)] max-w-full object-contain pointer-events-none"
            onLoad={handleImageLoad}
            draggable={false}
          />
          {/* SVG bounding box overlay — sized to match natural image, CSS scales it with the img */}
          {imgSize && annotations.length > 0 && (
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none"
              viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
              preserveAspectRatio="xMidYMid meet"
            >
              {annotations.map((ann) => {
                const color = labelColorMap[ann.label] || "#ef4444";
                return (
                  <g key={ann.id}>
                    <rect
                      x={ann.x_min}
                      y={ann.y_min}
                      width={ann.x_max - ann.x_min}
                      height={ann.y_max - ann.y_min}
                      fill="none"
                      stroke={color}
                      strokeWidth={Math.max(2, imgSize.w / 400)}
                      strokeOpacity={0.9}
                    />
                    <rect
                      x={ann.x_min}
                      y={Math.max(0, ann.y_min - imgSize.h * 0.022)}
                      width={ann.label.length * imgSize.w * 0.012 + imgSize.w * 0.01}
                      height={imgSize.h * 0.022}
                      fill={color}
                      fillOpacity={0.85}
                      rx={2}
                    />
                    <text
                      x={ann.x_min + imgSize.w * 0.005}
                      y={Math.max(0, ann.y_min - imgSize.h * 0.005)}
                      fill="white"
                      fontSize={imgSize.h * 0.016}
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {ann.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}
