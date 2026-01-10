import axios from 'axios';

// Connect to the Python Backend
const API_URL = 'http://127.0.0.1:8000';

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
    gradeSubmission: async (text: string, studentId: string, rubric: RubricItem[]): Promise<GradeResult> => {
        const payload = {
            submission_text: text,
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
    }
};
