"use client";

import { useState } from "react";
import { Search, Mail, MessageCircle, FileText, ChevronDown, ChevronUp, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function SupportPage() {
    const [openFaq, setOpenFaq] = useState<number | null>(null);

    const faqs = [
        {
            id: 1,
            question: "How do I upload a new grading rubric?",
            answer: "Navigate to the Dashboard and click on 'Import Rubric' in the Quick Actions section. You can drag and drop your PDF rubric file there."
        },
        {
            id: 2,
            question: "What file formats are supported for student submissions?",
            answer: "GradeWise currently supports PDF, DOCX, and TXT files for student submissions. We are working on adding support for image based submissions soon."
        },
        {
            id: 3,
            question: "How can I change my password?",
            answer: "Go to Settings > Security. Click on 'Change Password' to update your credentials."
        },
        {
            id: 4,
            question: "Is my data secure?",
            answer: "Yes, we use bank-level encryption for all data storage and transfer. Your student data is never used to train public AI models."
        }
    ];

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            <div className="max-w-4xl mx-auto pb-20">

                {/* Header */}
                <header className="mb-10 text-center">
                    <div className="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4 text-primary">
                        <HelpCircle className="w-8 h-8" />
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">How can we help you?</h1>
                    <p className="text-slate-500 dark:text-slate-400 max-w-lg mx-auto">Search our help center or contact our support team directly.</p>

                    <div className="mt-8 relative max-w-xl mx-auto">
                        <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search for answers..."
                            className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm transition-all"
                        />
                    </div>
                </header>

                {/* Contact Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <ContactCard
                        icon={<MessageCircle className="w-6 h-6" />}
                        title="Live Chat"
                        desc="Chat with our team in real-time."
                        action="Start Chat"
                        color="bg-blue-500"
                    />
                    <ContactCard
                        icon={<Mail className="w-6 h-6" />}
                        title="Email Support"
                        desc="Get a response within 24 hours."
                        action="Send Email"
                        color="bg-indigo-500"
                    />
                    <ContactCard
                        icon={<FileText className="w-6 h-6" />}
                        title="Documentation"
                        desc="Browse detailed guides and tutorials."
                        action="View Docs"
                        color="bg-amber-500"
                    />
                </div>

                {/* FAQ Section */}
                <section className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-100 dark:border-slate-800">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Frequently Asked Questions</h2>
                    </div>
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                        {faqs.map((faq) => (
                            <div key={faq.id} className="group">
                                <button
                                    onClick={() => setOpenFaq(openFaq === faq.id ? null : faq.id)}
                                    className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                                >
                                    <span className="font-medium text-slate-900 dark:text-slate-200 group-hover:text-primary transition-colors">{faq.question}</span>
                                    {openFaq === faq.id ? (
                                        <ChevronUp className="w-5 h-5 text-slate-400" />
                                    ) : (
                                        <ChevronDown className="w-5 h-5 text-slate-400" />
                                    )}
                                </button>
                                <AnimatePresence>
                                    {openFaq === faq.id && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="px-6 pb-5 pt-0 text-slate-600 dark:text-slate-400 leading-relaxed text-sm">
                                                {faq.answer}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        ))}
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 text-center">
                        <p className="text-sm text-slate-500 dark:text-slate-400">Still have questions? <a href="#" className="text-primary font-medium hover:underline">Contact us</a></p>
                    </div>
                </section>

            </div>
        </div>
    );
}

function ContactCard({ icon, title, desc, action, color }: any) {
    return (
        <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 p-6 rounded-xl shadow-sm hover:shadow-md transition-all group text-center">
            <div className={`w-12 h-12 mx-auto rounded-xl ${color} flex items-center justify-center text-white mb-4 shadow-lg shadow-blue-500/20 group-hover:scale-110 transition-transform`}>
                {icon}
            </div>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-1">{title}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{desc}</p>
            <button className="text-sm font-medium text-primary hover:text-blue-700 transition-colors flex items-center justify-center gap-1 mx-auto">
                {action} <ArrowRightSmall />
            </button>
        </div>
    )
}

function ArrowRightSmall() {
    return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
    )
}
