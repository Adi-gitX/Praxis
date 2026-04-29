import Link from "next/link";

import { Wordmark } from "@/components/wordmark";

export default function NotFound() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 text-center px-6">
      <Wordmark size="lg" />
      <p className="label">404 · route not registered</p>
      <Link href="/" className="text-sm mono text-accent hover:text-accent-hover">
        return to landing →
      </Link>
    </main>
  );
}
