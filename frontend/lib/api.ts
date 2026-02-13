import axios from 'axios';

// If the variable exists, use it. Otherwise, default to localhost.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface RubricItem {
    criteria: string;
    max_points: number;
    description: string;
    developing_points?: number;
    developing_description?: string;
    zero_points?: number;
    zero_description?: string;
}

export interface GradeResult {
    score: number;
    feedback: string;
    citations: string[];
    thinking_process: string[];
    confidence_score: number;
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
    gradeSubmission: async (files: {filename: string, content: string}[], studentId: string, rubric: RubricItem[]): Promise<GradeResult> => {
        const payload = {
            submission_files: files,
            student_id: studentId,
            rubric: rubric
        };
        return (await api.post<GradeResult>('/grade', payload)).data;
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

    // --- Business Plan Grading ---

    extractPPTX: async (file: File): Promise<{ markdown_content: string, slide_count: number, has_tables: boolean, has_images: boolean, text_length: number }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/extract-pptx', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    gradeBusinessPlan: async (
        pptxFiles: File[],
        docFiles: File[],
        rubric: RubricItem[],
        studentId: string,
        businessType: string
    ): Promise<GradeResult> => {
        const formData = new FormData();
        formData.append('student_id', studentId);
        formData.append('business_context_type', businessType);
        formData.append('rubric_json', JSON.stringify(rubric));
        pptxFiles.forEach(file => formData.append('pptx_files', file));
        docFiles.forEach(file => formData.append('document_files', file));
        const response = await api.post<GradeResult>('/grade-business-plan', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    getBusinessRubricTemplate: async (businessType: string): Promise<RubricItem[]> => {
        const response = await api.get<RubricItem[]>(`/business-rubric-template/${businessType}`);
        return response.data;
    },

    ingestBusinessContext: async (files: File[], contextType: string): Promise<{ status: string, files_processed: number, context_type: string }> => {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        formData.append('context_type', contextType);
        const response = await api.post('/ingest-business-context', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    }
};
