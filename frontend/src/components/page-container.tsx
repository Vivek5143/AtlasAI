import type { PropsWithChildren, ReactElement } from "react";

type PageContainerProps = PropsWithChildren<{
  subtitle: string;
  title: string;
}>;

export function PageContainer({
  children,
  subtitle,
  title,
}: PageContainerProps): ReactElement {
  return (
    <section className="mx-auto flex w-full max-w-[92rem] flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <header className="space-y-3">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
          AtlasAI
        </p>
        <h1 className="font-editorial text-4xl tracking-[-0.05em] text-slate-950 dark:text-white">
          {title}
        </h1>
        <p className="max-w-3xl text-sm leading-7 text-slate-500 dark:text-slate-400">
          {subtitle}
        </p>
      </header>
      {children}
    </section>
  );
}
