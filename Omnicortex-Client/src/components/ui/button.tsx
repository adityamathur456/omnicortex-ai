import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { LoaderCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  loading?: boolean;
  fullWidth?: boolean;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-ink text-white hover:bg-slate-800 focus-visible:ring-ink/20',
  secondary:
    'bg-white text-ink border border-line hover:bg-slate-50 focus-visible:ring-slate-200',
  ghost:
    'bg-transparent text-muted hover:bg-slate-100 focus-visible:ring-slate-200',
  danger:
    'bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-200',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      children,
      variant = 'primary',
      loading = false,
      fullWidth = false,
      disabled,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-60',
          variants[variant],
          fullWidth && 'w-full',
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
        <span>{children}</span>
      </button>
    );
  },
);

Button.displayName = 'Button';
