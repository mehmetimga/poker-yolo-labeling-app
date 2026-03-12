import { useRef, useEffect, useCallback } from "react";
import { Layer, Rect, Text, Group, Transformer } from "react-konva";
import Konva from "konva";
import { useAnnotationStore } from "@/stores/annotationStore";

interface Props {
  colorMap: Record<string, string>;
}

function BoundingBox({
  ann,
  color,
  isSelected,
  zoom,
  onSelect,
  onUpdate,
}: {
  ann: { tempId: string; label: string; x_min: number; y_min: number; x_max: number; y_max: number; source: string };
  color: string;
  isSelected: boolean;
  zoom: number;
  onSelect: () => void;
  onUpdate: (updates: { x_min: number; y_min: number; x_max: number; y_max: number }) => void;
}) {
  const rectRef = useRef<Konva.Rect>(null);
  const trRef = useRef<Konva.Transformer>(null);

  const w = ann.x_max - ann.x_min;
  const h = ann.y_max - ann.y_min;

  useEffect(() => {
    if (isSelected && trRef.current && rectRef.current) {
      trRef.current.nodes([rectRef.current]);
      trRef.current.getLayer()?.batchDraw();
    }
  }, [isSelected]);

  const handleTransformEnd = useCallback(() => {
    const node = rectRef.current;
    if (!node) return;

    const scaleX = node.scaleX();
    const scaleY = node.scaleY();

    node.scaleX(1);
    node.scaleY(1);

    const newX = node.x();
    const newY = node.y();
    const newW = Math.max(5, node.width() * scaleX);
    const newH = Math.max(5, node.height() * scaleY);

    onUpdate({
      x_min: newX,
      y_min: newY,
      x_max: newX + newW,
      y_max: newY + newH,
    });
  }, [onUpdate]);

  const handleDragEnd = useCallback(() => {
    const node = rectRef.current;
    if (!node) return;
    onUpdate({
      x_min: node.x(),
      y_min: node.y(),
      x_max: node.x() + w,
      y_max: node.y() + h,
    });
  }, [w, h, onUpdate]);

  // Anchor size: 6px on screen regardless of zoom
  const anchorPx = Math.min(8, Math.max(4, 6 / zoom));

  return (
    <Group>
      <Rect
        ref={rectRef}
        x={ann.x_min}
        y={ann.y_min}
        width={w}
        height={h}
        stroke={color}
        strokeWidth={(isSelected ? 3 : 2) / zoom}
        fill={isSelected ? color + "20" : "transparent"}
        draggable={isSelected}
        onClick={onSelect}
        onTap={onSelect}
        onDragEnd={handleDragEnd}
        onTransformEnd={handleTransformEnd}
      />
      {/* Label text */}
      <Text
        x={ann.x_min}
        y={ann.y_min - 16 / zoom}
        text={ann.label}
        fontSize={12 / zoom}
        fill={color}
        listening={false}
      />
      {/* Source indicator */}
      {ann.source !== "manual" && (
        <Text
          x={ann.x_max - 14 / zoom}
          y={ann.y_min + 2 / zoom}
          text={ann.source === "copied" ? "C" : ann.source === "model" ? "M" : "I"}
          fontSize={10 / zoom}
          fill="#ffffff80"
          listening={false}
        />
      )}
      {/* Transformer for resize handles - only on selected */}
      {isSelected && (
        <Transformer
          ref={trRef}
          rotateEnabled={false}
          keepRatio={false}
          borderEnabled={false}
          anchorSize={anchorPx}
          anchorStroke={color}
          anchorFill="#ffffff"
          anchorCornerRadius={2}
          enabledAnchors={[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "middle-left",
            "middle-right",
            "top-center",
            "bottom-center",
          ]}
          boundBoxFunc={(_oldBox, newBox) => {
            if (Math.abs(newBox.width) < 5 || Math.abs(newBox.height) < 5) {
              return _oldBox;
            }
            return newBox;
          }}
        />
      )}
    </Group>
  );
}

export default function BoundingBoxLayer({ colorMap }: Props) {
  const {
    annotations,
    selectedAnnotationId,
    setSelectedAnnotationId,
    updateAnnotation,
    zoom,
  } = useAnnotationStore();

  return (
    <Layer>
      {annotations.map((ann) => {
        const isSelected = ann.tempId === selectedAnnotationId;
        const color = colorMap[ann.label] || "#ffffff";

        return (
          <BoundingBox
            key={ann.tempId}
            ann={ann}
            color={color}
            isSelected={isSelected}
            zoom={zoom}
            onSelect={() => setSelectedAnnotationId(ann.tempId)}
            onUpdate={(updates) => updateAnnotation(ann.tempId, updates)}
          />
        );
      })}
    </Layer>
  );
}
