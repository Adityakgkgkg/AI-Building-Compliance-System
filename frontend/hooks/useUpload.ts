/**
 * AI Building Compliance System — useUpload Hook
 *
 * Custom React hook that wraps the file upload API call
 * with loading, progress, error, and response state management.
 */

"use client";

import { useState, useCallback } from "react";
import { uploadFile } from "@/services/api";
import type { UploadResponse } from "@/types";
import { AxiosError } from "axios";

interface UseUploadReturn {
  /** Trigger the file upload */
  upload: (file: File) => Promise<void>;
  /** Whether an upload is currently in progress */
  isUploading: boolean;
  /** Upload progress percentage (0–100) */
  progress: number;
  /** The upload response data on success */
  response: UploadResponse | null;
  /** Error message if upload failed */
  error: string | null;
  /** Reset state back to initial */
  reset: () => void;
}

export function useUpload(): UseUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [response, setResponse] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setIsUploading(false);
    setProgress(0);
    setResponse(null);
    setError(null);
  }, []);

  const upload = useCallback(async (file: File) => {
    try {
      setIsUploading(true);
      setProgress(0);
      setError(null);
      setResponse(null);

      const result = await uploadFile(file, (p) => setProgress(p));

      setResponse(result);
      setProgress(100);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ||
        axiosError.message ||
        "Upload failed. Please try again.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  }, []);

  return { upload, isUploading, progress, response, error, reset };
}
