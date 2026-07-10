import { Fraunces, Plus_Jakarta_Sans } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

// Display: Fraunces — a confident editorial serif with warmth, fitting an
// awards/judging product. Body/UI: Plus Jakarta Sans — modern, friendly, precise.
const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  axes: ["opsz"],
});
const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

export const metadata = {
  metadataBase: new URL('https://gradewise.cfd'),
  title: 'GradeWise | The AI judge for business-plan competitions',
  description: 'GradeWise screens, scores, and ranks a whole field of business plans against your rubric — every point cited to the plan, graded multiple times for a real confidence, and calibrated against your human judges.',
  openGraph: {
    title: 'GradeWise | The AI judge for business-plan competitions',
    description: 'Screen hundreds of plans, cite every point to the plan, and rank a defensible shortlist — calibrated against your human judges.',
    url: 'https://gradewise.cfd',
    siteName: 'GradeWise',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'GradeWise Preview' }],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'GradeWise | The AI judge for business-plan competitions',
    description: 'Screen hundreds of plans, cite every point to the plan, and rank a defensible shortlist.',
    images: ['/og-image.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${display.variable} ${sans.variable}`}>
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
