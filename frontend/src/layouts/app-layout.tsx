import type { PropsWithChildren, ReactElement } from "react";

import { AppShell } from "@/components/app-shell";

export function AppLayout({ children }: PropsWithChildren): ReactElement {
  return <AppShell>{children}</AppShell>;
}
