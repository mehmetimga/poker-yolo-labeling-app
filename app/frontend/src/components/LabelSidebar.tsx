import { useState, useEffect, useCallback, useRef } from "react";
import { useAnnotationStore } from "@/stores/annotationStore";
import { useTaxonomy, useScoreSchemas, useAssignSchema } from "@/api/schemas";
import { useSaveAnnotations, useAutosaveAnnotations } from "@/api/annotations";
import { useExportYolo, useExportMetadata } from "@/api/export";
import { useImages } from "@/api/images";
import { useProjectStore } from "@/stores/projectStore";
import api from "@/api/client";
import LabelDropdown from "./LabelDropdown";
import AnnotationList from "./AnnotationList";
import SchemaSuggestionPanel from "./SchemaSuggestionPanel";
import type { Annotation, AnnotationCreate, SchemaScoreResponse } from "@/types";

interface Props {
  imageId: number;
  projectId: number;
}

export default function LabelSidebar({ imageId, projectId }: Props) {
  const { data: taxonomy } = useTaxonomy();
  const {
    annotations,
    activeTool,
    setActiveTool,
    activeLabel,
    setActiveLabel,
    hasUnsavedChanges,
    setHasUnsavedChanges,
    addAnnotation,
    removeAnnotation,
    selectedAnnotationId,
  } = useAnnotationStore();
  const { setSelectedImageId } = useProjectStore();
  const { data: images } = useImages(projectId);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);

  const saveAnnotations = useSaveAnnotations(imageId);
  const autosave = useAutosaveAnnotations(imageId);
  const scoreSchemas = useScoreSchemas();
  const assignSchema = useAssignSchema(imageId);
  const exportYolo = useExportYolo(projectId);
  const exportMetadata = useExportMetadata(projectId);

  const schemaResults = useRef<SchemaScoreResponse | null>(null);

  // Convert local annotations to API format
  const toApiFormat = useCallback((): AnnotationCreate[] => {
    return annotations.map((a) => ({
      label: a.label,
      x_min: a.x_min,
      y_min: a.y_min,
      x_max: a.x_max,
      y_max: a.y_max,
      source: a.source,
      confidence: a.confidence,
    }));
  }, [annotations]);

  // Save
  const handleSave = useCallback(async () => {
    await saveAnnotations.mutateAsync(toApiFormat());
    setHasUnsavedChanges(false);

    // Re-score schemas after save
    const result = await scoreSchemas.mutateAsync(imageId);
    schemaResults.current = result;
  }, [
    toApiFormat,
    saveAnnotations,
    setHasUnsavedChanges,
    scoreSchemas,
    imageId,
  ]);

  // Autosave (debounced)
  useEffect(() => {
    if (!hasUnsavedChanges || annotations.length === 0) return;
    const timer = setTimeout(() => {
      autosave.mutate(toApiFormat());
    }, 3000);
    return () => clearTimeout(timer);
  }, [annotations, hasUnsavedChanges, toApiFormat, autosave]);

  // Copy annotations from previous image
  const copyFromPrevious = useCallback(async () => {
    if (!images) return;
    const idx = images.findIndex((img) => img.id === imageId);
    if (idx <= 0) {
      setCopyStatus("No previous image");
      setTimeout(() => setCopyStatus(null), 2000);
      return;
    }
    const prevId = images[idx - 1].id;
    try {
      const { data } = await api.get<Annotation[]>(`/images/${prevId}/annotations`);
      if (data.length === 0) {
        setCopyStatus("Previous image has no annotations");
        setTimeout(() => setCopyStatus(null), 2000);
        return;
      }
      for (const ann of data) {
        addAnnotation({
          tempId: crypto.randomUUID(),
          label: ann.label,
          x_min: ann.x_min,
          y_min: ann.y_min,
          x_max: ann.x_max,
          y_max: ann.y_max,
          source: "copied",
          confidence: ann.confidence,
        });
      }
      setCopyStatus(`Copied ${data.length} annotations`);
      setTimeout(() => setCopyStatus(null), 2000);
    } catch {
      setCopyStatus("Failed to copy");
      setTimeout(() => setCopyStatus(null), 2000);
    }
  }, [images, imageId, addAnnotation]);

  // Score schemas on load
  useEffect(() => {
    if (annotations.length > 0) {
      scoreSchemas.mutateAsync(imageId).then((r) => {
        schemaResults.current = r;
      });
    }
  }, [imageId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Warn on browser close/refresh with unsaved changes
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [hasUnsavedChanges]);

  // Navigation helpers
  const navigateImage = useCallback(
    (direction: "next" | "prev") => {
      if (!images) return;
      if (hasUnsavedChanges && !confirm("You have unsaved changes. Discard and continue?")) {
        return;
      }
      const idx = images.findIndex((img) => img.id === imageId);
      if (idx < 0) return;
      const newIdx = direction === "next" ? idx + 1 : idx - 1;
      if (newIdx >= 0 && newIdx < images.length) {
        setSelectedImageId(images[newIdx].id);
      }
    },
    [images, imageId, setSelectedImageId, hasUnsavedChanges]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA") {
        return;
      }

      switch (e.key.toLowerCase()) {
        case "n":
          navigateImage("next");
          break;
        case "p":
          navigateImage("prev");
          break;
        case "c":
          if (!e.metaKey && !e.ctrlKey) {
            copyFromPrevious();
          }
          break;
        case "b":
          setActiveTool("draw");
          break;
        case "v":
          setActiveTool("select");
          break;
        case "delete":
        case "backspace":
          if (selectedAnnotationId) {
            removeAnnotation(selectedAnnotationId);
          }
          break;
        case "s":
          if (e.metaKey || e.ctrlKey) {
            e.preventDefault();
            handleSave();
          }
          break;
        default: {
          // Number shortcuts for labels
          const num = parseInt(e.key);
          if (num >= 1 && num <= 9 && taxonomy) {
            const label = taxonomy.labels.find((l) => l.shortcut === e.key);
            if (label) {
              setActiveLabel(label.name);
            }
          }
          break;
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    navigateImage,
    copyFromPrevious,
    setActiveTool,
    selectedAnnotationId,
    removeAnnotation,
    handleSave,
    taxonomy,
    setActiveLabel,
  ]);

  return (
    <div className="flex flex-col h-full">
      {/* Tools */}
      <div className="p-3 border-b border-gray-700">
        <div className="flex gap-1 mb-2">
          <button
            onClick={() => setActiveTool("select")}
            className={`px-3 py-1 rounded text-sm ${activeTool === "select" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
          >
            Select (V)
          </button>
          <button
            onClick={() => setActiveTool("draw")}
            className={`px-3 py-1 rounded text-sm ${activeTool === "draw" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
          >
            Draw (B)
          </button>
        </div>

        {/* Active label */}
        <LabelDropdown
          labels={taxonomy?.labels || []}
          value={activeLabel}
          onChange={setActiveLabel}
        />
      </div>

      {/* Annotation list */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-gray-400 uppercase">
              Annotations ({annotations.length})
            </h4>
            <button
              onClick={copyFromPrevious}
              className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-0.5 rounded"
              title="Copy annotations from previous image (C)"
            >
              Copy Prev (C)
            </button>
          </div>
          {copyStatus && (
            <div className="text-xs text-blue-400 mb-1">{copyStatus}</div>
          )}
          <AnnotationList />
        </div>

        {/* Schema suggestions */}
        <div className="p-3 border-t border-gray-700">
          <SchemaSuggestionPanel
            imageId={imageId}
            schemaResults={scoreSchemas.data || null}
            onAssign={(name) => assignSchema.mutate(name)}
          />
        </div>
      </div>

      {/* Save / Export */}
      <div className="p-3 border-t border-gray-700 space-y-2">
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saveAnnotations.isPending}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 px-3 py-2 rounded text-sm font-medium"
          >
            {saveAnnotations.isPending ? "Saving..." : "Save (Ctrl+S)"}
          </button>
          {hasUnsavedChanges && (
            <span className="text-yellow-500 text-xs">Unsaved</span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportYolo.mutate(undefined)}
            disabled={exportYolo.isPending}
            className="flex-1 bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded text-xs"
          >
            Export YOLO
          </button>
          <button
            onClick={() => exportMetadata.mutate(undefined)}
            disabled={exportMetadata.isPending}
            className="flex-1 bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded text-xs"
          >
            Export JSON
          </button>
        </div>
      </div>
    </div>
  );
}
