import type { ReactNode } from 'react';
import { BrandLogo } from '@/components/brand-logo';

export function AuthShell({
  title,
  subtitle,
  children,
  sideTitle,
  sideText,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  sideTitle: string;
  sideText: string;
}) {
  return (
    <div className="grid min-h-screen bg-surface lg:grid-cols-[1.1fr_0.9fr]">
      <section className="hidden bg-ink px-10 py-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="inline-flex w-fit rounded-xl border border-white/10 bg-white/5 px-3 py-2">
          <BrandLogo size="sm" light />
        </div>
        <div className="max-w-xl space-y-5">
          <p className="text-sm uppercase tracking-[0.16em] text-white/50">
            Applied AI workspace
          </p>
          <h2 className="text-4xl font-semibold">{sideTitle}</h2>
          <p className="text-base text-white/70">{sideText}</p>
        </div>
        <p className="text-sm text-white/40">
          Resume drafting, image generation, and medical analysis in one product surface.
        </p>
      </section>

      <section className="flex items-center justify-center px-4 py-10 sm:px-6 lg:px-10">
        <div className="w-full max-w-md rounded-lg border border-line bg-white p-8 shadow-panel">
          <div className="mb-8 space-y-2">
            <div className="inline-flex rounded-xl bg-accentSoft px-3 py-2 lg:hidden">
              <BrandLogo size="sm" />
            </div>
            <h1 className="text-2xl font-semibold text-ink">{title}</h1>
            <p className="text-sm text-muted">{subtitle}</p>
          </div>
          {children}
        </div>
      </section>
    </div>
  );
}
