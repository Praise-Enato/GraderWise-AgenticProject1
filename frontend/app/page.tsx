"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle, GraduationCap, LayoutDashboard, Shield, Zap, BookOpen, Users, Brain } from "lucide-react";
import { motion } from "framer-motion";
import { ModeToggle } from "@/components/ModeToggle";
import { Logo } from "@/components/Logo";
import { RubricParserDemo } from "@/components/landing/RubricParserDemo";
import { InfoTooltip } from "@/components/InfoTooltip";
import { FileCode, FileSpreadsheet, FileText } from "lucide-react"; // Import new icons for Hero

export default function LandingPage() {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Grading Agent",
      description: "Our RAG-based agent analyzes student submissions against your rubrics with human-like reasoning."
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Student data is processed locally or via secure enterprise APIs. Your data never trains public models."
    },
    {
      icon: LayoutDashboard,
      title: "Professional Dashboard",
      description: "A split-screen interface designed for educators. Review, edit, and approve grades in seconds."
    },
    {
      icon: BookOpen,
      title: "Context-Aware",
      description: "Upload your textbooks and lecture notes. GradeWise benchmarks answers against your specific course material."
    }
  ];

  const stats = [
    { label: "Grading Time Saved", value: "90%" },
    { label: "Feedback Accuracy", value: "99.9%" },
    { label: "Active Educators", value: "500+" },
    { label: "Essays Graded", value: "10k+" }
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 transition-colors duration-500">
      {/* Navigation */}
      <nav className="fixed w-full z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-100 dark:border-white/10 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Logo className="w-10 h-10" />
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600 dark:text-slate-300">
            <a href="#features" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">How it Works</a>
          </div>
          <div className="flex items-center gap-4">
            <ModeToggle />
            <Link href="/signup" className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
              Log in
            </Link>
            <Link href="/signup" className="px-5 py-2.5 text-white text-sm font-medium rounded-full shadow-lg shadow-blue-600/20 hover:shadow-blue-600/30 transition-all bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:via-indigo-700 hover:to-violet-700">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 overflow-hidden relative bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-white to-white dark:from-slate-900 dark:via-slate-950 dark:to-slate-950 transition-colors">
        {/* Moving Training Animation Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            animate={{
              backgroundPosition: ["0% 0%", "100% 100%"],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              repeatType: "reverse"
            }}
            className="absolute -top-[50%] -left-[50%] w-[200%] h-[200%] bg-[radial-gradient(circle_at_center,_rgba(99,102,241,0.1)_0%,_transparent_50%)] dark:bg-[radial-gradient(circle_at_center,_rgba(99,102,241,0.05)_0%,_transparent_50%)]"
          />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50/50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 text-blue-600 dark:text-blue-400 text-xs font-semibold uppercase tracking-wider mb-6"
            >
              <span className="flex h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-400 animate-pulse"></span>
              v2.4 Intelligent Grading Agent
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-7xl font-bold text-slate-900 dark:text-white tracking-tight mb-8"
            >
              Intelligent Grading for <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 animate-gradient-x">Modern Educators</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-xl text-slate-600 dark:text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed"
            >
              GradeWise is an enterprise-grade agentic AI that revolutionizes assessment.
              It ingests your course materials, learns your rubrics, and provides personalized, accurate feedback in seconds.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Link href="/signup" className="w-full sm:w-auto px-8 py-4 text-white font-semibold rounded-full shadow-xl shadow-blue-600/20 hover:shadow-blue-600/30 transition-all flex items-center justify-center gap-2 group bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:via-indigo-700 hover:to-violet-700">
                Try Grading Agent
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform animate-bounce" />
              </Link>
              <a href="https://notebooklm.google.com/" target="_blank" rel="noopener noreferrer" className="w-full sm:w-auto px-8 py-4 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 font-semibold rounded-full border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 transition-all flex items-center justify-center gap-2">
                View NotebookLLM Demo
              </a>
            </motion.div>

            <div className="mt-12 flex items-center justify-center gap-6 text-sm text-slate-500 dark:text-slate-500">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Open Source Logic</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Bring Your Own Keys</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white dark:bg-slate-950 border-y border-slate-100 dark:border-white/5 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { label: "AI Model", value: "DeepSeek V3", tooltip: "State-of-the-art coding and reasoning model." },
              { label: "Architecture", value: "RAG + LangGraph", tooltip: "Retrieval Augmented Generation with agentic workflow control." },
              { label: "Infra", value: "Secure Cloud" },
              { label: "Target Latency", value: "< 2s/Essay" }
            ].map((stat, i) => (
              <div key={i} className="text-center group cursor-default">
                <div className="flex items-center gap-2 justify-center">
                  <span className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-blue-800 to-slate-700 dark:from-white dark:via-blue-200 dark:to-slate-300 group-hover:from-blue-600 group-hover:via-indigo-600 group-hover:to-violet-600 transition-all duration-300">
                    {stat.value}
                  </span>
                  {stat.tooltip && <InfoTooltip content={stat.tooltip} side="bottom" />}
                </div>
                <div className="text-sm font-medium text-slate-500 dark:text-slate-500 uppercase tracking-wide mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 bg-slate-50/50 dark:bg-slate-900/50 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Everything You Need to Scale</h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">Powerful tools built specifically for high-volume grading environments.</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { ...features[0], gradient: "from-blue-50 to-indigo-50 border-blue-100 dark:from-blue-900/20 dark:to-indigo-900/20 dark:border-blue-800" },
              { ...features[1], gradient: "from-indigo-50 to-purple-50 border-indigo-100 dark:from-indigo-900/20 dark:to-purple-900/20 dark:border-indigo-800" },
              { ...features[2], gradient: "from-purple-50 to-pink-50 border-purple-100 dark:from-purple-900/20 dark:to-pink-900/20 dark:border-purple-800" },
              { ...features[3], gradient: "from-emerald-50 to-teal-50 border-emerald-100 dark:from-emerald-900/20 dark:to-teal-900/20 dark:border-emerald-800" }
            ].map((feature, i) => (
              <div key={i} className={`p-8 rounded-2xl border ${feature.gradient} bg-gradient-to-br hover:shadow-xl hover:shadow-slate-200/50 dark:hover:shadow-indigo-900/20 transition-all group relative overflow-hidden`}>
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform bg-gradient-to-br from-blue-500 via-indigo-500 to-violet-600 shadow-lg shadow-blue-500/20">
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{feature.title}</h3>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Demo Section - NEW */}
      <RubricParserDemo />

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 bg-white dark:bg-slate-950 border-y border-slate-200 dark:border-white/5 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">How GradeWise Works</h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">From upload to feedback in three simple steps.</p>
          </div>

          <div className="relative">
            {/* Connector Line */}
            <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-slate-200 via-blue-200 to-slate-200 dark:from-slate-800 dark:via-indigo-900 dark:to-slate-800 -translate-y-1/2 hidden md:block z-0"></div>

            <div className="grid md:grid-cols-3 gap-12 relative z-10">
              {[
                {
                  step: "01",
                  title: "Ingest Context",
                  desc: "Upload rubrics, textbooks, and lecture notes. The AI indexes your materials for factual grounding.",
                  icon: BookOpen
                },
                {
                  step: "02",
                  title: "Agentic Analysis",
                  desc: "The AI Grader reads student work, cross-references your materials, and applies the rubric line-by-line.",
                  icon: Brain
                },
                {
                  step: "03",
                  title: "Review & Export",
                  desc: "Receive a fully drafted feedback report. Approve with one click or edit as needed, then sync to your gradebook.",
                  icon: CheckCircle
                }
              ].map((item, i) => (
                <div key={i} className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm text-center relative group hover:border-blue-300 dark:hover:border-indigo-700 transition-colors">
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-lg shadow-blue-600/20 group-hover:scale-110 transition-transform bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-600 text-white">
                    <item.icon className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                  <p className="text-slate-500 dark:text-slate-400 leading-relaxed">{item.desc}</p>
                  <span className="absolute -top-4 -right-4 text-6xl font-black text-slate-100 dark:text-slate-800 group-hover:text-blue-50 dark:group-hover:text-indigo-900/20 transition-colors -z-10">{item.step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section (Replaces Testimonials) */}
      <section className="py-24 bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 dark:from-indigo-950 dark:via-purple-950 dark:to-slate-950 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-2">Built for Academia</h2>
            <p className="text-indigo-100 dark:text-indigo-200 mt-2">Designed to support every role in the grading workflow.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                role: "University Professors",
                desc: "Focus on research and lectures while GradeWise handles the grading of hundreds of weekly assignments.",
                tags: ["Scale", "Consistency"],
                gradient: "from-blue-100 to-indigo-100 border-blue-200 dark:from-blue-900/40 dark:to-indigo-900/40 dark:border-indigo-700"
              },
              {
                role: "Teaching Assistants",
                desc: "Ensure grading consistency across multiple TAs. Use GradeWise as a 'first pass' to standardize feedback.",
                tags: ["Fairness", "Speed"],
                gradient: "from-violet-100 to-purple-100 border-violet-200 dark:from-violet-900/40 dark:to-purple-900/40 dark:border-violet-700"
              },
              {
                role: "Dept. Heads",
                desc: "Maintain rigorous academic standards with localized privacy. No data leaves your institution's control.",
                tags: ["Privacy", "Standards"],
                gradient: "from-fuchsia-100 to-pink-100 border-fuchsia-200 dark:from-fuchsia-900/40 dark:to-pink-900/40 dark:border-fuchsia-700"
              }
            ].map((t, i) => (
              <div key={i} className={`p-8 rounded-2xl border ${t.gradient} bg-gradient-to-br hover:shadow-2xl hover:shadow-black/20 hover:-translate-y-1 transition-all group`}>
                <div className="flex gap-2 mb-6">
                  {t.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 rounded bg-white/60 dark:bg-black/40 text-indigo-950 dark:text-indigo-100 text-xs font-semibold shadow-sm backdrop-blur-sm">{tag}</span>
                  ))}
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3 group-hover:text-indigo-800 dark:group-hover:text-indigo-300 transition-colors">{t.role}</h3>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed">{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-white/10 pt-16 pb-8 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <Logo className="w-8 h-8" textClassName="text-xl font-bold text-slate-900 dark:text-white ml-2" />
              </div>
              <p className="text-slate-500 dark:text-slate-400 max-w-sm">Empowering educators with AI-powered tools to automate admin tasks, track student progress, and focus on inspiring the next generation.</p>
            </div>
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white mb-4">Features</h4>
              <ul className="space-y-2 text-slate-500 dark:text-slate-400 text-sm">
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Student Portal</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Teacher Dashboard</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">AI Grading</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Analytics</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white mb-4">Company</h4>
              <ul className="space-y-2 text-slate-500 dark:text-slate-400 text-sm">
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">About Us</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Careers</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-200 dark:border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between text-sm text-slate-400">
            <p>© 2026 GradeWise. All rights reserved.</p>
            <p>Designed for Modern Education</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
