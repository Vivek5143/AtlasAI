import type { ReactElement } from "react";

import { PageContainer } from "@/components/page-container";

export function NewsPage(): ReactElement {
  return (
    <PageContainer
      title="News"
      subtitle="A placeholder shell for recent articles and company news coverage."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-medium text-slate-950 dark:text-white">
          News placeholder
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Feeds, article cards, and filters will be implemented in a later pass.
        </p>
      </section>
    </PageContainer>
  );
}
