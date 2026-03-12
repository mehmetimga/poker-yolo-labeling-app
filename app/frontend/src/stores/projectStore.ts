import { create } from "zustand";
import type { ImageStatus } from "@/types";

interface ProjectStore {
  selectedImageId: number | null;
  statusFilter: ImageStatus | null;
  schemaFilter: string | null;

  setSelectedImageId: (id: number | null) => void;
  setStatusFilter: (status: ImageStatus | null) => void;
  setSchemaFilter: (schema: string | null) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  selectedImageId: null,
  statusFilter: null,
  schemaFilter: null,

  setSelectedImageId: (id) => set({ selectedImageId: id }),
  setStatusFilter: (status) => set({ statusFilter: status }),
  setSchemaFilter: (schema) => set({ schemaFilter: schema }),
}));
