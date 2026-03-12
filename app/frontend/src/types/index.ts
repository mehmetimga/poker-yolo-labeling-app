export interface Project {
  id: number;
  name: string;
  description: string;
  image_root_path: string;
  taxonomy_version: number;
  schema_version: number;
  image_count: number;
  created_at: string;
  updated_at: string;
}

export type ImageStatus =
  | "new"
  | "in_progress"
  | "labeled"
  | "reviewed"
  | "approved"
  | "rejected";

export interface ImageRecord {
  id: number;
  project_id: number;
  filename: string;
  filepath: string;
  width: number;
  height: number;
  hash: string;
  status: ImageStatus;
  assigned_schema: string | null;
  suggested_schema: string | null;
  schema_confidence: number | null;
  review_status: string | null;
  annotation_count: number;
  created_at: string;
  updated_at: string;
}

export type AnnotationSource = "manual" | "copied" | "model" | "imported";

export interface Annotation {
  id: number;
  image_id: number;
  label: string;
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  normalized_x_center: number;
  normalized_y_center: number;
  normalized_width: number;
  normalized_height: number;
  source: AnnotationSource;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface AnnotationCreate {
  label: string;
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  source: AnnotationSource;
  confidence?: number | null;
}

export interface TaxonomyLabel {
  id: number;
  name: string;
  group: string;
  color: string;
  shortcut: string | null;
  description?: string;
}

export interface Taxonomy {
  version: number;
  labels: TaxonomyLabel[];
}

export interface SchemaRule {
  label: string;
  count?: number;
  count_min?: number;
  count_max?: number;
  region?: string;
}

export interface SchemaDefinition {
  name: string;
  description: string;
  required: SchemaRule[];
  optional: SchemaRule[];
  forbidden: SchemaRule[];
}

export interface SchemaMatch {
  schema: string;
  score: number;
  missing: string[];
  conflicts: string[];
}

export interface SchemaScoreResponse {
  top_matches: SchemaMatch[];
}
