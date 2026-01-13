"use client"

import React, { useState, useRef, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Paperclip, Bot, User, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react"

// --- TYPES ---
interface RubricItem {
    criteria: string
    max_points: number
    description: string
}

interface Course {
    id: string
    name: string
    rubric: RubricItem[]
}

interface Message {
    id: string
    role: "user" | "assistant"
    content: string
    isError?: boolean
}

// --- MOCK DATA ---
const COURSES: Course[] = [
    {
        id: "CS101",
        name: "CS101: Intro to Python",
        rubric: [
            { criteria: "Functionality", max_points: 10, description: "Code must run and produce correct output." },
            { criteria: "Logic", max_points: 10, description: "Algorithm is efficient and solves the problem." },
            { criteria: "Style", max_points: 5, description: "Follows PEP8 and clean coding practices." }
        ]
    },
    {
        id: "ENG101",
        name: "ENG101: Creative Writing",
        rubric: [
            { criteria: "Thesis", max_points: 20, description: "Clear and arguable thesis statement." },
            { criteria: "Evidence", max_points: 20, description: "Cites sources effectively." },
            { criteria: "Grammar", max_points: 10, description: "Proper grammar and spelling." }
        ]
    }
]

export default function StudentPortal() {
    // --- STATE ---
    const [messages, setMessages] = useState<Message[]>([
        { 
            id: "welcome", 
            role: "assistant", 
            content: "Welcome to GradeWise! 🎓\n\nI can help you grade your assignments and answer questions about your feedback.\n\nTo start, please **tell me which course** you are submitting work for? (e.g., `CS101`, `ENG101`)" 
        }
    ])
    const [input, setInput] = useState("")
    const [isTyping, setIsTyping] = useState(false)
    
    // Conversation State Machine
    const [chatStage, setChatStage] = useState<"SELECT_COURSE" | "SUBMIT_WORK" | "Q_AND_A">("SELECT_COURSE")
    const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
    const [gradeData, setGradeData] = useState<any>(null)
    
    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages, isTyping])

    // --- HELPERS ---
    const addMessage = (role: "user" | "assistant", content: string, isError = false) => {
        setMessages(prev => [...prev, { id: Date.now().toString(), role, content, isError }])
    }

    // --- LOGIC: HANDLE SEND ---
    const handleSend = async (textOverride?: string) => {
        const text = textOverride || input
        if (!text.trim()) return

        // 1. Add User Message
        // Avoid adding duplicate message if textOverride is used (e.g. file upload text)
        if (!textOverride) {
            addMessage("user", text)
            setInput("")
        } else {
             // For file uploads, we might want to show a specific message
             // But usually handleFileUpload calls this with the extracted text, 
             // so we should probably add a "Uploaded file..." message visually before calling this?
             // Let's rely on handleFile doing the UI update for the file.
        }

        setIsTyping(true)

        try {
            // --- STAGE 1: COURSE SELECTION ---
            if (chatStage === "SELECT_COURSE") {
                // Allow dynamic course selection
                const courseName = text.trim()
                
                // We create a temporary course object. 
                // The Rubric will be fetched by the backend dynamically.
                const tempCourse: Course = {
                    id: courseName,
                    name: courseName,
                    rubric: [] // Empty, backend will resolve
                }
                
                setSelectedCourse(tempCourse)
                setChatStage("SUBMIT_WORK")
                
                setTimeout(() => {
                    addMessage("assistant", `Selected **${courseName}**. \n\nChecking for course materials... If available, you can **upload your file** or **paste your work** below.`)
                    setIsTyping(false)
                }, 600)
                
                return
            }

            // --- STAGE 2 & 3: SUBMISSION & Q/A ---
            // Ideally we differentiate, but the API `/grade` handles it nicely if we manage `gradeData` state correctly.
            // However, we want to enforce the flow.

            const payload = {
                submission_text: text, 
                rubric: null, // Let backend find it
                course_name: selectedCourse?.name,
                student_id: "student_123",
                messages: messages.map(m => ({ role: m.role, content: m.content })), 
                grade_data: gradeData 
            }

            console.log("Sending payload:", payload)

            const res = await fetch("http://localhost:8000/grade", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })

            if (!res.ok) throw new Error(`API Error: ${res.statusText}`)
            const data = await res.json()

            // Detect Switch to Q&A
            if (chatStage === "SUBMIT_WORK" && data.grade_data && data.grade_data.score > 0) {
                setGradeData(data.grade_data)
                setChatStage("Q_AND_A")
                
                // Update rubric from backend for correct score display
                if (data.rubric && data.rubric.length > 0) {
                     setSelectedCourse(prev => prev ? { ...prev, rubric: data.rubric } : null)
                }
            }

            const botReply = data.final_feedback || "I processed your request."
            addMessage("assistant", botReply)

        } catch (error) {
            console.error(error)
            addMessage("assistant", "⚠️ Sorry, I'm having trouble connecting to the Grading Agent. Please define DEEPSEEK_API_KEY if trying to grade.", true)
        } finally {
            setIsTyping(false)
        }
    }

    // --- LOGIC: FILE UPLOAD ---
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        // UI: Show user uploaded a file
        addMessage("user", `📎 Uploaded: ${file.name}`)
        setIsTyping(true)

        try {
            const formData = new FormData()
            formData.append("file", file)

            // 1. Extract Text
            const res = await fetch("http://localhost:8000/extract-text", {
                method: "POST",
                body: formData
            })
            
            if (!res.ok) throw new Error("Failed to extract text")
            const data = await res.json()
            const extractedText = data.text

            // 2. Process as Submission (or Context)
            if (chatStage === "SELECT_COURSE") {
                 addMessage("assistant", "Please select a course first before uploading work.", true)
                 setIsTyping(false)
                 return
            }

            // Treat extracted text as the input for the next step
            await handleSend(extractedText)

        } catch (err) {
            console.error(err)
            addMessage("assistant", "⚠️ Error reading file. Please make sure it is a valid text, PDF, or Docx file.", true)
            setIsTyping(false)
        } finally {
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = ""
        }
    }

    // --- RENDER ---
    return (
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-slate-900 text-gray-900 dark:text-gray-100 font-sans">
            {/* HEADER */}
            <header className="px-6 py-4 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between shadow-sm z-10">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-indigo-600 rounded-lg">
                        <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">
                            GradeWise Tutor
                        </h1>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                            {selectedCourse ? `Current Course: ${selectedCourse.name}` : "Select a course to begin"}
                        </p>
                    </div>
                </div>
                {/* Score Badge */}
                <AnimatePresence>
                    {gradeData && (
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex items-center space-x-2 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 px-4 py-2 rounded-full"
                        >
                            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                            <div className="flex flex-col items-end">
                                <span className="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold tracking-wider">Score</span>
                                <span className="text-lg font-bold text-green-700 dark:text-green-300">
                                    {gradeData.score} <span className="text-sm font-normal text-gray-400">/ {selectedCourse?.rubric.reduce((a,b)=>a+b.max_points,0)}</span>
                                </span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </header>

            {/* CHAT AREA */}
            <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50 dark:bg-slate-950">
                <div className="max-w-3xl mx-auto space-y-6">
                    {messages.map((msg) => (
                        <motion.div 
                            key={msg.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`flex items-start max-w-[85%] sm:max-w-[75%] space-x-3 ${msg.role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"}`}>
                                
                                {/* Avatar */}
                                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm mt-1 ${
                                    msg.role === "user" 
                                    ? "bg-indigo-600" 
                                    : "bg-white dark:bg-slate-700 border border-gray-100 dark:border-slate-600"
                                }`}>
                                    {msg.role === "user" 
                                        ? <User className="w-5 h-5 text-white" /> 
                                        : <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                                    }
                                </div>

                                {/* Bubble */}
                                <div className={`p-4 rounded-2xl shadow-sm text-sm sm:text-base leading-relaxed ${
                                    msg.role === "user" 
                                    ? "bg-indigo-600 text-white rounded-tr-none" 
                                    : "bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 text-gray-800 dark:text-slate-200 rounded-tl-none"
                                } ${msg.isError ? "border-red-200 bg-red-50 dark:bg-red-900/10 dark:border-red-900" : ""}`}>
                                    <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}

                    {isTyping && (
                        <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }} 
                            className="flex justify-start items-center space-x-3"
                        >
                            <div className="w-8 h-8 rounded-full bg-white dark:bg-slate-800 flex items-center justify-center">
                                <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                            </div>
                            <span className="text-gray-400 text-sm">Thinking...</span>
                        </motion.div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* INPUT AREA */}
            <div className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 p-4">
                <div className="max-w-3xl mx-auto flex items-end space-x-3">
                    
                    {/* File Upload Button */}
                    <button 
                        onClick={() => fileInputRef.current?.click()}
                        className="p-3 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex-shrink-0"
                        title="Upload Assignment"
                        disabled={chatStage === "SELECT_COURSE"}
                    >
                        <Paperclip className="w-5 h-5" />
                    </button>
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="hidden" 
                        accept=".txt,.md,.py,.js,.pdf,.docx" 
                        onChange={handleFileSelect}
                    />

                    {/* Text Input */}
                    <div className="flex-1 bg-gray-50 dark:bg-slate-900 rounded-2xl border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-transparent transition-all">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault()
                                    handleSend()
                                }
                            }}
                            placeholder={
                                chatStage === "SELECT_COURSE" ? "Type 'CS101' or 'ENG101'..." :
                                chatStage === "SUBMIT_WORK" ? "Paste your work here or upload a file..." :
                                "Ask a question about your feedback..."
                            }
                            className="w-full bg-transparent p-3 max-h-32 min-h-[50px] resize-none focus:outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
                            rows={1}
                        />
                    </div>

                    {/* Send Button */}
                    <button 
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isTyping}
                        className={`p-3 rounded-full flex-shrink-0 transition-all ${
                            !input.trim() 
                            ? "bg-gray-200 dark:bg-slate-700 text-gray-400 cursor-not-allowed" 
                            : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                        }`}
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                <div className="max-w-3xl mx-auto mt-2 text-center text-xs text-gray-400">
                    <p>AI can make mistakes. Please verify important information.</p>
                </div>
            </div>
        </div>
    )
}
