import type { ReactElement } from "react";

import { PageContainer } from "@/components/page-container";

export function CompaniesPage(): ReactElement {
  return (
    <PageContainer
      title="Companies"
      subtitle="A placeholder shell for the company directory and profile workflows."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-medium text-slate-950 dark:text-white">
          Companies placeholder
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Tables, search, filters, and detail views will be introduced later.
        </p>
      </section>
    </PageContainer>
  );
}
