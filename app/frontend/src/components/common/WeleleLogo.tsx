import React from 'react';

interface WeleleLogoProps {
  variant?: 'full' | 'horizontal' | 'icon' | 'corporate' | 'stacked';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'splash';
  showTagline?: boolean;
  className?: string;
}

/**
 * Authentic Welele™ Logo Mark (Official Ribbon 'W' with Play Button & Radiant Energy Sparks)
 */
export const WeleleIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 38,
  className = '',
}) => {
  return (
    <img
      src="/brand/welele_mark.png"
      alt="Welele Icon Mark"
      width={size}
      height={size}
      style={{ width: size, height: size }}
      className={`object-contain shrink-0 drop-shadow-md transition-transform ${className}`}
    />
  );
};

/**
 * 3-Person Connection Icon for Corporate Master (Welele Media™)
 */
export const WeleleConnectionIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 28,
  className = '',
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 ${className}`}
    >
      <defs>
        <linearGradient id="conn-grad" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFA000" />
          <stop offset="50%" stopColor="#FF6500" />
          <stop offset="100%" stopColor="#D8005A" />
        </linearGradient>
      </defs>
      <circle cx="24" cy="14" r="5" stroke="url(#conn-grad)" strokeWidth="3" />
      <path
        d="M16 32C16 27.5817 19.5817 24 24 24C28.4183 24 32 27.5817 32 32"
        stroke="url(#conn-grad)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="12" cy="18" r="3.5" stroke="url(#conn-grad)" strokeWidth="2.5" />
      <path
        d="M6 34C6 30.5 8.5 28 12 28C13.5 28 14.8 28.5 15.8 29.3"
        stroke="url(#conn-grad)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="36" cy="18" r="3.5" stroke="url(#conn-grad)" strokeWidth="2.5" />
      <path
        d="M32.2 29.3C33.2 28.5 34.5 28 36 28C39.5 28 42 30.5 42 34"
        stroke="url(#conn-grad)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
};

export const WeleleLogo: React.FC<WeleleLogoProps> = ({
  variant = 'full',
  size = 'md',
  showTagline = true,
  className = '',
}) => {
  const sizeMap = {
    xs: { h: 'h-6', iconSize: 24, stackedH: 'h-12' },
    sm: { h: 'h-8 sm:h-9', iconSize: 32, stackedH: 'h-16' },
    md: { h: 'h-10 sm:h-11', iconSize: 42, stackedH: 'h-20' },
    lg: { h: 'h-12 sm:h-14', iconSize: 54, stackedH: 'h-28' },
    xl: { h: 'h-16 sm:h-20', iconSize: 72, stackedH: 'h-36' },
    '2xl': { h: 'h-24 sm:h-28', iconSize: 96, stackedH: 'h-48' },
    splash: { h: 'h-28 sm:h-36', iconSize: 128, stackedH: 'h-36 sm:h-48 md:h-60' },
  };

  const { h, iconSize, stackedH } = sizeMap[size];

  // 1. ICON ONLY
  if (variant === 'icon') {
    return <WeleleIcon size={iconSize} className={className} />;
  }

  // 2. CORPORATE MASTER (WELELE MEDIA™ | It's about connection.)
  if (variant === 'corporate') {
    return (
      <div className={`flex items-center gap-2.5 ${className}`}>
        <div className="w-10 h-10 rounded-[7px] bg-welele-surface-2 border border-white/10 flex items-center justify-center p-1.5 shadow-md">
          <WeleleConnectionIcon size={24} />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold tracking-tight text-white text-sm sm:text-base uppercase font-sans">
              WELELE MEDIA
            </span>
            <span className="text-[10px] text-welele-orange font-bold">™</span>
          </div>
          <p className="text-[11px] text-[#A8A5A1] font-medium tracking-wide">
            It's about connection.
          </p>
        </div>
      </div>
    );
  }

  // 3. STACKED VERTICAL LOCKUP (For Splash / Login / Brand Hero)
  if (variant === 'stacked') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <img
          src="/brand/welele_full_lockup.png"
          alt="Welele™ — Stories That Move You"
          className={`${stackedH} w-auto object-contain drop-shadow-2xl`}
        />
      </div>
    );
  }

  // 4. HORIZONTAL LOCKUP (Header / Top Navigation)
  return (
    <div className={`flex items-center ${className}`}>
      <img
        src="/brand/welele_horizontal_lockup.png"
        alt="Welele™ — Stories That Move You"
        className={`${h} w-auto object-contain drop-shadow-lg`}
      />
    </div>
  );
};
