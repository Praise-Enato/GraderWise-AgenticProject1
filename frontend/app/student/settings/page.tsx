"use client";

import { useState } from "react";
import { Settings, User, Bell, Lock, Save, Moon, Sun, Monitor } from "lucide-react";
import { motion } from "framer-motion";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'security'>('profile');
    const [darkMode, setDarkMode] = useState('system');

    return (
        <div className="max-w-5xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                    <Settings className="w-8 h-8 text-indigo-500" />
                    Account Settings
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Manage your profile, preferences, and security.</p>
            </div>

            <div className="grid md:grid-cols-[240px_1fr] gap-8">
                {/* Sidebar */}
                <div className="space-y-2">
                    {[
                        { id: 'profile', label: 'My Profile', icon: User },
                        { id: 'notifications', label: 'Notifications', icon: Bell },
                        { id: 'security', label: 'Security', icon: Lock },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id as any)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${activeTab === item.id
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            <item.icon className="w-4 h-4" />
                            {item.label}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-8 min-h-[500px]">
                    {activeTab === 'profile' && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-4">Profile Information</h2>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">First Name</label>
                                    <input type="text" defaultValue="Alex" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Last Name</label>
                                    <input type="text" defaultValue="Rivera" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                </div>
                                <div className="space-y-2 col-span-2">
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Email Address</label>
                                    <input type="email" defaultValue="alex.rivera@student.edu" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                </div>
                                <div className="space-y-2 col-span-2">
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Bio</label>
                                    <textarea rows={4} defaultValue="Computer Science major interested in AI and Machine Learning." className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                </div>
                            </div>

                            <div className="pt-4 flex justify-end">
                                <button className="px-6 py-2 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2">
                                    <Save className="w-4 h-4" /> Save Changes
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'notifications' && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-4">Notification Preferences</h2>

                            <div className="space-y-4">
                                {[
                                    { label: "Email me when an assignment is graded", default: true },
                                    { label: "Email me when feedback is updated", default: true },
                                    { label: "Weekly digest of upcoming deadlines", default: false },
                                    { label: "New course announcements", default: true }
                                ].map((setting, i) => (
                                    <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <span className="text-slate-700 dark:text-slate-300 font-medium">{setting.label}</span>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" defaultChecked={setting.default} className="sr-only peer" />
                                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'security' && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-4">Security</h2>

                            <div className="space-y-6">
                                <div className="space-y-4">
                                    <h3 className="font-semibold text-slate-900 dark:text-white">Change Password</h3>
                                    <div className="grid gap-4 max-w-md">
                                        <input type="password" placeholder="Current Password" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 outline-none" />
                                        <input type="password" placeholder="New Password" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 outline-none" />
                                        <input type="password" placeholder="Confirm New Password" className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 outline-none" />
                                        <button className="w-full py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-medium">Update Password</button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>
        </div>
    );
}
