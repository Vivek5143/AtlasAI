import {
  ArrowRight,
  Eye,
  EyeOff,
  Globe2,
  LineChart,
  Sparkles,
} from "lucide-react";
import { useState, type ReactElement } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Logo } from "@/components/logo";
import { useAuth } from "@/contexts/auth-context";

const highlights = [
  "AI companies and sector intelligence",
  "Problem mapping across live market data",
  "News monitoring tied to tracked companies",
  "AI-powered research through Ask AtlasAI",
];

function ContourPattern(): ReactElement {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 600 600"
      className="absolute inset-0 h-full w-full opacity-60"
      preserveAspectRatio="none"
    >
      <path
        d="M40 110C150 70 232 132 330 102C428 72 496 86 560 52"
        fill="none"
        stroke="rgba(33,73,56,0.18)"
        strokeWidth="1.5"
      />
      <path
        d="M20 178C146 144 222 214 348 182C442 158 514 166 590 126"
        fill="none"
        stroke="rgba(33,73,56,0.16)"
        strokeWidth="1.5"
      />
      <path
        d="M28 270C148 236 254 308 362 276C456 250 522 262 586 232"
        fill="none"
        stroke="rgba(33,73,56,0.18)"
        strokeWidth="1.5"
      />
      <path
        d="M40 360C154 324 244 394 352 366C458 338 508 346 570 318"
        fill="none"
        stroke="rgba(33,73,56,0.16)"
        strokeWidth="1.5"
      />
      <path
        d="M24 454C140 418 244 492 356 456C454 424 508 438 584 406"
        fill="none"
        stroke="rgba(33,73,56,0.14)"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function EditorialGrid(): ReactElement {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 opacity-40"
      style={{
        backgroundImage:
          "linear-gradient(rgba(33,73,56,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(33,73,56,0.08) 1px, transparent 1px)",
        backgroundPosition: "center",
        backgroundSize: "34px 34px",
      }}
    />
  );
}

export function LoginPage(): ReactElement {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, user } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setErrorMsg(null);
    if (!email || !password) {
      setErrorMsg("Please enter both email/username and password.");
      return;
    }
    try {
      setIsSubmitting(true);
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Sign in failed. Check your credentials.";
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f3efe6] px-4 py-5 text-slate-900 dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute left-[-6rem] top-[-5rem] h-56 w-56 rounded-full bg-emerald-900/12 blur-3xl dark:bg-emerald-400/12" />
      <div className="pointer-events-none absolute bottom-[-6rem] right-[-3rem] h-64 w-64 rounded-full bg-stone-400/25 blur-3xl dark:bg-slate-900/70" />

      <div className="relative mx-auto grid min-h-[calc(100vh-2.5rem)] w-full max-w-[92rem] overflow-hidden rounded-[2.4rem] border border-[#d7ddd1] bg-[linear-gradient(135deg,_rgba(255,255,255,0.9)_0%,_rgba(241,244,238,0.96)_100%)] shadow-[0_38px_120px_-56px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-[linear-gradient(135deg,_rgba(15,23,42,0.96)_0%,_rgba(2,6,23,0.98)_100%)] lg:grid-cols-[minmax(0,1.18fr)_minmax(24rem,30rem)]">
        <section className="relative flex flex-col justify-between overflow-hidden px-6 py-8 sm:px-8 sm:py-10 lg:px-12 lg:py-12">
          <ContourPattern />
          <EditorialGrid />

          <div className="relative">
            <Logo />
          </div>

          <div className="relative max-w-2xl py-10 lg:py-16">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.26em] text-[#2f6b51] dark:text-emerald-300">
              Premium AI Market Intelligence
            </p>
            <h1 className="mt-5 font-editorial text-4xl leading-none tracking-[-0.07em] text-slate-950 dark:text-white sm:text-5xl lg:text-[4.25rem]">
              Understand where AI is transforming industries.
            </h1>
            <p className="mt-6 max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-base">
              AtlasAI helps teams explore AI companies, industry problems, sectors,
              market developments, and AI-powered research through Ask AtlasAI.
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {highlights.map((item) => (
                <div
                  key={item}
                  className="rounded-[1.5rem] border border-[#d7ddd1] bg-white/75 px-4 py-4 text-sm text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-200"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="relative grid gap-4 sm:grid-cols-3">
            {[
              {
                icon: <Globe2 className="h-5 w-5" aria-hidden="true" />,
                label: "Global coverage",
              },
              {
                icon: <LineChart className="h-5 w-5" aria-hidden="true" />,
                label: "Structured analytics",
              },
              {
                icon: <Sparkles className="h-5 w-5" aria-hidden="true" />,
                label: "AI-assisted research",
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-[1.5rem] border border-[#d7ddd1] bg-white/80 px-4 py-4 dark:border-slate-800 dark:bg-slate-950/55"
              >
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-[#d7ddd1] bg-[#edf4ee] text-[#214938] dark:border-slate-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                  {item.icon}
                </div>
                <p className="mt-4 text-sm font-medium text-slate-700 dark:text-slate-200">
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </section>

        <aside className="flex items-center border-t border-[#d7ddd1] bg-white/80 px-4 py-6 dark:border-slate-800 dark:bg-slate-950/70 sm:px-6 lg:border-l lg:border-t-0 lg:px-8">
          <div className="mx-auto w-full max-w-md rounded-[2rem] border border-[#d7ddd1] bg-[#fcfaf6] p-6 shadow-[0_28px_70px_-50px_rgba(15,23,42,0.45)] dark:border-slate-800 dark:bg-slate-950 sm:p-8">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
              Welcome back
            </p>
            <h2 className="mt-4 font-editorial text-4xl tracking-[-0.05em] text-slate-950 dark:text-white">
              Sign in to AtlasAI
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-500 dark:text-slate-400">
              Enter your email/username and password to access your market-intelligence workspace.
            </p>

            {errorMsg ? (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
                {errorMsg}
              </div>
            ) : null}

            {user ? (
              <div className="mt-6 rounded-[1.5rem] border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
                <p>Signed in as <strong>{user.username}</strong> ({user.role})</p>
                <Link
                  to="/"
                  className="mt-3 inline-flex items-center gap-2 font-medium text-emerald-700 hover:underline dark:text-emerald-200"
                >
                  <span>Go to Workspace</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ) : (
              <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <label htmlFor="login-email" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Email / Username
                  </label>
                  <input
                    id="login-email"
                    type="text"
                    autoComplete="username"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="name@company.com"
                    className="h-12 w-full rounded-2xl border border-[#cfd8d1] bg-white px-4 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="login-password" className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter your password"
                      className="h-12 w-full rounded-2xl border border-[#cfd8d1] bg-white px-4 pr-12 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((current) => !current)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      className="absolute right-2 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-[#edf4ee] hover:text-[#214938] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" aria-hidden="true" />
                      ) : (
                        <Eye className="h-4 w-4" aria-hidden="true" />
                      )}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full bg-[#214938] px-5 text-sm font-medium text-[#f6f2e8] transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  <span>{isSubmitting ? "Signing in..." : "Sign In"}</span>
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
              </form>
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}
