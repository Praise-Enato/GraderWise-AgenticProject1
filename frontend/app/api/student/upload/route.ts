import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    const data = await request.formData();
    const file: File | null = data.get('file') as unknown as File;

    if (!file) {
        return NextResponse.json({ success: false, message: 'No file uploaded' }, { status: 400 });
    }

    // In a real app, we would save to disk here:
    // const bytes = await file.arrayBuffer();
    // const buffer = Buffer.from(bytes);
    // await fs.writeFile(path.join(process.cwd(), 'uploads', file.name), buffer);

    // For now, we just acknowledge receipt
    return NextResponse.json({
        success: true,
        fileName: file.name,
        size: file.size
    });
}
