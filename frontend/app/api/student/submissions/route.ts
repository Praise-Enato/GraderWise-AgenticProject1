import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const DATA_FILE = path.join(process.cwd(), 'data', 'submissions.json');

// Helper to read data
async function getSubmissions() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (e) {
        return [];
    }
}

// Helper to write data
async function saveSubmissions(submissions: any[]) {
    await fs.writeFile(DATA_FILE, JSON.stringify(submissions, null, 2));
}

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const studentId = searchParams.get('studentId');
    const submissions = await getSubmissions();

    if (studentId) {
        return NextResponse.json(submissions.filter((s: any) => s.studentId === studentId));
    }

    return NextResponse.json(submissions);
}

export async function POST(request: Request) {
    const body = await request.json();
    const submissions = await getSubmissions();

    const newSubmission = {
        id: Date.now().toString(),
        title: body.title || "Untitled Submission",
        status: "pending",
        date: new Date().toLocaleDateString(), // Simple date for now
        fileName: body.fileName,
        grade: undefined,
        feedback: undefined
    };

    // Prepend to list
    const updated = [newSubmission, ...submissions];
    await saveSubmissions(updated);

    // Simulate Background Grading (mock update after 5 seconds)
    // In a real app, this would be a separate worker, but here we just leave it pending
    // and rely on a specific "grade" endpoint or user action to trigger grading.
    // For the demo flow, let's just save it as pending.

    return NextResponse.json(newSubmission);
}
