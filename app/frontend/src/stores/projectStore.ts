import { create } from "zustand";
import type { ImageStatus } from "@/types";

interface ProjectStore {
  selectedImageId: number | null;
  statusFilter: ImageStatus | null;
  schemaFilter: string | null;
  selectedImageIds: number[];
  isMultiSelectMode: boolean;

  setSelectedImageId: (id: number | null) => void;
  setStatusFilter: (status: ImageStatus | null) => void;
  setSchemaFilter: (schema: string | null) => void;
  toggleImageSelection: (id: number) => void;
  selectAllImages: (ids: number[]) => void;
  clearSelection: () => void;
  setMultiSelectMode: (val: boolean) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  selectedImageId: null,
  statusFilter: null,
  schemaFilter: null,
  selectedImageIds: [],
  isMultiSelectMode: false,

  setSelectedImageId: (id) => set({ selectedImageId: id }),
  setStatusFilter: (status) => set({ statusFilter: status }),
  setSchemaFilter: (schema) => set({ schemaFilter: schema }),
  toggleImageSelection: (id) =>
    set((state) => ({
      selectedImageIds: state.selectedImageIds.includes(id)
        ? state.selectedImageIds.filter((i) => i !== id)
        : [...state.selectedImageIds, id],
    })),
  selectAllImages: (ids) => set({ selectedImageIds: ids }),
  clearSelection: () => set({ selectedImageIds: [] }),
  setMultiSelectMode: (val) =>
    set(val ? { isMultiSelectMode: true } : { isMultiSelectMode: false, selectedImageIds: [] }),
}));
