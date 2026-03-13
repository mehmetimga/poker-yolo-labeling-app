import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface Props {
  text: string;
  children: ReactNode;
  position?: "top" | "bottom";
  delay?: number;
}

export default function Tooltip({ text, children, position = "top", delay = 300 }: Props) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0 });
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const wrapperRef = useRef<HTMLDivElement>(null);

  const updateCoords = useCallback(() => {
    if (!wrapperRef.current) return;
    const rect = wrapperRef.current.getBoundingClientRect();
    setCoords({ top: rect.top, left: rect.left, width: rect.width });
  }, []);

  const show = useCallback(() => {
    timeoutRef.current = setTimeout(() => {
      updateCoords();
      setVisible(true);
    }, delay);
  }, [delay, updateCoords]);

  const hide = useCallback(() => {
    clearTimeout(timeoutRef.current);
    setVisible(false);
  }, []);

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  return (
    <div ref={wrapperRef} className="relative inline-flex w-full" onMouseEnter={show} onMouseLeave={hide}>
      {children}
      {visible && text && createPortal(
        <div
          style={{
            position: "fixed",
            left: coords.left,
            width: Math.max(coords.width, 220),
            ...(position === "top"
              ? { bottom: window.innerHeight - coords.top + 4 }
              : { top: coords.top + 4 }),
            zIndex: 99999,
          }}
          className="px-2 py-1.5 text-xs leading-snug bg-yellow-900 border border-yellow-600 text-yellow-100 rounded shadow-lg whitespace-normal pointer-events-none"
        >
          {text}
        </div>,
        document.body
      )}
    </div>
  );
}
