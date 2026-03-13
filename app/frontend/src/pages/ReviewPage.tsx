import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  useReviewQueue,
  useSubmitReview,
  useReviewComments,
} from "@/api/review";
import UserBadge from "@/components/UserBadge";

export default function ReviewPage() {
  const { projectId } = useParams();
  const pid = projectId ? parseInt(projectId) : null;
  const navigate = useNavigate();
  const { data: queue, isLoading } = useReviewQueue(pid);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar — review queue */}
      <div className="w-80 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={() => navigate(`/projects/${projectId}`)}
              className="text-gray-400 hover:text-gray-200 text-sm"
            >
              Back
            </button>
            <UserBadge />
          </div>
          <h2 className="text-lg font-bold">Review Queue</h2>
          <p className="text-xs text-gray-400">
            {queue?.length ?? 0} images awaiting review
          </p>
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
  const [comment, setComment] = useState("");
  const [decision, setDecision] = useState<string>("approved");

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

  const decisionColors: Record<string, string> = {
    approved: "bg-green-600 hover:bg-green-700",
    rejected: "bg-red-600 hover:bg-red-700",
    needs_work: "bg-yellow-600 hover:bg-yellow-700",
  };

  return (
    <div className="flex flex-col h-full">
      {/* Image preview */}
      <div className="flex-1 flex items-center justify-center bg-gray-950 p-4">
        <img
          src={`/api/images/${imageId}/file`}
          alt="Review"
          className="max-h-full max-w-full object-contain"
        />
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
              className={`px-3 py-1.5 rounded text-sm font-medium ${
                decision === d
                  ? decisionColors[d]
                  : "bg-gray-700 text-gray-400 hover:bg-gray-600"
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
