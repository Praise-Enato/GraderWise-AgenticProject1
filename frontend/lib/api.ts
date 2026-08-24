import axios from 'axios';

// If the variable exists, use it. Otherwise, default to localhost.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Normalize an axios/network error into a friendly, generic message. Keeps a
// deployment mismatch (a route that 404s because the server is outdated) or an
// unreachable backend from surfacing as a raw "Request failed with status code 404".
export function friendlyApiError(e: any, fallback = "Something went wrong."): string {
    const status = e?.response?.status;
    if (status === 404) return "This feature isn't available on the server yet — the backend may be outdated or still deploying.";
    if (status === 502 || status === 503 || status === 504) return "The grading service is temporarily unavailable. Please try again shortly.";
    if (e?.code === "ERR_NETWORK" || (e && !e.response)) return "Can't reach the grading service — check that the backend is running.";
    return e?.response?.data?.detail || e?.message || fallback;
}

/**
 * Document types the backend can grade — BOTH paths (text and vision). Kept in
 * step with input_adapter.ADAPTER_SUFFIXES on the backend; used for the file
 * pickers' `accept` and for the pre-upload check.
 *
 * Vision mode accepts all of these: PDF pages render to images, PPTX/DOCX give up
 * their embedded pictures plus text, and .txt/.md are graded from text alone
 * (there is nothing to render). It no longer refuses a file for having no images.
 */
export const SUPPORTED_PLAN_TYPES = [".pdf", ".pptx", ".docx", ".txt", ".md"] as const;

/** ".docx" -> true. Accepts a filename or a bare suffix. */
export function isSupportedPlanFile(name: string): boolean {
    const suffix = "." + (name.split(".").pop() || "").toLowerCase();
    return (SUPPORTED_PLAN_TYPES as readonly string[]).includes(suffix);
}

export interface RubricItem {
    criteria: string;
    max_points: number;
    description: string;
    developing_points?: number;
    developing_description?: string;
    zero_points?: number;
    zero_description?: string;
}

export interface CriterionAssessment {
    criteria_index: number;
    criteria_name: string;
    awarded_points: number;
    max_points: number;
    reason: string;
}

export interface GradeResult {
    score: number;
    feedback: string;
    citations: string[];
    thinking_process: string[];
    confidence_score: number;
    // Business Plan Grader fields
    /** Business name read from the plan document itself; "" if it never states one. */
    business_name?: string;
    assessments?: CriterionAssessment[];
    graded_ok?: boolean;
    error?: string | null;
    eligibility_status?: string;   // eligible | needs_review | ineligible
    dq_reasons?: string[];
    ai_content_flag?: boolean;
}

export interface BpcRubricResponse {
    plan: RubricItem[];
    video: RubricItem[];
    full: RubricItem[];
    plan_total: number;
    video_total: number;
    full_total: number;
    guideline: string;
}

export interface GradeOptions {
    guideline?: string;
    skip_rag?: boolean;
    max_retries?: number;
    use_calibration?: boolean;   // false for the general rubric (BYUMS example doesn't apply)
}

export interface FewShotScore {
    filename: string;
    business_name: string;
    human_total: number;
    items: { criteria: string; awarded: number; max_points: number }[];
}

// A past graded run (row in the Business -> History view).
export interface HistoryRow {
    submission_id: number;
    filename: string;
    team: string;
    score: number;
    total_points: number;
    eligibility_status: string;
    graded_ok: boolean;
    created_at: string;
    has_file: boolean;
}

export interface HistoryDetail extends HistoryRow {
    feedback: string;
    confidence_score: number;
    ai_content_flag: boolean;
    assessments: CriterionAssessment[];
}

export const GradeWiseAPI = {
    // Member C uses this
    ingestFiles: async (files: File[]) => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        const response = await api.post('/ingest', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    // Member B uses this
    gradeSubmission: async (files: {filename: string, content: string}[], studentId: string, rubric: RubricItem[], options?: GradeOptions): Promise<GradeResult> => {
        const payload = {
            submission_files: files,
            student_id: studentId,
            rubric: rubric,
            ...(options || {})
        };
        return (await api.post<GradeResult>('/grade', payload)).data;
    },

    // Business Plan Grader: fetch the BYUMS plan/video rubric + judges' guideline
    getBpcRubric: async (): Promise<BpcRubricResponse> => {
        return (await api.get<BpcRubricResponse>('/bpc-rubric')).data;
    },

    // History: past graded plans (persisted server-side, text + vision runs).
    getGradeHistory: async (limit = 100): Promise<HistoryRow[]> => {
        return (await api.get<HistoryRow[]>(`/grade-history?limit=${limit}`)).data;
    },
    getGradeHistoryDetail: async (submissionId: number): Promise<HistoryDetail> => {
        return (await api.get<HistoryDetail>(`/grade-history/${submissionId}`)).data;
    },
    // Direct URL for downloading a stored plan file (used as an <a href>).
    planFileUrl: (submissionId: number): string => `${API_URL}/plan-file/${submissionId}`,

    // General (non-competition) business-plan rubric (150 pts)
    getGeneralRubric: async (): Promise<{ rubric: RubricItem[]; total: number }> => {
        return (await api.get<{ rubric: RubricItem[]; total: number }>('/general-rubric')).data;
    },

    // Human reference scores for the AI-vs-human head-to-head
    getFewShotScores: async (): Promise<FewShotScore[]> => {
        return (await api.get<FewShotScore[]>('/bpc-fewshot-scores')).data;
    },

    // Vision grading (Phase 1b): upload the raw PDF; backend renders slides and
    // grades them with a multimodal model (sees financial tables, license, bank).
    gradeVision: async (file: File, studentId: string, rubric: RubricItem[], guideline: string, useCalibration: boolean = true): Promise<GradeResult> => {
        const fd = new FormData();
        fd.append('files', file);
        fd.append('rubric', JSON.stringify(rubric));
        fd.append('guideline', guideline || '');
        fd.append('student_id', studentId);
        fd.append('use_calibration', String(useCalibration));
        const r = await api.post<GradeResult>('/grade-vision', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return r.data;
    },

    parseRubric: async (files: File[]): Promise<RubricItem[]> => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        const response = await api.post<RubricItem[]>('/parse-rubric', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    extractText: async (file: File): Promise<{ text: string }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post<{ text: string }>('/extract-text', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    extractFilesContent: async (files: File[]): Promise<{ filename: string, content: string }[]> => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        const response = await api.post<{ filename: string, content: string }[]>('/extract-files-content', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    chatWithFeedback: async (question: string, feedback: string, submissionText: string = ""): Promise<{ response: string, sources: string[] }> => {
        const payload = {
            question,
            feedback,
            submission_text: submissionText,
            context_files: []
        };
        return (await api.post<{ response: string, sources: string[] }>('/chat', payload)).data;
    },

    // Download the graded result as a server-rendered PDF. Generic across rubrics —
    // the client posts back the GradeResult it already received.
    downloadReport: async (result: GradeResult, teamName: string = "", rubricLabel: string = ""): Promise<void> => {
        const resp = await api.post('/grade/report',
            { result, team_name: teamName, rubric_label: rubricLabel },
            { responseType: 'blob' });
        const base = (teamName || 'business-plan').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'business-plan';
        const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
        const a = document.createElement('a');
        a.href = url;
        a.download = `${base}-report.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    },
};
