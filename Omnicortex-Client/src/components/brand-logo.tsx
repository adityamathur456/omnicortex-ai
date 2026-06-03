type BrandLogoProps = {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  light?: boolean;
};

const sizes = {
  sm: {
    mark: 'h-8 w-8',
    wordmark: 'h-7 w-auto',
  },
  md: {
    mark: 'h-9 w-9',
    wordmark: 'h-8 w-auto',
  },
  lg: {
    mark: 'h-10 w-10',
    wordmark: 'h-9 w-auto',
  },
};

export function BrandLogo({
  size = 'md',
  showText = true,
  light = false,
}: BrandLogoProps) {
  const palette = light
    ? {
        bg: '#FFFFFF',
        ink: '#0F172A',
        sub: '#64748B',
      }
    : {
        bg: '#0F172A',
        ink: '#0F172A',
        sub: '#64748B',
      };

  return (
    <div className="inline-flex items-center gap-3">
      <svg
        viewBox="0 0 48 48"
        className={sizes[size].mark}
        role="img"
        aria-label="Omnicortex AI logo"
      >
        <rect width="48" height="48" rx="12" fill={light ? '#FFFFFF' : '#060B16'} />
        <rect
          x="2"
          y="2"
          width="44"
          height="44"
          rx="10"
          stroke={light ? '#D8E2F1' : '#1E293B'}
          strokeWidth="1"
        />
        <circle cx="24" cy="24" r="14.5" fill="url(#omnicortexGlow)" fillOpacity="0.18" />
        <circle cx="24" cy="24" r="13.25" stroke="url(#omnicortexRing)" strokeWidth="3" />
        <circle
          cx="24"
          cy="24"
          r="9"
          fill={light ? '#F8FAFC' : '#09101D'}
          stroke={light ? '#0F766E' : '#9FFFE0'}
          strokeWidth="1.4"
        />
        <path
          d="M24 15L27.187 20.4253L33 21.6649L29.076 25.6421L29.6584 31.4635L24 28.6342L18.3416 31.4635L18.924 25.6421L15 21.6649L20.813 20.4253L24 15Z"
          fill="url(#omnicortexCore)"
        />
        <circle
          cx="24"
          cy="24"
          r="2.8"
          fill={light ? '#FFFFFF' : '#07111D'}
          stroke={light ? '#0F172A' : '#E8FFF8'}
          strokeWidth="1"
        />
        <path d="M24 5L26.5 9.25L24 13.5L21.5 9.25L24 5Z" fill="#7CFFB2" />
        <path d="M43 24L38.75 26.5L34.5 24L38.75 21.5L43 24Z" fill="#55E6FF" />
        <path d="M24 43L21.5 38.75L24 34.5L26.5 38.75L24 43Z" fill="#8B7CFF" />
        <path d="M5 24L9.25 21.5L13.5 24L9.25 26.5L5 24Z" fill="#8BFFDA" />
        <defs>
          <linearGradient
            id="omnicortexRing"
            x1="10.5"
            y1="11"
            x2="37"
            y2="37.5"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#7CFFB2" />
            <stop offset="0.48" stopColor="#55E6FF" />
            <stop offset="1" stopColor="#8B7CFF" />
          </linearGradient>
          <radialGradient
            id="omnicortexGlow"
            cx="0"
            cy="0"
            r="1"
            gradientUnits="userSpaceOnUse"
            gradientTransform="translate(24 24) rotate(90) scale(15.5)"
          >
            <stop stopColor="#55E6FF" />
            <stop offset="1" stopColor="#55E6FF" stopOpacity="0" />
          </radialGradient>
          <linearGradient
            id="omnicortexCore"
            x1="17"
            y1="17"
            x2="31"
            y2="31"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#B2FFC5" />
            <stop offset="0.5" stopColor="#58F5FF" />
            <stop offset="1" stopColor="#A48BFF" />
          </linearGradient>
        </defs>
      </svg>

      {showText ? (
        <svg
          viewBox="0 0 210 36"
          className={sizes[size].wordmark}
          role="img"
          aria-label="Omnicortex AI wordmark"
        >
          <text
            x="0"
            y="17"
            fill={light ? '#FFFFFF' : palette.ink}
            fontFamily="Inter, ui-sans-serif, system-ui, sans-serif"
            fontSize="18"
            fontWeight="700"
          >
            Omnicortex
          </text>
          <text
            x="0"
            y="31"
            fill={light ? 'rgba(255,255,255,0.72)' : palette.sub}
            fontFamily="Inter, ui-sans-serif, system-ui, sans-serif"
            fontSize="10"
            fontWeight="600"
            letterSpacing="1.4"
          >
            MULTIMODAL AGENT
          </text>
        </svg>
      ) : null}
    </div>
  );
}
