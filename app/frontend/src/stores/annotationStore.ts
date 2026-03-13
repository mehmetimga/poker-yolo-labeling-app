import { create } from "zustand";
import type { AnnotationCreate } from "@/types";

export type CanvasTool = "select" | "draw" | "pan" | "zoom";

interface LocalAnnotation extends AnnotationCreate {
  tempId: string;
}

const MAX_UNDO = 50;

interface AnnotationStore {
  annotations: LocalAnnotation[];
  selectedAnnotationId: string | null;
  activeTool: CanvasTool;
  activeLabel: string;
  hasUnsavedChanges: boolean;
  zoom: number;
  panOffset: { x: number; y: number };
  undoStack: LocalAnnotation[][];
  redoStack: LocalAnnotation[][];

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
  acceptAllModelAnnotations: () => void;
  undo: () => void;
  redo: () => void;
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
  undoStack: [],
  redoStack: [],

  setAnnotations: (annotations) =>
    set({ annotations, hasUnsavedChanges: false, undoStack: [], redoStack: [] }),

  addAnnotation: (ann) =>
    set((state) => ({
      undoStack: [...state.undoStack.slice(-(MAX_UNDO - 1)), state.annotations],
      redoStack: [],
      annotations: [...state.annotations, ann],
      hasUnsavedChanges: true,
      selectedAnnotationId: ann.tempId,
    })),

  updateAnnotation: (tempId, updates) =>
    set((state) => ({
      undoStack: [...state.undoStack.slice(-(MAX_UNDO - 1)), state.annotations],
      redoStack: [],
      annotations: state.annotations.map((a) =>
        a.tempId === tempId ? { ...a, ...updates } : a
      ),
      hasUnsavedChanges: true,
    })),

  removeAnnotation: (tempId) =>
    set((state) => ({
      undoStack: [...state.undoStack.slice(-(MAX_UNDO - 1)), state.annotations],
      redoStack: [],
      annotations: state.annotations.filter((a) => a.tempId !== tempId),
      selectedAnnotationId:
        state.selectedAnnotationId === tempId
          ? null
          : state.selectedAnnotationId,
      hasUnsavedChanges: true,
    })),

  undo: () =>
    set((state) => {
      if (state.undoStack.length === 0) return state;
      const prev = state.undoStack[state.undoStack.length - 1];
      return {
        undoStack: state.undoStack.slice(0, -1),
        redoStack: [...state.redoStack, state.annotations],
        annotations: prev,
        selectedAnnotationId: null,
        hasUnsavedChanges: true,
      };
    }),

  redo: () =>
    set((state) => {
      if (state.redoStack.length === 0) return state;
      const next = state.redoStack[state.redoStack.length - 1];
      return {
        redoStack: state.redoStack.slice(0, -1),
        undoStack: [...state.undoStack, state.annotations],
        annotations: next,
        selectedAnnotationId: null,
        hasUnsavedChanges: true,
      };
    }),

  acceptAllModelAnnotations: () =>
    set((state) => {
      const hasModel = state.annotations.some((a) => a.source === "model");
      if (!hasModel) return state;
      return {
        undoStack: [...state.undoStack.slice(-(MAX_UNDO - 1)), state.annotations],
        redoStack: [],
        annotations: state.annotations.map((a) =>
          a.source === "model" ? { ...a, source: "manual" as const } : a
        ),
        hasUnsavedChanges: true,
      };
    }),

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
      undoStack: [],
      redoStack: [],
    }),
}));
