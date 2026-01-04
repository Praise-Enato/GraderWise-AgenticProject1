"use client";

import { useState, useEffect } from "react";
import { User, Users, Bell, Lock, Globe, Save, Smartphone, Shield, LogOut, Moon, Sun, Monitor, GraduationCap } from "lucide-react";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState("profile");

    const tabs = [
        { id: "profile", label: "Profile", icon: User },
        { id: "education", label: "Education", icon: GraduationCap },
        { id: "notifications", label: "Notifications", icon: Bell },
        { id: "security", label: "Security", icon: Lock },
        { id: "preferences", label: "Preferences", icon: Globe },
    ];

    return (
        <div className="h-screen overflow-y-auto bg-slate-50 dark:bg-background p-8 transition-colors duration-300">
            <div className="max-w-4xl mx-auto pb-20">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Settings</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your account settings and preferences.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
                    {/* Sidebar Navigation */}
                    <div className="md:col-span-3">
                        <nav className="flex flex-col space-y-1 sticky top-8">
                            {tabs.map((tab) => {
                                const Icon = tab.icon;
                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                                            ? "bg-primary text-white shadow-md shadow-primary/25"
                                            : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                            }`}
                                    >
                                        <Icon className="w-4 h-4" />
                                        {tab.label}
                                    </button>
                                );
                            })}
                        </nav>
                    </div>

                    {/* Main Content Area */}
                    <div className="md:col-span-9">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2 }}
                            className="bg-white dark:bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden"
                        >
                            {activeTab === "profile" && <ProfileSettings />}
                            {activeTab === "education" && <EducationSettings />}
                            {activeTab === "notifications" && <NotificationSettings />}
                            {activeTab === "security" && <SecuritySettings />}
                            {activeTab === "preferences" && <PreferenceSettings />}
                        </motion.div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function EducationSettings() {
    const [settings, setSettings] = useState({
        persona: 'Standard',
        requireRubric: true,
        gradeScale: 'Percentage (0-100)'
    });

    useEffect(() => {
        const stored = localStorage.getItem('educationSettings');
        if (stored) setSettings(JSON.parse(stored));
    }, []);

    const handleSave = () => {
        localStorage.setItem('educationSettings', JSON.stringify(settings));
        alert('Education settings saved!');
    };

    return (
        <div className="p-8 space-y-8">
            <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">AI Grader Persona</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {['Standard', 'Strict', 'Encouraging'].map((persona) => (
                        <button
                            key={persona}
                            onClick={() => setSettings({ ...settings, persona })}
                            className={`p-4 rounded-xl border text-left transition-all ${settings.persona === persona ? 'border-primary bg-blue-50/50 dark:bg-blue-900/20 ring-1 ring-primary' : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'}`}
                        >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-3 ${settings.persona === persona ? 'bg-primary text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                                <Users className="w-4 h-4" />
                            </div>
                            <p className="font-medium text-slate-900 dark:text-white">{persona}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                {persona === 'Standard' && "Balanced feedback focusing on accuracy."}
                                {persona === 'Strict' && "High scrutiny on technical details."}
                                {persona === 'Encouraging' && "Focus on growth and positive reinforcement."}
                            </p>
                        </button>
                    ))}
                </div>
            </div>

            <div className="pt-8 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Grading Standards</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div>
                            <p className="font-medium text-slate-900 dark:text-white">Require Rubric</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">All assessments must have a rubric attached</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                checked={settings.requireRubric}
                                onChange={(e) => setSettings({ ...settings, requireRubric: e.target.checked })}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/10 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div>
                            <p className="font-medium text-slate-900 dark:text-white">Grade Scale</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Default scale for new jobs</p>
                        </div>
                        <select
                            value={settings.gradeScale}
                            onChange={(e) => setSettings({ ...settings, gradeScale: e.target.value })}
                            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-sm font-medium"
                        >
                            <option>Percentage (0-100)</option>
                            <option>Points (x/Total)</option>
                            <option>Letter Grade (A-F)</option>
                        </select>
                    </div>
                </div>
            </div>
            <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-6 py-2.5 rounded-lg hover:opacity-90 transition-opacity font-medium"
                >
                    <Save className="w-4 h-4" /> Save Education Settings
                </button>
            </div>
        </div>
    );
}

function ProfileSettings() {
    const [profile, setProfile] = useState({ firstName: "Wilson", lastName: "Admin", email: "wilson@gradewise.ai" });

    const handleSave = () => {
        localStorage.setItem('userProfile', JSON.stringify(profile));
        // Force reload to update sidebar or dispatch event (Reload is simpler for MVP)
        window.location.reload();
    };

    return (
        <div className="p-8 space-y-8">
            <div className="flex items-center gap-6 pb-8 border-b border-slate-100 dark:border-slate-800">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-blue-500/20">
                    {profile.firstName[0]}{profile.lastName[0]}
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Profile Picture</h3>
                    <div className="flex gap-3 mt-2">
                        <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">Change</button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-900 dark:text-slate-200">First Name</label>
                    <input
                        type="text"
                        value={profile.firstName}
                        onChange={(e) => setProfile({ ...profile, firstName: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-900 dark:text-slate-200">Last Name</label>
                    <input
                        type="text"
                        value={profile.lastName}
                        onChange={(e) => setProfile({ ...profile, lastName: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    />
                </div>
                <div className="md:col-span-2 space-y-2">
                    <label className="text-sm font-medium text-slate-900 dark:text-slate-200">Email Address</label>
                    <input
                        type="email"
                        value={profile.email}
                        onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    />
                </div>
                <div className="md:col-span-2 space-y-2">
                    <label className="text-sm font-medium text-slate-900 dark:text-slate-200">Bio</label>
                    <textarea rows={4} className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none" placeholder="Tell us a little about yourself..."></textarea>
                </div>
            </div>

            <div className="pt-4 flex justify-end border-t border-slate-100 dark:border-slate-800">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 bg-primary text-white px-6 py-2.5 rounded-lg hover:bg-blue-600 transition-colors shadow-lg shadow-blue-500/25 font-medium"
                >
                    <Save className="w-4 h-4" /> Save Changes
                </button>
            </div>
        </div>
    );
}

function NotificationSettings() {
    return (
        <div className="p-8 space-y-8">
            <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Email Notifications</h3>
                <div className="space-y-4">
                    {[
                        { label: "Grading completed", desc: "Receive an email when AI finishes grading a batch." },
                        { label: "New student submission", desc: "Get notified when a student uploads a new file." },
                        { label: "Weekly report", desc: "A summary of class performance every Monday." },
                        { label: "System updates", desc: "News about GradeWise features and maintenance." }
                    ].map((item, i) => (
                        <div key={i} className="flex items-center justify-between py-4 border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/30 -mx-4 px-4 rounded-lg transition-colors">
                            <div>
                                <p className="font-medium text-slate-900 dark:text-slate-200">{item.label}</p>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{item.desc}</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" defaultChecked={i < 2} className="sr-only peer" />
                                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/10 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                            </label>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function SecuritySettings() {
    return (
        <div className="p-8 space-y-8">
            <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">Password & Authentication</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Update your password or enable clear two-factor authentication.</p>

                <div className="space-y-4">
                    <button className="w-full flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left group">
                        <div className="flex items-center gap-4">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-primary">
                                <Lock className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="font-medium text-slate-900 dark:text-white group-hover:text-primary transition-colors">Change Password</p>
                                <p className="text-sm text-slate-500 dark:text-slate-400">Last changed 3 months ago</p>
                            </div>
                        </div>
                        <span className="px-3 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700">Update</span>
                    </button>

                    <button className="w-full flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left group">
                        <div className="flex items-center gap-4">
                            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">
                                <Smartphone className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="font-medium text-slate-900 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">Two-Factor Authentication</p>
                                <p className="text-sm text-slate-500 dark:text-slate-400">Add an extra layer of security</p>
                            </div>
                        </div>
                        <span className="px-3 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded border border-green-200 dark:border-green-800/50">Enabled</span>
                    </button>
                </div>
            </div>

            <div className="pt-8 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Active Sessions</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <div className="flex items-center gap-4">
                            <Monitor className="w-5 h-5 text-slate-500" />
                            <div>
                                <p className="font-medium text-slate-900 dark:text-white">Windows 11 • Chrome</p>
                                <p className="text-xs text-slate-500">192.168.1.102 • Current Session</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-sm text-green-600 dark:text-green-400 font-medium">Active</span>
                        </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-900/30 border border-slate-100 dark:border-slate-800 rounded-lg">
                        <div className="flex items-center gap-4">
                            <Smartphone className="w-5 h-5 text-slate-500" />
                            <div>
                                <p className="font-medium text-slate-900 dark:text-white">iPhone 14 Pro • Safari</p>
                                <p className="text-xs text-slate-500">London, UK • 2 hours ago</p>
                            </div>
                        </div>
                        <button className="p-2 text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors">
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            <div className="pt-8 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-semibold text-red-600 dark:text-red-500 mb-2">Danger Zone</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Once you delete your account, there is no going back. Please be certain.</p>
                <button className="px-5 py-2.5 bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/30 rounded-lg font-medium hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors text-sm">
                    Delete Account
                </button>
            </div>
        </div>
    );
}

function PreferenceSettings() {
    const { theme, setTheme, resolvedTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    return (
        <div className="p-8 space-y-8">
            <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Start-up & Appearance</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button
                        onClick={() => setTheme("system")}
                        className={`p-4 rounded-xl border transition-all relative group overflow-hidden text-left ${theme === 'system'
                            ? 'border-primary bg-blue-50/50 dark:bg-blue-900/20 ring-1 ring-primary'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                            }`}
                    >
                        {theme === 'system' && (
                            <div className="absolute top-2 right-2 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                                <Shield className="w-3 h-3 text-white fill-current" />
                            </div>
                        )}
                        <Monitor className={`w-8 h-8 mb-3 ${theme === 'system' ? 'text-primary' : 'text-slate-500'}`} />
                        <p className="font-medium text-slate-900 dark:text-white">System Default</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Follows your OS theme settings
                            {mounted && <span className="block text-xs opacity-70 font-semibold mt-1">(Detected: {resolvedTheme === 'dark' ? 'Dark' : 'Light'})</span>}
                        </p>
                    </button>

                    <button
                        onClick={() => setTheme("light")}
                        className={`p-4 rounded-xl border transition-all relative group overflow-hidden text-left ${theme === 'light'
                            ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-900/10 ring-1 ring-amber-500'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                            }`}
                    >
                        {theme === 'light' && (
                            <div className="absolute top-2 right-2 w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center">
                                <Shield className="w-3 h-3 text-white fill-current" />
                            </div>
                        )}
                        <Sun className={`w-8 h-8 mb-3 ${theme === 'light' ? 'text-amber-500' : 'text-slate-500'}`} />
                        <p className="font-medium text-slate-900 dark:text-white">Light Mode</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Always use light theme</p>
                    </button>

                    <button
                        onClick={() => setTheme("dark")}
                        className={`p-4 rounded-xl border transition-all relative group overflow-hidden text-left ${theme === 'dark'
                            ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/20 ring-1 ring-indigo-500'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                            }`}
                    >
                        {theme === 'dark' && (
                            <div className="absolute top-2 right-2 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center">
                                <Shield className="w-3 h-3 text-white fill-current" />
                            </div>
                        )}
                        <Moon className={`w-8 h-8 mb-3 ${theme === 'dark' ? 'text-indigo-500' : 'text-slate-500'}`} />
                        <p className="font-medium text-slate-900 dark:text-white">Dark Mode</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Always use dark theme</p>
                    </button>
                </div>
            </div>

            <div className="pt-8 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Localization</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900 dark:text-slate-200">Language</label>
                        <select className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                            <option>English (United States)</option>
                            <option>Spanish (Español)</option>
                            <option>French (Français)</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900 dark:text-slate-200">Timezone</label>
                        <select className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                            <option>(GMT-08:00) Pacific Time</option>
                            <option>(GMT-05:00) Eastern Time</option>
                            <option>(GMT+00:00) UTC</option>
                            <option>(GMT+01:00) London</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                <button className="flex items-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-6 py-2.5 rounded-lg hover:opacity-90 transition-opacity font-medium">
                    <Save className="w-4 h-4" /> Save Preferences
                </button>
            </div>
        </div>
    )
}

