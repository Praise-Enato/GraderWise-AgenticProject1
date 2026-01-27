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
    try {
        const body = await request.json();
        const { id, manualGrade } = body;
        
        if (!id || !manualGrade) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        const submissions = await getSubmissions();
        const index = submissions.findIndex((s: any) => s.id === id);

        if (index === -1) {
             return NextResponse.json({ error: "Submission not found" }, { status: 404 });
        }

        // Update the submission
        submissions[index].grade = manualGrade.score;
        submissions[index].feedback = manualGrade.feedback;
        submissions[index].thinkingProcess = manualGrade.thinkingProcess;
        submissions[index].status = 'graded';
        submissions[index].gradedAt = new Date().toISOString();

        await saveSubmissions(submissions);

        return NextResponse.json({ success: true, submission: submissions[index] });

    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}
