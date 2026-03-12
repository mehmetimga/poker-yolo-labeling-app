import { useEffect, useRef, useState, useCallback } from "react";
import { Stage, Layer, Image as KonvaImage, Rect } from "react-konva";
import Konva from "konva";
import { useAnnotationStore } from "@/stores/annotationStore";
import { useAnnotations } from "@/api/annotations";
import { getImageFileUrl } from "@/api/images";
import { useTaxonomy } from "@/api/schemas";
import BoundingBoxLayer from "./BoundingBoxLayer";

interface Props {
  imageId: number;
}

const PAN_STEP = 100;
const ZOOM_STEP = 1.3;

export default function AnnotationCanvas({ imageId }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const [drawRect, setDrawRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [spaceDown, setSpaceDown] = useState(false);

  const {
    setAnnotations,
    addAnnotation,
    activeTool,
    setActiveTool,
    activeLabel,
    zoom,
    setZoom,
    panOffset,
    setPanOffset,
    setSelectedAnnotationId,
    undo,
    redo,
    undoStack,
    redoStack,
  } = useAnnotationStore();

  const { data: serverAnnotations } = useAnnotations(imageId);
  const { data: taxonomy } = useTaxonomy();

  const colorMap = useRef<Record<string, string>>({});
  useEffect(() => {
    if (taxonomy) {
      const map: Record<string, string> = {};
      for (const label of taxonomy.labels) {
        map[label.name] = label.color;
      }
      colorMap.current = map;
    }
  }, [taxonomy]);

  // Fit image into view (top-left aligned with padding)
  const fitToView = useCallback(() => {
    if (!image) return;
    const cw = containerSize.width;
    const ch = containerSize.height;
    const iw = image.naturalWidth;
    const ih = image.naturalHeight;
    if (!iw || !ih || !cw || !ch) return;

    const padding = 16;
    const scaleX = (cw - padding * 2) / iw;
    const scaleY = (ch - padding * 2) / ih;
    const newZoom = Math.min(scaleX, scaleY, 1);

    setZoom(newZoom);
    setPanOffset({ x: padding, y: padding });
  }, [image, containerSize, setZoom, setPanOffset]);

  // Load image
  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.src = getImageFileUrl(imageId);
    img.onload = () => setImage(img);
    return () => {
      img.onload = null;
    };
  }, [imageId]);

  // Auto-fit when image loads or container resizes
  useEffect(() => {
    if (image) fitToView();
  }, [image, containerSize.width, containerSize.height]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load annotations from server
  useEffect(() => {
    if (serverAnnotations) {
      const local = serverAnnotations.map((a) => ({
        tempId: `server-${a.id}`,
        label: a.label,
        x_min: a.x_min,
        y_min: a.y_min,
        x_max: a.x_max,
        y_max: a.y_max,
        source: a.source as "manual" | "copied" | "model" | "imported",
        confidence: a.confidence,
      }));
      setAnnotations(local);
    }
  }, [serverAnnotations, setAnnotations]);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setContainerSize({ width, height });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Zoom centered on viewport
  const zoomAtCenter = useCallback(
    (factor: number) => {
      const cx = containerSize.width / 2;
      const cy = containerSize.height / 2;
      const oldZoom = zoom;
      const newZoom = Math.max(0.05, Math.min(10, oldZoom * factor));

      const pointTo = {
        x: (cx - panOffset.x) / oldZoom,
        y: (cy - panOffset.y) / oldZoom,
      };

      setPanOffset({
        x: cx - pointTo.x * newZoom,
        y: cy - pointTo.y * newZoom,
      });
      setZoom(newZoom);
    },
    [zoom, panOffset, containerSize, setZoom, setPanOffset]
  );

  // Space key for panning
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat) {
        e.preventDefault();
        setSpaceDown(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        setSpaceDown(false);
        setIsPanning(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  // Arrow keys + Ctrl+/- for navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA") return;

      switch (e.key) {
        case "h":
        case "H":
          setActiveTool("pan");
          break;
        case "d":
        case "D":
          setActiveTool("draw");
          break;
        case "ArrowLeft":
          e.preventDefault();
          setPanOffset({ x: panOffset.x + PAN_STEP, y: panOffset.y });
          break;
        case "ArrowRight":
          e.preventDefault();
          setPanOffset({ x: panOffset.x - PAN_STEP, y: panOffset.y });
          break;
        case "ArrowUp":
          e.preventDefault();
          setPanOffset({ x: panOffset.x, y: panOffset.y + PAN_STEP });
          break;
        case "ArrowDown":
          e.preventDefault();
          setPanOffset({ x: panOffset.x, y: panOffset.y - PAN_STEP });
          break;
        case "=":
        case "+":
          if (e.metaKey || e.ctrlKey) {
            e.preventDefault();
            zoomAtCenter(ZOOM_STEP);
          }
          break;
        case "-":
          if (e.metaKey || e.ctrlKey) {
            e.preventDefault();
            zoomAtCenter(1 / ZOOM_STEP);
          }
          break;
        case "0":
          if (e.metaKey || e.ctrlKey) {
            e.preventDefault();
            fitToView();
          }
          break;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [panOffset, setPanOffset, zoomAtCenter, fitToView, setActiveTool]);

  const getPointerPos = useCallback(() => {
    const stage = stageRef.current;
    if (!stage) return null;
    const pointer = stage.getPointerPosition();
    if (!pointer) return null;
    return {
      x: (pointer.x - panOffset.x) / zoom,
      y: (pointer.y - panOffset.y) / zoom,
    };
  }, [zoom, panOffset]);

  const handleWheel = useCallback(
    (e: Konva.KonvaEventObject<WheelEvent>) => {
      e.evt.preventDefault();
      const stage = stageRef.current;
      if (!stage) return;

      const pointer = stage.getPointerPosition();
      if (!pointer) return;

      const scaleBy = 1.1;
      const oldZoom = zoom;
      const newZoom =
        e.evt.deltaY < 0 ? oldZoom * scaleBy : oldZoom / scaleBy;

      const clampedZoom = Math.max(0.05, Math.min(10, newZoom));

      const mousePointTo = {
        x: (pointer.x - panOffset.x) / oldZoom,
        y: (pointer.y - panOffset.y) / oldZoom,
      };

      setPanOffset({
        x: pointer.x - mousePointTo.x * clampedZoom,
        y: pointer.y - mousePointTo.y * clampedZoom,
      });
      setZoom(clampedZoom);
    },
    [zoom, panOffset, setZoom, setPanOffset]
  );

  const handleMouseDown = useCallback(
    (e: Konva.KonvaEventObject<MouseEvent>) => {
      const isBackground = e.target === e.target.getStage() || e.target.getClassName() === "Image";

      // Panning with space or middle mouse button — only on background
      if (spaceDown || e.evt.button === 1 || (activeTool === "pan" && isBackground)) {
        setIsPanning(true);
        // Deselect when panning on background
        if (isBackground) setSelectedAnnotationId(null);
        return;
      }

      // Drawing — only on background
      if (activeTool === "draw" && isBackground) {
        const pos = getPointerPos();
        if (!pos) return;
        setIsDrawing(true);
        setDrawStart(pos);
        setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
        return;
      }

      // Deselect on empty click
      if (isBackground) {
        setSelectedAnnotationId(null);
      }
    },
    [activeTool, spaceDown, getPointerPos, setSelectedAnnotationId]
  );

  const handleMouseMove = useCallback(
    (e: Konva.KonvaEventObject<MouseEvent>) => {
      if (isPanning) {
        setPanOffset({
          x: panOffset.x + e.evt.movementX,
          y: panOffset.y + e.evt.movementY,
        });
        return;
      }

      if (isDrawing && drawStart) {
        const pos = getPointerPos();
        if (!pos) return;
        setDrawRect({
          x: Math.min(drawStart.x, pos.x),
          y: Math.min(drawStart.y, pos.y),
          w: Math.abs(pos.x - drawStart.x),
          h: Math.abs(pos.y - drawStart.y),
        });
      }
    },
    [isPanning, isDrawing, drawStart, panOffset, setPanOffset, getPointerPos]
  );

  const handleMouseUp = useCallback(() => {
    if (isPanning) {
      setIsPanning(false);
      return;
    }

    if (isDrawing && drawRect && drawRect.w > 5 && drawRect.h > 5) {
      const tempId = `ann-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      addAnnotation({
        tempId,
        label: activeLabel,
        x_min: drawRect.x,
        y_min: drawRect.y,
        x_max: drawRect.x + drawRect.w,
        y_max: drawRect.y + drawRect.h,
        source: "manual",
        confidence: null,
      });
    }
    setIsDrawing(false);
    setDrawStart(null);
    setDrawRect(null);
  }, [isPanning, isDrawing, drawRect, activeLabel, addAnnotation]);

  const cursorStyle =
    spaceDown || activeTool === "pan"
      ? "grab"
      : activeTool === "draw"
        ? "crosshair"
        : "default";

  const zoomPercent = Math.round(zoom * 100);

  return (
    <div ref={containerRef} className="w-full h-full relative" style={{ cursor: cursorStyle }}>
      {/* Navigation toolbar - top left */}
      <div
        className="absolute top-2 left-2 z-10 flex items-center gap-1 bg-gray-900/85 backdrop-blur-sm rounded-lg px-2 py-1.5 select-none shadow-lg border border-gray-700/50"
        title="H=Pan, D=Draw | Arrows=Pan | Ctrl+/-=Zoom | Ctrl+0=Fit | Click box to select/resize/move"
      >
        {/* Hand (pan) tool */}
        <button
          onClick={() => setActiveTool("pan")}
          className={`w-7 h-7 flex items-center justify-center rounded ${activeTool === "pan" ? "bg-blue-600 text-white" : "hover:bg-gray-700 text-gray-400"}`}
          title="Pan / Move (H) — Drag to move image. Arrows to pan. Click box to select, drag to move, handles to resize."
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M10 2a1.5 1.5 0 0 1 1.5 1.5V11h1V4.5a1.5 1.5 0 0 1 3 0V11h1V6.5a1.5 1.5 0 0 1 3 0V15a7 7 0 0 1-7 7h-1a7 7 0 0 1-5.5-2.7L3.4 15.8a1.5 1.5 0 0 1 2.1-2.1L7.5 16V3.5A1.5 1.5 0 0 1 9 2h1Z"/></svg>
        </button>

        {/* Draw tool */}
        <button
          onClick={() => setActiveTool("draw")}
          className={`w-7 h-7 flex items-center justify-center rounded ${activeTool === "draw" ? "bg-blue-600 text-white" : "hover:bg-gray-700 text-gray-400"}`}
          title="Draw bounding box (D) — Click and drag to draw a new box."
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><rect x="4" y="4" width="16" height="16" rx="1" strokeDasharray="5 3"/><line x1="4" y1="4" x2="10" y2="10"/></svg>
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Zoom out */}
        <button
          onClick={() => zoomAtCenter(1 / ZOOM_STEP)}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-lg font-bold"
          title="Zoom out (Ctrl+- or scroll down)"
        >
          -
        </button>

        {/* Zoom percentage */}
        <span className="text-xs text-gray-400 w-11 text-center tabular-nums font-mono">
          {zoomPercent}%
        </span>

        {/* Zoom in */}
        <button
          onClick={() => zoomAtCenter(ZOOM_STEP)}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-lg font-bold"
          title="Zoom in (Ctrl++ or scroll up)"
        >
          +
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Fit */}
        <button
          onClick={fitToView}
          className="px-2 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-xs font-medium"
          title="Fit image to view (Ctrl+0)"
        >
          Fit
        </button>

        {/* 1:1 */}
        <button
          onClick={() => {
            setZoom(1);
            setPanOffset({ x: 0, y: 0 });
          }}
          className="px-2 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 text-xs font-medium"
          title="Original size (100%)"
        >
          1:1
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Undo */}
        <button
          onClick={undo}
          disabled={undoStack.length === 0}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 disabled:text-gray-600 disabled:hover:bg-transparent"
          title="Undo (Ctrl+Z)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7v6h6"/><path d="M3 13a9 9 0 0 1 15.36-6.36L21 9"/></svg>
        </button>

        {/* Redo */}
        <button
          onClick={redo}
          disabled={redoStack.length === 0}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-300 disabled:text-gray-600 disabled:hover:bg-transparent"
          title="Redo (Ctrl+Y / Ctrl+Shift+Z)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 7v6h-6"/><path d="M21 13a9 9 0 0 0-15.36-6.36L3 9"/></svg>
        </button>

        <div className="w-px h-5 bg-gray-600 mx-1" />

        {/* Pan direction controls */}
        <button
          onClick={() => setPanOffset({ x: panOffset.x + PAN_STEP, y: panOffset.y })}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
          title="Pan left (Arrow Left)"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M8 1L3 6l5 5"/></svg>
        </button>
        <div className="flex flex-col">
          <button
            onClick={() => setPanOffset({ x: panOffset.x, y: panOffset.y + PAN_STEP })}
            className="w-7 h-3.5 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
            title="Pan up (Arrow Up)"
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="currentColor"><path d="M1 7l5-5 5 5"/></svg>
          </button>
          <button
            onClick={() => setPanOffset({ x: panOffset.x, y: panOffset.y - PAN_STEP })}
            className="w-7 h-3.5 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
            title="Pan down (Arrow Down)"
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="currentColor"><path d="M1 1l5 5 5-5"/></svg>
          </button>
        </div>
        <button
          onClick={() => setPanOffset({ x: panOffset.x - PAN_STEP, y: panOffset.y })}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400"
          title="Pan right (Arrow Right)"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M4 1l5 5-5 5"/></svg>
        </button>
      </div>

      {/* Image info - bottom left */}
      {image && (
        <div className="absolute bottom-2 left-2 z-10 bg-gray-900/80 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-500 font-mono">
          {image.naturalWidth} x {image.naturalHeight}px
        </div>
      )}

      <Stage
        ref={stageRef}
        width={containerSize.width}
        height={containerSize.height}
        scaleX={zoom}
        scaleY={zoom}
        x={panOffset.x}
        y={panOffset.y}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <Layer>
          {image && <KonvaImage image={image} />}
        </Layer>
        <BoundingBoxLayer colorMap={colorMap.current} />
        {/* Drawing preview */}
        {drawRect && (
          <Layer>
            <Rect
              x={drawRect.x}
              y={drawRect.y}
              width={drawRect.w}
              height={drawRect.h}
              stroke={colorMap.current[activeLabel] || "#ffffff"}
              strokeWidth={2 / zoom}
              dash={[6 / zoom, 3 / zoom]}
            />
          </Layer>
        )}
      </Stage>
    </div>
  );
}
