import type { ReactElement } from "react";
import { createBrowserRouter, Outlet } from "react-router-dom";

import { AppLayout } from "@/layouts/app-layout";
import { CompaniesPage } from "@/pages/companies-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { NewsPage } from "@/pages/news-page";
import { ProblemsPage } from "@/pages/problems-page";
import { SectorsPage } from "@/pages/sectors-page";

function RootLayout(): ReactElement {
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "companies",
        element: <CompaniesPage />,
      },
      {
        path: "problems",
        element: <ProblemsPage />,
      },
      {
        path: "sectors",
        element: <SectorsPage />,
      },
      {
        path: "news",
        element: <NewsPage />,
      },
    ],
  },
]);
