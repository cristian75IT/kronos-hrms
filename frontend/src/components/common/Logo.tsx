/**
 * KRONOS - Common Logo Component
 */


interface LogoProps {
    className?: string;
    size?: number | string;
}

export function Logo({ className, size = 40 }: LogoProps) {
    return (
        <div
            className={`relative flex items-center justify-center ${className}`}
            style={{ width: size, height: size }}
        >
            <svg
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full"
            >
                <defs>
                    <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#4F46E5" />
                        <stop offset="100%" stopColor="#7C3AED" />
                    </linearGradient>
                    <filter id="logo-shadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
                        <feOffset dx="0" dy="2" result="offsetblur" />
                        <feComponentTransfer>
                            <feFuncA type="linear" slope="0.3" />
                        </feComponentTransfer>
                        <feMerge>
                            <feMergeNode />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Background Shape - A modern hexagonal circle */}
                <path
                    d="M50 5C25.147 5 5 25.147 5 50C5 74.853 25.147 95 50 95C74.853 95 95 74.853 95 50"
                    stroke="url(#logo-gradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    className="opacity-20"
                />

                {/* The "K" Integrated with Time and Growth */}
                <g filter="url(#logo-shadow)">
                    {/* Main vertical bar (The trunk/back of K) - Styled as a stylized figure */}
                    <rect x="32" y="25" width="10" height="50" rx="5" fill="url(#logo-gradient)" />

                    {/* Upper arm of K - Styled as a clock hand or growth arrow */}
                    <path
                        d="M37 50C37 50 55 45 65 30C68 25.5 63 22 60 25L37 45"
                        fill="url(#logo-gradient)"
                    />

                    {/* Lower arm of K - Styled as a support or path */}
                    <path
                        d="M37 50L65 75C68 78 72 75 70 70C65 60 37 50 37 50Z"
                        fill="url(#logo-gradient)"
                    />

                    {/* Central Connecting Node - The "Heart" of HR */}
                    <circle cx="42" cy="50" r="7" fill="white" />
                    <circle cx="42" cy="50" r="4" fill="url(#logo-gradient)" />

                    {/* External Nodes - Representing interconnected people */}
                    <circle cx="65" cy="30" r="6" fill="url(#logo-gradient)" />
                    <circle cx="68" cy="73" r="6" fill="url(#logo-gradient)" />
                </g>
            </svg>
        </div>
    );
}

export default Logo;
