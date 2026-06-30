/**
 * FileDropzone Component
 *
 * Drag-and-drop file upload zone with validation,
 * progress bar, and upload response display.
 */

"use client";

import { useState, useCallback, useRef } from "react";
import { useUpload } from "@/hooks/useUpload";

const ALLOWED_EXTENSIONS = [".ifc", ".dxf"];

export default function FileDropzone() {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { upload, isUploading, progress, response, error, reset } = useUpload();

  const validateFile = useCallback((file: File): boolean => {
    const extension = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setValidationError(
        `Invalid file type "${extension}". Only ${ALLOWED_EXTENSIONS.join(", ")} files are accepted.`
      );
      return false;
    }
    setValidationError(null);
    return true;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file);
        reset();
      }
    },
    [validateFile, reset]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleUpload = useCallback(async () => {
    if (selectedFile) {
      await upload(selectedFile);
    }
  }, [selectedFile, upload]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setValidationError(null);
    reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [reset]);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* ── Drop Zone ────────────────────────────────────────── */}
      <div
        className={`dropzone ${isDragging ? "dragover" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".ifc,.dxf"
          onChange={handleInputChange}
          className="hidden"
          id="file-upload-input"
        />

        {/* Icon */}
        <div className="mb-4">
          <svg
            className="mx-auto"
            width="56"
            height="56"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent-purple)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ opacity: 0.7 }}
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <p className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          {isDragging ? "Drop your file here" : "Drag & drop your building plan"}
        </p>
        <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
          or click to browse files
        </p>
        <div className="flex items-center justify-center gap-2">
          {ALLOWED_EXTENSIONS.map((ext) => (
            <span
              key={ext}
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: "rgba(139, 92, 246, 0.1)",
                color: "var(--accent-purple)",
                border: "1px solid rgba(139, 92, 246, 0.2)",
              }}
            >
              {ext.toUpperCase()}
            </span>
          ))}
        </div>
      </div>

      {/* ── Validation Error ─────────────────────────────────── */}
      {validationError && (
        <div
          className="p-4 rounded-xl text-sm animate-fade-in"
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            color: "#fca5a5",
          }}
        >
          <span className="font-semibold">⚠ Validation Error: </span>
          {validationError}
        </div>
      )}

      {/* ── Selected File ────────────────────────────────────── */}
      {selectedFile && !validationError && (
        <div className="glass-card p-5 animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: "rgba(139, 92, 246, 0.1)" }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--accent-purple)"
                  strokeWidth="1.5"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div>
                <p className="font-medium" style={{ color: "var(--text-primary)" }}>
                  {selectedFile.name}
                </p>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {formatSize(selectedFile.size)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {!response && (
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="btn-primary text-sm"
                  style={{
                    opacity: isUploading ? 0.7 : 1,
                    cursor: isUploading ? "not-allowed" : "pointer",
                  }}
                >
                  {isUploading ? (
                    <>
                      <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                      </svg>
                      Uploading…
                    </>
                  ) : (
                    "Upload"
                  )}
                </button>
              )}
              <button
                onClick={handleReset}
                className="p-2 rounded-lg transition-colors"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                aria-label="Remove file"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          {isUploading && (
            <div className="mt-4">
              <div
                className="h-1.5 rounded-full overflow-hidden"
                style={{ background: "rgba(139, 92, 246, 0.1)" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${progress}%`,
                    background: "var(--gradient-primary)",
                  }}
                />
              </div>
              <p className="text-xs mt-2 text-right" style={{ color: "var(--text-muted)" }}>
                {progress}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Upload Error ─────────────────────────────────────── */}
      {error && (
        <div
          className="p-4 rounded-xl text-sm animate-fade-in"
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            color: "#fca5a5",
          }}
        >
          <span className="font-semibold">✕ Upload Failed: </span>
          {error}
        </div>
      )}

      {/* ── Upload Success ───────────────────────────────────── */}
      {response && (
        <div
          className="p-5 rounded-xl animate-fade-in-up"
          style={{
            background: "rgba(20, 184, 166, 0.08)",
            border: "1px solid rgba(20, 184, 166, 0.2)",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--accent-teal)"
              strokeWidth="2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span className="font-semibold text-sm" style={{ color: "var(--accent-teal)" }}>
              Upload Successful
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Filename", value: response.filename },
              { label: "Size", value: formatSize(response.size) },
              { label: "Type", value: response.type.toUpperCase() },
              { label: "Uploaded", value: new Date(response.upload_time).toLocaleString() },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xs mb-0.5" style={{ color: "var(--text-muted)" }}>
                  {item.label}
                </p>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
