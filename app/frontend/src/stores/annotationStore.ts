import { create } from "zustand";
import type { AnnotationCreate } from "@/types";

export type CanvasTool = "select" | "draw" | "pan" | "zoom";

interface LocalAnnotation extends AnnotationCreate {
  tempId: string;
}

interface AnnotationStore {
  annotations: LocalAnnotation[];
  selectedAnnotationId: string | null;
  activeTool: CanvasTool;
  activeLabel: string;
  hasUnsavedChanges: boolean;
  zoom: number;
  panOffset: { x: number; y: number };

  setAnnotations: (anns: LocalAnnotation[]) => void;
  addAnnotation: (ann: LocalAnnotation) => void;
  updateAnnotation: (tempId: string, updates: Partial<LocalAnnotation>) => void;
  removeAnnotation: (tempId: string) => void;
  setSelectedAnnotationId: (id: string | null) => void;
  setActiveTool: (tool: CanvasTool) => void;
  setActiveLabel: (label: string) => void;
  setHasUnsavedChanges: (val: boolean) => void;
  setZoom: (zoom: number) => void;
  setPanOffset: (offset: { x: number; y: number }) => void;
  reset: () => void;
}

export const useAnnotationStore = create<AnnotationStore>((set) => ({
  annotations: [],
  selectedAnnotationId: null,
  activeTool: "pan",
  activeLabel: "hero_card",
  hasUnsavedChanges: false,
  zoom: 1,
  panOffset: { x: 0, y: 0 },

  setAnnotations: (annotations) =>
    set({ annotations, hasUnsavedChanges: false }),
  addAnnotation: (ann) =>
    set((state) => ({
      annotations: [...state.annotations, ann],
      hasUnsavedChanges: true,
      selectedAnnotationId: ann.tempId,
    })),
  updateAnnotation: (tempId, updates) =>
    set((state) => ({
      annotations: state.annotations.map((a) =>
        a.tempId === tempId ? { ...a, ...updates } : a
      ),
      hasUnsavedChanges: true,
    })),
  removeAnnotation: (tempId) =>
    set((state) => ({
      annotations: state.annotations.filter((a) => a.tempId !== tempId),
      selectedAnnotationId:
        state.selectedAnnotationId === tempId
          ? null
          : state.selectedAnnotationId,
      hasUnsavedChanges: true,
    })),
  setSelectedAnnotationId: (id) => set({ selectedAnnotationId: id }),
  setActiveTool: (tool) => set({ activeTool: tool }),
  setActiveLabel: (label) => set({ activeLabel: label }),
  setHasUnsavedChanges: (val) => set({ hasUnsavedChanges: val }),
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(10, zoom)) }),
  setPanOffset: (offset) => set({ panOffset: offset }),
  reset: () =>
    set({
      annotations: [],
      selectedAnnotationId: null,
      activeTool: "pan",
      hasUnsavedChanges: false,
      zoom: 1,
      panOffset: { x: 0, y: 0 },
    }),
}));
