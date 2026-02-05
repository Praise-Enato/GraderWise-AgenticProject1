
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

export const metadata = {
  metadataBase: new URL('https://gradewise.cfd'),
  title: 'GradeWise | AI Grading Agent for Modern Educators',
  description: 'GradeWise is an intelligent AI grading agent that delivers accurate, fast, and consistent feedback for student assignments. Join the future of education today.',
  openGraph: {
    title: 'GradeWise | AI Grading Agent for Modern Educators',
    description: 'GradeWise is an intelligent AI grading agent that delivers accurate, fast, and consistent feedback for student assignments. Join the future of education today.',
    url: 'https://gradewise.cfd',
    siteName: 'GradeWise',
    images: [
      {
        url: '/og-image.png', // Relative path to be resolved by metadataBase
        width: 1200,
        height: 630,
        alt: 'GradeWise Preview',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'GradeWise | AI Grading Agent for Modern Educators',
    description: 'GradeWise is an intelligent AI grading agent that delivers accurate, fast, and consistent feedback for student assignments. Join the future of education today.',
    images: ['/og-image.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground" suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
