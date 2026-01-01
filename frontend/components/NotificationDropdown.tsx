"use client";

import { useState, useRef, useEffect } from "react";
import { Bell, Check, Clock, Info, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function NotificationDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState([
        {
            id: 1,
            title: "New Submission",
            message: "Jane Doe submitted 'Midterm Essay'",
            time: "2 min ago",
            type: "info",
            read: false,
        },
        {
            id: 2,
            title: "Grading Complete",
            message: "Batch processing for Physics 101 finished",
            time: "1 hour ago",
            type: "success",
            read: false,
        },
        {
            id: 3,
            title: "System Update",
            message: "GradeWise will be down for maintenance at 2 AM",
            time: "5 hours ago",
            type: "warning",
            read: true,
        },
    ]);

    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const unreadCount = notifications.filter((n) => !n.read).length;

    const markAsRead = (id: number) => {
        setNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n));
    };

    const markAllAsRead = () => {
        setNotifications(notifications.map(n => ({ ...n, read: true })));
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`relative p-2.5 rounded-xl border transition-all shadow-sm ${isOpen
                        ? "bg-primary text-white border-primary"
                        : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-white"
                    }`}
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-slate-800 animate-pulse"></span>
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="absolute right-0 mt-3 w-80 md:w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl z-50 overflow-hidden ring-1 ring-black/5"
                    >
                        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
                            <h3 className="font-semibold text-sm text-slate-900 dark:text-white">Notifications</h3>
                            {unreadCount > 0 && (
                                <button
                                    onClick={markAllAsRead}
                                    className="text-xs font-medium text-primary hover:text-blue-600 transition-colors"
                                >
                                    Mark all as read
                                </button>
                            )}
                        </div>

                        <div className="max-h-[400px] overflow-y-auto">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center text-slate-500">
                                    <Bell className="w-8 h-8 mx-auto mb-2 opacity-20" />
                                    <p className="text-sm">No notifications</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {notifications.map((notification) => (
                                        <div
                                            key={notification.id}
                                            className={`p-4 flex gap-3 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50 ${!notification.read ? "bg-blue-50/40 dark:bg-blue-900/10" : ""
                                                }`}
                                            onClick={() => markAsRead(notification.id)}
                                        >
                                            <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${!notification.read ? "bg-blue-500" : "bg-transparent"
                                                }`}></div>

                                            <div className="flex-1 space-y-1">
                                                <div className="flex justify-between items-start">
                                                    <p className={`text-sm font-medium ${!notification.read ? "text-slate-900 dark:text-white" : "text-slate-600 dark:text-slate-400"}`}>
                                                        {notification.title}
                                                    </p>
                                                    <span className="text-xs text-slate-400 whitespace-nowrap ml-2">{notification.time}</span>
                                                </div>
                                                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                                                    {notification.message}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="p-2 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
                            <button className="w-full py-2 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
                                View all notifications
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
