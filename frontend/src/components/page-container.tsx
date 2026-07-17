import type { PropsWithChildren, ReactElement } from "react";

type PageContainerProps = PropsWithChildren<{
  title: string;
  subtitle: string;
}>;

export function PageContainer({
  children,
  subtitle,
  title,
}: PageContainerProps): ReactElement {
  return (
    <section className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {title}
        </h1>
        <p className="max-w-2xl text-sm text-slate-500 dark:text-slate-400">
          {subtitle}
        </p>
      </header>
      {children}
    </section>
  );
}
