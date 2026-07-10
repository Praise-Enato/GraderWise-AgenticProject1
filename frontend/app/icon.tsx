import { ImageResponse } from 'next/og';

// Favicon — the standalone graduation cap (no container), matching the Logo.
export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
        }}
      >
        <svg width="30" height="30" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* head */}
          <path d="M32 50 L50 58 L68 50 L68 66 C68 72 60 75.5 50 75.5 C40 75.5 32 72 32 66 Z" fill="#0f766e" />
          {/* mortarboard */}
          <path d="M50 20 L94 40 L50 60 L6 40 Z" fill="#10b981" />
          {/* button + tassel */}
          <circle cx="50" cy="40" r="3" fill="#e0a92e" />
          <path d="M50 40 C 70 40, 79 48, 79 62" stroke="#e0a92e" strokeWidth="2.6" strokeLinecap="round" fill="none" />
          <circle cx="79" cy="64" r="3.8" fill="#f5c451" />
        </svg>
      </div>
    ),
    { ...size },
  );
}
