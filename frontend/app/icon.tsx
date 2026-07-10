import { ImageResponse } from 'next/og';

// Favicon — matches the Logo: a graduation cap on a blue→emerald rounded tile.
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
          borderRadius: 8,
          background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 55%, #0d9488 100%)',
        }}
      >
        <svg width="22" height="22" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M50 28 L82 43 L50 58 L18 43 Z" fill="#ffffff" />
          <path d="M35 50.5 L50 57.5 L65 50.5 V61 C65 66.5 56 69 50 69 C44 69 35 66.5 35 61 Z" fill="#ffffff" />
          <path d="M72 46 V60" stroke="#ffffff" strokeWidth="2.6" strokeLinecap="round" />
          <circle cx="72" cy="63" r="3.4" fill="#fde68a" />
        </svg>
      </div>
    ),
    { ...size },
  );
}
