import type { ReactElement } from "react";

import { PageContainer } from "@/components/page-container";

export function SectorsPage(): ReactElement {
  return (
    <PageContainer
      title="Sectors"
      subtitle="A placeholder shell for sector organization and company grouping."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-medium text-slate-950 dark:text-white">
          Sectors placeholder
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Sector breakdowns and filtering experiences are planned next.
        </p>
      </section>
    </PageContainer>
  );
}
