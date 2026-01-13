import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const DATA_FILE = path.join(process.cwd(), 'data', 'submissions.json');

async function getSubmissions() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (e) {
        return [];
    }
}

async function saveSubmissions(submissions: any[]) {
    await fs.writeFile(DATA_FILE, JSON.stringify(submissions, null, 2));
}

export async function POST(request: Request) {
    const body = await request.json();
    const { id, manualGrade } = body;

    const submissions = await getSubmissions();
    const index = submissions.findIndex((s: any) => s.id === id);

    if (index === -1) {
        return NextResponse.json({ error: "Submission not found" }, { status: 404 });
    }

    let gradedSubmission;

    if (manualGrade) {
        // Manual update from Educator Dashboard
        gradedSubmission = {
            ...submissions[index],
            status: 'graded',
            grade: manualGrade.score, // e.g. "95/100"
            feedback: manualGrade.feedback,
            thinkingProcess: manualGrade.thinkingProcess || [],
            gradedAt: new Date().toISOString()
        };
    } else {
        // Auto-grade simulation (Student Loop)
        gradedSubmission = {
            ...submissions[index],
            status: 'graded',
            grade: 'B+',
            feedback: "Good effort! The core concepts are there, but the structure needs refinement. Focus on your thesis statement clarity.",
            thinkingProcess: [
                "Analyzing submission context...",
                "Checking rubric criteria: Argument Structure",
                "Validating initial score: 87/100",
                "Generating constructive feedback..."
            ]
        };
    }

    submissions[index] = gradedSubmission;
    await saveSubmissions(submissions);

    return NextResponse.json(gradedSubmission);
}
