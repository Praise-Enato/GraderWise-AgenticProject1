import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const DATA_FILE = path.join(process.cwd(), 'data', 'submissions.json');
const PYTHON_API = 'http://127.0.0.1:8000';

// Mock Rubric for Auto-Grading (In real app, fetch from DB or request)
const GLOBAL_RUBRIC = [
    { criteria: "Thesis & Argument", max_points: 30, description: "Clear, arguable thesis supported by evidence." },
    { criteria: "Evidence & Analysis", max_points: 40, description: "Strong use of sources and deep analysis." },
    { criteria: "Structure & Clarity", max_points: 30, description: "Logical flow and professional tone." }
];

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
        const submissions = await getSubmissions();
        const pending = submissions.filter((s: any) => s.status === 'pending');

        if (pending.length === 0) {
            return NextResponse.json({ message: "No pending submissions to grade.", count: 0 });
        }

        const results = [];

        // Process sequentially to avoid overwhelming the local Python backend
        for (const sub of pending) {
            // 1. Prepare payload for Python Agent
            const payload = {
                submission_text: "Mock text for " + sub.title, // Ideally read actual file content
                student_id: sub.studentId || "unknown",
                rubric: GLOBAL_RUBRIC
            };

            // If file exists on disk, we should read it, but for this demo we'll use placeholder text 
            // OR if the python backend has `extract-text` we could call that first.
            // For robustness in this demo step, let's use a generic text if we can't read the file.

            try {
                const gradeRes = await fetch(`${PYTHON_API}/grade`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!gradeRes.ok) {
                    throw new Error(`Python backend error: ${gradeRes.statusText}`);
                }

                const gradeData = await gradeRes.json();

                // 2. Update Submission Record
                sub.status = 'graded';
                sub.grade = `${gradeData.score} / 100`; // Assuming 100 total
                sub.feedback = gradeData.feedback;
                sub.thinkingProcess = gradeData.thinking_process;
                sub.gradedAt = new Date().toISOString();

                results.push({ id: sub.id, status: 'success' });

            } catch (err) {
                console.error(`Failed to grade ${sub.id}:`, err);
                results.push({ id: sub.id, status: 'error', error: String(err) });
            }
        }

        // Save updates
        await saveSubmissions(submissions);

        return NextResponse.json({
            message: `Batch processing complete. Graded ${results.filter(r => r.status === 'success').length} submissions.`,
            results
        });

    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}
