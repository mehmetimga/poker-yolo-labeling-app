import { Fragment, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProject, useImportImages, useUploadImages } from "@/api/projects";
import { useImages } from "@/api/images";
import { useProjectStore } from "@/stores/projectStore";
import { useAuthStore } from "@/stores/authStore";
import UserBadge from "@/components/UserBadge";
import ImageQueue from "@/components/ImageQueue";
import AnnotationCanvas from "@/components/AnnotationCanvas";
import LabelSidebar from "@/components/LabelSidebar";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const pid = projectId ? parseInt(projectId, 10) : null;
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: project } = useProject(pid);
  const importImages = useImportImages(pid || 0);
  const uploadImages = useUploadImages(pid || 0);
  const { selectedImageId, statusFilter, schemaFilter, sortOrder } = useProjectStore();
  const { user } = useAuthStore();
  const isAdmin = user?.role === "admin";
  const isReviewerOrAdmin = user?.role === "admin" || user?.role === "reviewer";
  const { data: images } = useImages(pid, {
    status: statusFilter || undefined,
    schema: schemaFilter || undefined,
    sort: sortOrder !== "filename" ? sortOrder : undefined,
  });

  const showMsg = (msg: string) => {
    setImportMsg(msg);
    setTimeout(() => setImportMsg(null), 8000);
  };

  const handleImport = async () => {
    if (!pid) return;
    setImportMsg(null);
    try {
      const result = await importImages.mutateAsync();
      const parts: string[] = [];
      if (result.imported > 0) parts.push(`${result.imported} imported`);
      if (result.skipped > 0) parts.push(`${result.skipped} skipped`);
      if (result.errors?.length > 0) parts.push(`${result.errors.length} errors: ${result.errors[0]}`);
      showMsg(parts.length > 0 ? parts.join(", ") : "No images found in folder");
    } catch {
      showMsg("Import failed — check the image folder path");
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !pid) return;
    setImportMsg(null);
    try {
      const result = await uploadImages.mutateAsync(files);
      const parts: string[] = [];
      if (result.uploaded > 0) parts.push(`${result.uploaded} uploaded`);
      if (result.imported > 0) parts.push(`${result.imported} imported`);
      if (result.skipped > 0) parts.push(`${result.skipped} skipped`);
      showMsg(parts.length > 0 ? parts.join(", ") : "No valid images selected");
    } catch {
      showMsg("Upload failed");
    }
    // Reset input so the same files can be selected again
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  if (!pid) return null;

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="text-gray-400 hover:text-white text-sm"
          >
            &larr; Projects
          </button>
          <h2 className="font-semibold">{project?.name || "Loading..."}</h2>
          <span className="text-sm text-gray-500">
            {project?.image_count || 0} images
          </span>
        </div>
        <div className="flex items-center gap-2">
          {importMsg && (
            <span className={`text-xs ${importMsg.includes("error") || importMsg.includes("failed") || importMsg.includes("No images") ? "text-yellow-400" : "text-green-400"}`}>
              {importMsg}
            </span>
          )}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".png,.jpg,.jpeg,.webp"
            onChange={handleUpload}
            className="hidden"
          />
          {isAdmin && (
            <Fragment>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadImages.isPending}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 px-3 py-1 rounded text-sm"
              >
                {uploadImages.isPending ? "Uploading..." : "Upload Images"}
              </button>
              <button
                onClick={handleImport}
                disabled={importImages.isPending}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-3 py-1 rounded text-sm"
              >
                {importImages.isPending ? "Importing..." : "Import from Folder"}
              </button>
            </Fragment>
          )}
          {isAdmin && (
            <button
              onClick={() => navigate(`/projects/${pid}/training`)}
              className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-sm"
            >
              Training
            </button>
          )}
          {isReviewerOrAdmin && (
            <Fragment>
              <button
                onClick={() => navigate(`/projects/${pid}/review`)}
                className="bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-sm"
              >
                Review
              </button>
              <button
                onClick={() => navigate(`/projects/${pid}/dashboard`)}
                className="bg-teal-600 hover:bg-teal-700 px-3 py-1 rounded text-sm"
              >
                Dashboard
              </button>
            </Fragment>
          )}
          {isAdmin && (
            <button
              onClick={() => navigate("/admin")}
              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
            >
              Admin
            </button>
          )}
          <UserBadge />
        </div>
      </div>

      {/* Three-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Image Queue */}
        <div className="w-64 bg-gray-850 border-r border-gray-700 overflow-y-auto shrink-0">
          <ImageQueue images={images || []} projectId={pid} />
        </div>

        {/* Center: Canvas */}
        <div className="flex-1 overflow-hidden bg-gray-950">
          {selectedImageId ? (
            <AnnotationCanvas imageId={selectedImageId} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-600">
              Select an image from the queue
            </div>
          )}
        </div>

        {/* Right: Label Sidebar */}
        <div className="w-80 bg-gray-850 border-l border-gray-700 overflow-y-auto shrink-0">
          {selectedImageId ? (
            <LabelSidebar imageId={selectedImageId} projectId={pid} />
          ) : (
            <div className="p-4 text-gray-600 text-sm">
              Select an image to start labeling
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
