const { execSync } = require('child_process');
const path = require('path');

// Set the environment variable explicitly for this process and children
process.env.DATABASE_URL = "file:./dev.db";

console.log('Running prisma db push with DATABASE_URL="file:./dev.db"...');

try {
    execSync('npx prisma db push', {
        stdio: 'inherit',
        cwd: __dirname
    });
    console.log('Database push successful.');

    console.log('Generating client...');
    execSync('npx prisma generate', {
        stdio: 'inherit',
        cwd: __dirname
    });
    console.log('Client generation successful.');

} catch (error) {
    console.error('Migration failed:', error);
    process.exit(1);
}
