import React, { useEffect, useRef, useState } from "react";
import { Camera, X } from "@phosphor-icons/react";

// Live camera capture modal. facingMode "user" = front (selfie), "environment" = rear (documents on mobile).
export default function CameraCapture({ facingMode = "user", onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [err, setErr] = useState("");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode }, audio: false });
        if (!active) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play().catch(() => {}); }
        setReady(true);
      } catch (e) {
        setErr("Couldn't access the camera. Please allow camera permission in your browser, or use the Upload option instead.");
      }
    })();
    return () => { active = false; if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop()); };
  }, [facingMode]);

  const capture = () => {
    const v = videoRef.current;
    if (!v || !v.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth; canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      onCapture(new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  };

  return (
    <div className="fixed inset-0 z-[120] bg-black/85 backdrop-blur grid place-items-center p-4" data-testid="camera-capture-modal">
      <div className="glass-strong rounded-3xl p-4 w-full max-w-md">
        <div className="flex items-center justify-between mb-3">
          <div className="font-display font-bold flex items-center gap-2"><Camera size={18} /> Take a photo</div>
          <button onClick={onClose} className="btn-ghost !px-2 !py-2" data-testid="camera-close"><X size={16} /></button>
        </div>
        {err ? (
          <div className="text-rose-200 text-sm py-10 text-center" data-testid="camera-error">{err}</div>
        ) : (
          <>
            <div className="rounded-2xl overflow-hidden bg-black aspect-[3/4] grid place-items-center">
              <video ref={videoRef} playsInline muted className="w-full h-full object-cover"
                style={{ transform: facingMode === "user" ? "scaleX(-1)" : "none" }} />
            </div>
            <button onClick={capture} disabled={!ready} className="btn-primary w-full justify-center mt-4 disabled:opacity-50" data-testid="camera-capture-btn">
              <Camera size={16} /> Capture
            </button>
          </>
        )}
      </div>
    </div>
  );
}
