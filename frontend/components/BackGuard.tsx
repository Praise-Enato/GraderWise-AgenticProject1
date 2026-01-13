
"use client";

import { useEffect, useState } from "react";
import { UnsavedChangesModal } from "@/components/UnsavedChangesModal";

export function BackGuard() {
    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        // 1. Push a dummy state so we have something to "pop"
        history.pushState(null, "", window.location.href);

        const handlePopState = (event: PopStateEvent) => {
            // 2. Prevent navigation by pushing state again immediately
            history.pushState(null, "", window.location.href);
            // 3. Show the warning modal
            setShowModal(true);
        };

        window.addEventListener("popstate", handlePopState);

        return () => {
            window.removeEventListener("popstate", handlePopState);
        };
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('userProfile');
        window.location.href = '/signup';
    };

    return (
        <UnsavedChangesModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            onConfirm={handleLogout}
        />
    );
}
