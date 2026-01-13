import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

async function main() {
    // Create Student
    const student = await prisma.user.upsert({
        where: { email: 'student@example.com' },
        update: {},
        create: {
            email: 'student@example.com',
            firstName: 'Student',
            lastName: 'User',
            password: 'password123',
            role: 'STUDENT'
        },
    })

    console.log({ student })

    // Create Assignment
    const assignment = await prisma.assignment.create({
        data: {
            title: 'History Essay - Causes of WWI',
            description: 'Analyze the major geopolitical causes.',
            dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 1 week
        }
    })

    console.log({ assignment })
}

main()
    .then(async () => {
        await prisma.$disconnect()
    })
    .catch(async (e) => {
        console.error(e)
        await prisma.$disconnect()
        process.exit(1)
    })
