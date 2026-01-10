
import { ImageResponse } from 'next/og';

// Image metadata
export const size = {
    width: 32,
    height: 32,
};
export const contentType = 'image/svg+xml'; // Force SVG for animation support

// Generate the icon
export default function Icon() {
    return new ImageResponse(
        (
            <svg
                width="32"
                height="32"
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >
                {/* CSS for Animation */}
                <style>
                    {`
            @keyframes float {
              0%, 100% { transform: translateY(0); }
              50% { transform: translateY(-5px); }
            }
            @keyframes orbit {
              0% { transform: rotate(0deg) translateX(35px) rotate(0deg); }
              100% { transform: rotate(360deg) translateX(35px) rotate(-360deg); }
            }
            @keyframes pulse {
              0%, 100% { opacity: 0.8; r: 6; }
              50% { opacity: 1; r: 8; }
            }
          `}
                </style>

                {/* 3D Cube Base */}
                <g style={{ animation: 'float 3s ease-in-out infinite' }}>
                    {/* Right Face */}
                    <path d="M50 55 L85 35 V75 L50 95 Z" fill="#1e3a8a" />

                    {/* Left Face */}
                    <path d="M50 55 L15 35 V75 L50 95 Z" fill="#3b82f6" />

                    {/* Top Face */}
                    <path d="M50 55 L15 35 L50 15 L85 35 Z" fill="#93c5fd" />

                    {/* Cap Detail */}
                    <path d="M50 25 L30 35 L50 45 L70 35 Z" fill="white" fillOpacity="0.9" />
                </g>

                {/* Orbiting Spark */}
                {/* Note: In SVG favicons, simpler animations are more reliable. We simulate orbit with a group rotation */}
                <g transform="translate(50, 50)">
                    <g style={{ animation: 'orbit 4s linear infinite' }}>
                        <circle cx="0" cy="0" r="6" fill="#FDE047" style={{ animation: 'pulse 2s ease-in-out infinite' }} />
                    </g>
                </g>
            </svg>
        ),
        {
            ...size,
        }
    );
}
