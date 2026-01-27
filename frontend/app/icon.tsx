
import { ImageResponse } from 'next/og';

// Image metadata
export const size = {
    width: 32,
    height: 32,
};
export const contentType = 'image/png';

// Generate the icon
export default function Icon() {
    return new ImageResponse(
        (
            <div
                style={{
                    fontSize: 24,
                    background: 'transparent',
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <svg
                    width="32"
                    height="32"
                    viewBox="0 0 100 100"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    {/* 3D Cube Base */}
                    <g>
                        {/* Right Face */}
                        <path d="M50 55 L85 35 V75 L50 95 Z" fill="#1e3a8a" />

                        {/* Left Face */}
                        <path d="M50 55 L15 35 V75 L50 95 Z" fill="#3b82f6" />

                        {/* Top Face */}
                        <path d="M50 55 L15 35 L50 15 L85 35 Z" fill="#93c5fd" />

                        {/* Cap Detail */}
                        <path d="M50 25 L30 35 L50 45 L70 35 Z" fill="white" fillOpacity="0.9" />
                    </g>

                    {/* Simple Spark (Static) */}
                    <circle cx="85" cy="50" r="6" fill="#FDE047" />
                </svg>
            </div>
        ),
        {
            ...size,
        }
    );
}
