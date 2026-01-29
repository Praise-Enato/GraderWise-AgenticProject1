import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

const DATA_FILE = path.join(process.cwd(), 'data', 'submissions.json');

// Helper to read data
async function getSubmissions() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (e) {
        // Create file if not exists
        try {
             await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
             await fs.writeFile(DATA_FILE, '[]', 'utf8');
             return [];
        } catch (mkErr) {
             return [];
        }
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
        // Filter by studentId if provided (though studentId might be legacy concept)
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
        date: new Date().toLocaleDateString(),
        fileName: body.fileName,
        content: body.content || "",
        grade: undefined,
        feedback: undefined
    };

    // Prepend to list
    const updated = [newSubmission, ...submissions];
    await saveSubmissions(updated);

    return NextResponse.json(newSubmission);
}

export async function DELETE(request: Request) {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    
    if (id) {
        // Delete specific submission
        const submissions = await getSubmissions();
        const updated = submissions.filter((s: any) => s.id !== id);
        await saveSubmissions(updated);
        return NextResponse.json({ message: "Deleted submission" });
    } else {
        // Clear all
        await saveSubmissions([]);
        return NextResponse.json({ message: "Cleared all submissions" });
    }
}
