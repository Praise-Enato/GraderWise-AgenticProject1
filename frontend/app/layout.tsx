
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

export const metadata = {
  title: 'GradeWise',
  description: 'Intelligent Grading Agent',
  openGraph: {
    title: 'GradeWise',
    description: 'Intelligent Grading Agent',
    url: 'https://gradewise.cfd',
    siteName: 'GradeWise',
    images: [
      {
        url: 'https://gradewise.cfd/og-image.png', // Must be an absolute URL
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'GradeWise',
    description: 'Intelligent Grading Agent',
    images: ['https://gradewise.cfd/og-image.png'],
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
