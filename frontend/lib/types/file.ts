export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface UploadedFile {
  id: string;
  user_id: number;
  session_id: string | null;
  filename: string;
  file_type: string | null;
  file_size: number | null;
  processing_status: ProcessingStatus;
  uploaded_at: string;
}

